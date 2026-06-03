import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from kinematic_model import PlanarArmModel, finite_difference_jacobian


def test_forward_straight_arm():
    arm = PlanarArmModel([1.0, 0.5])
    pose = arm.forward([0.0, 0.0])
    assert np.allclose([pose.x, pose.y, pose.yaw], [1.5, 0.0, 0.0])


def test_jacobian_matches_finite_difference():
    arm = PlanarArmModel([0.45, 0.35, 0.18])
    q = [0.2, -0.4, 0.7]
    assert np.allclose(arm.jacobian(q), finite_difference_jacobian(arm, q), atol=1e-5)


def test_workspace_margin():
    arm = PlanarArmModel([1.0, 1.0])
    assert arm.workspace_margin([1.0, 0.0]) > 0.0
    assert arm.workspace_margin([3.0, 0.0]) < 0.0

