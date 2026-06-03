import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from launcher_executor import LauncherModel


def test_command_roundtrip_speed():
    model = LauncherModel(speed_gain=0.1, yaw_gain=1.0, pitch_gain=1.0)
    command = model.command_for_velocity([10, 0, 0])
    assert abs(model.estimate_exit_speed(command) - 10.0) < 1e-9


def test_spin_offsets_wheels():
    model = LauncherModel(speed_gain=0.1, yaw_gain=1.0, pitch_gain=1.0, spin_gain=2.0)
    command = model.command_for_velocity([1, 0, 0], side_spin=1.0)
    assert command.wheel_right > command.wheel_left

