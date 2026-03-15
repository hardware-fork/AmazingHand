"""
tactile_sensing_post_visualize.py — Bokeh offline visualisation of logged tactile sensor data.

Expected CSV schema (long format, one row per channel per sample):
    sensor_time, channel, raw, volts, force_norm

The default log directory is read from config.toml ([logging] log_dir),
resolved relative to this file's directory (Demo/Sensors/).
"""

import argparse
from pathlib import Path

import pandas as pd
from bokeh.layouts import gridplot
from bokeh.models import TabPanel, Tabs
from bokeh.palettes import Set2_8
from bokeh.plotting import figure, show

# ---------------------------------------------------------------------------
# Load config.toml — same file used by tactile_sensing.py
# ---------------------------------------------------------------------------
import tomllib

_CONFIG_PATH = Path(__file__).parent / "config.toml"
with _CONFIG_PATH.open("rb") as _f:
    _TOML = tomllib.load(_f)

_SENSORS_DIR = Path(__file__).parent
_LOG_DIR     = _SENSORS_DIR / _TOML["logging"]["log_dir"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_latest_csv(log_dir: Path) -> Path:
    csvs = sorted(log_dir.glob("tactile_*.csv"))
    if not csvs:
        raise FileNotFoundError(f"No tactile_*.csv files found in {log_dir}")
    return csvs[-1]


def _customize_plot(fig) -> None:
    fig.title.text_font_size = "16px"
    fig.title.align = "center"
    fig.xaxis.axis_label_text_font_size = "13px"
    fig.yaxis.axis_label_text_font_size = "13px"
    fig.legend.title = "Channels"
    fig.legend.border_line_width = 2
    fig.legend.border_line_color = "black"
    fig.legend.location = "top_right"
    fig.legend.click_policy = "hide"


def build_tabs(data: pd.DataFrame) -> Tabs:
    channels  = sorted(data["channel"].unique(), key=lambda x: (x.isdigit(), x))
    color_map = {ch: Set2_8[i % len(Set2_8)] for i, ch in enumerate(channels)}

    def _make_fig(title, y_label):
        return figure(
            title=title,
            x_axis_label="Sensor Time (s)",
            y_axis_label=y_label,
            width=900, height=400,
        )

    fig_volts = _make_fig("FSR Sensor Data — Voltage", "Voltage (V)")
    fig_raw   = _make_fig("FSR Sensor Data — Raw ADC Counts", "Raw")
    fig_force = _make_fig("FSR Sensor Data — Normalised Force", "Force (0–1)")

    for ch in channels:
        dfc   = data[data["channel"] == ch]
        color = color_map[ch]
        label = str(ch)
        fig_volts.line(dfc["sensor_time"], dfc["volts"],
                       line_width=2, color=color, legend_label=label)
        fig_raw.line(dfc["sensor_time"], dfc["raw"],
                     line_width=2, color=color, legend_label=label)
        fig_force.line(dfc["sensor_time"], dfc["force_norm"],
                       line_width=2, color=color, legend_label=label)

    for fig in (fig_volts, fig_raw, fig_force):
        _customize_plot(fig)

    grid = gridplot([[fig_volts], [fig_raw], [fig_force]])
    return Tabs(tabs=[TabPanel(child=grid, title="FSR (all channels)")])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Visualise FSR tactile sensor CSV log",
    )
    parser.add_argument(
        "--file", type=Path, default=None,
        help=f"Path to CSV file (default: latest in {_LOG_DIR})",
    )
    args = parser.parse_args()

    file_path = args.file or _find_latest_csv(_LOG_DIR)
    print(f"Loading: {file_path}")

    data = pd.read_csv(file_path).dropna().reset_index(drop=True)
    data["sensor_time"] = data["sensor_time"] - data["sensor_time"].iloc[0]
    data["channel"]     = data["channel"].astype(str)

    tabs = build_tabs(data)
    show(tabs)


if __name__ == "__main__":
    main()
