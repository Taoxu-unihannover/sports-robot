"""Safety gates for planned ball-striking commands."""

from dataclasses import dataclass
from typing import Iterable, Tuple

import numpy as np


@dataclass
class SafetyLimits:
    workspace_radius: float
    max_speed: float
    min_time_to_impact: float


class SafetySupervisor:
    def __init__(self, limits: SafetyLimits):
        self.limits = limits
        self.last_safe_position = None

    def check(self, position: Iterable[float], velocity: Iterable[float], time_to_impact: float) -> Tuple[bool, str]:
        p = np.asarray(list(position), dtype=float)
        v = np.asarray(list(velocity), dtype=float)
        if np.linalg.norm(p[:2]) > self.limits.workspace_radius:
            return False, "workspace_limit"
        if np.linalg.norm(v) > self.limits.max_speed:
            return False, "speed_limit"
        if time_to_impact < self.limits.min_time_to_impact:
            return False, "too_late"
        self.last_safe_position = p.copy()
        return True, "ok"

    def fallback_position(self):
        if self.last_safe_position is None:
            return np.zeros(3)
        return self.last_safe_position.copy()


def clamp_velocity(velocity: Iterable[float], max_speed: float) -> np.ndarray:
    v = np.asarray(list(velocity), dtype=float)
    speed = float(np.linalg.norm(v))
    if speed <= max_speed or speed < 1e-12:
        return v
    return v * (max_speed / speed)

