"""End-to-end execution pipeline for mapping commands to hardware envelopes."""

import argparse
import os
import sys

import yaml

_SKILLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "skills")
for _skill in ["ball-launcher-executor", "high-speed-manipulator", "mobile-base-executor", "whole-body-executor", "servo-drive-safety"]:
    sys.path.insert(0, os.path.join(_SKILLS_DIR, _skill, "scripts"))

from launcher_executor import LauncherModel
from manipulator_executor import trapezoid_profile
from mobile_base_executor import pure_pursuit_command
from servo_safety import ServoLimit, check_servo_command
from whole_body_executor import allocate_task_delta


class ExecutionPipeline:
    def __init__(self, config_path: str):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        self.launcher = LauncherModel(**self.config["launcher"])
        self.servo_limit = ServoLimit(**self.config["servo"])

    def execute_preview(self, target_velocity, arm_distance, base_pose, waypoint):
        launcher_command = self.launcher.command_for_velocity(target_velocity)
        manipulator = self.config["manipulator"]
        arm_profile = trapezoid_profile(arm_distance, manipulator["max_velocity"], manipulator["max_acceleration"], manipulator["dt"])
        base_command = pure_pursuit_command(base_pose, waypoint, self.config["base"]["linear_speed"], self.config["base"]["angular_gain"])
        base_delta, arm_delta = allocate_task_delta([arm_distance, 0, 0], base_weight=0.25)
        ok, reason = check_servo_command(0.0, arm_profile[0].velocity, 5.0, self.servo_limit)
        return {"status": "ok" if ok else "unsafe", "reason": reason, "launcher": launcher_command, "arm_profile": arm_profile, "base_command": base_command, "base_delta": base_delta, "arm_delta": arm_delta}


def main():
    parser = argparse.ArgumentParser(description="Ball execution pipeline")
    parser.add_argument("--config", default=os.path.join(os.path.dirname(__file__), "..", "assets", "config.yaml"))
    args = parser.parse_args()
    pipeline = ExecutionPipeline(args.config)
    result = pipeline.execute_preview([6, 0, 1], 0.5, [0, 0, 0], [1, 0])
    print(f"{result['status']} points={len(result['arm_profile'])}")


if __name__ == "__main__":
    main()
