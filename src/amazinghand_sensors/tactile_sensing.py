"""
tactile_sensing.py — Unified FSR tactile sensing interface + real-time logger.

Includes:
  - TactileSensor  hardware driver (ADS1256 via ads1256.py)
  - DataLogger      auto-timestamped CSV output
  - Real-time display: PyQtGraph GUI (default) or terminal-only (--terminal)

Hardware config lives in config.toml; low-level driver lives in ads1256.py.
"""

import argparse
import csv
import sys
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from loguru import logger

import amazinghand_sensors.ads1256 as _ads1256_mod
from amazinghand_sensors.ads1256 import ADS1256
from amazinghand_sensors._config import load_config

# ---------------------------------------------------------------------------
# Load shared settings from config.toml
# ---------------------------------------------------------------------------

_TOML       = load_config()
_SENSOR_CFG = _TOML["sensor"]
_LOG_CFG    = _TOML["logging"]
_VIZ_CFG    = _TOML["visualization"]

# Log dir is relative to the current working directory so it lands next to
# wherever the user invokes the script, not inside the installed package.
_LOG_DIR = Path(_LOG_CFG["log_dir"])

_MAX_CONSECUTIVE_POLL_ERRORS = 10


# ---------------------------------------------------------------------------
# loguru — configured lazily in _configure_logging() called from main()
# ---------------------------------------------------------------------------

def _configure_logging() -> None:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = _LOG_DIR / f"tactile_{datetime.now():%Y%m%d_%H%M%S}.log"
    logger.remove()
    logger.add(
        sys.stderr, level="INFO", colorize=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    )
    logger.add(log_file, level="DEBUG", rotation="10 MB",
               format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}")
    logger.info("Log file: {}", log_file)


# ---------------------------------------------------------------------------
# TactileReading
# ---------------------------------------------------------------------------

@dataclass
class TactileReading:
    sensor_time: float              # seconds since sensor.start()
    raw:         dict[str, int]     # signed raw ADC counts  {name: int}
    volts:       dict[str, float]   # voltage (V)            {name: float}
    force_norm:  dict[str, float]   # 0–1 normalised force   {name: float}

    def as_rows(self) -> list[dict]:
        """One dict per channel — long format for CSV / Bokeh."""
        return [
            {
                "sensor_time": round(self.sensor_time, 6),
                "channel":     name,
                "raw":         self.raw[name],
                "volts":       round(self.volts[name], 6),
                "force_norm":  round(self.force_norm[name], 4),
            }
            for name in self.raw
        ]


# ---------------------------------------------------------------------------
# TactileSensor
# ---------------------------------------------------------------------------

class TactileSensor:
    """
    Thread-safe tactile sensor interface for ADS1256.

    Parameters
    ----------
    channels : list[int] | None
        ADC input channels (0–7).
    channel_names : list[str] | None
        Human-readable labels aligned with *channels*.
    gain_key : str | None
        Key into the driver's GAIN dict.  None → config.toml default.
    drate_key : str | None
        Key into the driver's DRATE dict.  None → config.toml default.
    ref_voltage : float | None
        Override ADC reference voltage (V).  None → chip default.
    fsr_vcc : float
        Supply voltage across the FSR divider (V).
    fsr_r_fixed : float
        Fixed resistor (Ω) in the FSR voltage-divider.  0 = no force calc.
    polling_hz : float
        Background polling rate.  0 = manual reads only.
    on_reading : callable | None
        Callback fn(reading: TactileReading) invoked from the polling thread.
    """

    _DEFAULTS = dict(
        channels=_SENSOR_CFG["channels"],
        gain_key=_SENSOR_CFG["gain_key"],
        drate_key=_SENSOR_CFG["drate_key"],
        ref_voltage=_ads1256_mod.REF_VOLTAGE,
        adc_max=_ads1256_mod.ADC_MAX,
    )

    def __init__(
        self,
        channels:      list[int] | None                             = None,
        channel_names: list[str] | None                             = None,
        gain_key:      str | None                                   = None,
        drate_key:     str | None                                   = None,
        ref_voltage:   float | None                                 = None,
        fsr_vcc:       float                                        = _SENSOR_CFG["fsr_vcc"],
        fsr_r_fixed:   float                                        = _SENSOR_CFG["fsr_r_fixed"],
        polling_hz:    float                                        = _SENSOR_CFG["polling_hz"],
        on_reading:    Callable[[TactileReading], None] | None      = None,
    ):
        defaults = self._DEFAULTS
        self._channels  = list(channels) if channels is not None else list(defaults["channels"])
        self._names     = list(channel_names) if channel_names else [f"ch{c}" for c in self._channels]
        if len(self._names) != len(self._channels):
            raise ValueError("channel_names length must match channels length")

        self._gain_key   = gain_key   or defaults["gain_key"]
        self._drate_key  = drate_key  or defaults["drate_key"]
        self._ref_v      = ref_voltage if ref_voltage is not None else defaults["ref_voltage"]
        self._adc_max    = defaults["adc_max"]
        self._vcc        = fsr_vcc
        self._r_fixed    = fsr_r_fixed
        self._polling_hz = polling_hz
        self._on_reading = on_reading

        self._adc:    ADS1256 | None           = None
        self._lock    = threading.Lock()
        self._latest: TactileReading | None    = None
        self._t0:     float                    = 0.0
        self._thread: threading.Thread | None  = None
        self._running = False

        logger.info(
            "TactileSensor | channels={} names={} hz={}",
            self._channels, self._names, polling_hz,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Initialise hardware and start the background polling thread."""
        adc = ADS1256()
        adc.init(self._gain_key, self._drate_key)
        self._adc = adc
        self._t0  = time.perf_counter()

        if self._polling_hz > 0:
            self._running = True
            self._thread  = threading.Thread(
                target=self._poll_loop, daemon=True, name="TactileSensor-poll"
            )
            self._thread.start()
        logger.info("ADS1256 ready, polling at {}Hz", self._polling_hz)

    def stop(self) -> None:
        """Stop background thread and release hardware resources."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        if self._adc is not None:
            self._adc.exit()
        logger.info("TactileSensor stopped")

    def read(self) -> TactileReading:
        """
        Return a reading.  If the poller is running, returns the latest cached
        sample (zero latency).  Otherwise acquires the ADC synchronously.
        """
        if self._running and self._latest is not None:
            with self._lock:
                return self._latest
        return self._acquire()

    @property
    def latest(self) -> TactileReading | None:
        with self._lock:
            return self._latest

    @property
    def channel_names(self) -> list[str]:
        return list(self._names)

    def __enter__(self) -> "TactileSensor":
        self.start()
        return self

    def __exit__(self, *_) -> None:
        self.stop()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _acquire(self) -> TactileReading:
        if self._adc is None:
            raise RuntimeError("Call start() before reading")
        raw:   dict[str, int]   = {}
        volts: dict[str, float] = {}
        force: dict[str, float] = {}
        for ch, name in zip(self._channels, self._names):
            counts      = self._adc.get_channel_value(ch)
            v           = counts / self._adc_max * self._ref_v
            raw[name]   = counts
            volts[name] = round(v, 6)
            force[name] = self._to_force_norm(v)
        return TactileReading(
            sensor_time=time.perf_counter() - self._t0,
            raw=raw,
            volts=volts,
            force_norm=force,
        )

    def _to_force_norm(self, v: float) -> float:
        """FSR resistor-divider: Vout = Vcc * R_fixed / (R_fsr + R_fixed)."""
        if self._r_fixed <= 0 or v <= 0:
            return 0.0
        r_fsr = self._r_fixed * (self._vcc / v - 1.0)
        if r_fsr <= 0:
            return 1.0
        return min(1.0, self._r_fixed / r_fsr)

    def _poll_loop(self) -> None:
        interval = 1.0 / self._polling_hz
        consecutive_errors = 0
        while self._running:
            t0 = time.perf_counter()
            try:
                reading = self._acquire()
                with self._lock:
                    self._latest = reading
                consecutive_errors = 0
                if self._on_reading is not None:
                    self._on_reading(reading)
            except Exception as exc:
                consecutive_errors += 1
                logger.error("Poll error ({}/{}): {}", consecutive_errors,
                             _MAX_CONSECUTIVE_POLL_ERRORS, exc)
                if consecutive_errors >= _MAX_CONSECUTIVE_POLL_ERRORS:
                    logger.critical("Too many consecutive poll errors — stopping sensor")
                    self._running = False
                    break
            remaining = interval - (time.perf_counter() - t0)
            if remaining > 0:
                time.sleep(remaining)


# ---------------------------------------------------------------------------
# DataLogger
# ---------------------------------------------------------------------------

class DataLogger:
    """Writes one row per channel per sample (long format) for post-viz compatibility."""

    FIELDNAMES = ["sensor_time", "channel", "raw", "volts", "force_norm"]

    def __init__(self, output_dir: Path):
        output_dir.mkdir(parents=True, exist_ok=True)
        fname = output_dir / f"tactile_{datetime.now():%Y%m%d_%H%M%S}.csv"
        self._file      = fname.open("w", newline="", buffering=1)   # line-buffered
        self._writer    = csv.DictWriter(self._file, fieldnames=self.FIELDNAMES)
        self._writer.writeheader()
        self._row_count = 0
        logger.info("CSV logger opened: {}", fname)

    def write(self, reading: TactileReading) -> None:
        if self._file.closed:
            return
        for row in reading.as_rows():
            self._writer.writerow(row)
        self._row_count += len(reading.raw)

    def close(self) -> None:
        self._file.flush()
        self._file.close()
        logger.info("CSV logger closed — {} rows written", self._row_count)


# ---------------------------------------------------------------------------
# Terminal display
# ---------------------------------------------------------------------------

class TerminalDisplay:
    """
    Prints live readings to stdout in-place using carriage returns.
    No GUI required — runs in the calling thread via a blocking loop.
    """

    def __init__(self, sensor: TactileSensor, csv_logger: DataLogger | None):
        self._sensor     = sensor
        self._csv        = csv_logger
        self._sample_count = 0
        self._fps_t0     = time.perf_counter()

    def run(self) -> None:
        """Block until KeyboardInterrupt, printing one line per reading."""
        names  = self._sensor.channel_names
        header = "  ".join(f"{n:>8}" for n in names)
        print(f"\n{'t (s)':>7}  {header}")
        print("-" * (9 + 11 * len(names)))

        try:
            while True:
                reading = self._sensor.read()
                if reading is None:
                    time.sleep(0.01)
                    continue

                cols = "  ".join(
                    f"{reading.volts[n]:5.3f}V/{reading.force_norm[n]:.2f}"
                    for n in names
                )
                print(f"\r{reading.sensor_time:7.2f}  {cols}", end="", flush=True)

                if self._csv is not None:
                    self._csv.write(reading)

                self._sample_count += 1
                elapsed = time.perf_counter() - self._fps_t0
                if elapsed >= 1.0:
                    rate = self._sample_count / elapsed
                    print(f"   [{rate:.0f} Sa/s]", end="", flush=True)
                    self._sample_count = 0
                    self._fps_t0 = time.perf_counter()

                time.sleep(0.02)   # ~50 Hz terminal refresh

        except KeyboardInterrupt:
            print()   # newline after the last \r line
            logger.info("Terminal display stopped by user")


# ---------------------------------------------------------------------------
# PyQtGraph GUI
# ---------------------------------------------------------------------------

def _run_gui(sensor: TactileSensor, csv_logger: DataLogger | None,
             polling_hz: float) -> None:
    """Import PySide6 / pyqtgraph lazily so terminal mode works without them."""
    import os
    import signal

    try:
        from PySide6.QtCore import Qt, QTimer, Signal, QObject
        from PySide6.QtGui import QFont
        from PySide6.QtWidgets import (
            QApplication, QGridLayout, QHBoxLayout,
            QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget,
        )
        import pyqtgraph as pg
    except ImportError as exc:
        logger.error("GUI dependencies not available ({}). Use --terminal.", exc)
        sys.exit(1)

    PLOT_WINDOW_SECS: float = _VIZ_CFG["plot_window_secs"]
    VOLTAGE_YMAX:     float = _VIZ_CFG["voltage_ymax"]
    COLORS = [
        "#4FC3F7", "#81C784", "#FFB74D", "#F48FB1",
        "#CE93D8", "#80DEEA", "#FFCC02", "#FF7043",
        "#A5D6A7", "#90CAF9",
    ]

    # --- Signal bridge (sensor callback → GUI thread) ---
    class _SensorBridge(QObject):
        new_reading = Signal(object)

    # --- Per-channel plot widget ---
    class ChannelPlot(QWidget):
        def __init__(self, name: str, color: str, max_points: int, parent=None):
            super().__init__(parent)
            self._times:    deque[float] = deque(maxlen=max_points)
            self._voltages: deque[float] = deque(maxlen=max_points)

            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)

            header = QHBoxLayout()
            title  = QLabel(name)
            title.setFont(QFont("Monospace", 9, QFont.Bold))
            title.setStyleSheet(f"color: {color};")
            self._volt_label  = QLabel("-.-- V")
            self._volt_label.setFont(QFont("Monospace", 9))
            self._force_label = QLabel("force: -.-")
            self._force_label.setFont(QFont("Monospace", 9))
            header.addWidget(title)
            header.addStretch()
            header.addWidget(self._volt_label)
            header.addWidget(self._force_label)
            layout.addLayout(header)

            self._plot_widget = pg.PlotWidget(background="#1e1e1e")
            self._plot_widget.setYRange(0, VOLTAGE_YMAX)
            self._plot_widget.setMaximumHeight(120)
            self._plot_widget.hideAxis("bottom")
            self._plot_widget.getAxis("left").setStyle(tickFont=QFont("Monospace", 7))
            self._plot_widget.showGrid(x=False, y=True, alpha=0.2)
            self._curve = self._plot_widget.plot(pen=pg.mkPen(color=color, width=1.5))
            layout.addWidget(self._plot_widget)

            self._plot_window = PLOT_WINDOW_SECS

        def update_data(self, t_rel: float, voltage: float, force: float) -> None:
            self._times.append(t_rel)
            self._voltages.append(voltage)
            self._curve.setData(list(self._times), list(self._voltages))
            self._plot_widget.setXRange(t_rel - self._plot_window, t_rel, padding=0)
            self._volt_label.setText(f"{voltage:5.3f} V")
            self._force_label.setText(f"force: {force:.2f}")

    # --- Main window ---
    class TactileGUI(QMainWindow):
        def __init__(self):
            super().__init__()
            names    = sensor.channel_names
            max_pts  = int(PLOT_WINDOW_SECS * polling_hz * 1.2)
            self._t0 = time.perf_counter()

            self.setWindowTitle("AmazingHand — Tactile Sensor Monitor")
            self.setStyleSheet("background-color: #121212; color: #e0e0e0;")

            central = QWidget()
            self.setCentralWidget(central)
            root = QVBoxLayout(central)
            root.setSpacing(6)
            root.setContentsMargins(8, 8, 8, 8)

            # Status bar
            status_row = QHBoxLayout()
            self._status_label = QLabel("Waiting for data…")
            self._status_label.setFont(QFont("Monospace", 8))
            self._rate_label = QLabel("")
            self._rate_label.setFont(QFont("Monospace", 8))
            self._csv_label = QLabel(f"CSV: {'ON' if csv_logger else 'OFF'}")
            self._csv_label.setFont(QFont("Monospace", 8))
            self._csv_label.setStyleSheet(
                "color: #81C784;" if csv_logger else "color: #888;"
            )
            stop_btn = QPushButton("Stop")
            stop_btn.clicked.connect(self.close)
            stop_btn.setFixedWidth(60)
            status_row.addWidget(self._status_label)
            status_row.addStretch()
            status_row.addWidget(self._csv_label)
            status_row.addWidget(self._rate_label)
            status_row.addWidget(stop_btn)
            root.addLayout(status_row)

            # Channel plots (2-column grid)
            grid = QGridLayout()
            grid.setSpacing(6)
            self._channel_plots: dict[str, ChannelPlot] = {}
            for i, name in enumerate(names):
                color = COLORS[i % len(COLORS)]
                cp    = ChannelPlot(name, color, max_pts)
                self._channel_plots[name] = cp
                row, col = divmod(i, 2)
                grid.addWidget(cp, row, col)
            root.addLayout(grid)

            self.resize(900, max(400, len(names) // 2 * 160 + 60))

            # _pending_reading is written by the sensor thread and read by the
            # GUI refresh timer (main thread). A single object-reference swap is
            # atomic under the GIL, so an explicit lock is deliberately omitted
            # here to avoid blocking the sensor thread on every sample. This is
            # intentionally different from _latest in TactileSensor, which uses
            # a lock because it is also read from user code outside the GUI.
            self._pending_reading: TactileReading | None = None

            # CSV writes happen in the sensor polling thread (not the GUI
            # thread) so heavy I/O never blocks the event loop.
            def _sensor_callback(reading: TactileReading) -> None:
                if csv_logger is not None:
                    csv_logger.write(reading)
                self._pending_reading = reading

            sensor._on_reading = _sensor_callback  # type: ignore[assignment]

            # Refresh plots at ~30 Hz regardless of sensor polling rate.
            self._sample_count = 0
            refresh_timer = QTimer(self)
            refresh_timer.timeout.connect(self._refresh_plots)
            refresh_timer.start(33)   # ~30 Hz

            fps_timer = QTimer(self)
            fps_timer.timeout.connect(self._update_fps)
            fps_timer.start(1000)

            logger.info("GUI window created for channels: {}", names)

        def _refresh_plots(self) -> None:
            reading = self._pending_reading
            if reading is None:
                return
            self._pending_reading = None
            t_rel = time.perf_counter() - self._t0
            for name, cp in self._channel_plots.items():
                cp.update_data(
                    t_rel,
                    reading.volts.get(name, 0.0),
                    reading.force_norm.get(name, 0.0),
                )
            self._sample_count += 1
            self._status_label.setText(
                f"t={t_rel:.1f}s  sensor_t={reading.sensor_time:.3f}s"
            )

        def _update_fps(self) -> None:
            self._rate_label.setText(f"{self._sample_count} Sa/s")
            self._sample_count = 0

        def closeEvent(self, event) -> None:
            # Stop the sensor callback so no new readings arrive after close.
            sensor._on_reading = None  # type: ignore[assignment]
            self._pending_reading = None
            logger.info("Window closing — stopping sensor")
            super().closeEvent(event)
            QApplication.instance().quit()

    os.environ.setdefault("QT_QPA_PLATFORMTHEME", "")
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    window = TactileGUI()
    window.show()

    # Allow Ctrl+C (SIGINT) to quit the Qt event loop.
    # Qt blocks Python signal delivery during event processing, so a short
    # timer wakes the loop periodically to let Python check for signals.
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    _sigint_timer = QTimer()
    _sigint_timer.start(200)
    _sigint_timer.timeout.connect(lambda: None)

    exit_code = app.exec()
    # Cleanup happens here, after the event loop exits, so the GUI thread
    # is never blocked during window close.
    sensor.stop()
    if csv_logger is not None:
        csv_logger.close()
    logger.info("Application exited with code {}", exit_code)
    sys.exit(exit_code)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Tactile sensor real-time logger — GUI (default) or terminal",
    )
    p.add_argument(
        "--channels", nargs="+", type=int,
        default=_SENSOR_CFG["channels"],
        help="ADS1256 channels to read (default from config.toml)",
    )
    p.add_argument(
        "--names", nargs="+", type=str, default=None,
        help="Channel labels — must match --channels count",
    )
    p.add_argument(
        "--hz", type=float, default=_SENSOR_CFG["polling_hz"],
        help="Sensor polling rate in Hz (default from config.toml)",
    )
    p.add_argument(
        "--csv-dir", type=Path, default=_LOG_DIR,
        help="Directory for CSV output (default from config.toml)",
    )
    p.add_argument(
        "--no-csv", action="store_true",
        help="Disable CSV logging",
    )
    p.add_argument(
        "--terminal", action="store_true",
        help="Print readings to terminal only — no GUI window",
    )
    return p.parse_args()


def main() -> None:
    _configure_logging()
    args = _parse_args()

    channel_names = args.names or _SENSOR_CFG["channel_names"]
    if len(channel_names) != len(args.channels):
        logger.error(
            "--names count ({}) must match --channels count ({})",
            len(channel_names), len(args.channels),
        )
        sys.exit(1)

    sensor = TactileSensor(
        channels=args.channels,
        channel_names=channel_names,
        polling_hz=args.hz,
    )

    csv_logger: DataLogger | None = None
    if not args.no_csv:
        csv_logger = DataLogger(args.csv_dir)

    sensor.start()

    if args.terminal:
        display = TerminalDisplay(sensor, csv_logger)
        try:
            display.run()
        finally:
            try:
                sensor.stop()
            finally:
                if csv_logger is not None:
                    csv_logger.close()
    else:
        _run_gui(sensor, csv_logger, args.hz)


if __name__ == "__main__":
    main()
