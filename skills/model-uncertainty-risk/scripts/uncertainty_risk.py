"""Uncertainty propagation and risk gates for ball robot models.

Provides covariance propagation, Mahalanobis gating, risk scoring,
delay/noise modeling, CVaR computation, and model switching logic.
"""

from dataclasses import dataclass
from typing import Iterable, List, Optional

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


@dataclass
class DelayModel:
    mean: float = 0.015
    std: float = 0.003
    max_delay: float = 0.050

    def position_uncertainty(self, ball_speed: float) -> float:
        return ball_speed * (self.mean + 2.0 * self.std)

    def delay_covariance_contribution(self, ball_speed: float, direction: Iterable[float] = (1.0, 0.0, 0.0)) -> np.ndarray:
        d = np.asarray(list(direction), dtype=float)
        d = d / max(float(np.linalg.norm(d)), 1e-9)
        scale = (ball_speed * self.std) ** 2
        return scale * np.outer(d, d)


@dataclass
class NoiseModel:
    near_sigma: float = 0.005
    far_sigma: float = 0.050
    transition_distance: float = 3.0

    def sigma_at_distance(self, distance: float) -> float:
        if distance <= self.transition_distance:
            alpha = distance / self.transition_distance
            return self.near_sigma * (1.0 - alpha) + self.far_sigma * alpha
        return self.far_sigma

    def observation_covariance(self, distance: float) -> np.ndarray:
        s = self.sigma_at_distance(distance)
        return np.eye(3) * s * s


def compute_cvar(samples: Iterable[float], alpha: float = 0.05) -> float:
    arr = np.asarray(list(samples), dtype=float)
    if len(arr) == 0:
        return 0.0
    sorted_arr = np.sort(arr)[::-1]
    n_tail = max(1, int(np.ceil(len(sorted_arr) * alpha)))
    return float(np.mean(sorted_arr[:n_tail]))


def hit_probability(position_covariance: Iterable[Iterable[float]], paddle_radius: float = 0.08) -> float:
    P = np.asarray(position_covariance, dtype=float)
    if P.shape != (3, 3):
        P = np.eye(3) * float(np.mean(np.diag(P[:3, :3]))) if P.ndim == 2 and P.shape[0] >= 3 else np.eye(3) * 0.01
    sigma_xy = float(np.sqrt(0.5 * (P[0, 0] + P[1, 1])))
    if sigma_xy < 1e-9:
        return 1.0
    r = paddle_radius / sigma_xy
    try:
        from scipy.stats import norm as _norm
        p = float(_norm.cdf(r) - _norm.cdf(-r))
        return min(max(p, 0.0), 1.0)
    except ImportError:
        p = 1.0 - np.exp(-0.5 * r * r)
        return min(max(p, 0.0), 1.0)


class ModelSwitchController:
    def __init__(
        self,
        covariance_trace_threshold: float = 0.1,
        residual_threshold: float = 0.05,
        min_switch_interval: float = 0.5,
    ):
        self.cov_trace_threshold = covariance_trace_threshold
        self.residual_threshold = residual_threshold
        self.min_switch_interval = min_switch_interval
        self._current_model = "high_fidelity"
        self._last_switch_time = -1.0
        self._switch_count = 0

    def evaluate(self, covariance_trace: float, residual_rms: float, current_time: float) -> dict:
        should_switch = False
        target_model = self._current_model
        if covariance_trace > self.cov_trace_threshold or residual_rms > self.residual_threshold:
            if self._current_model == "high_fidelity":
                target_model = "reduced"
                should_switch = True
        else:
            if self._current_model == "reduced":
                target_model = "high_fidelity"
                should_switch = True
        if should_switch and (current_time - self._last_switch_time) < self.min_switch_interval:
            should_switch = False
        if should_switch:
            self._current_model = target_model
            self._last_switch_time = current_time
            self._switch_count += 1
        risk_level = "low"
        if covariance_trace > self.cov_trace_threshold * 2 or residual_rms > self.residual_threshold * 2:
            risk_level = "critical"
        elif covariance_trace > self.cov_trace_threshold or residual_rms > self.residual_threshold:
            risk_level = "high"
        elif covariance_trace > self.cov_trace_threshold * 0.5:
            risk_level = "medium"
        return {
            "current_model": self._current_model,
            "risk_level": risk_level,
            "switched": should_switch,
            "switch_count": self._switch_count,
        }

