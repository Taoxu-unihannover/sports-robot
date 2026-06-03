import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from flight_model import BallFlightModel, FlightState


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

