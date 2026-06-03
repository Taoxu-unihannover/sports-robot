import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from mobile_base_executor import integrate_unicycle, pure_pursuit_command, wrap_angle


def test_wrap_angle():
    assert -3.1416 <= wrap_angle(10.0) <= 3.1416


def test_pure_pursuit_forward():
    cmd = pure_pursuit_command([0, 0, 0], [1, 0], 1.0)
    assert cmd.linear > 0.9
    assert abs(cmd.angular) < 1e-9


def test_integrate_unicycle_moves_forward():
    pose = integrate_unicycle([0, 0, 0], pure_pursuit_command([0, 0, 0], [1, 0], 1.0), 0.1)
    assert pose[0] > 0

