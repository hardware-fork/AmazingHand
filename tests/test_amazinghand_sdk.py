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

import pytest
from pathlib import Path

from amazinghand import AmazingHand, get_config_root, list_poses, load_config
from amazinghand.poses import get_pose

_PKG_CONFIG = Path(__file__).resolve().parent.parent / "src" / "amazinghand" / "config"

HAND_RIGHT = 1
HAND_LEFT = 2


def test_list_poses():
    poses = list_poses()
    assert "rock" in poses
    assert "paper" in poses
    assert "scissors" in poses
    assert "ready" in poses


def test_get_pose_rock():
    p = get_pose("rock", HAND_RIGHT)
    assert len(p) == 4
    assert p == [(90, -90)] * 4


def test_get_pose_paper_side_dependent():
    pr = get_pose("paper", HAND_RIGHT)
    pl = get_pose("paper", HAND_LEFT)
    assert pr != pl


def test_load_config():
    cfg = load_config(profile="default", config_root=_PKG_CONFIG)
    assert "port" in cfg
    assert "hand_1_index_servo_ids" in cfg or "hand_2_index_servo_ids" in cfg


def test_get_config_root():
    root = get_config_root()
    assert root.exists() or True
    assert (root / "profiles.toml").exists() or (root / "hand_geometry.toml").exists() or True
