import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from robot_dynamics import FrictionParams, LinkParams, PlanarDynamicsModel, step_dynamics


def test_mass_matrix_symmetric():
    links = [LinkParams(mass=1.0, length=0.5), LinkParams(mass=0.5, length=0.3)]
    model = PlanarDynamicsModel(links)
    M = model.mass_matrix([0.3, -0.5])
    assert np.allclose(M, M.T)


def test_mass_matrix_positive_definite():
    links = [LinkParams(mass=2.0, length=0.4), LinkParams(mass=1.0, length=0.3)]
    model = PlanarDynamicsModel(links)
    M = model.mass_matrix([0.1, 0.2])
    eigvals = np.linalg.eigvalsh(M)
    assert np.all(eigvals > 0)


def test_inverse_dynamics_output_shape():
    links = [LinkParams(mass=1.0, length=0.5), LinkParams(mass=0.5, length=0.3)]
    model = PlanarDynamicsModel(links)
    tau = model.inverse_dynamics([0.0, 0.0], [0.0, 0.0], [0.0, 0.0])
    assert tau.shape == (2,)


def test_inverse_dynamics_gravity_only():
    links = [LinkParams(mass=1.0, length=0.5)]
    model = PlanarDynamicsModel(links, gravity=9.81)
    tau = model.inverse_dynamics([0.0], [0.0], [0.0])
    assert tau[0] != 0.0


def test_forward_dynamics_zero_torque():
    links = [LinkParams(mass=1.0, length=0.5)]
    model = PlanarDynamicsModel(links, gravity=9.81)
    qdd = model.forward_dynamics([0.0], [0.0], [0.0])
    assert qdd.shape == (1,)


def test_forward_inverse_consistency():
    links = [LinkParams(mass=1.0, length=0.5), LinkParams(mass=0.5, length=0.3)]
    model = PlanarDynamicsModel(links)
    q = [0.3, -0.5]
    qd = [0.5, -0.2]
    qdd = [1.0, -0.5]
    tau = model.inverse_dynamics(q, qd, qdd)
    qdd_recovered = model.forward_dynamics(q, qd, tau)
    assert np.allclose(qdd_recovered, qdd, atol=1e-6)


def test_friction_effects():
    links = [LinkParams(mass=1.0, length=0.5)]
    model = PlanarDynamicsModel(links)
    friction = FrictionParams(viscous=np.array([0.1]), coulomb=np.array([0.05]))
    tau_no_friction = model.inverse_dynamics([0.0], [1.0], [0.0])
    tau_with_friction = model.inverse_dynamics([0.0], [1.0], [0.0], friction=friction)
    assert abs(tau_with_friction[0]) >= abs(tau_no_friction[0])


def test_torque_feasibility():
    links = [LinkParams(mass=1.0, length=0.5)]
    model = PlanarDynamicsModel(links)
    result = model.torque_feasibility([0.0], [0.0], [0.0], [10.0])
    assert result["feasible"] is True
    assert result["margin"] > 0


def test_step_dynamics():
    links = [LinkParams(mass=1.0, length=0.5)]
    model = PlanarDynamicsModel(links)
    q_new, qd_new = step_dynamics(model, [0.0], [0.0], [0.0], 0.001)
    assert len(q_new) == 1
    assert len(qd_new) == 1
