import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from hit_planner import BallSample, HitPlanner, paddle_normal_for_velocity_change


def test_selects_reachable_hit():
    planner = HitPlanner(workspace_radius=1.0)
    samples = [BallSample(0.2, [0.4, 0, 0.8], [-2, 0, 0])]
    plan = planner.select_hit(samples, [1.5, 0, 0])
    assert plan is not None
    assert np.allclose(plan.contact_position, [0.4, 0, 0.8])


def test_rejects_outside_workspace():
    planner = HitPlanner(workspace_radius=0.5)
    assert planner.select_hit([BallSample(0.2, [1.0, 0, 0.8], [-2, 0, 0])], [1, 0, 0]) is None


def test_paddle_normal_unit():
    n = paddle_normal_for_velocity_change([0, 0, 0], [1, 1, 0])
    assert abs(np.linalg.norm(n) - 1.0) < 1e-12

