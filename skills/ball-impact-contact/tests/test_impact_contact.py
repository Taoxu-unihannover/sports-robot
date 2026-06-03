import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from impact_contact import PaddleImpactModel, bounce_ground


def test_elastic_reflection_in_paddle_frame():
    model = PaddleImpactModel(restitution=1.0, tangential_damping=0.0)
    out = model.impact([1, 0, 0], [0, 0, 0], [1, 0, 0])
    assert np.allclose(out, [-1, 0, 0])


def test_moving_paddle_adds_velocity():
    model = PaddleImpactModel(restitution=1.0, tangential_damping=0.0)
    out = model.impact([-1, 0, 0], [1, 0, 0], [1, 0, 0])
    assert np.allclose(out, [3, 0, 0])


def test_ground_bounce_reverses_vertical_component():
    assert np.allclose(bounce_ground([1, 0, -2], restitution=0.5), [1, 0, 1])

