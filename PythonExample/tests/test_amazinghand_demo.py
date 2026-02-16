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
from unittest.mock import MagicMock, patch

import numpy as np

_EXAMPLE_ROOT = Path(__file__).resolve().parent.parent
if str(_EXAMPLE_ROOT) not in sys.path:
    sys.path.insert(0, str(_EXAMPLE_ROOT))

sys.modules["rustypot"] = MagicMock()
sys.modules["rustypot"].Scs0009PyController = MagicMock()


_DEMO_CONFIG_LEFT = {
    "side": 2,
    "port": "",
    "baudrate": 1000000,
    "timeout": 0.5,
    "max_speed": 7,
    "close_speed": 3,
    "hand_2_index_servo_ids": [15, 16],
    "hand_2_index_middle_pos": [-12, 2],
    "hand_2_middle_servo_ids": [13, 14],
    "hand_2_middle_middle_pos": [2, 5],
    "hand_2_ring_servo_ids": [11, 12],
    "hand_2_ring_middle_pos": [-2, -8],
    "hand_2_thumb_servo_ids": [17, 18],
    "hand_2_thumb_middle_pos": [0, -15],
}

_DEMO_CONFIG_RIGHT = {
    "side": 1,
    "port": "",
    "baudrate": 1000000,
    "timeout": 0.5,
    "max_speed": 7,
    "close_speed": 3,
    "hand_1_index_servo_ids": [1, 2],
    "hand_1_index_middle_pos": [-2, 0],
    "hand_1_middle_servo_ids": [3, 4],
    "hand_1_middle_middle_pos": [1, 2],
    "hand_1_ring_servo_ids": [6, 5],
    "hand_1_ring_middle_pos": [-3, 8],
    "hand_1_thumb_servo_ids": [8, 7],
    "hand_1_thumb_middle_pos": [8, -8],
}


def _reload_demo(config=None):
    config = config or _DEMO_CONFIG_LEFT
    name = "AmazingHand_Demo"
    if name in sys.modules:
        del sys.modules[name]
    with patch("common.load_config", return_value=config):
        return importlib.import_module(name)


class TestAmazingHandDemoServoIDs(unittest.TestCase):
    """ServoIDs and constants for default (Left Hand, Side=2)."""

    def test_servo_ids_left_hand(self):
        mod = _reload_demo()
        self.assertEqual(mod.side, 2)
        self.assertEqual(
            mod.servo_ids,
            [15, 16, 13, 14, 11, 12, 17, 18],
        )

    def test_middle_pos_length(self):
        mod = _reload_demo()
        self.assertEqual(len(mod.middle_pos), 8)


class TestMoveFingerFunctions(unittest.TestCase):
    """Move_Index, Move_Middle, Move_Ring, Move_Thumb use correct ServoIDs and MiddlePos indices."""

    def setUp(self):
        self.mock_c = MagicMock()
        self.mod = _reload_demo()
        self.mod.c = self.mock_c

    def test_move_index_uses_servos_0_1_and_middle_pos_0_1(self):
        self.mod.Move_Index(10, -20, 5)
        self.mock_c.write_goal_speed.assert_any_call(15, 5)
        self.mock_c.write_goal_speed.assert_any_call(16, 5)
        self.mock_c.write_goal_position.assert_any_call(
            15, np.deg2rad(self.mod.middle_pos[0] + 10)
        )
        self.mock_c.write_goal_position.assert_any_call(
            16, np.deg2rad(self.mod.middle_pos[1] + (-20))
        )

    def test_move_middle_uses_servos_2_3_and_middle_pos_2_3(self):
        self.mod.Move_Middle(30, -40, 6)
        self.mock_c.write_goal_speed.assert_any_call(13, 6)
        self.mock_c.write_goal_speed.assert_any_call(14, 6)
        self.mock_c.write_goal_position.assert_any_call(
            13, np.deg2rad(self.mod.middle_pos[2] + 30)
        )
        self.mock_c.write_goal_position.assert_any_call(
            14, np.deg2rad(self.mod.middle_pos[3] + (-40))
        )

    def test_move_ring_uses_servos_4_5_and_middle_pos_4_5(self):
        self.mod.Move_Ring(-50, 60, 7)
        self.mock_c.write_goal_speed.assert_any_call(11, 7)
        self.mock_c.write_goal_speed.assert_any_call(12, 7)
        self.mock_c.write_goal_position.assert_any_call(
            11, np.deg2rad(self.mod.middle_pos[4] + (-50))
        )
        self.mock_c.write_goal_position.assert_any_call(
            12, np.deg2rad(self.mod.middle_pos[5] + 60)
        )

    def test_move_thumb_uses_servos_6_7_and_middle_pos_6_7(self):
        self.mod.Move_Thumb(0, -90, 4)
        self.mock_c.write_goal_speed.assert_any_call(17, 4)
        self.mock_c.write_goal_speed.assert_any_call(18, 4)
        self.mock_c.write_goal_position.assert_any_call(
            17, np.deg2rad(self.mod.middle_pos[6] + 0)
        )
        self.mock_c.write_goal_position.assert_any_call(
            18, np.deg2rad(self.mod.middle_pos[7] + (-90))
        )


class TestAmazingHandDemoOpenClose(unittest.TestCase):
    """OpenHand and CloseHand call controller with expected speeds and positions."""

    def setUp(self):
        self.mock_c = MagicMock()
        self.mod = _reload_demo()
        self.mod.c = self.mock_c

    def test_open_hand_writes_all_fingers_open(self):
        self.mod.OpenHand()
        # Index (15,16): -35, 35 -> rad(MiddlePos[0]-35), rad(MiddlePos[1]+35)
        self.mock_c.write_goal_position.assert_any_call(
            15, np.deg2rad(self.mod.middle_pos[0] + (-35))
        )
        self.mock_c.write_goal_position.assert_any_call(
            16, np.deg2rad(self.mod.middle_pos[1] + 35)
        )
        # All 8 servos get speed and position
        self.assertEqual(self.mock_c.write_goal_speed.call_count, 8)
        self.assertEqual(self.mock_c.write_goal_position.call_count, 8)

    def test_close_hand_writes_all_fingers_closed(self):
        self.mod.CloseHand()
        self.mock_c.write_goal_position.assert_any_call(
            15, np.deg2rad(self.mod.middle_pos[0] + 90)
        )
        self.mock_c.write_goal_position.assert_any_call(
            16, np.deg2rad(self.mod.middle_pos[1] + (-90))
        )
        self.assertEqual(self.mock_c.write_goal_speed.call_count, 8)
        self.assertEqual(self.mock_c.write_goal_position.call_count, 8)


class TestAmazingHandDemoGestures(unittest.TestCase):
    """Index_Pointing, SpreadHand (left), and one composite gesture."""

    def setUp(self):
        self.mock_c = MagicMock()
        self.mod = _reload_demo()
        self.mod.c = self.mock_c

    def test_index_pointing_index_open_others_closed(self):
        self.mod.Index_Pointing()
        # Index open: -40, 40
        self.mock_c.write_goal_position.assert_any_call(
            15, np.deg2rad(self.mod.middle_pos[0] + (-40))
        )
        self.mock_c.write_goal_position.assert_any_call(
            16, np.deg2rad(self.mod.middle_pos[1] + 40)
        )
        # Middle/Ring/Thumb closed (90, -90)
        self.mock_c.write_goal_position.assert_any_call(
            13, np.deg2rad(self.mod.middle_pos[2] + 90)
        )
        self.mock_c.write_goal_position.assert_any_call(
            14, np.deg2rad(self.mod.middle_pos[3] + (-90))
        )

    def test_spread_hand_left_uses_expected_angles(self):
        self.mod.SpreadHand()
        # Left: Index(-60,0), Middle(-35,35), Ring(-4,90), Thumb(-4,90)
        self.mock_c.write_goal_position.assert_any_call(
            15, np.deg2rad(self.mod.middle_pos[0] + (-60))
        )
        self.mock_c.write_goal_position.assert_any_call(
            16, np.deg2rad(self.mod.middle_pos[1] + 0)
        )
        self.mock_c.write_goal_position.assert_any_call(
            11, np.deg2rad(self.mod.middle_pos[4] + (-4))
        )
        self.mock_c.write_goal_position.assert_any_call(
            12, np.deg2rad(self.mod.middle_pos[5] + 90)
        )

    def test_victory_left_calls_controller(self):
        self.mod.Victory()
        # Index and Middle extended; Ring/Thumb closed
        self.mock_c.write_goal_position.assert_any_call(
            15, np.deg2rad(self.mod.middle_pos[0] + (-65))
        )
        self.mock_c.write_goal_position.assert_any_call(
            16, np.deg2rad(self.mod.middle_pos[1] + 15)
        )
        self.assertEqual(self.mock_c.write_goal_position.call_count, 8)

    @patch("AmazingHand_Demo.time.sleep")
    def test_open_hand_progressive_orders_index_middle_ring_thumb(self, mock_sleep):
        self.mod.OpenHand_Progressive()
        # Each finger: (-35, 35), speed MaxSpeed-2 = 5
        self.mock_c.write_goal_position.assert_any_call(
            15, np.deg2rad(self.mod.middle_pos[0] + (-35))
        )
        self.mock_c.write_goal_position.assert_any_call(
            13, np.deg2rad(self.mod.middle_pos[2] + (-35))
        )
        self.mock_c.write_goal_position.assert_any_call(
            11, np.deg2rad(self.mod.middle_pos[4] + (-35))
        )
        self.mock_c.write_goal_position.assert_any_call(
            17, np.deg2rad(self.mod.middle_pos[6] + (-35))
        )
        self.assertEqual(self.mock_c.write_goal_position.call_count, 8)

    def test_clench_hand_left_uses_expected_angles(self):
        self.mod.ClenchHand()
        # Left: Index(0,60), Middle(-35,35), Ring(-70,0), Thumb(-90,-4)
        self.mock_c.write_goal_position.assert_any_call(
            15, np.deg2rad(self.mod.middle_pos[0] + 0)
        )
        self.mock_c.write_goal_position.assert_any_call(
            16, np.deg2rad(self.mod.middle_pos[1] + 60)
        )
        self.mock_c.write_goal_position.assert_any_call(
            11, np.deg2rad(self.mod.middle_pos[4] + (-70))
        )
        self.mock_c.write_goal_position.assert_any_call(
            18, np.deg2rad(self.mod.middle_pos[7] + (-4))
        )

    def test_perfect_left_uses_expected_angles(self):
        self.mod.Perfect()
        # Left: Index(50,-50), Middle(0,0), Ring(-20,20), Thumb(-12,-65)
        self.mock_c.write_goal_position.assert_any_call(
            15, np.deg2rad(self.mod.middle_pos[0] + 50)
        )
        self.mock_c.write_goal_position.assert_any_call(
            13, np.deg2rad(self.mod.middle_pos[2] + 0)
        )
        self.mock_c.write_goal_position.assert_any_call(
            17, np.deg2rad(self.mod.middle_pos[6] + (-12))
        )
        self.mock_c.write_goal_position.assert_any_call(
            18, np.deg2rad(self.mod.middle_pos[7] + (-65))
        )

    def test_pinched_left_uses_expected_angles(self):
        self.mod.Pinched()
        # Left: Index/Middle/Ring (90,-90), Thumb (75,5)
        self.mock_c.write_goal_position.assert_any_call(
            15, np.deg2rad(self.mod.middle_pos[0] + 90)
        )
        self.mock_c.write_goal_position.assert_any_call(
            18, np.deg2rad(self.mod.middle_pos[7] + 5)
        )

    def test_fuck_left_uses_expected_angles(self):
        self.mod.Fuck()
        # Left: Index/Ring (90,-90), Middle (-35,35), Thumb (75,0)
        self.mock_c.write_goal_position.assert_any_call(
            15, np.deg2rad(self.mod.middle_pos[0] + 90)
        )
        self.mock_c.write_goal_position.assert_any_call(
            14, np.deg2rad(self.mod.middle_pos[3] + 35)
        )
        self.mock_c.write_goal_position.assert_any_call(
            18, np.deg2rad(self.mod.middle_pos[7] + 0)
        )

    @patch("AmazingHand_Demo.time.sleep")
    def test_nonono_calls_index_pointing_then_wag_then_open(self, mock_sleep):
        self.mod.Nonono()
        # Index_Pointing: Index (-40,40), others closed
        self.mock_c.write_goal_position.assert_any_call(
            15, np.deg2rad(self.mod.middle_pos[0] + (-40))
        )
        # Wag: (-10,80) and (-80,10) each 3 times; then final open (-35,35)
        self.mock_c.write_goal_position.assert_any_call(
            15, np.deg2rad(self.mod.middle_pos[0] + (-10))
        )
        self.mock_c.write_goal_position.assert_any_call(
            16, np.deg2rad(self.mod.middle_pos[1] + 80)
        )
        self.mock_c.write_goal_position.assert_any_call(
            15, np.deg2rad(self.mod.middle_pos[0] + (-80))
        )
        self.mock_c.write_goal_position.assert_any_call(
            16, np.deg2rad(self.mod.middle_pos[1] + 10)
        )
        self.mock_c.write_goal_position.assert_any_call(
            15, np.deg2rad(self.mod.middle_pos[0] + (-35))
        )
        self.mock_c.write_goal_position.assert_any_call(
            16, np.deg2rad(self.mod.middle_pos[1] + 35)
        )

    @patch("AmazingHand_Demo.time.sleep")
    def test_scissors_left_calls_victory_then_alternating_index_middle(self, mock_sleep):
        self.mod.Scissors()
        # Victory: Index (-65,15), Middle (-15,65), Ring/Thumb closed
        self.mock_c.write_goal_position.assert_any_call(
            15, np.deg2rad(self.mod.middle_pos[0] + (-65))
        )
        self.mock_c.write_goal_position.assert_any_call(
            14, np.deg2rad(self.mod.middle_pos[3] + 65)
        )
        # Left loop 3x: Index (-20,50) then (-65,15); Middle (-50,20) then (-15,65)
        self.mock_c.write_goal_position.assert_any_call(
            15, np.deg2rad(self.mod.middle_pos[0] + (-20))
        )
        self.mock_c.write_goal_position.assert_any_call(
            16, np.deg2rad(self.mod.middle_pos[1] + 50)
        )
        self.mock_c.write_goal_position.assert_any_call(
            13, np.deg2rad(self.mod.middle_pos[2] + (-50))
        )
        self.mock_c.write_goal_position.assert_any_call(
            14, np.deg2rad(self.mod.middle_pos[3] + 20)
        )


class TestAmazingHandDemoGesturesRightHand(unittest.TestCase):
    """Right-hand (Side=1) branches of gestures. Uses same pattern as left-hand tests."""

    def setUp(self):
        self.mock_c = MagicMock()
        self.mod = _reload_demo(_DEMO_CONFIG_RIGHT)
        self.mod.c = self.mock_c

    def test_servo_ids_right_hand(self):
        self.assertEqual(self.mod.side, 1)
        self.assertEqual(self.mod.servo_ids, [1, 2, 3, 4, 6, 5, 8, 7])

    def test_spread_hand_right_uses_expected_angles(self):
        self.mod.SpreadHand()
        # Right: Index(4,90), Middle(-32,32), Ring(-90,-4), Thumb(-90,-4)
        self.mock_c.write_goal_position.assert_any_call(
            1, np.deg2rad(self.mod.middle_pos[0] + 4)
        )
        self.mock_c.write_goal_position.assert_any_call(
            2, np.deg2rad(self.mod.middle_pos[1] + 90)
        )
        self.mock_c.write_goal_position.assert_any_call(
            6, np.deg2rad(self.mod.middle_pos[4] + (-90))
        )
        self.mock_c.write_goal_position.assert_any_call(
            8, np.deg2rad(self.mod.middle_pos[6] + (-90))
        )

    def test_clench_hand_right_uses_expected_angles(self):
        self.mod.ClenchHand()
        # Right: Index(-60,0), Middle(-35,35), Ring(0,70), Thumb(-4,90). Ring = ServoIDs[4], [5] = 6, 5.
        self.mock_c.write_goal_position.assert_any_call(
            1, np.deg2rad(self.mod.middle_pos[0] + (-60))
        )
        self.mock_c.write_goal_position.assert_any_call(
            6, np.deg2rad(self.mod.middle_pos[4] + 0)
        )
        self.mock_c.write_goal_position.assert_any_call(
            5, np.deg2rad(self.mod.middle_pos[5] + 70)
        )
        self.mock_c.write_goal_position.assert_any_call(
            8, np.deg2rad(self.mod.middle_pos[6] + (-4))
        )

    def test_perfect_right_uses_expected_angles(self):
        self.mod.Perfect()
        # Right: Index(50,-50), Middle(0,0), Ring(-20,20), Thumb(65,12)
        self.mock_c.write_goal_position.assert_any_call(
            1, np.deg2rad(self.mod.middle_pos[0] + 50)
        )
        self.mock_c.write_goal_position.assert_any_call(
            8, np.deg2rad(self.mod.middle_pos[6] + 65)
        )
        self.mock_c.write_goal_position.assert_any_call(
            7, np.deg2rad(self.mod.middle_pos[7] + 12)
        )

    def test_victory_right_uses_expected_angles(self):
        self.mod.Victory()
        # Right: Index(-15,65), Middle(-65,15), Ring/Thumb (90,-90)
        self.mock_c.write_goal_position.assert_any_call(
            1, np.deg2rad(self.mod.middle_pos[0] + (-15))
        )
        self.mock_c.write_goal_position.assert_any_call(
            2, np.deg2rad(self.mod.middle_pos[1] + 65)
        )
        self.mock_c.write_goal_position.assert_any_call(
            3, np.deg2rad(self.mod.middle_pos[2] + (-65))
        )
        self.mock_c.write_goal_position.assert_any_call(
            4, np.deg2rad(self.mod.middle_pos[3] + 15)
        )
        self.assertEqual(self.mock_c.write_goal_position.call_count, 8)

    def test_pinched_right_uses_expected_angles(self):
        self.mod.Pinched()
        # Right: Index/Middle/Ring (90,-90), Thumb (0,-75)
        self.mock_c.write_goal_position.assert_any_call(
            1, np.deg2rad(self.mod.middle_pos[0] + 90)
        )
        self.mock_c.write_goal_position.assert_any_call(
            8, np.deg2rad(self.mod.middle_pos[6] + 0)
        )
        self.mock_c.write_goal_position.assert_any_call(
            7, np.deg2rad(self.mod.middle_pos[7] + (-75))
        )

    def test_fuck_right_uses_expected_angles(self):
        self.mod.Fuck()
        # Right: Index/Ring (90,-90), Middle(-35,35), Thumb(0,-75)
        self.mock_c.write_goal_position.assert_any_call(
            1, np.deg2rad(self.mod.middle_pos[0] + 90)
        )
        self.mock_c.write_goal_position.assert_any_call(
            4, np.deg2rad(self.mod.middle_pos[3] + 35)
        )
        self.mock_c.write_goal_position.assert_any_call(
            7, np.deg2rad(self.mod.middle_pos[7] + (-75))
        )

    @patch("AmazingHand_Demo.time.sleep")
    def test_scissors_right_calls_victory_then_alternating_index_middle(self, mock_sleep):
        self.mod.Scissors()
        # Victory right: Index(-15,65), Middle(-65,15)
        self.mock_c.write_goal_position.assert_any_call(
            1, np.deg2rad(self.mod.middle_pos[0] + (-15))
        )
        # Right loop 3x: Index(-50,20) then (-15,65); Middle(-20,50) then (-65,15)
        self.mock_c.write_goal_position.assert_any_call(
            1, np.deg2rad(self.mod.middle_pos[0] + (-50))
        )
        self.mock_c.write_goal_position.assert_any_call(
            2, np.deg2rad(self.mod.middle_pos[1] + 20)
        )
        self.mock_c.write_goal_position.assert_any_call(
            3, np.deg2rad(self.mod.middle_pos[2] + (-20))
        )
        self.mock_c.write_goal_position.assert_any_call(
            4, np.deg2rad(self.mod.middle_pos[3] + 50)
        )


class TestAmazingHandDemoMain(unittest.TestCase):
    """main() behavior (init failure path only; loop not run)."""

    def test_main_returns_on_controller_init_failure(self):
        mod = _reload_demo()
        with patch("sys.argv", ["AmazingHand_Demo.py"]):
            with patch("AmazingHand_Demo.create_controller", side_effect=RuntimeError("no device")):
                mod.main()
        self.assertIsNone(mod.c)

    def test_main_sets_controller_on_success(self):
        mod = _reload_demo()
        fake = MagicMock()
        with patch("sys.argv", ["AmazingHand_Demo.py"]):
            with patch("AmazingHand_Demo.create_controller", return_value=fake):
                with patch("time.sleep", side_effect=SystemExit(0)):
                    with patch("time.time", return_value=0.0):
                        try:
                            mod.main()
                        except SystemExit:
                            pass
        self.assertIs(mod.c, fake)


if __name__ == "__main__":
    unittest.main()
