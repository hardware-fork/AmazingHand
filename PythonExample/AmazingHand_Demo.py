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

import argparse
import sys
import time
import numpy as np

from common import (
    create_controller,
    default_serial_port,
    get_demo_hand_config,
    load_config,
)

HAND_RIGHT = 1
HAND_LEFT = 2

_cfg = load_config()
_side_from_config = _cfg.get("hand_test_id") if _cfg.get("hand_test_id") is not None else _cfg.get("side")
_default_hand_used = _side_from_config is None
side = _side_from_config if _side_from_config is not None else HAND_LEFT
max_speed = _cfg.get("max_speed", 7)
close_speed = _cfg.get("close_speed", 3)

try:
    _hand = get_demo_hand_config(_cfg, side)
except ValueError as e:
    print("Hand config error:", str(e))
    sys.exit(1)
side = _hand["side"]
servo_ids = _hand["servo_ids"]
middle_pos = _hand["middle_pos"]  # degrees, one per joint (8 values)

c = None  # Set in main()

# Timings (s)
INTER_SERVO_DELAY = 0.0002
POST_MOVE_DELAY = 0.005
GESTURE_STEP_DELAY = 0.2

# Angles in pose / Move_* are degrees; converted to rad in _move_finger.
# max_speed / close_speed: controller unit for write_goal_speed (see rustypot/servo spec).


def main():
	global c, side, servo_ids, middle_pos
	# CLI overrides config side when given
	parser = argparse.ArgumentParser(description="AmazingHand demo (one hand).")
	parser.add_argument("--side", type=int, choices=(HAND_RIGHT, HAND_LEFT), default=None, help="1 = right, 2 = left (overrides config)")
	args = parser.parse_args()
	if _default_hand_used and args.side is None:
		hand_name = "right" if side == HAND_RIGHT else "left"
		print(f"Using default hand: hand_{side} ({hand_name})")
	if args.side is not None:
		try:
			_hand = get_demo_hand_config(_cfg, args.side)
		except ValueError as e:
			print("Hand config error:", str(e))
			sys.exit(1)
		side = _hand["side"]
		servo_ids = _hand["servo_ids"]
		middle_pos = _hand["middle_pos"]

	port = _cfg.get("port") or default_serial_port()
	try:
		print(f"Initializing controller on {port}...")
		c = create_controller(timeout=_cfg.get("timeout"))
		print("Controller initialized successfully!")
	except RuntimeError as e:
		print(f"Failed to initialize controller: {e}")
		print(f"Check that the device is powered on and connected to {port}.")
		return

	c.write_torque_enable(servo_ids[0], 1)  # 1 = On, 2 = Off, 3 = Free

	# Demo loop: run gesture sequence repeatedly
	while True:
		print("OpenHand")
		OpenHand()
		time.sleep(0.5)

		print("CloseHand")
		CloseHand()
		time.sleep(3)

		print("OpenHand_Progressive")
		OpenHand_Progressive()
		time.sleep(0.5)

		print("SpreadHand")
		SpreadHand()
		time.sleep(0.6)
		print("ClenchHand")
		ClenchHand()
		time.sleep(0.6)

		print("OpenHand")
		OpenHand()
		time.sleep(0.2)

		print("Index_Pointing")
		Index_Pointing()
		time.sleep(0.4)
		print("Nonono")
		Nonono()
		time.sleep(0.5)

		print("OpenHand")
		OpenHand()
		time.sleep(0.3)

		print("Perfect")
		Perfect()
		time.sleep(0.8)

		print("OpenHand")
		OpenHand()
		time.sleep(0.4)

		print("Victory")
		Victory()
		time.sleep(1)
		print("Scissors")
		Scissors()
		time.sleep(0.5)

		print("OpenHand")
		OpenHand()
		time.sleep(0.4)

		print("Pinched")
		Pinched()
		time.sleep(1)

		print("Fuck")
		Fuck()
		time.sleep(0.8)


		#trials

		#c.sync_write_raw_goal_position([1,2], [50,50])
		#time.sleep(1)

		#a=c.read_present_position(1)
		#b=c.read_present_position(2)
		#a=np.rad2deg(a)
		#b=np.rad2deg(b)
		#print(f'{a} {b}')
		#time.sleep(0.001)



def OpenHand():
    # Index, Middle, Ring, Thumb: open angles (same left/right)
    pose = [(-35, 35)] * 4
    _apply_pose(pose, max_speed)


def CloseHand():
    pose = [(90, -90)] * 4
    # Thumb (finger 3) uses slightly higher close speed
    for finger_idx, (a1, a2) in enumerate(pose):
        speed = close_speed + 1 if finger_idx == 3 else close_speed
        _move_finger(finger_idx, a1, a2, speed)


def OpenHand_Progressive():
    # Open each finger in sequence with delay between
    pose = [(-35, 35)] * 4
    speed = max_speed - 2
    for finger_idx, (a1, a2) in enumerate(pose):
        _move_finger(finger_idx, a1, a2, speed)
        time.sleep(GESTURE_STEP_DELAY)


def SpreadHand():
    # Right: fingers splayed out; left: mirror angles
    if side == HAND_RIGHT:
        pose = [(4, 90), (-32, 32), (-90, -4), (-90, -4)]
    else:
        pose = [(-60, 0), (-35, 35), (-4, 90), (-4, 90)]
    _apply_pose(pose, max_speed)


def ClenchHand():
    # Right: curl in one direction; left: mirror
    if side == HAND_RIGHT:
        pose = [(-60, 0), (-35, 35), (0, 70), (-4, 90)]
    else:
        pose = [(0, 60), (-35, 35), (-70, 0), (-90, -4)]
    _apply_pose(pose, max_speed)


def Index_Pointing():
    # Index extended, others closed (same left/right)
    pose = [(-40, 40), (90, -90), (90, -90), (90, -90)]
    _apply_pose(pose, max_speed)


def Nonono():
    # Index pointing, then wag index 3 times, then open
    Index_Pointing()
    for _ in range(3):
        time.sleep(GESTURE_STEP_DELAY)
        Move_Index(-10, 80, max_speed)
        time.sleep(GESTURE_STEP_DELAY)
        Move_Index(-80, 10, max_speed)
    Move_Index(-35, 35, max_speed)
    time.sleep(0.4)


def Perfect():
    # OK sign: thumb and index circle; middle/ring slight curl
    if side == HAND_RIGHT:
        pose = [(50, -50), (0, 0), (-20, 20), (65, 12)]
    else:
        pose = [(50, -50), (0, 0), (-20, 20), (-12, -65)]
    _apply_pose(pose, max_speed)


def Victory():
    # Index and middle extended; ring and thumb closed
    if side == HAND_RIGHT:
        pose = [(-15, 65), (-65, 15), (90, -90), (90, -90)]
    else:
        pose = [(-65, 15), (-15, 65), (90, -90), (90, -90)]
    _apply_pose(pose, max_speed)


def Pinched():
    # Index/middle/ring closed; thumb to pinch
    if side == HAND_RIGHT:
        pose = [(90, -90), (90, -90), (90, -90), (0, -75)]
    else:
        pose = [(90, -90), (90, -90), (90, -90), (75, 5)]
    _apply_pose(pose, max_speed)


def Scissors():
    # Victory then open/close index and middle 3 times
    Victory()
    if side == HAND_RIGHT:
        for _ in range(3):
            time.sleep(GESTURE_STEP_DELAY)
            Move_Index(-50, 20, max_speed)
            Move_Middle(-20, 50, max_speed)
            time.sleep(GESTURE_STEP_DELAY)
            Move_Index(-15, 65, max_speed)
            Move_Middle(-65, 15, max_speed)
    else:
        for _ in range(3):
            time.sleep(GESTURE_STEP_DELAY)
            Move_Index(-20, 50, max_speed)
            Move_Middle(-50, 20, max_speed)
            time.sleep(GESTURE_STEP_DELAY)
            Move_Index(-65, 15, max_speed)
            Move_Middle(-15, 65, max_speed)


def Fuck():
    # Middle extended; index/ring closed; thumb orientation by side
    if side == HAND_RIGHT:
        pose = [(90, -90), (-35, 35), (90, -90), (0, -75)]
    else:
        pose = [(90, -90), (-35, 35), (90, -90), (75, 0)]
    _apply_pose(pose, max_speed)


def _move_finger(finger_idx, angle_1_deg, angle_2_deg, speed_controller_unit):
    """Move one finger (0=Index, 1=Middle, 2=Ring, 3=Thumb).
    Angles in degrees; speed_controller_unit passed to write_goal_speed (see rustypot/servo spec)."""
    i, j = 2 * finger_idx, 2 * finger_idx + 1
    c.write_goal_speed(servo_ids[i], speed_controller_unit)
    time.sleep(INTER_SERVO_DELAY)
    c.write_goal_speed(servo_ids[j], speed_controller_unit)
    time.sleep(INTER_SERVO_DELAY)
    c.write_goal_position(servo_ids[i], np.deg2rad(middle_pos[i] + angle_1_deg))
    c.write_goal_position(servo_ids[j], np.deg2rad(middle_pos[j] + angle_2_deg))
    time.sleep(POST_MOVE_DELAY)


def _apply_pose(pose, speed_controller_unit):
    """Apply a pose to all fingers. pose: list of 4 (angle_1_deg, angle_2_deg) per finger.
    speed_controller_unit: value for write_goal_speed (controller unit, not RPM)."""
    for finger_idx, (a1, a2) in enumerate(pose):
        _move_finger(finger_idx, a1, a2, speed_controller_unit)


def Move_Index(angle_1_deg, angle_2_deg, speed_controller_unit):
    # Finger 0: Index (servo_ids 0, 1). Angles in degrees; speed in controller unit.
    _move_finger(0, angle_1_deg, angle_2_deg, speed_controller_unit)


def Move_Middle(angle_1_deg, angle_2_deg, speed_controller_unit):
    # Finger 1: Middle (servo_ids 2, 3). Angles in degrees; speed in controller unit.
    _move_finger(1, angle_1_deg, angle_2_deg, speed_controller_unit)


def Move_Ring(angle_1_deg, angle_2_deg, speed_controller_unit):
    # Finger 2: Ring (servo_ids 4, 5). Angles in degrees; speed in controller unit.
    _move_finger(2, angle_1_deg, angle_2_deg, speed_controller_unit)


def Move_Thumb(angle_1_deg, angle_2_deg, speed_controller_unit):
    # Finger 3: Thumb (servo_ids 6, 7). Angles in degrees; speed in controller unit.
    _move_finger(3, angle_1_deg, angle_2_deg, speed_controller_unit)


if __name__ == '__main__':
	main()
