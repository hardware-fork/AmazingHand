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
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# PythonExample root: one level up from tests/
_EXAMPLE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_EXAMPLE_ROOT))

# Allow tests to run without rustypot (hardware) installed
sys.modules["rustypot"] = MagicMock()
sys.modules["rustypot"].Scs0009PyController = MagicMock()

import common  # noqa: E402


class TestDefaultSerialPort(unittest.TestCase):
    def test_returns_string(self):
        self.assertIsInstance(common.default_serial_port(), str)

    def test_platform_value(self):
        port = common.default_serial_port()
        if sys.platform == "win32":
            self.assertEqual(port, "COM3")
        else:
            self.assertEqual(port, "/dev/ttyUSB0")


class TestLoadConfig(unittest.TestCase):
    def test_missing_profiles_returns_defaults(self):
        """When config_root has no profiles.toml, load_config returns defaults (no hand data)."""
        cfg = common.load_config(config_root=Path("/nonexistent"))
        self.assertEqual(cfg["baudrate"], 1000000)
        self.assertEqual(cfg["timeout"], 0.5)
        self.assertEqual(cfg["port"], "")

    def test_canonical_profile_team_julia(self):
        config_root = _EXAMPLE_ROOT.parent / "config"
        if not (config_root / "profiles.toml").exists():
            self.skipTest("config/profiles.toml not found")
        cfg = common.load_config(profile="team_julia", config_root=config_root)
        self.assertIn("port", cfg)
        self.assertIn("baudrate", cfg)
        self.assertIn("timeout", cfg)
        self.assertEqual(cfg["port"], "/dev/ttyACM0")
        self.assertEqual(cfg["timeout"], 0.5)

    def test_canonical_profile_team_krishan(self):
        config_root = _EXAMPLE_ROOT.parent / "config"
        if not (config_root / "profiles.toml").exists():
            self.skipTest("config/profiles.toml not found")
        cfg = common.load_config(profile="team_krishan", config_root=config_root)
        self.assertEqual(cfg["port"], "COM3")
        self.assertEqual(cfg["timeout"], 2.5)


class TestCreateController(unittest.TestCase):
    @patch("common.Scs0009PyController")
    def test_called_with_config_values(self, mock_controller):
        with patch("common.load_config") as mock_load:
            mock_load.return_value = {"port": "COM9", "baudrate": 1000000, "timeout": 1.0}
            common.create_controller(profile="team_krishan")
        mock_controller.assert_called_once_with(
            serial_port="COM9", baudrate=1000000, timeout=1.0
        )

    @patch("common.Scs0009PyController")
    def test_explicit_args_override_config(self, mock_controller):
        with patch("common.load_config") as mock_load:
            mock_load.return_value = {"port": "COM9", "baudrate": 1000000, "timeout": 1.0}
            common.create_controller(serial_port="/dev/ttyUSB1", timeout=0.1)
        mock_controller.assert_called_once_with(
            serial_port="/dev/ttyUSB1", baudrate=1000000, timeout=0.1
        )


class TestGetDemoHandConfig(unittest.TestCase):
    def test_returns_servo_ids_and_middle_pos_when_complete(self):
        cfg = {
            "hand_2_index_servo_ids": [15, 16],
            "hand_2_index_middle_pos": [-12, 2],
            "hand_2_middle_servo_ids": [13, 14],
            "hand_2_middle_middle_pos": [2, 5],
            "hand_2_ring_servo_ids": [11, 12],
            "hand_2_ring_middle_pos": [-2, -8],
            "hand_2_thumb_servo_ids": [17, 18],
            "hand_2_thumb_middle_pos": [0, -15],
        }
        out = common.get_demo_hand_config(cfg, 2)
        self.assertEqual(out["servo_ids"], [15, 16, 13, 14, 11, 12, 17, 18])
        self.assertEqual(out["middle_pos"], [-12, 2, 2, 5, -2, -8, 0, -15])

    def test_hand_1_finger_order_index_middle_ring_thumb(self):
        """Regression: get_demo_hand_config must return ids and middle_pos in order index, middle, ring, thumb (2 per finger)."""
        cfg = {
            "hand_1_index_servo_ids": [1, 2],
            "hand_1_index_middle_pos": [-2, 0],
            "hand_1_middle_servo_ids": [3, 4],
            "hand_1_middle_middle_pos": [1, 2],
            "hand_1_ring_servo_ids": [6, 5],
            "hand_1_ring_middle_pos": [-3, 8],
            "hand_1_thumb_servo_ids": [8, 7],
            "hand_1_thumb_middle_pos": [8, -8],
        }
        out = common.get_demo_hand_config(cfg, 1)
        self.assertEqual(out["servo_ids"], [1, 2, 3, 4, 6, 5, 8, 7])
        self.assertEqual(out["middle_pos"], [-2, 0, 1, 2, -3, 8, 8, -8])

    def test_raises_when_hand_config_incomplete(self):
        cfg = {"hand_2_index_servo_ids": [], "hand_2_index_middle_pos": []}
        with self.assertRaises(ValueError) as ctx:
            common.get_demo_hand_config(cfg, 2)
        self.assertIn("not configured", str(ctx.exception))

    def test_raises_when_wrong_length(self):
        """Regression: 8 servo IDs and 8 middle_pos required; wrong length must raise with clear message."""
        with patch.object(common, "_parse_hand_section") as mock_parse:
            mock_parse.return_value = ([1] * 7, [0] * 8)
            with self.assertRaises(ValueError) as ctx:
                common.get_demo_hand_config({}, 1)
            self.assertIn("8 servo IDs", str(ctx.exception))
            self.assertIn("7", str(ctx.exception))

    def test_load_config_and_get_demo_hand_config_team_julia_side_1(self):
        """Regression: load_config(profile=team_julia) + get_demo_hand_config(cfg, 1) must succeed."""
        config_root = _EXAMPLE_ROOT.parent / "config"
        if not (config_root / "profiles.toml").exists():
            self.skipTest("config/profiles.toml not found")
        cfg = common.load_config(profile="team_julia", config_root=config_root)
        out = common.get_demo_hand_config(cfg, 1)
        self.assertEqual(len(out["servo_ids"]), 8)
        self.assertEqual(len(out["middle_pos"]), 8)
        self.assertFalse(all(s == 0 for s in out["servo_ids"]))

    def test_load_config_uses_AMAZINGHAND_PROFILE(self):
        """When AMAZINGHAND_PROFILE is set, load_config() returns that profile's config."""
        config_root = _EXAMPLE_ROOT.parent / "config"
        if not (config_root / "profiles.toml").exists():
            self.skipTest("config/profiles.toml not found")
        with patch.dict(os.environ, {"AMAZINGHAND_PROFILE": "team_julia"}, clear=False):
            cfg = common.load_config(config_root=config_root)
        out = common.get_demo_hand_config(cfg, 1)
        self.assertEqual(out["servo_ids"], [1, 2, 3, 4, 6, 5, 8, 7])
        self.assertEqual(out["middle_pos"], [-2, 0, 1, 2, -3, 8, 8, -8])


if __name__ == "__main__":
    unittest.main()
