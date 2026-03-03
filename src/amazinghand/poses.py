# Code derived from Pollen Robotics AmazingHand.
# See: https://github.com/pollen-robotics/AmazingHand
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

"""Named poses for Amazing Hand. Each pose is list of 4 (angle_1_deg, angle_2_deg) per finger."""

HAND_RIGHT = 1
HAND_LEFT = 2

# Pose: list of 4 (a1, a2) tuples for index, middle, ring, thumb.
# Side-specific poses are dicts: {HAND_RIGHT: pose, HAND_LEFT: pose}

_POSES = {
    "open": [(-35, 35)] * 4,
    "close": [(90, -90)] * 4,
    "rock": [(90, -90)] * 4,
    "paper_right": [(4, 90), (-32, 32), (-90, -4), (-90, -4)],
    "paper_left": [(-60, 0), (-35, 35), (-4, 90), (-4, 90)],
    "scissors_right": [(-15, 65), (-65, 15), (90, -90), (90, -90)],
    "scissors_left": [(-65, 15), (-15, 65), (90, -90), (90, -90)],
    "ready": [(-35, 35)] * 4,
    "spread_right": [(4, 90), (-32, 32), (-90, -4), (-90, -4)],
    "spread_left": [(-60, 0), (-35, 35), (-4, 90), (-4, 90)],
    "clench_right": [(-60, 0), (-35, 35), (0, 70), (-4, 90)],
    "clench_left": [(0, 60), (-35, 35), (-70, 0), (-90, -4)],
    "index_pointing": [(-40, 40), (90, -90), (90, -90), (90, -90)],
    "perfect_right": [(50, -50), (0, 0), (-20, 20), (65, 12)],
    "perfect_left": [(50, -50), (0, 0), (-20, 20), (-12, -65)],
    "victory_right": [(-15, 65), (-65, 15), (90, -90), (90, -90)],
    "victory_left": [(-65, 15), (-15, 65), (90, -90), (90, -90)],
    "pinched_right": [(90, -90), (90, -90), (90, -90), (0, -75)],
    "pinched_left": [(90, -90), (90, -90), (90, -90), (75, 5)],
    "middle_right": [(90, -90), (-35, 35), (90, -90), (0, -75)],
    "middle_left": [(90, -90), (-35, 35), (90, -90), (75, 0)],
}


def get_pose(name: str, side: int) -> list[tuple[float, float]]:
    """Resolve pose by name and hand side. Returns list of 4 (a1, a2) tuples."""
    name_lower = name.lower().strip()
    if name_lower in ("open", "close", "rock", "ready", "index_pointing"):
        return _POSES[name_lower]
    if name_lower == "paper":
        return _POSES["paper_right"] if side == HAND_RIGHT else _POSES["paper_left"]
    if name_lower == "scissors":
        return _POSES["scissors_right"] if side == HAND_RIGHT else _POSES["scissors_left"]
    if name_lower == "spread":
        return _POSES["spread_right"] if side == HAND_RIGHT else _POSES["spread_left"]
    if name_lower == "clench":
        return _POSES["clench_right"] if side == HAND_RIGHT else _POSES["clench_left"]
    if name_lower == "perfect":
        return _POSES["perfect_right"] if side == HAND_RIGHT else _POSES["perfect_left"]
    if name_lower == "victory":
        return _POSES["victory_right"] if side == HAND_RIGHT else _POSES["victory_left"]
    if name_lower == "pinched":
        return _POSES["pinched_right"] if side == HAND_RIGHT else _POSES["pinched_left"]
    if name_lower == "middle":
        return _POSES["middle_right"] if side == HAND_RIGHT else _POSES["middle_left"]
    if name_lower in _POSES:
        return _POSES[name_lower]
    raise ValueError(f"Unknown pose: {name}. Use list_poses() for valid names.")


def list_poses() -> list[str]:
    """Return user-facing pose names (rock, paper, scissors, ready, etc.)."""
    return [
        "open",
        "close",
        "rock",
        "paper",
        "scissors",
        "ready",
        "spread",
        "clench",
        "index_pointing",
        "perfect",
        "victory",
        "pinched",
        "middle",
    ]
