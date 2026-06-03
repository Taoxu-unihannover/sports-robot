"""Hit target selection for ball-striking control stacks."""

from dataclasses import dataclass
from typing import Iterable, List, Optional

import numpy as np


@dataclass
class BallSample:
    t: float
    position: np.ndarray
    velocity: np.ndarray

    def __init__(self, t: float, position: Iterable[float], velocity: Iterable[float]):
        self.t = float(t)
        self.position = np.asarray(list(position), dtype=float)
        self.velocity = np.asarray(list(velocity), dtype=float)


@dataclass
class HitPlan:
    t: float
    contact_position: np.ndarray
    desired_outgoing_velocity: np.ndarray
    score: float


class HitPlanner:
    def __init__(self, workspace_radius: float, min_time: float = 0.08, max_time: float = 0.8):
        self.workspace_radius = float(workspace_radius)
        self.min_time = float(min_time)
        self.max_time = float(max_time)

    def reachable(self, sample: BallSample) -> bool:
        radius = float(np.linalg.norm(sample.position[:2]))
        return radius <= self.workspace_radius and self.min_time <= sample.t <= self.max_time

    def desired_velocity_to_target(self, sample: BallSample, target_landing: Iterable[float], flight_time: float = 0.45) -> np.ndarray:
        target = np.asarray(list(target_landing), dtype=float)
        gravity = np.array([0.0, 0.0, -9.81])
        return (target - sample.position - 0.5 * gravity * flight_time * flight_time) / flight_time

    def select_hit(self, samples: List[BallSample], target_landing: Iterable[float]) -> Optional[HitPlan]:
        best = None
        for sample in samples:
            if not self.reachable(sample):
                continue
            desired = self.desired_velocity_to_target(sample, target_landing)
            speed_cost = float(np.linalg.norm(desired))
            time_cost = abs(sample.t - 0.25)
            score = speed_cost + 2.0 * time_cost
            if best is None or score < best.score:
                best = HitPlan(sample.t, sample.position.copy(), desired, score)
        return best


def paddle_normal_for_velocity_change(incoming: Iterable[float], outgoing: Iterable[float]) -> np.ndarray:
    delta = np.asarray(list(outgoing), dtype=float) - np.asarray(list(incoming), dtype=float)
    norm = float(np.linalg.norm(delta))
    if norm < 1e-12:
        return np.array([1.0, 0.0, 0.0])
    return delta / norm

