# Original authors: Pollen Robotics, AmazingHand authors.
# See: https://github.com/pollen-robotics/AmazingHand
#
# Copyright (C) 2026 Julia Jia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
from pathlib import Path

from rustypot import Scs0009PyController

try:
    import tomllib
except ImportError:
    tomllib = None

_CONFIG_PATH = Path(__file__).resolve().parent / "config.toml"
_TEAM_ENV = "AMAZINGHAND_TEAM"
# Section names in config.toml are [team_<name>], e.g. [team_julia], [team_krishan].
_CONFIG_TEAM_SECTION_PREFIX = "team_"

_DEFAULTS = {
    "port": "",
    "baudrate": 1000000,
    "timeout": 0.5,
}


def default_serial_port():
    """Return default serial port for current OS (Linux: /dev/ttyUSB0, Windows: COM3)."""
    if sys.platform == "win32":
        return "COM3"
    return "/dev/ttyUSB0"


def get_team():
    """Return current team name (e.g. 'julia', 'krishan'). From AMAZINGHAND_TEAM env; default 'julia'.
    Accepts either the short name or the full section name; strips config section prefix so it matches [team_<name>] in config.toml."""
    raw = (os.environ.get(_TEAM_ENV) or "julia").strip().lower()
    return raw.removeprefix(_CONFIG_TEAM_SECTION_PREFIX)


def load_config(team=None, path=None):
    """Load section [team_<name>] from config.toml. Returns dict with port, baudrate, timeout and all other section keys."""
    p = path or _CONFIG_PATH
    if not p.exists() or tomllib is None:
        return _DEFAULTS.copy()
    with open(p, "rb") as f:
        data = tomllib.load(f)
    name = (team or get_team()).strip().lower()
    section_key = f"{_CONFIG_TEAM_SECTION_PREFIX}{name}"
    section = data.get(section_key, {})
    out = {
        "port": (section.get("port") or _DEFAULTS["port"]) or "",
        "baudrate": section.get("baudrate", _DEFAULTS["baudrate"]),
        "timeout": section.get("timeout", _DEFAULTS["timeout"]),
    }
    for k, v in section.items():
        if k not in out:
            out[k] = v
    return out


def create_controller(team=None, serial_port=None, baudrate=None, timeout=None):
    """Create Scs0009PyController. Section from AMAZINGHAND_TEAM or team=; explicit args override."""
    cfg = load_config(team=team)
    port = serial_port if serial_port is not None else (cfg["port"] or default_serial_port())
    br = baudrate if baudrate is not None else cfg["baudrate"]
    to = timeout if timeout is not None else cfg["timeout"]
    return Scs0009PyController(serial_port=port, baudrate=br, timeout=to)


# Demo script: one hand (side 1 = right, side 2 = left). Servo IDs and middle poses per finger.
# Layout is isolated in _parse_hand_section so config shape (flat vs nested) can change later.


def _parse_hand_section(cfg, side):
    """Extract servo_ids and middle_pos for one hand from team config. side 1 = hand_1, 2 = hand_2.
    Missing or empty entries default to [0, 0] per finger. Returns (servo_ids, middle_pos)."""
    prefix = "hand_1" if side == 1 else "hand_2"
    servo_ids = []
    middle_pos = []
    for name in ("index", "middle", "ring", "thumb"):
        ids = cfg.get(f"{prefix}_{name}_servo_ids", [])
        mid = cfg.get(f"{prefix}_{name}_middle_pos", [])
        servo_ids.extend(ids if len(ids) == 2 else [0, 0])
        middle_pos.extend(mid if len(mid) == 2 else [0, 0])
    return servo_ids, middle_pos


def get_demo_hand_config(cfg, side, config_path=None):
    """Return dict with servo_ids, middle_pos, and side (1 or 2) for one hand.
    Raises ValueError with a friendly message if the hand is not configured (all zeros)."""
    servo_ids, middle_pos = _parse_hand_section(cfg, side)
    if len(servo_ids) != 8 or len(middle_pos) != 8:
        prefix = "hand_1" if side == 1 else "hand_2"
        raise ValueError(
            f"config must define {prefix}_*_servo_ids and {prefix}_*_middle_pos for index, middle, ring, thumb "
            f"(8 servo IDs and 8 middle positions); got {len(servo_ids)} ids and {len(middle_pos)} positions"
        )
    if all(s == 0 for s in servo_ids):
        prefix = "hand_1" if side == 1 else "hand_2"
        hand_name = "right" if side == 1 else "left"
        keys = ", ".join(
            f"{prefix}_{name}_{suffix}"
            for name in ("index", "middle", "ring", "thumb")
            for suffix in ("servo_ids", "middle_pos")
        )
        path_hint = f" Edit {config_path or _CONFIG_PATH} in your team section."
        raise ValueError(
            f"{prefix} ({hand_name} hand) is not configured. "
            f"Set: {keys}.{path_hint} "
            f"Or run with --side {3 - side} to use the other hand."
        )
    return {"servo_ids": servo_ids, "middle_pos": middle_pos, "side": side}
