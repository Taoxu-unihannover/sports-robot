"""Reference kinematic utilities for ball-striking robots.

The implementation is intentionally lightweight. It gives a deterministic
planar arm model that can be used in skill examples and tests, while the same
interfaces map cleanly to Pinocchio, RBDL, or a URDF-backed implementation.
"""

from dataclasses import dataclass
from math import cos, sin
from typing import Iterable, List

import numpy as np


@dataclass
class Pose2D:
    x: float
    y: float
    yaw: float


class PlanarArmModel:
    def __init__(self, link_lengths: Iterable[float]):
        self.link_lengths = np.asarray(list(link_lengths), dtype=float)
        if self.link_lengths.ndim != 1 or len(self.link_lengths) == 0:
            raise ValueError("link_lengths must be a non-empty 1D sequence")

    @property
    def dof(self) -> int:
        return int(len(self.link_lengths))

    def _check_q(self, q: Iterable[float]) -> np.ndarray:
        q_arr = np.asarray(list(q), dtype=float)
        if q_arr.shape != (self.dof,):
            raise ValueError(f"expected {self.dof} joint values, got {q_arr.shape}")
        return q_arr

    def forward(self, q: Iterable[float]) -> Pose2D:
        q_arr = self._check_q(q)
        angles = np.cumsum(q_arr)
        x = float(np.sum(self.link_lengths * np.cos(angles)))
        y = float(np.sum(self.link_lengths * np.sin(angles)))
        return Pose2D(x=x, y=y, yaw=float(angles[-1]))

    def jacobian(self, q: Iterable[float]) -> np.ndarray:
        q_arr = self._check_q(q)
        angles = np.cumsum(q_arr)
        jac = np.zeros((3, self.dof), dtype=float)
        for j in range(self.dof):
            suffix = slice(j, self.dof)
            jac[0, j] = -np.sum(self.link_lengths[suffix] * np.sin(angles[suffix]))
            jac[1, j] = np.sum(self.link_lengths[suffix] * np.cos(angles[suffix]))
            jac[2, j] = 1.0
        return jac

    def end_effector_velocity(self, q: Iterable[float], qd: Iterable[float]) -> np.ndarray:
        qd_arr = np.asarray(list(qd), dtype=float)
        if qd_arr.shape != (self.dof,):
            raise ValueError(f"expected {self.dof} joint velocities")
        return self.jacobian(q) @ qd_arr

    def workspace_margin(self, point_xy: Iterable[float]) -> float:
        point = np.asarray(list(point_xy), dtype=float)
        if point.shape != (2,):
            raise ValueError("point_xy must contain two values")
        reach = float(np.sum(self.link_lengths))
        return reach - float(np.linalg.norm(point))


def finite_difference_jacobian(model: PlanarArmModel, q: List[float], eps: float = 1e-6) -> np.ndarray:
    q_arr = np.asarray(q, dtype=float)
    base = model.forward(q_arr)
    jac = np.zeros((3, model.dof), dtype=float)
    for i in range(model.dof):
        q_next = q_arr.copy()
        q_next[i] += eps
        pose_next = model.forward(q_next)
        jac[:, i] = [
            (pose_next.x - base.x) / eps,
            (pose_next.y - base.y) / eps,
            (pose_next.yaw - base.yaw) / eps,
        ]
    return jac

