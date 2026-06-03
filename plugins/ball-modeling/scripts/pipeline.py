"""End-to-end modeling pipeline for ball robot prediction."""

import argparse
import os
import sys

import numpy as np
import yaml

_SKILLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "skills")
for _skill in [
    "ball-kinematic-model",
    "ball-flight-model",
    "ball-impact-contact",
    "model-uncertainty-risk",
]:
    sys.path.insert(0, os.path.join(_SKILLS_DIR, _skill, "scripts"))

from flight_model import BallFlightModel, FlightState
from impact_contact import PaddleImpactModel
from kinematic_model import PlanarArmModel
from uncertainty_risk import risk_score


class ModelingPipeline:
    def __init__(self, config_path: str):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        kin = self.config["kinematics"]
        flight = self.config["flight"]
        impact = self.config["impact"]
        self.arm = PlanarArmModel(kin["link_lengths"])
        self.flight = BallFlightModel(**flight)
        self.impact = PaddleImpactModel(**impact)

    def predict_hit(self, q, incoming_position, incoming_velocity, paddle_velocity, paddle_normal, dt=0.01, steps=50):
        pose = self.arm.forward(q)
        outgoing = self.impact.impact(incoming_velocity, paddle_velocity, paddle_normal)
        states = self.flight.rollout(FlightState(incoming_position, outgoing), dt=dt, steps=steps)
        margin = self.arm.workspace_margin([pose.x, pose.y])
        risk = risk_score(time_to_impact=dt * steps, position_sigma=0.03, workspace_margin=margin)
        return {"contact_pose": pose, "outgoing_velocity": outgoing, "states": states, "risk": risk}


def main():
    parser = argparse.ArgumentParser(description="Ball modeling pipeline")
    parser.add_argument("--config", default=os.path.join(os.path.dirname(__file__), "..", "assets", "config.yaml"))
    args = parser.parse_args()
    pipeline = ModelingPipeline(args.config)
    result = pipeline.predict_hit([0.1, -0.2, 0.3], [0, 0, 1], [5, 0, 0], [1, 0, 0], [-1, 0, 0])
    print(f"predicted_states={len(result['states'])} risk={result['risk']:.3f}")


if __name__ == "__main__":
    main()
