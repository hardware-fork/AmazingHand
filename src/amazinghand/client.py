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

"""AmazingHand client - high-level API for pose and gesture control."""

import time
from pathlib import Path
from typing import Any

import numpy as np
from rustypot import Scs0009PyController

from amazinghand.config import get_config_root, get_hand_config, load_config
from amazinghand.poses import HAND_LEFT, HAND_RIGHT, get_pose, list_poses

_INTER_SERVO_DELAY = 0.0002
_POST_MOVE_DELAY = 0.005


def _default_port() -> str:
    import sys
    return "COM3" if sys.platform == "win32" else "/dev/ttyUSB0"


class AmazingHand:
    """Control Amazing Hand robotic hand via named poses and raw angles.

    Configuration:
        profile: config profile name (default from AMAZINGHAND_PROFILE or 'default')
        config_root: path to config directory (default from AMAZINGHAND_CONFIG or auto-detect)
        side: 1 = right hand, 2 = left hand (default from profile)

    Example:
        hand = AmazingHand(profile="default")
        hand.apply_pose("rock")
        hand.apply_pose("paper")
    """

    def __init__(
        self,
        profile: str | None = None,
        config_root: str | Path | None = None,
        side: int | None = None,
    ):
        self._config_root = get_config_root(config_root)
        self._cfg = load_config(profile=profile, config_root=self._config_root)
        self._side = side or self._cfg.get("hand_test_id") or self._cfg.get("side") or HAND_LEFT
        self._hand = get_hand_config(self._cfg, self._side)
        self._servo_ids = self._hand["servo_ids"]
        self._middle_pos = self._hand["middle_pos"]
        self._max_speed = self._cfg.get("max_speed", 7)
        self._close_speed = self._cfg.get("close_speed", 3)

        port = self._cfg.get("port") or _default_port()
        self._controller: Scs0009PyController = Scs0009PyController(
            serial_port=port,
            baudrate=self._cfg["baudrate"],
            timeout=self._cfg.get("timeout", 0.5),
        )
        self._controller.write_torque_enable(self._servo_ids[0], 1)

    @property
    def side(self) -> int:
        """1 = right, 2 = left."""
        return self._side

    def apply_pose(self, name: str, speed: float | None = None) -> None:
        """Apply a named pose (e.g. 'rock', 'paper', 'scissors', 'ready')."""
        pose = get_pose(name, self._side)
        sp = speed if speed is not None else self._max_speed
        if name.lower() == "close" or name.lower() == "rock":
            for finger_idx, (a1, a2) in enumerate(pose):
                s = self._close_speed + 1 if finger_idx == 3 else self._close_speed
                self._move_finger(finger_idx, a1, a2, s)
        else:
            for finger_idx, (a1, a2) in enumerate(pose):
                self._move_finger(finger_idx, a1, a2, sp)

    def apply_pose_target(self, angles: list[float] | list[tuple[float, float]], speed: float | None = None) -> None:
        """Apply raw joint angles. angles: 8 floats (rad or deg) or 4 (a1,a2) tuples in degrees."""
        sp = speed if speed is not None else self._max_speed
        if len(angles) == 4 and isinstance(angles[0], (tuple, list)):
            pose = [(float(a1), float(a2)) for a1, a2 in angles]
        elif len(angles) == 8:
            pose = [(angles[i], angles[i + 1]) for i in range(0, 8, 2)]
        else:
            raise ValueError("angles must be 8 floats or 4 (a1,a2) tuples")
        for finger_idx, (a1, a2) in enumerate(pose):
            self._move_finger(finger_idx, a1, a2, sp)

    def _move_finger(self, finger_idx: int, angle_1_deg: float, angle_2_deg: float, speed: float) -> None:
        i, j = 2 * finger_idx, 2 * finger_idx + 1
        self._controller.write_goal_speed(self._servo_ids[i], speed)
        time.sleep(_INTER_SERVO_DELAY)
        self._controller.write_goal_speed(self._servo_ids[j], speed)
        time.sleep(_INTER_SERVO_DELAY)
        self._controller.write_goal_position(
            self._servo_ids[i], np.deg2rad(self._middle_pos[i] + angle_1_deg)
        )
        self._controller.write_goal_position(
            self._servo_ids[j], np.deg2rad(self._middle_pos[j] + angle_2_deg)
        )
        time.sleep(_POST_MOVE_DELAY)

    def torque_enable(self, enable: bool = True) -> None:
        """Enable (True) or disable (False) motors. Use disable when moving hand manually."""
        val = 1 if enable else 2
        for sid in self._servo_ids:
            self._controller.write_torque_enable(sid, val)

    def read_positions(self) -> list[float]:
        """Return current joint positions in degrees (8 values, relative to middle)."""
        degs = []
        for i, sid in enumerate(self._servo_ids):
            rad = self._controller.read_present_position(sid)
            degs.append(np.rad2deg(rad) - self._middle_pos[i])
        return degs

    def list_poses(self) -> list[str]:
        """Return available pose names."""
        return list_poses()

    def close(self) -> None:
        """Release resources. Call when done or use as context manager."""
        pass

    def __enter__(self) -> "AmazingHand":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
