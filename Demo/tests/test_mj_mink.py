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

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import unittest

_DEMO_ROOT = Path(__file__).resolve().parent.parent
_AH_SIM = _DEMO_ROOT / "AHSimulation" / "AHSimulation"
if str(_AH_SIM) not in sys.path:
    sys.path.insert(0, str(_AH_SIM))

try:
    import mj_mink_common as common
except Exception:
    common = None


def _scene_exists(side):
    scene_dir = "AH_Right" if side == "right" else "AH_Left"
    return (_AH_SIM / scene_dir / "mjcf" / "scene.xml").exists()


@unittest.skipIf(common is None, "mj_mink_common not importable (mujoco/mink/dora)")
class TestMocapOffsets(unittest.TestCase):
    def test_has_right_and_left(self):
        self.assertIn("right", common.MOCAP_POS_OFFSETS)
        self.assertIn("left", common.MOCAP_POS_OFFSETS)

    def test_each_side_has_four_tips(self):
        for side in ("right", "left"):
            with self.subTest(side=side):
                offsets = common.MOCAP_POS_OFFSETS[side]
                self.assertEqual(len(offsets), 4, f"{side} should have 4 tip offsets")

    def test_each_offset_is_three_floats(self):
        for side in ("right", "left"):
            for i, t in enumerate(common.MOCAP_POS_OFFSETS[side]):
                with self.subTest(side=side, tip=i):
                    self.assertEqual(len(t), 3)
                    for v in t:
                        self.assertIsInstance(v, (int, float))


@unittest.skipIf(common is None, "mj_mink_common not importable")
class TestClientValidation(unittest.TestCase):
    def test_invalid_side_raises(self):
        with self.assertRaises(ValueError) as ctx:
            common.Client(side="invalid", mode="pos")
        self.assertIn("side must be 'left' or 'right'", str(ctx.exception))

    def test_invalid_mode_raises_when_model_loaded(self):
        if not _scene_exists("right"):
            self.skipTest("AH_Right scene.xml not found")
        with self.assertRaises(ValueError) as ctx:
            common.Client(side="right", mode="bad")
        self.assertIn("unknown mode", str(ctx.exception))


@unittest.skipIf(common is None, "mj_mink_common not importable")
@unittest.skipIf(not _scene_exists("right"), "AH_Right scene.xml not found")
class TestClientRightAttrs(unittest.TestCase):
    def setUp(self):
        with patch.object(common, "Node", MagicMock()):
            self.client = common.Client(side="right", mode="pos")

    def test_prefix(self):
        self.assertEqual(self.client.prefix, "r_")

    def test_joints_output(self):
        self.assertEqual(self.client.joints_output, "mj_r_joints_pos")

    def test_hand_pos_id(self):
        self.assertEqual(self.client.hand_pos_id, "r_hand_pos")

    def test_hand_quat_id(self):
        self.assertEqual(self.client.hand_quat_id, "r_hand_quat")

    def test_tip_names(self):
        self.assertEqual(
            self.client.tip_names,
            ["r_tip1", "r_tip2", "r_tip3", "r_tip4"],
        )

    def test_finger_keys(self):
        self.assertEqual(
            self.client.finger_keys,
            ["r_finger1", "r_finger2", "r_finger3", "r_finger4"],
        )

    def test_mocap_offsets_is_right(self):
        self.assertEqual(
            self.client.mocap_offsets,
            common.MOCAP_POS_OFFSETS["right"],
        )


@unittest.skipIf(common is None, "mj_mink_common not importable")
@unittest.skipIf(not _scene_exists("left"), "AH_Left scene.xml not found")
class TestClientLeftAttrs(unittest.TestCase):
    def setUp(self):
        with patch.object(common, "Node", MagicMock()):
            self.client = common.Client(side="left", mode="pos")

    def test_prefix(self):
        self.assertEqual(self.client.prefix, "l_")

    def test_joints_output(self):
        self.assertEqual(self.client.joints_output, "mj_l_joints_pos")

    def test_hand_pos_id(self):
        self.assertEqual(self.client.hand_pos_id, "l_hand_pos")

    def test_tip_names(self):
        self.assertEqual(
            self.client.tip_names,
            ["l_tip1", "l_tip2", "l_tip3", "l_tip4"],
        )

    def test_finger_keys(self):
        self.assertEqual(
            self.client.finger_keys,
            ["l_finger1", "l_finger2", "l_finger3", "l_finger4"],
        )

    def test_mocap_offsets_is_left(self):
        self.assertEqual(
            self.client.mocap_offsets,
            common.MOCAP_POS_OFFSETS["left"],
        )


if __name__ == "__main__":
    unittest.main()
