import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from impact_contact import (
    CompliantContactModel,
    CompliantParams,
    ContactParams,
    PaddleImpactModel,
    SurfaceContactModel,
    bounce_ground,
)


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


def test_surface_contact_table():
    model = SurfaceContactModel()
    v_after = model.impulse_contact([1, 0, -5], [0, 0, 1], contact_type="table")
    assert v_after[2] > 0
    assert abs(v_after[2] - 5 * model.table.restitution) < 0.5


def test_surface_contact_ground_lower_restitution():
    model = SurfaceContactModel()
    v_table = model.impulse_contact([1, 0, -5], [0, 0, 1], contact_type="table")
    v_ground = model.impulse_contact([1, 0, -5], [0, 0, 1], contact_type="ground")
    assert abs(v_ground[2]) < abs(v_table[2])


def test_surface_contact_paddle_with_velocity():
    model = SurfaceContactModel()
    v_after = model.impulse_contact([1, 0, -5], [0, 0, 1], surface_velocity=[0, 0, 2], contact_type="paddle")
    assert v_after[2] > 0


def test_energy_loss_positive():
    model = SurfaceContactModel()
    loss = model.energy_loss([1, 0, -5], [0, 0, 1], contact_type="table")
    assert 0.0 < loss < 1.0


def test_compliant_contact_no_penetration():
    model = CompliantContactModel()
    assert model.normal_force(-0.01, 0.0) == 0.0


def test_compliant_contact_with_penetration():
    model = CompliantContactModel()
    f = model.normal_force(0.001, 0.1)
    assert f > 0


def test_compliant_tangent_friction():
    model = CompliantContactModel(CompliantParams(friction=0.5))
    ft = model.tangent_force([1.0, 0.0], 10.0)
    assert float(np.linalg.norm(ft)) <= 0.5 * 10.0 + 1e-9
