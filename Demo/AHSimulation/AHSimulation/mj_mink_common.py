"""Shared Mujoco client for left/right hand simulation nodes."""

import argparse
import os
import sys
import time
from pathlib import Path

import mujoco
import mujoco.viewer
import numpy as np
import pyarrow as pa
from dora import Node

import mink
from loop_rate_limiters import RateLimiter

ROOT_PATH = Path(os.path.dirname(os.path.abspath(__file__))).parent

# Per-tip (dx, dy, dz) for pos: result = x*1.5+dx, y*1.5+dy, z*1.5+dz
MOCAP_POS_OFFSETS = {
    "right": [
        (-0.025, 0.022, 0.098),
        (-0.025, -0.009, 0.092),
        (-0.025, -0.040, 0.082),
        (0.024, 0.019, 0.017),
    ],
    "left": [
        (0.025, -0.022, 0.098),
        (0.025, 0.009, 0.092),
        (0.025, 0.040, 0.082),
        (0.024, -0.019, 0.017),
    ],
}


class Client:
    """Mujoco client for one hand (left or right)."""

    def __init__(self, side, mode="pos"):
        if side not in ("left", "right"):
            raise ValueError(f"side must be 'left' or 'right', got {side!r}")
        self.side = side
        self.prefix = "r_" if side == "right" else "l_"
        scene_dir = "AH_Right" if side == "right" else "AH_Left"
        self.joints_output = f"mj_{self.prefix[0]}_joints_pos"
        self.hand_pos_id = f"{self.prefix}hand_pos"
        self.hand_quat_id = f"{self.prefix}hand_quat"
        self.mocap_offsets = MOCAP_POS_OFFSETS[side]
        self.tip_names = [f"{self.prefix}tip{i}" for i in range(1, 5)]
        self.finger_keys = [f"{self.prefix}finger{i}" for i in range(1, 5)]

        self.model = mujoco.MjModel.from_xml_path(
            f"{ROOT_PATH}/AHSimulation/{scene_dir}/mjcf/scene.xml"
        )
        self.configuration = mink.Configuration(self.model)
        self.posture_task = mink.PostureTask(self.model, cost=1e-2)

        pos_cost = 1.0 if mode == "pos" else 0.0
        ori_cost = 0.0 if mode == "pos" else 1.0
        self.task1 = mink.FrameTask(
            frame_name="tip1", frame_type="site",
            position_cost=pos_cost, orientation_cost=ori_cost, lm_damping=1.0,
        )
        self.task2 = mink.FrameTask(
            frame_name="tip2", frame_type="site",
            position_cost=pos_cost, orientation_cost=ori_cost, lm_damping=1.0,
        )
        self.task3 = mink.FrameTask(
            frame_name="tip3", frame_type="site",
            position_cost=pos_cost, orientation_cost=ori_cost, lm_damping=1.0,
        )
        self.task4 = mink.FrameTask(
            frame_name="tip4", frame_type="site",
            position_cost=pos_cost, orientation_cost=ori_cost, lm_damping=1.0,
        )
        if mode not in ("pos", "quat"):
            raise ValueError(f"unknown mode: {mode}")
        eq_task = mink.EqualityConstraintTask(self.model, cost=1000.0)
        self.tasks = [
            eq_task,
            self.posture_task,
            self.task1,
            self.task2,
            self.task3,
            self.task4,
        ]

        self.model = self.configuration.model
        self.data = self.configuration.data
        self.solver = "quadprog"
        self.motor_pos = []
        self.metadata = []
        self.node = Node()

    def run(self):
        with mujoco.viewer.launch_passive(self.model, self.data) as viewer:
            rate = RateLimiter(frequency=1000.0)
            self.configuration.update_from_keyframe("zero")
            self.posture_task.set_target_from_configuration(self.configuration)
            mink.move_mocap_to_frame(self.model, self.data, "finger1_target", "tip1", "site")
            mink.move_mocap_to_frame(self.model, self.data, "finger2_target", "tip2", "site")
            mink.move_mocap_to_frame(self.model, self.data, "finger3_target", "tip3", "site")
            mink.move_mocap_to_frame(self.model, self.data, "finger4_target", "tip4", "site")

            for event in self.node:
                event_type = event["type"]
                if event_type == "INPUT":
                    event_id = event["id"]
                    if event_id == "tick":
                        if not viewer.is_running():
                            break
                        step_start = time.time()
                        self.task1.set_target(
                            mink.SE3.from_mocap_name(self.model, self.data, "finger1_target")
                        )
                        self.task2.set_target(
                            mink.SE3.from_mocap_name(self.model, self.data, "finger2_target")
                        )
                        self.task3.set_target(
                            mink.SE3.from_mocap_name(self.model, self.data, "finger3_target")
                        )
                        self.task4.set_target(
                            mink.SE3.from_mocap_name(self.model, self.data, "finger4_target")
                        )
                        vel = mink.solve_ik(
                            self.configuration, self.tasks, rate.dt, self.solver, 1e-5
                        )
                        self.configuration.integrate_inplace(vel, rate.dt)

                        f1_m1 = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "finger1_motor1")
                        f1_m2 = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "finger1_motor2")
                        f2_m1 = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "finger2_motor1")
                        f2_m2 = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "finger2_motor2")
                        f3_m1 = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "finger3_motor1")
                        f3_m2 = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "finger3_motor2")
                        f4_m1 = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "finger4_motor1")
                        f4_m2 = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "finger4_motor2")
                        self.metadata = dict(event["metadata"])
                        for i, key in enumerate(self.finger_keys):
                            self.metadata[key] = [2 * i, 2 * i + 1]
                        self.motor_pos = np.zeros(8)
                        self.motor_pos[self.metadata[self.finger_keys[0]]] = np.array(
                            [self.data.joint(f1_m1).qpos[0], self.data.joint(f1_m2).qpos[0]]
                        )
                        self.motor_pos[self.metadata[self.finger_keys[1]]] = np.array(
                            [self.data.joint(f2_m1).qpos[0], self.data.joint(f2_m2).qpos[0]]
                        )
                        self.motor_pos[self.metadata[self.finger_keys[2]]] = np.array(
                            [self.data.joint(f3_m1).qpos[0], self.data.joint(f3_m2).qpos[0]]
                        )
                        self.motor_pos[self.metadata[self.finger_keys[3]]] = np.array(
                            [self.data.joint(f4_m1).qpos[0], self.data.joint(f4_m2).qpos[0]]
                        )

                        viewer.sync()
                        time_until_next_step = self.model.opt.timestep - (time.time() - step_start)
                        if time_until_next_step > 0:
                            time.sleep(time_until_next_step)

                    elif event_id == "pull_position":
                        self.pull_position(self.node, event["metadata"])
                    elif event_id == "tick_ctrl":
                        if len(self.metadata) > 0:
                            self.node.send_output(
                                self.joints_output, pa.array(self.motor_pos), self.metadata
                            )
                    elif event_id == "pull_velocity":
                        self.pull_velocity(self.node, event["metadata"])
                    elif event_id == "pull_current":
                        self.pull_current(self.node, event["metadata"])
                    elif event_id == "write_goal_position":
                        self.write_goal_position(event["value"])
                    elif event_id == self.hand_pos_id:
                        self.write_mocap_pos(event["value"])
                    elif event_id == self.hand_quat_id:
                        self.write_mocap_quat(event["value"])
                    elif event_id == "end":
                        break

                elif event_type == "STOP":
                    break
                elif event_type == "ERROR":
                    raise ValueError("An error occurred in the dataflow: " + event["error"])

            self.node.send_output("end", pa.array([]))

    def pull_position(self, node, metadata):
        pass

    def pull_velocity(self, node, metadata):
        pass

    def pull_current(self, node, metadata):
        pass

    def write_goal_position(self, goal_position_with_joints):
        joints = goal_position_with_joints.field("joints")
        goal_position = goal_position_with_joints.field("values")
        for i, joint in enumerate(joints):
            self.data.joint(joint.as_py()).qpos[0] = goal_position[i].as_py()

    def write_mocap_pos(self, hand):
        hand0 = hand[0]
        scale = 1.5
        for i, tip in enumerate(self.tip_names):
            if tip in hand0:
                x, y, z = hand0[tip].values
                dx, dy, dz = self.mocap_offsets[i]
                self.data.mocap_pos[i] = [
                    x.as_py() * scale + dx,
                    y.as_py() * scale + dy,
                    z.as_py() * scale + dz,
                ]

    def write_mocap_quat(self, hand):
        hand0 = hand[0]
        for i, tip in enumerate(self.tip_names):
            if tip in hand0:
                w, x, y, z = hand0[tip].values
                self.data.mocap_quat[i] = [
                    w.as_py(), x.as_py(), y.as_py(), z.as_py(),
                ]


def run_main(side):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m", "--mode", type=str, choices=["pos", "quat"], default="pos",
        help="control mode: pos=position, quat=quaternion",
    )
    args = parser.parse_args()
    client = Client(side=side, mode=args.mode)
    try:
        client.run()
    except KeyboardInterrupt:
        sys.exit(0)
    except RuntimeError as e:
        if "event stream" in str(e) or "subscribe failed" in str(e) or "exited before" in str(e):
            sys.exit(0)
        raise
