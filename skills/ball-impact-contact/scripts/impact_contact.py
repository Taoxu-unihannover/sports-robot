"""Impact/contact reference model for ball and paddle interactions.

Provides impulse-based contact for table, ground, and paddle surfaces
with separate parameter sets, as well as a compliant contact model
suitable for gradient-based optimization (MuJoCo-style).
"""

from dataclasses import dataclass
from typing import Iterable, Optional

import numpy as np


@dataclass
class ContactParams:
    restitution: float = 0.85
    friction: float = 0.3
    tangential_damping: float = 0.1


@dataclass
class CompliantParams:
    stiffness: float = 1e4
    damping: float = 50.0
    friction: float = 0.3


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
        normal_delta = np.dot(vout + self.restitution * vin, n) / (1.0 + self.restitution)
        return normal_delta * n


def bounce_ground(velocity: Iterable[float], normal: Iterable[float] = (0.0, 0.0, 1.0), restitution: float = 0.75) -> np.ndarray:
    v = np.asarray(list(velocity), dtype=float)
    n = PaddleImpactModel._unit(normal)
    vn = np.dot(v, n) * n
    vt = v - vn
    return vt - restitution * vn


class SurfaceContactModel:
    def __init__(
        self,
        table_params: Optional[ContactParams] = None,
        ground_params: Optional[ContactParams] = None,
        paddle_params: Optional[ContactParams] = None,
    ):
        self.table = table_params or ContactParams(restitution=0.90, friction=0.30, tangential_damping=0.05)
        self.ground = ground_params or ContactParams(restitution=0.60, friction=0.50, tangential_damping=0.10)
        self.paddle = paddle_params or ContactParams(restitution=0.85, friction=0.40, tangential_damping=0.10)

    def impulse_contact(
        self,
        ball_velocity: Iterable[float],
        surface_normal: Iterable[float],
        surface_velocity: Iterable[float] = (0.0, 0.0, 0.0),
        contact_type: str = "table",
    ) -> np.ndarray:
        params = {"table": self.table, "ground": self.ground, "paddle": self.paddle}.get(contact_type)
        if params is None:
            raise ValueError(f"unknown contact_type: {contact_type}")
        vb = np.asarray(list(ball_velocity), dtype=float)
        vs = np.asarray(list(surface_velocity), dtype=float)
        n = PaddleImpactModel._unit(surface_normal)
        relative = vb - vs
        vn = np.dot(relative, n) * n
        vt = relative - vn
        vt_norm = float(np.linalg.norm(vt[:2]))
        if vt_norm > 1e-9 and params.friction * abs(np.dot(relative, n)) < vt_norm:
            scale = 1.0 - params.friction * abs(np.dot(relative, n)) / vt_norm
            vt[:2] *= scale
        else:
            vt[:2] *= 0.0
        return vs - params.restitution * vn + vt

    def energy_loss(
        self,
        ball_velocity: Iterable[float],
        surface_normal: Iterable[float],
        surface_velocity: Iterable[float] = (0.0, 0.0, 0.0),
        contact_type: str = "table",
    ) -> float:
        vb = np.asarray(list(ball_velocity), dtype=float)
        v_after = self.impulse_contact(vb, surface_normal, surface_velocity, contact_type)
        ke_before = 0.5 * float(np.dot(vb, vb))
        ke_after = 0.5 * float(np.dot(v_after, v_after))
        return 1.0 - ke_after / max(ke_before, 1e-12)


class CompliantContactModel:
    def __init__(self, params: Optional[CompliantParams] = None):
        self.params = params or CompliantParams()

    def normal_force(self, penetration: float, penetration_rate: float) -> float:
        if penetration <= 0:
            return 0.0
        return self.params.stiffness * penetration + self.params.damping * max(penetration_rate, 0.0)

    def tangent_force(self, tangent_velocity: Iterable[float], normal_force_value: float) -> np.ndarray:
        vt = np.asarray(list(tangent_velocity), dtype=float)
        vt_norm = float(np.linalg.norm(vt))
        if vt_norm < 1e-9 or normal_force_value <= 0:
            return np.zeros_like(vt)
        max_friction = self.params.friction * normal_force_value
        if vt_norm <= max_friction:
            return -vt
        return -max_friction * vt / vt_norm

