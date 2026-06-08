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
    "model-identification",
    "sensor-calibration-alignment",
    "robot-dynamics-model",
]:
    sys.path.insert(0, os.path.join(_SKILLS_DIR, _skill, "scripts"))

from calibration_alignment import CalibrationParams, Extrinsics, SpatiotemporalAligner
from flight_model import BallFlightModel, FlightState
from impact_contact import PaddleImpactModel, SurfaceContactModel
from identification import RecursiveLeastSquares
from kinematic_model import PlanarArmModel
from robot_dynamics import FrictionParams, LinkParams, PlanarDynamicsModel
from uncertainty_risk import ModelSwitchController, risk_score


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
        self.surface_contact = SurfaceContactModel()
        self.aligner = SpatiotemporalAligner(CalibrationParams())
        self.model_switch = ModelSwitchController()
        dyn_cfg = self.config.get("dynamics", {})
        if dyn_cfg:
            links = [LinkParams(**lk) for lk in dyn_cfg.get("links", [])]
            self.dynamics = PlanarDynamicsModel(links, gravity=dyn_cfg.get("gravity", 9.81))
        else:
            self.dynamics = None

    def predict_hit(self, q, incoming_position, incoming_velocity, paddle_velocity, paddle_normal, dt=0.01, steps=50):
        pose = self.arm.forward(q)
        outgoing = self.impact.impact(incoming_velocity, paddle_velocity, paddle_normal)
        states = self.flight.rollout(FlightState(incoming_position, outgoing), dt=dt, steps=steps)
        margin = self.arm.workspace_margin([pose.x, pose.y])
        risk = risk_score(time_to_impact=dt * steps, position_sigma=0.03, workspace_margin=margin)
        return {"contact_pose": pose, "outgoing_velocity": outgoing, "states": states, "risk": risk}

    def predict_with_bounces(self, state_dict, dt=0.001, duration=1.0, table_height=0.0, restitution=0.9):
        state = FlightState(**state_dict)
        return self.flight.predict_with_bounces(state, dt=dt, duration=duration, table_height=table_height, restitution=restitution)

    def align_observation(self, position_camera, timestamp, sensor_id="cam0"):
        return self.aligner.full_compensate(position_camera, timestamp)

    def evaluate_model_switch(self, covariance_trace, residual_rms, current_time):
        return self.model_switch.evaluate(covariance_trace, residual_rms, current_time)

    def surface_bounce(self, ball_velocity, surface_normal, contact_type="table"):
        return self.surface_contact.impulse_contact(ball_velocity, surface_normal, contact_type=contact_type)

    def compute_inverse_dynamics(self, q, qd, qdd):
        if self.dynamics is None:
            raise RuntimeError("dynamics model not configured")
        return self.dynamics.inverse_dynamics(q, qd, qdd)


def main():
    parser = argparse.ArgumentParser(description="Ball modeling pipeline")
    parser.add_argument("--config", default=os.path.join(os.path.dirname(__file__), "..", "assets", "config.yaml"))
    args = parser.parse_args()
    pipeline = ModelingPipeline(args.config)
    result = pipeline.predict_hit([0.1, -0.2, 0.3], [0, 0, 1], [5, 0, 0], [1, 0, 0], [-1, 0, 0])
    print(f"predicted_states={len(result['states'])} risk={result['risk']:.3f}")


if __name__ == "__main__":
    main()
