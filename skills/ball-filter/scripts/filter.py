"""
Module 3: Kalman Filter for Ball State Estimation

Responsibility: Temporal smoothing of noisy 2D/3D measurements using a
physical motion model. Estimates unobservable states (velocity, acceleration).

Implements:
- Constant Velocity (CV) Kalman Filter - default for ball tracking
- Constant Acceleration (CA) Kalman Filter - for highly dynamic sports
- Extended Kalman Filter (EKF) - for nonlinear observation models
"""

import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class BallState:
    x: float
    y: float
    z: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    ax: float = 0.0
    ay: float = 0.0
    az: float = 0.0
    timestamp: float = 0.0

    @property
    def position(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])

    @property
    def velocity(self) -> np.ndarray:
        return np.array([self.vx, self.vy, self.vz])

    @property
    def speed(self) -> float:
        return float(np.linalg.norm(self.velocity))


class BallKalmanFilter:
    def __init__(
        self,
        dt: float = 1.0 / 125.0,
        dim: int = 2,
        process_noise: float = 1.0,
        measurement_noise: float = 10.0,
        model: str = "CV",
    ):
        self.dt = dt
        self.dim = dim
        self.model_type = model

        if model == "CV":
            self._init_cv(process_noise, measurement_noise)
        elif model == "CA":
            self._init_ca(process_noise, measurement_noise)
        else:
            raise ValueError(f"Unknown model: {model}")

        self.initialized = False
        self.last_timestamp: Optional[float] = None

    def _init_cv(self, process_noise: float, measurement_noise: float):
        state_dim = self.dim * 2
        meas_dim = self.dim

        self.F = np.eye(state_dim)
        for i in range(self.dim):
            self.F[i, i + self.dim] = self.dt

        self.H = np.zeros((meas_dim, state_dim))
        for i in range(self.dim):
            self.H[i, i] = 1.0

        self.Q = np.eye(state_dim) * process_noise
        self.R = np.eye(meas_dim) * measurement_noise

        self.x = np.zeros(state_dim)
        self.P = np.eye(state_dim) * 100.0

    def _init_ca(self, process_noise: float, measurement_noise: float):
        state_dim = self.dim * 3
        meas_dim = self.dim

        self.F = np.eye(state_dim)
        for i in range(self.dim):
            self.F[i, i + self.dim] = self.dt
            self.F[i, i + 2 * self.dim] = 0.5 * self.dt ** 2
            self.F[i + self.dim, i + 2 * self.dim] = self.dt

        self.H = np.zeros((meas_dim, state_dim))
        for i in range(self.dim):
            self.H[i, i] = 1.0

        self.Q = np.eye(state_dim) * process_noise
        self.R = np.eye(meas_dim) * measurement_noise

        self.x = np.zeros(state_dim)
        self.P = np.eye(state_dim) * 100.0

    def predict(self, dt: Optional[float] = None) -> BallState:
        if dt is not None:
            self._update_transition_matrix(dt)

        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q

        return self._state_from_vector()

    def update(self, measurement: np.ndarray) -> BallState:
        z = measurement[: self.dim]

        y = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)

        self.x = self.x + K @ y
        self.P = (np.eye(len(self.x)) - K @ self.H) @ self.P

        self.initialized = True
        return self._state_from_vector()

    def update_2d(self, x: float, y: float) -> BallState:
        return self.update(np.array([x, y]))

    def update_3d(self, x: float, y: float, z: float) -> BallState:
        return self.update(np.array([x, y, z]))

    def _update_transition_matrix(self, dt: float):
        if self.model_type == "CV":
            for i in range(self.dim):
                self.F[i, i + self.dim] = dt
        elif self.model_type == "CA":
            for i in range(self.dim):
                self.F[i, i + self.dim] = dt
                self.F[i, i + 2 * self.dim] = 0.5 * dt ** 2
                self.F[i + self.dim, i + 2 * self.dim] = dt

    def _state_from_vector(self) -> BallState:
        if self.model_type == "CV":
            if self.dim == 2:
                return BallState(x=self.x[0], y=self.x[1], vx=self.x[2], vy=self.x[3])
            else:
                return BallState(x=self.x[0], y=self.x[1], z=self.x[2],
                                 vx=self.x[3], vy=self.x[4], vz=self.x[5])
        else:
            if self.dim == 2:
                return BallState(x=self.x[0], y=self.x[1],
                                 vx=self.x[2], vy=self.x[3],
                                 ax=self.x[4], ay=self.x[5])
            else:
                return BallState(x=self.x[0], y=self.x[1], z=self.x[2],
                                 vx=self.x[3], vy=self.x[4], vz=self.x[5],
                                 ax=self.x[6], ay=self.x[7], az=self.x[8])

    def predict_future(self, t: float) -> np.ndarray:
        if self.model_type == "CV":
            pos = self.x[:self.dim]
            vel = self.x[self.dim:self.dim * 2]
            return pos + vel * t
        else:
            pos = self.x[:self.dim]
            vel = self.x[self.dim:self.dim * 2]
            acc = self.x[self.dim * 2:self.dim * 3]
            return pos + vel * t + 0.5 * acc * t ** 2

    def reset(self):
        self.x = np.zeros_like(self.x)
        self.P = np.eye(len(self.x)) * 100.0
        self.initialized = False


class ExtendedBallKalmanFilter:
    def __init__(
        self,
        dt: float = 1.0 / 125.0,
        process_noise: float = 1.0,
        measurement_noise: float = 10.0,
        drag_coefficient: float = 0.0,
    ):
        self.dt = dt
        self.drag_coefficient = drag_coefficient

        self.x = np.zeros(6)
        self.P = np.eye(6) * 100.0

        self.Q = np.eye(6) * process_noise
        self.R = np.eye(3) * measurement_noise

        self.initialized = False

    def _state_transition(self, x: np.ndarray, dt: float) -> np.ndarray:
        px, py, pz, vx, vy, vz = x
        speed = np.sqrt(vx ** 2 + vy ** 2 + vz ** 2)
        drag = self.drag_coefficient * speed

        new_x = np.zeros(6)
        new_x[0] = px + vx * dt - 0.5 * drag * vx * dt ** 2
        new_x[1] = py + vy * dt - 0.5 * drag * vy * dt ** 2
        new_x[2] = pz + vz * dt - 0.5 * drag * vz * dt ** 2 - 0.5 * 9.81 * dt ** 2
        new_x[3] = vx - drag * vx * dt
        new_x[4] = vy - drag * vy * dt
        new_x[5] = vz - drag * vz * dt - 9.81 * dt
        return new_x

    def _jacobian_F(self, x: np.ndarray, dt: float) -> np.ndarray:
        _, _, _, vx, vy, vz = x
        speed = max(np.sqrt(vx ** 2 + vy ** 2 + vz ** 2), 1e-6)
        drag = self.drag_coefficient

        F = np.eye(6)
        F[0, 3] = dt
        F[1, 4] = dt
        F[2, 5] = dt

        F[3, 3] = 1.0 - drag * (speed + vx ** 2 / speed) * dt
        F[3, 4] = -drag * vx * vy / speed * dt
        F[3, 5] = -drag * vx * vz / speed * dt
        F[4, 3] = -drag * vx * vy / speed * dt
        F[4, 4] = 1.0 - drag * (speed + vy ** 2 / speed) * dt
        F[4, 5] = -drag * vy * vz / speed * dt
        F[5, 3] = -drag * vx * vz / speed * dt
        F[5, 4] = -drag * vy * vz / speed * dt
        F[5, 5] = 1.0 - drag * (speed + vz ** 2 / speed) * dt

        return F

    def predict(self, dt: Optional[float] = None) -> BallState:
        if dt is None:
            dt = self.dt

        F = self._jacobian_F(self.x, dt)
        self.x = self._state_transition(self.x, dt)
        self.P = F @ self.P @ F.T + self.Q

        return BallState(
            x=self.x[0], y=self.x[1], z=self.x[2],
            vx=self.x[3], vy=self.x[4], vz=self.x[5],
        )

    def update(self, measurement: np.ndarray) -> BallState:
        H = np.zeros((3, 6))
        H[0, 0] = 1.0
        H[1, 1] = 1.0
        H[2, 2] = 1.0

        z = measurement[:3]
        y = z - H @ self.x
        S = H @ self.P @ H.T + self.R
        K = self.P @ H.T @ np.linalg.inv(S)

        self.x = self.x + K @ y
        self.P = (np.eye(6) - K @ H) @ self.P
        self.initialized = True

        return BallState(
            x=self.x[0], y=self.x[1], z=self.x[2],
            vx=self.x[3], vy=self.x[4], vz=self.x[5],
        )

    def reset(self):
        self.x = np.zeros(6)
        self.P = np.eye(6) * 100.0
        self.initialized = False
