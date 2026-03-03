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

"""Configuration loading with fallback for pip-installed package."""

import os
from pathlib import Path

try:
    import tomllib
except ImportError:
    tomllib = None

_CONFIG_ENV = "AMAZINGHAND_CONFIG"
_PROFILE_ENV = "AMAZINGHAND_PROFILE"
_FINGER_ORDER = ("index", "middle", "ring", "thumb")

_DEFAULTS = {
    "port": "",
    "baudrate": 1000000,
    "timeout": 0.5,
}


def _user_config_dir() -> Path:
    """Platform-specific user config directory."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return Path(base) / "amazinghand"


def get_config_root(config_root=None) -> Path:
    """Resolve config directory. Order: env AMAZINGHAND_CONFIG > arg > repo > user config > bundled."""
    if config_root is not None:
        return Path(config_root)
    env_path = os.environ.get(_CONFIG_ENV)
    if env_path:
        return Path(env_path)
    pkg_dir = Path(__file__).resolve().parent
    repo_config = pkg_dir.parent.parent / "config"
    if (repo_config / "profiles.toml").exists():
        return repo_config
    user_config = _user_config_dir()
    if (user_config / "profiles.toml").exists():
        return user_config
    try:
        from importlib.resources import files
        bundled = files("amazinghand") / "config"
        if bundled.joinpath("profiles.toml").exists():
            return Path(str(bundled))
    except (ImportError, TypeError):
        pass
    return user_config


def _default_serial_port() -> str:
    import sys
    return "COM3" if sys.platform == "win32" else "/dev/ttyUSB0"


def _load_hand_geometry(root: Path) -> tuple | None:
    if tomllib is None:
        return None
    path = root / "hand_geometry.toml"
    if not path.exists():
        return None
    with open(path, "rb") as f:
        data = tomllib.load(f)
    fingers = data.get("fingers")
    if isinstance(fingers, list) and len(fingers) >= 4:
        return tuple(str(x) for x in fingers[:4])
    return None


def _load_calibration(name: str, root: Path) -> dict | None:
    if not name or tomllib is None:
        return None
    path = root / "calibration" / f"{name}.toml"
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return tomllib.load(f)


def _calibration_to_hand_flat(cal: dict, hand_prefix: str, finger_order: tuple) -> dict:
    out = {}
    for name in finger_order:
        section = cal.get(name, {})
        ids = section.get("ids", [0, 0])[:2]
        rest = section.get("rest_deg", [0, 0])[:2]
        out[f"{hand_prefix}_{name}_servo_ids"] = ids if len(ids) == 2 else [0, 0]
        out[f"{hand_prefix}_{name}_middle_pos"] = rest if len(rest) == 2 else [0, 0]
    return out


def load_config(profile=None, config_root=None) -> dict:
    """Load config (profiles + calibration). Returns dict with port, baudrate, hand_* keys.

    Config resolution:
    1. AMAZINGHAND_CONFIG env: path to config directory
    2. config_root argument
    3. Repo config/ (when run from source)
    4. User config dir (~/.config/amazinghand or %LOCALAPPDATA%\\amazinghand)
    5. Bundled config (when pip-installed)

    Profile: AMAZINGHAND_PROFILE env or 'default'.
    """
    root = get_config_root(config_root)
    if not (root / "profiles.toml").exists() or tomllib is None:
        return _DEFAULTS.copy()

    with open(root / "profiles.toml", "rb") as f:
        data = tomllib.load(f)

    name = (profile or os.environ.get(_PROFILE_ENV) or "default").strip().lower()
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
    for hand_prefix, cal_name in [
        ("hand_1", section.get("right_hand_calibration", "")),
        ("hand_2", section.get("left_hand_calibration", "")),
    ]:
        cal = _load_calibration(cal_name, root)
        if cal:
            out.update(_calibration_to_hand_flat(cal, hand_prefix, finger_order))
        else:
            for n in finger_order:
                out[f"{hand_prefix}_{n}_servo_ids"] = [0, 0]
                out[f"{hand_prefix}_{n}_middle_pos"] = [0, 0]

    return out


def get_hand_config(cfg: dict, side: int) -> dict:
    """Return servo_ids, middle_pos, side for one hand. Raises ValueError if not configured."""
    prefix = "hand_1" if side == 1 else "hand_2"
    servo_ids = []
    middle_pos = []
    for name in _FINGER_ORDER:
        ids = cfg.get(f"{prefix}_{name}_servo_ids", [])
        mid = cfg.get(f"{prefix}_{name}_middle_pos", [])
        servo_ids.extend(ids if len(ids) == 2 else [0, 0])
        middle_pos.extend(mid if len(mid) == 2 else [0, 0])

    if len(servo_ids) != 8 or len(middle_pos) != 8:
        raise ValueError(
            f"config must define {prefix}_*_servo_ids and {prefix}_*_middle_pos "
            f"for index, middle, ring, thumb (8 each); got {len(servo_ids)} ids"
        )
    if all(s == 0 for s in servo_ids):
        hand_name = "right" if side == 1 else "left"
        raise ValueError(
            f"{prefix} ({hand_name} hand) not configured. "
            f"Set AMAZINGHAND_PROFILE and ensure calibration exists, or use config_root."
        )
    return {"servo_ids": servo_ids, "middle_pos": middle_pos, "side": side}
