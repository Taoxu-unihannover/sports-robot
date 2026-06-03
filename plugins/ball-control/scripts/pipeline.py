"""End-to-end control pipeline for selecting and supervising hit commands."""

import argparse
import os
import sys

import numpy as np
import yaml

_SKILLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "skills")
for _skill in ["hit-planner", "mpc-controller", "skill-policy-controller", "control-safety-supervisor"]:
    sys.path.insert(0, os.path.join(_SKILLS_DIR, _skill, "scripts"))

from hit_planner import BallSample, HitPlanner
from mpc_controller import LinearMPCTracker, double_integrator
from safety_supervisor import SafetyLimits, SafetySupervisor, clamp_velocity
from skill_policy import Skill, SkillLibrary


class ControlPipeline:
    def __init__(self, config_path: str):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        p = self.config["planner"]
        self.planner = HitPlanner(**p)
        A, B = double_integrator(self.config["mpc"]["dt"])
        self.tracker = LinearMPCTracker(A, B, np.diag([10.0, 1.0]), np.eye(1), self.config["mpc"]["horizon"], self.config["mpc"]["u_limit"])
        self.library = SkillLibrary()
        for item in self.config["skills"]:
            self.library.add(Skill(**item))
        self.supervisor = SafetySupervisor(SafetyLimits(**self.config["safety"]))

    def command(self, samples, target_landing, context):
        plan = self.planner.select_hit(samples, target_landing)
        if plan is None:
            return {"status": "no_plan"}
        skill = self.library.select(context)
        safe_velocity = clamp_velocity(plan.desired_outgoing_velocity, self.config["safety"]["max_speed"])
        ok, reason = self.supervisor.check(plan.contact_position, safe_velocity, plan.t)
        return {"status": "ok" if ok else "unsafe", "reason": reason, "skill": None if skill is None else skill.name, "plan": plan, "velocity": safe_velocity}


def main():
    parser = argparse.ArgumentParser(description="Ball control pipeline")
    parser.add_argument("--config", default=os.path.join(os.path.dirname(__file__), "..", "assets", "config.yaml"))
    args = parser.parse_args()
    pipeline = ControlPipeline(args.config)
    samples = [BallSample(0.2, [0.4, 0.0, 0.8], [-2, 0, 0])]
    result = pipeline.command(samples, [1.5, 0, 0], {"side": "right", "workspace_margin": 0.3})
    print(result["status"])


if __name__ == "__main__":
    main()
