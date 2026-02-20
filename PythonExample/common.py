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

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CANONICAL_CONFIG_ROOT = _REPO_ROOT / "config"
_PROFILE_ENV = "AMAZINGHAND_PROFILE"
_FINGER_ORDER = ("index", "middle", "ring", "thumb")

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


def load_config(profile=None, config_root=None):
    """Load canonical config (profiles + calibration). Returns dict with port, baudrate, timeout, hand_* keys.
    profile: from AMAZINGHAND_PROFILE env or default 'team_julia'. config_root: repo config/ dir."""
    return load_config_canonical(
        profile=profile or os.environ.get(_PROFILE_ENV),
        config_root=config_root or _CANONICAL_CONFIG_ROOT,
    )


def create_controller(profile=None, serial_port=None, baudrate=None, timeout=None):
    """Create Scs0009PyController from canonical config. Set AMAZINGHAND_PROFILE or pass profile=."""
    cfg = load_config(profile=profile)
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
        path_hint = " Set AMAZINGHAND_PROFILE and ensure that profile references a calibration file in config/calibration/."
        raise ValueError(
            f"{prefix} ({hand_name} hand) is not configured. "
            f"{path_hint} Or run with --side {3 - side} to use the other hand."
        )
    return {"servo_ids": servo_ids, "middle_pos": middle_pos, "side": side}


# Canonical config: load from config/hand_geometry.toml, config/profiles.toml + config/calibration/*.toml.


def _load_hand_geometry(config_root):
    """Load shared finger order from config/hand_geometry.toml. Returns tuple of finger names or None if missing."""
    if tomllib is None:
        return None
    path = config_root / "hand_geometry.toml"
    if not path.exists():
        return None
    with open(path, "rb") as f:
        data = tomllib.load(f)
    fingers = data.get("fingers")
    if isinstance(fingers, list) and len(fingers) >= 4:
        return tuple(str(x) for x in fingers[:4])
    return None


def _load_canonical_calibration(calibration_name, config_root):
    """Load one calibration file. Returns dict with keys [finger].ids and [finger].rest_deg for each finger."""
    if not calibration_name:
        return None
    path = config_root / "calibration" / f"{calibration_name}.toml"
    if not path.exists() or tomllib is None:
        return None
    with open(path, "rb") as f:
        return tomllib.load(f)


def _calibration_to_hand_flat(cal, hand_prefix, finger_order=None):
    """Turn calibration dict into hand_1_* or hand_2_* flat keys. finger_order from hand_geometry.toml or default."""
    order = finger_order or _FINGER_ORDER
    out = {}
    for name in order:
        section = cal.get(name, {})
        ids = section.get("ids", [0, 0])[:2]
        rest = section.get("rest_deg", [0, 0])[:2]
        out[f"{hand_prefix}_{name}_servo_ids"] = ids if len(ids) == 2 else [0, 0]
        out[f"{hand_prefix}_{name}_middle_pos"] = rest if len(rest) == 2 else [0, 0]
    return out


def load_config_canonical(profile=None, config_root=None):
    """Load canonical config (profiles + calibration) and return dict in same shape as load_config().
    Use this when AMAZINGHAND_PROFILE is set or when migrating to single source of truth.
    profile: name of profile (e.g. 'team_julia', 'team_krishan'); default from AMAZINGHAND_PROFILE or 'team_julia'.
    config_root: path to repo config/ directory; default _CANONICAL_CONFIG_ROOT."""
    root = config_root or _CANONICAL_CONFIG_ROOT
    profiles_path = root / "profiles.toml"
    if not profiles_path.exists() or tomllib is None:
        return _DEFAULTS.copy()
    with open(profiles_path, "rb") as f:
        data = tomllib.load(f)
    name = (profile or os.environ.get(_PROFILE_ENV) or "team_julia").strip().lower()
    section = data.get("profile", {}).get(name, {})
    if not section:
        return _DEFAULTS.copy()
    out = {
        "port": (section.get("port") or _DEFAULTS["port"]) or "",
        "baudrate": section.get("baudrate", _DEFAULTS["baudrate"]),
        "timeout": section.get("timeout", _DEFAULTS["timeout"]),
    }
    for k, v in section.items():
        if k not in out:
            out[k] = v
    finger_order = _load_hand_geometry(root) or _FINGER_ORDER
    right_cal = _load_canonical_calibration(section.get("right_hand_calibration", ""), root)
    if right_cal:
        out.update(_calibration_to_hand_flat(right_cal, "hand_1", finger_order))
    else:
        for name in finger_order:
            out[f"hand_1_{name}_servo_ids"] = [0, 0]
            out[f"hand_1_{name}_middle_pos"] = [0, 0]
    left_cal = _load_canonical_calibration(section.get("left_hand_calibration", ""), root)
    if left_cal:
        out.update(_calibration_to_hand_flat(left_cal, "hand_2", finger_order))
    else:
        for name in finger_order:
            out[f"hand_2_{name}_servo_ids"] = [0, 0]
            out[f"hand_2_{name}_middle_pos"] = [0, 0]
    return out
