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

import time
import numpy as np

from common import create_controller, load_config

# Config-driven; 1 = On, 2 = Off, 3 = Free for torque
TORQUE_ENABLE = 1
FINGER_SPEED = 6
DEG_CLOSE_OFFSET = 90
DEG_OPEN_OFFSET = 30

_cfg = load_config()
_ids = _cfg.get("finger_test_servo_ids", [13, 14])
_mid = _cfg.get("finger_test_middle_pos", [5, -2])
id_1, id_2 = _ids[0], _ids[1]
middle_pos_1, middle_pos_2 = _mid[0], _mid[1]
controller = create_controller(timeout=_cfg.get("timeout", 0.5))


def main():
    """Run finger open/close loop using two servos from config."""
    controller.write_torque_enable(id_1, TORQUE_ENABLE)
    controller.write_torque_enable(id_2, TORQUE_ENABLE)
    while True:
        close_finger()
        time.sleep(3)
        open_finger()
        time.sleep(1)


def close_finger():
    """Drive both servos to closed position (middle + offset)."""
    controller.write_goal_speed(id_1, FINGER_SPEED)
    controller.write_goal_speed(id_2, FINGER_SPEED)
    controller.write_goal_position(id_1, np.deg2rad(middle_pos_1 + DEG_CLOSE_OFFSET))
    controller.write_goal_position(id_2, np.deg2rad(middle_pos_2 - DEG_CLOSE_OFFSET))
    time.sleep(0.01)


def open_finger():
    """Drive both servos to open position (middle - offset)."""
    controller.write_goal_speed(id_1, FINGER_SPEED)
    controller.write_goal_speed(id_2, FINGER_SPEED)
    controller.write_goal_position(id_1, np.deg2rad(middle_pos_1 - DEG_OPEN_OFFSET))
    controller.write_goal_position(id_2, np.deg2rad(middle_pos_2 + DEG_OPEN_OFFSET))
    time.sleep(0.01)


if __name__ == "__main__":
    main()
