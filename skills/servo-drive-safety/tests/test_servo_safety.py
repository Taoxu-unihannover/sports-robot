import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from servo_safety import ServoLimit, check_servo_command, thermal_derating


def test_servo_command_ok():
    ok, reason = check_servo_command(0, 1, 2, ServoLimit(-1, 1, 2, 3))
    assert ok and reason == "ok"


def test_servo_rejects_torque():
    ok, reason = check_servo_command(0, 1, 4, ServoLimit(-1, 1, 2, 3))
    assert not ok and reason == "torque_limit"


def test_thermal_derating():
    assert thermal_derating(10, 90) == 0
    assert thermal_derating(10, 60) == 10

