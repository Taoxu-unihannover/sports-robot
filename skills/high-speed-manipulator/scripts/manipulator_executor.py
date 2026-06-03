"""Trajectory utilities for high-speed manipulators."""

from dataclasses import dataclass
from typing import List


@dataclass
class ProfilePoint:
    t: float
    position: float
    velocity: float


def trapezoid_profile(distance: float, max_velocity: float, max_acceleration: float, dt: float) -> List[ProfilePoint]:
    if distance < 0 or max_velocity <= 0 or max_acceleration <= 0 or dt <= 0:
        raise ValueError("invalid profile parameters")
    t_acc = max_velocity / max_acceleration
    d_acc = 0.5 * max_acceleration * t_acc * t_acc
    if 2 * d_acc > distance:
        t_acc = (distance / max_acceleration) ** 0.5
        t_flat = 0.0
        peak_v = max_acceleration * t_acc
    else:
        t_flat = (distance - 2 * d_acc) / max_velocity
        peak_v = max_velocity
    total = 2 * t_acc + t_flat
    points = []
    t = 0.0
    while t <= total + 1e-12:
        if t < t_acc:
            pos = 0.5 * max_acceleration * t * t
            vel = max_acceleration * t
        elif t < t_acc + t_flat:
            pos = 0.5 * max_acceleration * t_acc * t_acc + peak_v * (t - t_acc)
            vel = peak_v
        else:
            td = t - t_acc - t_flat
            pos = distance - 0.5 * max_acceleration * max(total - t, 0.0) ** 2
            vel = max(0.0, peak_v - max_acceleration * td)
        points.append(ProfilePoint(t, min(pos, distance), vel))
        t += dt
    if points[-1].position < distance:
        points.append(ProfilePoint(total, distance, 0.0))
    return points


def within_joint_limits(q, lower, upper) -> bool:
    return all(l <= value <= u for value, l, u in zip(q, lower, upper))

