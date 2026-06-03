"""Finite-horizon LQR baseline for MPC skill recipes."""

from typing import Iterable, List

import numpy as np


def finite_horizon_lqr(A: Iterable[Iterable[float]], B: Iterable[Iterable[float]], Q: Iterable[Iterable[float]], R: Iterable[Iterable[float]], horizon: int) -> List[np.ndarray]:
    a = np.asarray(A, dtype=float)
    b = np.asarray(B, dtype=float)
    q = np.asarray(Q, dtype=float)
    r = np.asarray(R, dtype=float)
    if horizon <= 0:
        raise ValueError("horizon must be positive")
    p = q.copy()
    gains = []
    for _ in range(horizon):
        s = r + b.T @ p @ b
        k = np.linalg.solve(s, b.T @ p @ a)
        gains.append(k)
        p = q + a.T @ p @ (a - b @ k)
    return list(reversed(gains))


class LinearMPCTracker:
    def __init__(self, A, B, Q, R, horizon: int, u_limit: float | None = None):
        self.A = np.asarray(A, dtype=float)
        self.B = np.asarray(B, dtype=float)
        self.gains = finite_horizon_lqr(A, B, Q, R, horizon)
        self.u_limit = u_limit

    def control(self, x, x_ref) -> np.ndarray:
        error = np.asarray(x, dtype=float) - np.asarray(x_ref, dtype=float)
        u = -self.gains[0] @ error
        if self.u_limit is not None:
            u = np.clip(u, -self.u_limit, self.u_limit)
        return u


def double_integrator(dt: float):
    A = np.array([[1.0, dt], [0.0, 1.0]])
    B = np.array([[0.5 * dt * dt], [dt]])
    return A, B

