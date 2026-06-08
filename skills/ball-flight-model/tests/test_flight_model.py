import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from flight_model import BallFlightModel, FlightState, HitCandidate, ShuttleFlightModel


def test_gravity_only_matches_constant_acceleration():
    model = BallFlightModel(mass=1.0, radius=0.1, drag_coefficient=0.0)
    result = model.step(FlightState([0, 0, 1], [1, 0, 0]), 0.1)
    assert np.allclose(result.position, [0.1, 0.0, 1.0 - 0.5 * 9.81 * 0.01], atol=1e-5)


def test_drag_slows_ball():
    model = BallFlightModel(mass=0.0027, radius=0.02, drag_coefficient=0.47)
    result = model.step(FlightState([0, 0, 1], [10, 0, 0]), 0.02)
    assert np.linalg.norm(result.velocity) < 10.0


def test_plane_crossing():
    model = BallFlightModel(mass=1.0, radius=0.1, drag_coefficient=0.0, gravity=(0, 0, 0))
    hit = model.first_plane_crossing(FlightState([0, 0, 0], [1, 0, 0]), axis=0, value=0.5, dt=0.1, max_steps=10)
    assert hit is not None
    assert abs(hit.position[0] - 0.5) < 1e-9


def test_magnus_force_deflects_ball():
    model = BallFlightModel(mass=0.0027, radius=0.02, drag_coefficient=0.0, magnus_gain=0.001)
    state = FlightState([0, 0, 1], [10, 0, 0], spin=[0, 0, 100])
    result = model.step(state, 0.01)
    assert abs(result.velocity[1]) > 1e-6


def test_predict_with_bounces():
    model = BallFlightModel(mass=0.0027, radius=0.02, drag_coefficient=0.1)
    state = FlightState([0, 0, 1.0], [2, 0, 0])
    result = model.predict_with_bounces(state, dt=0.001, duration=1.0, table_height=0.0, restitution=0.9)
    assert len(result["trajectory"]) > 0
    if len(result["bounces"]) > 0:
        bounce = result["bounces"][0]
        assert bounce.velocity_after[2] > 0
        assert bounce.position[2] == 0.0


def test_extract_hit_candidates():
    model = BallFlightModel(mass=0.0027, radius=0.02, drag_coefficient=0.1)
    state = FlightState([0, 0, 0.5], [1.0, 0, -1.0])
    candidates = model.extract_hit_candidates(
        state, dt=0.001, duration=1.0,
        hit_zone_center=[0.5, 0, 0.2],
        hit_zone_radius=0.3,
        table_height=0.0,
        restitution=0.9,
    )
    assert isinstance(candidates, list)


def test_shuttle_flight_model_drag():
    model = ShuttleFlightModel(mass=0.005, drag_coefficient=0.01)
    state = FlightState([0, 0, 2.0], [5, 0, 2])
    result = model.step(state, 0.01)
    assert np.linalg.norm(result.velocity) < np.linalg.norm(state.velocity)


def test_shuttle_rollout():
    model = ShuttleFlightModel(mass=0.005, drag_coefficient=0.01)
    state = FlightState([0, 0, 2.0], [5, 0, 2])
    traj = model.rollout(state, dt=0.01, steps=100)
    assert len(traj) == 101
    assert traj[-1].position[2] < traj[0].position[2]
