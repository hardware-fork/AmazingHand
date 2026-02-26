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
from unittest.mock import MagicMock

import numpy as np

# HandTracking package: Demo/HandTracking/HandTracking/
_DEMO_ROOT = Path(__file__).resolve().parent.parent
_HANDTRACKING_ROOT = _DEMO_ROOT / "HandTracking"
sys.path.insert(0, str(_HANDTRACKING_ROOT))

import mediapipe as mp
from HandTracking.main import _hand_frame, _landmark_vec, _tip_vector, process_img

mp_hands = mp.solutions.hands


def _make_landmarks(landmark_dict):
    """Create mock landmarks: landmark_dict maps HandLandmark idx -> (x, y, z)."""
    class Landmark:
        pass

    class Landmarks:
        def __init__(self, d):
            self.landmark = {}
            for idx, (x, y, z) in d.items():
                lm = Landmark()
                lm.x, lm.y, lm.z = x, y, z
                self.landmark[idx] = lm

    return Landmarks(landmark_dict)


class TestLandmarkVec:
    def test_returns_numpy_array(self):
        lm = _make_landmarks({0: (1.0, 2.0, 3.0)})
        out = _landmark_vec(lm, 0)
        np.testing.assert_array_equal(out, [1.0, 2.0, 3.0])

    def test_different_indices(self):
        lm = _make_landmarks({5: (0.1, 0.2, 0.3), 9: (-1.0, 0.0, 1.0)})
        np.testing.assert_array_equal(_landmark_vec(lm, 5), [0.1, 0.2, 0.3])
        np.testing.assert_array_equal(_landmark_vec(lm, 9), [-1.0, 0.0, 1.0])


class TestTipVector:
    def test_tip_minus_mcp(self):
        lm = _make_landmarks({
            mp_hands.HandLandmark.INDEX_FINGER_TIP: (1.0, 2.0, 3.0),
            mp_hands.HandLandmark.INDEX_FINGER_MCP: (0.0, 1.0, 2.0),
        })
        out = _tip_vector(lm, mp_hands.HandLandmark.INDEX_FINGER_TIP, mp_hands.HandLandmark.INDEX_FINGER_MCP)
        np.testing.assert_array_equal(out, [1.0, 1.0, 1.0])


class TestHandFrame:
    def test_returns_3x3_rotation_matrix(self):
        # Wrist at origin, middle MCP along z, pinky MCP for y
        lm = _make_landmarks({
            mp_hands.HandLandmark.WRIST: (0.0, 0.0, 0.0),
            mp_hands.HandLandmark.MIDDLE_FINGER_MCP: (0.0, 0.0, 1.0),
            mp_hands.HandLandmark.PINKY_MCP: (0.0, 1.0, 0.0),
            mp_hands.HandLandmark.INDEX_FINGER_MCP: (0.0, -1.0, 0.0),
        })
        R = _hand_frame(lm, is_right=True)
        assert R.shape == (3, 3)
        # R should be orthogonal
        np.testing.assert_array_almost_equal(R @ R.T, np.eye(3))

    def test_left_hand_uses_index_mcp_for_y(self):
        lm = _make_landmarks({
            mp_hands.HandLandmark.WRIST: (0.0, 0.0, 0.0),
            mp_hands.HandLandmark.MIDDLE_FINGER_MCP: (0.0, 0.0, 1.0),
            mp_hands.HandLandmark.PINKY_MCP: (1.0, 0.0, 0.0),
            mp_hands.HandLandmark.INDEX_FINGER_MCP: (0.0, 1.0, 0.0),
        })
        R = _hand_frame(lm, is_right=False)
        assert R.shape == (3, 3)
        np.testing.assert_array_almost_equal(R @ R.T, np.eye(3))


class TestProcessImg:
    def test_no_hands_returns_none_results(self):
        mock_proc = MagicMock()
        mock_proc.process.return_value = MagicMock(multi_hand_landmarks=None)
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        _, r_res, l_res = process_img(mock_proc, img.copy())
        assert r_res is None
        assert l_res is None
