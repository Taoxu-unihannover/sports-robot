"""Small identification routines used by modeling recipes."""

from dataclasses import dataclass
from typing import Iterable

import numpy as np


def fit_linear_map(inputs: Iterable[Iterable[float]], outputs: Iterable[Iterable[float]], ridge: float = 0.0) -> np.ndarray:
    x = np.asarray(list(inputs), dtype=float)
    y = np.asarray(list(outputs), dtype=float)
    if x.ndim != 2 or y.ndim != 2 or x.shape[0] != y.shape[0]:
        raise ValueError("inputs and outputs must be 2D arrays with matching rows")
    xtx = x.T @ x + ridge * np.eye(x.shape[1])
    return np.linalg.solve(xtx, x.T @ y)


def fit_quadratic_drag_1d(times: Iterable[float], velocities: Iterable[float]) -> float:
    t = np.asarray(list(times), dtype=float)
    v = np.asarray(list(velocities), dtype=float)
    if len(t) < 3 or t.shape != v.shape:
        raise ValueError("need at least three time/velocity samples")
    dvdt = np.gradient(v, t)
    feature = -v * np.abs(v)
    coefficient = np.dot(feature, dvdt) / max(np.dot(feature, feature), 1e-12)
    return float(max(coefficient, 0.0))


@dataclass
class RecursiveLeastSquares:
    theta: np.ndarray
    covariance: np.ndarray
    forgetting: float = 0.99

    @classmethod
    def create(cls, dimension: int, covariance_scale: float = 1000.0, forgetting: float = 0.99):
        return cls(theta=np.zeros(dimension), covariance=np.eye(dimension) * covariance_scale, forgetting=forgetting)

    def update(self, features: Iterable[float], measurement: float) -> np.ndarray:
        phi = np.asarray(list(features), dtype=float)
        p_phi = self.covariance @ phi
        gain = p_phi / (self.forgetting + phi.T @ p_phi)
        residual = float(measurement - phi.T @ self.theta)
        self.theta = self.theta + gain * residual
        self.covariance = (self.covariance - np.outer(gain, phi) @ self.covariance) / self.forgetting
        return self.theta.copy()

