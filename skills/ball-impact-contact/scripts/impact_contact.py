"""Impact/contact reference model for ball and paddle interactions."""

from typing import Iterable

import numpy as np


class PaddleImpactModel:
    def __init__(self, restitution: float = 0.85, tangential_damping: float = 0.1):
        if not 0.0 <= restitution <= 1.5:
            raise ValueError("restitution should be in a physically plausible range")
        if not 0.0 <= tangential_damping <= 1.0:
            raise ValueError("tangential_damping must be between 0 and 1")
        self.restitution = float(restitution)
        self.tangential_damping = float(tangential_damping)

    @staticmethod
    def _unit(v: Iterable[float]) -> np.ndarray:
        arr = np.asarray(list(v), dtype=float)
        norm = float(np.linalg.norm(arr))
        if norm < 1e-12:
            raise ValueError("normal vector cannot be zero")
        return arr / norm

    def impact(self, ball_velocity: Iterable[float], paddle_velocity: Iterable[float], paddle_normal: Iterable[float]) -> np.ndarray:
        vb = np.asarray(list(ball_velocity), dtype=float)
        vp = np.asarray(list(paddle_velocity), dtype=float)
        n = self._unit(paddle_normal)
        relative = vb - vp
        normal_component = np.dot(relative, n) * n
        tangent_component = relative - normal_component
        reflected_relative = -self.restitution * normal_component + (1.0 - self.tangential_damping) * tangent_component
        return vp + reflected_relative

    def required_paddle_velocity(self, incoming_velocity: Iterable[float], desired_outgoing_velocity: Iterable[float], paddle_normal: Iterable[float]) -> np.ndarray:
        vin = np.asarray(list(incoming_velocity), dtype=float)
        vout = np.asarray(list(desired_outgoing_velocity), dtype=float)
        n = self._unit(paddle_normal)
        # Solve only the normal component exactly; tangent is left to planner limits.
        normal_delta = np.dot(vout + self.restitution * vin, n) / (1.0 + self.restitution)
        return normal_delta * n


def bounce_ground(velocity: Iterable[float], normal: Iterable[float] = (0.0, 0.0, 1.0), restitution: float = 0.75) -> np.ndarray:
    v = np.asarray(list(velocity), dtype=float)
    n = PaddleImpactModel._unit(normal)
    vn = np.dot(v, n) * n
    vt = v - vn
    return vt - restitution * vn

