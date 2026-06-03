import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from manipulator_executor import trapezoid_profile, within_joint_limits


def test_profile_reaches_distance():
    profile = trapezoid_profile(1.0, 2.0, 4.0, 0.01)
    assert abs(profile[-1].position - 1.0) < 1e-9


def test_joint_limits():
    assert within_joint_limits([0, 1], [-1, 0], [1, 2])
    assert not within_joint_limits([2], [-1], [1])

