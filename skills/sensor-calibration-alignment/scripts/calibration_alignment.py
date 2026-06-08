"""Spatiotemporal calibration alignment for multi-sensor ball-robot systems.

Provides spatial alignment (extrinsics), temporal alignment (time offset),
distortion correction, and online bias drift compensation.
"""

from dataclasses import dataclass, field
from typing import Iterable, Optional

import numpy as np


@dataclass
class Extrinsics:
    T: np.ndarray = field(default_factory=lambda: np.eye(4))

    def __post_init__(self):
        if self.T.shape != (4, 4):
            raise ValueError("Extrinsics T must be 4x4")

    def transform_point(self, point: Iterable[float]) -> np.ndarray:
        p = np.asarray(list(point), dtype=float)
        if p.shape != (3,):
            raise ValueError("point must be 3D")
        p_h = np.append(p, 1.0)
        return (self.T @ p_h)[:3]

    def inverse(self) -> "Extrinsics":
        T_inv = np.linalg.inv(self.T)
        return Extrinsics(T=T_inv)


@dataclass
class Intrinsics:
    K: np.ndarray = field(default_factory=lambda: np.eye(3))
    D: np.ndarray = field(default_factory=lambda: np.zeros(5))

    def undistort_normalized(self, pixel: Iterable[float]) -> np.ndarray:
        uv = np.asarray(list(pixel), dtype=float)
        if uv.shape != (2,):
            raise ValueError("pixel must be 2D")
        uv_h = np.array([uv[0], uv[1], 1.0])
        normalized = np.linalg.solve(self.K, uv_h)
        r2 = float(normalized[0] ** 2 + normalized[1] ** 2)
        r4 = r2 * r2
        r6 = r4 * r2
        k1, k2, k3, p1, p2 = self.D[:5]
        radial = 1.0 + k1 * r2 + k2 * r4 + k3 * r6
        x_d = normalized[0] * radial + 2.0 * p1 * normalized[0] * normalized[1] + p2 * (r2 + 2.0 * normalized[0] ** 2)
        y_d = normalized[1] * radial + p1 * (r2 + 2.0 * normalized[1] ** 2) + 2.0 * p2 * normalized[0] * normalized[1]
        return np.array([x_d, y_d])


@dataclass
class CalibrationParams:
    extrinsics: Extrinsics = field(default_factory=Extrinsics)
    time_offset: float = 0.0
    intrinsics: Optional[Intrinsics] = None


class SpatiotemporalAligner:
    def __init__(self, calib: CalibrationParams):
        self.calib = calib
        self._bias_drift = np.zeros(3)
        self._bias_count = 0

    def spatial_align(self, position_camera: Iterable[float]) -> np.ndarray:
        p_cam = np.asarray(list(position_camera), dtype=float)
        p_world = self.calib.extrinsics.transform_point(p_cam)
        return p_world + self._bias_drift

    def temporal_align(self, timestamp: float) -> float:
        return timestamp - self.calib.time_offset

    def undistort(self, pixel: Iterable[float]) -> np.ndarray:
        if self.calib.intrinsics is None:
            return np.asarray(list(pixel), dtype=float)
        return self.calib.intrinsics.undistort_normalized(pixel)

    def full_compensate(self, position_camera: Iterable[float], timestamp: float) -> dict:
        p_world = self.spatial_align(position_camera)
        t_true = self.temporal_align(timestamp)
        return {"position_world": p_world, "true_timestamp": t_true}

    def update_bias(self, observed_position: Iterable[float], predicted_position: Iterable[float], learning_rate: float = 0.01):
        obs = np.asarray(list(observed_position), dtype=float)
        pred = np.asarray(list(predicted_position), dtype=float)
        residual = obs - pred
        self._bias_count += 1
        alpha = learning_rate / (1.0 + 0.001 * self._bias_count)
        self._bias_drift = (1.0 - alpha) * self._bias_drift + alpha * residual

    def residual_diagnostics(self, observed: Iterable[float], predicted: Iterable[float]) -> dict:
        obs = np.asarray(list(observed), dtype=float)
        pred = np.asarray(list(predicted_position), dtype=float) if False else np.asarray(list(predicted), dtype=float)
        error = obs - pred
        rmse = float(np.sqrt(np.mean(error ** 2)))
        confidence = float(np.exp(-rmse / 0.01))
        return {"reprojection_error": rmse, "calibration_confidence": min(confidence, 1.0)}


class CoordinateChain:
    def __init__(self):
        self._frames: dict = {}

    def register(self, name: str, parent: str, transform: np.ndarray):
        if transform.shape != (4, 4):
            raise ValueError("transform must be 4x4")
        self._frames[name] = {"parent": parent, "T": transform}

    def lookup(self, source: str, target: str) -> np.ndarray:
        result = np.eye(4)
        current = source
        visited = set()
        while current != target:
            if current in visited:
                raise ValueError(f"circular frame detected at {current}")
            visited.add(current)
            if current not in self._frames:
                raise ValueError(f"frame {current} not registered")
            info = self._frames[current]
            result = info["T"] @ result
            current = info["parent"]
        return result
