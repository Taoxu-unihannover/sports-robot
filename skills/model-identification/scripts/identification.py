"""Small identification routines used by modeling recipes.

Provides batch NLS, RLS, and dual EKF parameter identification with
freeze conditions and physical constraint enforcement.
"""

from dataclasses import dataclass, field
from typing import Iterable, List, Optional

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


@dataclass
class ParameterBounds:
    lower: np.ndarray
    upper: np.ndarray

    def clamp(self, theta: np.ndarray) -> np.ndarray:
        return np.clip(theta, self.lower, self.upper)


class DualEKF:
    def __init__(
        self,
        state_dim: int,
        param_dim: int,
        process_noise_state: float = 1e-4,
        process_noise_param: float = 1e-6,
        measurement_noise: float = 1e-2,
        bounds: Optional[ParameterBounds] = None,
    ):
        self.state_dim = state_dim
        self.param_dim = param_dim
        self.x = np.zeros(state_dim)
        self.P_x = np.eye(state_dim) * 1.0
        self.theta = np.zeros(param_dim)
        self.P_theta = np.eye(param_dim) * 100.0
        self.Q_x = np.eye(state_dim) * process_noise_state
        self.Q_theta = np.eye(param_dim) * process_noise_param
        self.R = np.eye(1) * measurement_noise
        self.bounds = bounds
        self._frozen = False
        self._freeze_residual_threshold = 0.01
        self._freeze_rate_threshold = 1e-5
        self._prev_theta = self.theta.copy()

    def predict_state(self, state_transition: np.ndarray, control: np.ndarray):
        self.x = state_transition @ self.x + control
        self.P_x = state_transition @ self.P_x @ state_transition.T + self.Q_x

    def update_state(self, observation_matrix: np.ndarray, measurement: float):
        H = observation_matrix.reshape(1, -1)
        y = float(measurement) - float((H @ self.x).item())
        S = float((H @ self.P_x @ H.T + self.R[0, 0]).item())
        K = self.P_x @ H.T / S
        self.x = self.x + K.flatten() * y
        self.P_x = (np.eye(self.state_dim) - K @ H) @ self.P_x

    def update_params(self, observation_matrix: np.ndarray, measurement: float):
        if self._frozen:
            return self.theta.copy()
        H = observation_matrix.reshape(1, -1)
        y = float(measurement) - float((H @ self.theta).item())
        if abs(y) < self._freeze_residual_threshold:
            rate = float(np.linalg.norm(self.theta - self._prev_theta))
            if rate < self._freeze_rate_threshold:
                self._frozen = True
                return self.theta.copy()
        S = float((H @ self.P_theta @ H.T + self.R[0, 0]).item())
        K = self.P_theta @ H.T / S
        self._prev_theta = self.theta.copy()
        self.theta = self.theta + K.flatten() * y
        self.P_theta = (np.eye(self.param_dim) - K @ H) @ self.P_theta + self.Q_theta
        if self.bounds is not None:
            self.theta = self.bounds.clamp(self.theta)
        return self.theta.copy()

    def unfreeze(self):
        self._frozen = False

    @property
    def frozen(self) -> bool:
        return self._frozen


def batch_nls(
    model_fn,
    initial_params: Iterable[float],
    data_inputs: List,
    data_outputs: List[float],
    bounds: Optional[ParameterBounds] = None,
    max_iterations: int = 100,
    tolerance: float = 1e-6,
    step_size: float = 0.01,
) -> dict:
    theta = np.asarray(list(initial_params), dtype=float).copy()
    n = len(theta)
    prev_cost = float("inf")
    for iteration in range(max_iterations):
        residuals = []
        jacobians = []
        for inp, out in zip(data_inputs, data_outputs):
            pred = model_fn(theta, inp)
            residuals.append(out - pred)
            J_row = np.zeros(n)
            for j in range(n):
                theta_plus = theta.copy()
                theta_plus[j] += 1e-6
                J_row[j] = (model_fn(theta_plus, inp) - pred) / 1e-6
            jacobians.append(J_row)
        r = np.array(residuals)
        J = np.array(jacobians)
        cost = float(0.5 * np.dot(r, r))
        if abs(prev_cost - cost) < tolerance:
            break
        prev_cost = cost
        try:
            delta = np.linalg.solve(J.T @ J + 1e-6 * np.eye(n), J.T @ r)
        except np.linalg.LinAlgError:
            delta = step_size * J.T @ r
        theta = theta + step_size * delta
        if bounds is not None:
            theta = bounds.clamp(theta)
    return {"parameters": theta, "cost": prev_cost, "iterations": iteration + 1}

