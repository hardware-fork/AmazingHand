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


class TestGetTeam(unittest.TestCase):
    def test_default_is_julia(self):
        with patch.dict(os.environ, {"AMAZINGHAND_TEAM": ""}, clear=False):
            self.assertEqual(common.get_team(), "julia")

    def test_env_team_used(self):
        with patch.dict(os.environ, {"AMAZINGHAND_TEAM": "krishan"}, clear=False):
            self.assertEqual(common.get_team(), "krishan")

    def test_normalized_lower(self):
        with patch.dict(os.environ, {"AMAZINGHAND_TEAM": "  Krishan  "}, clear=False):
            self.assertEqual(common.get_team(), "krishan")


class TestLoadConfig(unittest.TestCase):
    def test_missing_file_returns_defaults(self):
        cfg = common.load_config(path=Path("/nonexistent/config.toml"))
        self.assertEqual(cfg["baudrate"], 1000000)
        self.assertEqual(cfg["timeout"], 0.5)
        self.assertEqual(cfg["port"], "")

    def test_existing_config_team_section(self):
        config_path = _EXAMPLE_ROOT / "config.toml"
        if not config_path.exists():
            self.skipTest("config.toml not found")
        cfg = common.load_config(team="krishan", path=config_path)
        self.assertIn("port", cfg)
        self.assertIn("baudrate", cfg)
        self.assertIn("timeout", cfg)
        self.assertEqual(cfg["port"], "COM3")
        self.assertEqual(cfg["timeout"], 2.5)

    def test_team_julia_section(self):
        config_path = _EXAMPLE_ROOT / "config.toml"
        if not config_path.exists():
            self.skipTest("config.toml not found")
        cfg = common.load_config(team="julia", path=config_path)
        self.assertEqual(cfg["port"], "/dev/ttyACM0")
        self.assertEqual(cfg["timeout"], 0.5)


class TestCreateController(unittest.TestCase):
    @patch("common.Scs0009PyController")
    def test_called_with_config_values(self, mock_controller):
        if not (_EXAMPLE_ROOT / "config.toml").exists():
            self.skipTest("config.toml not found")
        with patch("common.load_config") as mock_load:
            mock_load.return_value = {"port": "COM9", "baudrate": 1000000, "timeout": 1.0}
            common.create_controller(team="krishan")
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

    def test_raises_when_hand_config_incomplete(self):
        cfg = {"hand_2_index_servo_ids": [], "hand_2_index_middle_pos": []}
        with self.assertRaises(ValueError) as ctx:
            common.get_demo_hand_config(cfg, 2)
        self.assertIn("not configured", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
