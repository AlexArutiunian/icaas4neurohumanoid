#!/usr/bin/env python3
"""Simple upper-body control for the Unitree G1 Isaac Sim task.

Intended for the fixed-base G1 + Inspire simulation launched with:
    Isaac-PickPlace-RedBlock-G129-Inspire-Joint

DDS domain 1 is used to match unitree_sim_isaaclab simulation.
"""

from __future__ import annotations

import argparse
import sys
import termios
import threading
import time
import tty

from unitree_sdk2py.core.channel import (
    ChannelFactoryInitialize,
    ChannelPublisher,
    ChannelSubscriber,
)
from unitree_sdk2py.idl.default import (
    unitree_go_msg_dds__MotorCmd_,
    unitree_hg_msg_dds__LowCmd_,
)
from unitree_sdk2py.idl.unitree_go.msg.dds_ import MotorCmds_
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_, LowState_
from unitree_sdk2py.utils.crc import CRC


ARM_START = 15
ARM_COUNT = 14
MOTOR_COUNT = 29

HOME = [0.0] * ARM_COUNT
READY = [
    -0.35, 0.25, 0.00, 0.75, 0.00, 0.00, 0.00,
    -0.35, -0.25, 0.00, 0.75, 0.00, 0.00, 0.00,
]
LEFT_UP = [
    -1.00, 0.30, 0.00, 0.35, 0.00, 0.00, 0.00,
    0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00,
]
RIGHT_UP = [
    0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00,
    -1.00, -0.30, 0.00, 0.35, 0.00, 0.00, 0.00,
]
BOTH_UP = [
    -1.00, 0.30, 0.00, 0.35, 0.00, 0.00, 0.00,
    -1.00, -0.30, 0.00, 0.35, 0.00, 0.00, 0.00,
]

POSES = {
    "0": ("home", HOME),
    "1": ("left arm up", LEFT_UP),
    "2": ("right arm up", RIGHT_UP),
    "3": ("both arms up", BOTH_UP),
    "4": ("ready pose", READY),
}


class UpperBodyController:
    def __init__(self, rate_hz: float, arm_speed: float, hand_speed: float):
        self.dt = 1.0 / rate_hz
        self.arm_step = arm_speed * self.dt
        self.hand_step = hand_speed * self.dt
        self.running = True
        self.lock = threading.Lock()

        self.crc = CRC()
        self.mode_machine = 0
        self.latest_q = [0.0] * MOTOR_COUNT
        self.have_state = False

        self.arm_cmd = HOME.copy()
        self.arm_target = HOME.copy()
        self.hand_cmd = [1.0] * 12
        self.hand_target = [1.0] * 12

        self.low_cmd = unitree_hg_msg_dds__LowCmd_()
        self.inspire_cmd = MotorCmds_()
        self.inspire_cmd.cmds = [unitree_go_msg_dds__MotorCmd_() for _ in range(12)]

        self.lowcmd_pub = ChannelPublisher("rt/lowcmd", LowCmd_)
        self.lowcmd_pub.Init()

        self.inspire_pub = ChannelPublisher("rt/inspire/cmd", MotorCmds_)
        self.inspire_pub.Init()

        self.lowstate_sub = ChannelSubscriber("rt/lowstate", LowState_)
        self.lowstate_sub.Init(self._on_lowstate, 10)

        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _on_lowstate(self, msg: LowState_) -> None:
        with self.lock:
            self.mode_machine = int(msg.mode_machine)
            count = min(MOTOR_COUNT, len(msg.motor_state))
            for i in range(count):
                self.latest_q[i] = float(msg.motor_state[i].q)

            if not self.have_state and count >= MOTOR_COUNT:
                self.arm_cmd = self.latest_q[ARM_START:ARM_START + ARM_COUNT].copy()
                self.arm_target = self.arm_cmd.copy()
                self.have_state = True

    @staticmethod
    def _move_toward(current: float, target: float, max_step: float) -> float:
        delta = target - current
        if delta > max_step:
            return current + max_step
        if delta < -max_step:
            return current - max_step
        return target

    def set_pose(self, pose: list[float]) -> None:
        with self.lock:
            self.arm_target = pose.copy()

    def set_hands(self, value: float) -> None:
        with self.lock:
            self.hand_target = [value] * 12

    def _publish_arms(self) -> None:
        self.low_cmd.mode_pr = 0
        self.low_cmd.mode_machine = self.mode_machine

        for i in range(MOTOR_COUNT):
            motor = self.low_cmd.motor_cmd[i]
            motor.mode = 1
            motor.tau = 0.0
            motor.dq = 0.0
            motor.kp = 40.0
            motor.kd = 1.0
            motor.q = self.latest_q[i]

        for j, q in enumerate(self.arm_cmd):
            self.low_cmd.motor_cmd[ARM_START + j].q = float(q)

        self.low_cmd.crc = self.crc.Crc(self.low_cmd)
        self.lowcmd_pub.Write(self.low_cmd)

    def _publish_hands(self) -> None:
        for i, q in enumerate(self.hand_cmd):
            motor = self.inspire_cmd.cmds[i]
            motor.q = float(q)
            motor.dq = 0.0
            motor.tau = 0.0
            motor.kp = 1.0
            motor.kd = 0.1
        self.inspire_pub.Write(self.inspire_cmd)

    def _loop(self) -> None:
        while self.running:
            started = time.perf_counter()
            with self.lock:
                for i in range(ARM_COUNT):
                    self.arm_cmd[i] = self._move_toward(
                        self.arm_cmd[i], self.arm_target[i], self.arm_step
                    )
                for i in range(12):
                    self.hand_cmd[i] = self._move_toward(
                        self.hand_cmd[i], self.hand_target[i], self.hand_step
                    )
                self._publish_arms()
                self._publish_hands()

            delay = self.dt - (time.perf_counter() - started)
            if delay > 0:
                time.sleep(delay)

    def stop(self) -> None:
        self.running = False
        self.thread.join(timeout=1.0)


def read_key() -> str:
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def print_help() -> None:
    print(
        "\nControls:\n"
        "  0  home\n"
        "  1  left arm up\n"
        "  2  right arm up\n"
        "  3  both arms up\n"
        "  4  ready pose\n"
        "  o  open Inspire hands\n"
        "  c  close Inspire hands\n"
        "  h  show help\n"
        "  q  quit\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="G1 upper-body keyboard control for Isaac Sim")
    parser.add_argument("--domain", type=int, default=1, help="DDS domain; Isaac Sim uses 1")
    parser.add_argument("--rate", type=float, default=50.0, help="command rate, Hz")
    parser.add_argument("--arm-speed", type=float, default=1.2, help="max arm speed, rad/s")
    parser.add_argument("--hand-speed", type=float, default=2.0, help="normalized hand speed, 1/s")
    args = parser.parse_args()

    ChannelFactoryInitialize(args.domain)
    controller = UpperBodyController(args.rate, args.arm_speed, args.hand_speed)

    print("G1 upper-body controller started on DDS domain", args.domain)
    print("Waiting briefly for rt/lowstate from Isaac Sim...")
    time.sleep(1.0)
    if controller.have_state:
        print("LowState received. Initial arm pose synchronized.")
    else:
        print("LowState not received yet; commands will start from the default pose.")

    print_help()

    try:
        while True:
            key = read_key().lower()
            if key in POSES:
                name, pose = POSES[key]
                controller.set_pose(pose)
                print(name)
            elif key == "o":
                controller.set_hands(1.0)
                print("hands open")
            elif key == "c":
                controller.set_hands(0.0)
                print("hands close")
            elif key == "h":
                print_help()
            elif key == "q":
                break
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()
        print("controller stopped")


if __name__ == "__main__":
    main()
