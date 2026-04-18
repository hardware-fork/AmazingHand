"""
ADS1256 driver — 24-bit, 8-channel ADC (lgpio + spidev, no RPi.GPIO).

Hardware pin and SPI settings are read from config.toml in the same directory.
"""

import time

import lgpio
import spidev

from amazinghand_sensors._config import load_config

# ---------------------------------------------------------------------------
# Load hardware settings from config.toml
# ---------------------------------------------------------------------------

_hw = load_config()["hardware"]

_RST_PIN          : int = _hw["rst_pin"]
_CS_PIN           : int = _hw["cs_pin"]
_CS_DAC_PIN       : int = _hw["cs_dac_pin"]
_DRDY_PIN         : int = _hw["drdy_pin"]
_SPI_MAX_SPEED_HZ : int = _hw["spi_max_speed_hz"]
_SPI_MODE         : int = _hw["spi_mode"]

# ---------------------------------------------------------------------------
# Hardware handles — initialised in _hw_init(), released in _hw_exit()
# ---------------------------------------------------------------------------

_SPI: spidev.SpiDev | None = None
_h:   int | None           = None


# ---------------------------------------------------------------------------
# Hardware lifecycle
# ---------------------------------------------------------------------------

def _hw_init() -> None:
    global _h, _SPI
    _SPI = spidev.SpiDev(0, 0)
    _SPI.max_speed_hz = _SPI_MAX_SPEED_HZ
    _SPI.mode         = _SPI_MODE
    _h = lgpio.gpiochip_open(4)
    lgpio.gpio_claim_output(_h, _RST_PIN)
    lgpio.gpio_claim_output(_h, _CS_DAC_PIN)
    lgpio.gpio_claim_output(_h, _CS_PIN)
    lgpio.gpio_claim_input(_h, _DRDY_PIN)


def _hw_exit() -> None:
    global _h, _SPI
    if _SPI is not None:
        _SPI.close()
        _SPI = None
    if _h is not None:
        lgpio.gpiochip_close(_h)
        _h = None


# ---------------------------------------------------------------------------
# ADS1256 register / command constants
# ---------------------------------------------------------------------------

GAIN = {
    "ADS1256_GAIN_1":  0,
    "ADS1256_GAIN_2":  1,
    "ADS1256_GAIN_4":  2,
    "ADS1256_GAIN_8":  3,
    "ADS1256_GAIN_16": 4,
    "ADS1256_GAIN_32": 5,
    "ADS1256_GAIN_64": 6,
}

DRATE = {
    "ADS1256_30000SPS": 0xF0,
    "ADS1256_15000SPS": 0xE0,
    "ADS1256_7500SPS":  0xD0,
    "ADS1256_3750SPS":  0xC0,
    "ADS1256_2000SPS":  0xB0,
    "ADS1256_1000SPS":  0xA1,
    "ADS1256_500SPS":   0x92,
    "ADS1256_100SPS":   0x82,
    "ADS1256_60SPS":    0x72,
    "ADS1256_50SPS":    0x63,
    "ADS1256_30SPS":    0x53,
    "ADS1256_25SPS":    0x43,
    "ADS1256_15SPS":    0x33,
    "ADS1256_10SPS":    0x20,
    "ADS1256_5SPS":     0x13,
    "ADS1256_2d5SPS":   0x03,
}

REG = {
    "REG_STATUS": 0,
    "REG_MUX":    1,
    "REG_ADCON":  2,
    "REG_DRATE":  3,
    "REG_IO":     4,
    "REG_OFC0":   5,
    "REG_OFC1":   6,
    "REG_OFC2":   7,
    "REG_FSC0":   8,
    "REG_FSC1":   9,
    "REG_FSC2":  10,
}

CMD = {
    "CMD_WAKEUP":   0x00,
    "CMD_RDATA":    0x01,
    "CMD_RDATAC":   0x03,
    "CMD_SDATAC":   0x0F,
    "CMD_RREG":     0x10,
    "CMD_WREG":     0x50,
    "CMD_SELFCAL":  0xF0,
    "CMD_SELFOCAL": 0xF1,
    "CMD_SELFGCAL": 0xF2,
    "CMD_SYSOCAL":  0xF3,
    "CMD_SYSGCAL":  0xF4,
    "CMD_SYNC":     0xFC,
    "CMD_STANDBY":  0xFD,
    "CMD_RESET":    0xFE,
}

_STATUS_DRDY     = 0x04
_EXPECTED_CHIP_ID = 3       # ADS1256 always reports chip ID 3 in STATUS[7:4]
ADC_MAX          = 0x7FFFFF  # 24-bit signed positive full-scale

# ADS1256 internal Vref = 2.5 V; with PGA=1 full-scale input = ±2×Vref = ±5 V
REF_VOLTAGE = 2.5


# ---------------------------------------------------------------------------
# Driver class
# ---------------------------------------------------------------------------

class ADS1256:
    """Low-level ADS1256 driver."""

    def __init__(self):
        self.rst_pin  = _RST_PIN
        self.cs_pin   = _CS_PIN
        self.drdy_pin = _DRDY_PIN

    # --- SPI / GPIO primitives ---

    def _write_cmd(self, cmd: int) -> None:
        lgpio.gpio_write(_h, self.cs_pin, 0)
        _SPI.writebytes([cmd])
        lgpio.gpio_write(_h, self.cs_pin, 1)

    def _write_reg(self, reg: int, data: int) -> None:
        lgpio.gpio_write(_h, self.cs_pin, 0)
        _SPI.writebytes([CMD["CMD_WREG"] | reg, 0x00, data])
        lgpio.gpio_write(_h, self.cs_pin, 1)

    def _read_reg(self, reg: int) -> int:
        lgpio.gpio_write(_h, self.cs_pin, 0)
        _SPI.writebytes([CMD["CMD_RREG"] | reg, 0x00])
        data = _SPI.readbytes(1)
        lgpio.gpio_write(_h, self.cs_pin, 1)
        return data[0]

    def _wait_drdy(self, timeout: int = 400_000) -> None:
        for _ in range(timeout):
            if lgpio.gpio_read(_h, self.drdy_pin) == 0:
                return
        raise TimeoutError("ADS1256 DRDY timeout — check wiring / power")

    # --- Init helpers ---

    def _reset(self) -> None:
        lgpio.gpio_write(_h, self.rst_pin, 1)
        time.sleep(0.2)
        lgpio.gpio_write(_h, self.rst_pin, 0)
        time.sleep(0.2)
        lgpio.gpio_write(_h, self.rst_pin, 1)

    def _read_chip_id(self) -> int:
        self._wait_drdy()
        return self._read_reg(REG["REG_STATUS"]) >> 4

    def _config_adc(self, gain: int, drate: int) -> None:
        self._wait_drdy()
        buf = [
            (0 << 3) | _STATUS_DRDY | (0 << 1),  # STATUS
            0x08,                                   # MUX default
            (0 << 5) | (0 << 3) | gain,             # ADCON
            drate,                                  # DRATE
        ]
        lgpio.gpio_write(_h, self.cs_pin, 0)
        _SPI.writebytes([CMD["CMD_WREG"] | 0, 0x03])
        _SPI.writebytes(buf)
        lgpio.gpio_write(_h, self.cs_pin, 1)
        time.sleep(0.001)

    def _set_channel(self, channel: int) -> None:
        if channel > 7:
            raise ValueError(f"ADS1256 single-ended channel must be 0–7, got {channel}")
        self._write_reg(REG["REG_MUX"], (channel << 4) | 0x08)

    def _set_diff_channel(self, diff_channel: int) -> None:
        # diff_channel is a pair index (0–3), not a physical pin number;
        # pair 0 → AIN0/AIN1, pair 1 → AIN2/AIN3, etc.
        pairs = [(0, 1), (2, 3), (4, 5), (6, 7)]
        if diff_channel >= len(pairs):
            raise ValueError(f"ADS1256 differential channel must be 0–3, got {diff_channel}")
        pos, neg = pairs[diff_channel]
        self._write_reg(REG["REG_MUX"], (pos << 4) | neg)

    def _read_adc_data(self) -> int:
        self._wait_drdy()
        lgpio.gpio_write(_h, self.cs_pin, 0)
        _SPI.writebytes([CMD["CMD_RDATA"]])
        buf = _SPI.readbytes(3)
        lgpio.gpio_write(_h, self.cs_pin, 1)
        raw = ((buf[0] << 16) & 0xFF0000) | ((buf[1] << 8) & 0xFF00) | (buf[2] & 0xFF)
        if raw & 0x800000:          # two's-complement sign extension
            raw -= 0x1000000
        return raw

    # --- Public API ---

    def init(self, gain_key: str = "ADS1256_GAIN_1",
             drate_key: str = "ADS1256_30000SPS") -> None:
        _hw_init()
        self._reset()
        chip_id = self._read_chip_id()
        if chip_id != _EXPECTED_CHIP_ID:
            raise RuntimeError(f"ADS1256 chip ID mismatch: got {chip_id}, expected {_EXPECTED_CHIP_ID}")
        self._config_adc(GAIN[gain_key], DRATE[drate_key])

    def get_channel_value(self, channel: int, diff: bool = False) -> int:
        """Return signed 24-bit raw count for the given channel."""
        if diff:
            self._set_diff_channel(channel)
        else:
            self._set_channel(channel)
        self._write_cmd(CMD["CMD_SYNC"])
        self._write_cmd(CMD["CMD_WAKEUP"])
        return self._read_adc_data()

    def exit(self) -> None:
        _hw_exit()
