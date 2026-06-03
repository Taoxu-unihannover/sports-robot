"""Mobile base tracking helpers."""

from dataclasses import dataclass
from math import atan2, cos, sin
from typing import Iterable

import numpy as np


@dataclass
class BaseCommand:
    linear: float
    angular: float


def wrap_angle(angle: float) -> float:
    return float((angle + np.pi) % (2 * np.pi) - np.pi)


def pure_pursuit_command(pose: Iterable[float], waypoint: Iterable[float], linear_speed: float, angular_gain: float = 2.0) -> BaseCommand:
    x, y, yaw = list(pose)
    wx, wy = list(waypoint)
    heading = atan2(wy - y, wx - x)
    error = wrap_angle(heading - yaw)
    return BaseCommand(linear=float(linear_speed * max(0.0, cos(error))), angular=float(angular_gain * error))


def integrate_unicycle(pose: Iterable[float], command: BaseCommand, dt: float):
    x, y, yaw = list(pose)
    return np.array([
        x + command.linear * cos(yaw) * dt,
        y + command.linear * sin(yaw) * dt,
        wrap_angle(yaw + command.angular * dt),
    ])

