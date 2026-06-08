import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from kinematic_model import (
    MotionChainConfig,
    PlanarArmModel,
    Pose2D,
    SingularityInfo,
    WorkspaceAnalysis,
    finite_difference_jacobian,
)


def test_forward_kinematics_zero():
    arm = PlanarArmModel([0.3, 0.3])
    pose = arm.forward([0.0, 0.0])
    assert abs(pose.x - 0.6) < 1e-9
    assert abs(pose.y) < 1e-9


def test_forward_kinematics_ninety():
    arm = PlanarArmModel([0.3, 0.3])
    pose = arm.forward([np.pi / 2, 0.0])
    assert abs(pose.x) < 1e-9
    assert abs(pose.y - 0.6) < 1e-9


def test_jacobian_matches_finite_difference():
    arm = PlanarArmModel([0.3, 0.25])
    q = [0.5, -0.3]
    J_analytic = arm.jacobian(q)
    J_numeric = finite_difference_jacobian(arm, q)
    assert np.allclose(J_analytic, J_numeric, atol=1e-5)


def test_end_effector_velocity():
    arm = PlanarArmModel([0.3, 0.3])
    v = arm.end_effector_velocity([0.0, 0.0], [1.0, 0.0])
    assert v.shape == (3,)


def test_workspace_margin():
    arm = PlanarArmModel([0.3, 0.3])
    margin = arm.workspace_margin([0.5, 0.0])
    assert margin > 0


def test_workspace_margin_negative():
    arm = PlanarArmModel([0.3, 0.3])
    margin = arm.workspace_margin([1.0, 0.0])
    assert margin < 0


def test_manipulability():
    arm = PlanarArmModel([0.3, 0.3])
    m = arm.manipulability([0.5, -0.3])
    assert m > 0


def test_singularity_check_normal():
    arm = PlanarArmModel([0.3, 0.3])
    info = arm.singularity_check([0.5, -0.3])
    assert isinstance(info, SingularityInfo)
    assert not info.is_singular


def test_singularity_check_extended():
    arm = PlanarArmModel([0.3, 0.3])
    info = arm.singularity_check([0.0, 0.0])
    assert info.min_sv < 1.0


def test_inverse_damped_converges():
    arm = PlanarArmModel([0.3, 0.3])
    target = Pose2D(x=0.4, y=0.2, yaw=0.0)
    q_sol, converged = arm.inverse_damped(target, [0.1, 0.1], damping=0.05, max_iterations=200, tolerance=1e-3)
    assert converged
    pose = arm.forward(q_sol)
    assert abs(pose.x - target.x) < 0.01
    assert abs(pose.y - target.y) < 0.01


def test_analyze_workspace_reachable():
    arm = PlanarArmModel([0.3, 0.3])
    analysis = arm.analyze_workspace([0.4, 0.0])
    assert isinstance(analysis, WorkspaceAnalysis)
    assert analysis.reachable
    assert analysis.margin > 0
    assert analysis.max_reach == 0.6


def test_analyze_workspace_unreachable():
    arm = PlanarArmModel([0.3, 0.3])
    analysis = arm.analyze_workspace([1.0, 0.0])
    assert not analysis.reachable


def test_motion_chain_clamp():
    chain = MotionChainConfig(
        joint_types=["revolute", "revolute"],
        joint_limits=[(-1.0, 1.0), (-0.5, 0.5)],
    )
    clamped = chain.clamp_joints([2.0, -1.0])
    assert np.allclose(clamped, [1.0, -0.5])


def test_motion_chain_within_limits():
    chain = MotionChainConfig(
        joint_types=["revolute", "revolute"],
        joint_limits=[(-1.0, 1.0), (-0.5, 0.5)],
    )
    assert chain.is_within_limits([0.5, 0.0])
    assert not chain.is_within_limits([2.0, 0.0])
