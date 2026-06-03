"""Servo command validation and derating utilities."""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class ServoLimit:
    position_min: float
    position_max: float
    velocity_max: float
    torque_max: float


def check_servo_command(position: float, velocity: float, torque: float, limit: ServoLimit) -> Tuple[bool, str]:
    if position < limit.position_min or position > limit.position_max:
        return False, "position_limit"
    if abs(velocity) > limit.velocity_max:
        return False, "velocity_limit"
    if abs(torque) > limit.torque_max:
        return False, "torque_limit"
    return True, "ok"


def thermal_derating(command_torque: float, temperature_c: float, start_c: float = 65.0, stop_c: float = 85.0) -> float:
    if temperature_c <= start_c:
        return command_torque
    if temperature_c >= stop_c:
        return 0.0
    scale = (stop_c - temperature_c) / (stop_c - start_c)
    return command_torque * scale

