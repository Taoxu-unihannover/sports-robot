"""Uncertainty propagation and risk gates for ball robot models."""

from typing import Iterable

import numpy as np


def propagate_linear(covariance: Iterable[Iterable[float]], transition: Iterable[Iterable[float]], process_noise: Iterable[Iterable[float]]) -> np.ndarray:
    p = np.asarray(covariance, dtype=float)
    f = np.asarray(transition, dtype=float)
    q = np.asarray(process_noise, dtype=float)
    return f @ p @ f.T + q


def mahalanobis_squared(residual: Iterable[float], covariance: Iterable[Iterable[float]]) -> float:
    r = np.asarray(list(residual), dtype=float)
    s = np.asarray(covariance, dtype=float)
    return float(r.T @ np.linalg.pinv(s) @ r)


def chi_square_gate(residual: Iterable[float], covariance: Iterable[Iterable[float]], threshold: float) -> bool:
    return mahalanobis_squared(residual, covariance) <= threshold


def risk_score(time_to_impact: float, position_sigma: float, workspace_margin: float) -> float:
    if time_to_impact <= 0:
        return 1.0
    time_risk = min(1.0, 0.15 / time_to_impact)
    uncertainty_risk = min(1.0, position_sigma / 0.08)
    workspace_risk = 1.0 if workspace_margin <= 0 else min(1.0, 0.05 / workspace_margin)
    return float(0.4 * time_risk + 0.4 * uncertainty_risk + 0.2 * workspace_risk)

