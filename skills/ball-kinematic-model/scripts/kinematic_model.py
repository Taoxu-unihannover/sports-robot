"""Reference kinematic utilities for ball-striking robots.

The implementation is intentionally lightweight. It gives a deterministic
planar arm model that can be used in skill examples and tests, while the same
interfaces map cleanly to Pinocchio, RBDL, or a URDF-backed implementation.

Includes workspace analysis, singularity detection, damped-least-squares IK,
and motion chain configuration helpers.
"""

from dataclasses import dataclass
from math import cos, sin
from typing import Iterable, List, Optional, Tuple

import numpy as np


@dataclass
class Pose2D:
    x: float
    y: float
    yaw: float


@dataclass
class SingularityInfo:
    is_singular: bool
    manipulability: float
    condition_number: float
    min_sv: float
    recommendation: str


@dataclass
class WorkspaceAnalysis:
    max_reach: float
    min_reach: float
    dexterous_reach: float
    reachable: bool
    margin: float


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

    def manipulability(self, q: Iterable[float]) -> float:
        J = self.jacobian(q)
        svs = np.linalg.svd(J, compute_uv=False)
        return float(np.prod(svs))

    def singularity_check(self, q: Iterable[float], threshold: float = 1e-3) -> SingularityInfo:
        J = self.jacobian(q)
        svs = np.linalg.svd(J, compute_uv=False)
        min_sv = float(svs.min())
        max_sv = float(svs.max())
        cond = max_sv / max(min_sv, 1e-12)
        manip = float(np.prod(svs))
        is_singular = min_sv < threshold
        if is_singular:
            recommendation = "damped_least_squares"
        elif cond > 100:
            recommendation = "monitor"
        else:
            recommendation = "standard"
        return SingularityInfo(
            is_singular=is_singular,
            manipulability=manip,
            condition_number=cond,
            min_sv=min_sv,
            recommendation=recommendation,
        )

    def inverse_damped(
        self,
        target: Pose2D,
        q_init: Iterable[float],
        damping: float = 0.01,
        max_iterations: int = 200,
        tolerance: float = 1e-4,
        position_weight: float = 1.0,
        yaw_weight: float = 0.01,
    ) -> Tuple[np.ndarray, bool]:
        q = np.asarray(list(q_init), dtype=float).copy()
        for _ in range(max_iterations):
            pose = self.forward(q)
            pos_error = np.array([target.x - pose.x, target.y - pose.y])
            if float(np.linalg.norm(pos_error)) < tolerance:
                return q, True
            J_full = self.jacobian(q)
            J_pos = J_full[:2, :]
            JJT = J_pos @ J_pos.T + damping * np.eye(2)
            dq = J_pos.T @ np.linalg.solve(JJT, pos_error)
            q = q + dq
        pose = self.forward(q)
        pos_err = float(np.linalg.norm([target.x - pose.x, target.y - pose.y]))
        return q, pos_err < tolerance * 10

    def analyze_workspace(self, point_xy: Iterable[float]) -> WorkspaceAnalysis:
        point = np.asarray(list(point_xy), dtype=float)
        dist = float(np.linalg.norm(point))
        max_reach = float(np.sum(self.link_lengths))
        min_reach = max(0.0, float(self.link_lengths[0] - np.sum(self.link_lengths[1:])))
        dexterous_reach = max_reach * 0.85
        reachable = min_reach <= dist <= max_reach
        margin = max_reach - dist if reachable else -1.0
        return WorkspaceAnalysis(
            max_reach=max_reach,
            min_reach=min_reach,
            dexterous_reach=dexterous_reach,
            reachable=reachable,
            margin=margin,
        )


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


class MotionChainConfig:
    def __init__(
        self,
        joint_types: Iterable[str],
        joint_limits: Optional[Iterable[Tuple[float, float]]] = None,
        base_offset: Iterable[float] = (0.0, 0.0),
    ):
        self.joint_types = list(joint_types)
        self.n = len(self.joint_types)
        if joint_limits is None:
            self.joint_limits = [(-np.pi, np.pi)] * self.n
        else:
            self.joint_limits = [tuple(lim) for lim in joint_limits]
        self.base_offset = np.asarray(list(base_offset), dtype=float)

    def clamp_joints(self, q: Iterable[float]) -> np.ndarray:
        q_arr = np.asarray(list(q), dtype=float)
        clamped = np.zeros_like(q_arr)
        for i, (lo, hi) in enumerate(self.joint_limits):
            clamped[i] = np.clip(q_arr[i], lo, hi)
        return clamped

    def is_within_limits(self, q: Iterable[float]) -> bool:
        q_arr = np.asarray(list(q), dtype=float)
        for i, (lo, hi) in enumerate(self.joint_limits):
            if q_arr[i] < lo or q_arr[i] > hi:
                return False
        return True

