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

import importlib
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np

_EXAMPLE_ROOT = Path(__file__).resolve().parent.parent
if str(_EXAMPLE_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXAMPLE_ROOT))

sys.modules["rustypot"] = MagicMock()
sys.modules["rustypot"].Scs0009PyController = MagicMock()


_FINGER_CONFIG = {
    "finger_test_servo_ids": [13, 14],
    "finger_test_middle_pos": [5, -2],
    "timeout": 0.5,
}


def _reload_with_mock(module_name, mock_controller):
    if module_name in sys.modules:
        del sys.modules[module_name]
    with patch("common.create_controller", return_value=mock_controller), patch(
        "common.load_config", return_value=_FINGER_CONFIG
    ):
        mod = importlib.import_module(module_name)
    return mod


class TestAmazingHandFingerTest(unittest.TestCase):
    """Unit tests for AmazingHand_FingerTest (CloseFinger / OpenFinger)."""

    def test_close_finger_calls_controller_with_expected_positions(self):
        mock_c = MagicMock()
        mod = _reload_with_mock("AmazingHand_FingerTest", mock_c)
        mod.close_finger()
        mock_c.write_goal_speed.assert_any_call(13, 6)
        mock_c.write_goal_speed.assert_any_call(14, 6)
        mock_c.write_goal_position.assert_any_call(13, np.deg2rad(5 + 90))
        mock_c.write_goal_position.assert_any_call(14, np.deg2rad(-2 - 90))

    def test_open_finger_calls_controller_with_expected_positions(self):
        mock_c = MagicMock()
        mod = _reload_with_mock("AmazingHand_FingerTest", mock_c)
        mod.open_finger()
        mock_c.write_goal_speed.assert_any_call(13, 6)
        mock_c.write_goal_speed.assert_any_call(14, 6)
        mock_c.write_goal_position.assert_any_call(13, np.deg2rad(5 - 30))
        mock_c.write_goal_position.assert_any_call(14, np.deg2rad(-2 + 30))


class TestAmazingHandHandFingerMiddlePos(unittest.TestCase):
    """Unit tests for AmazingHand_Hand_FingerMiddlePos (ServosInMiddle)."""

    def test_servos_in_middle_calls_controller_with_expected_positions(self):
        mock_c = MagicMock()
        mod = _reload_with_mock("AmazingHand_Hand_FingerMiddlePos", mock_c)
        mod.servos_in_middle()
        mock_c.write_goal_speed.assert_any_call(13, 6)
        mock_c.write_goal_speed.assert_any_call(14, 6)
        mock_c.write_goal_position.assert_any_call(13, np.deg2rad(5))
        mock_c.write_goal_position.assert_any_call(14, np.deg2rad(-2))


if __name__ == "__main__":
    unittest.main()
