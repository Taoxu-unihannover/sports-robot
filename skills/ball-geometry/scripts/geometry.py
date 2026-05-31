"""
Module 4: 3D Geometry Reconstruction

Responsibility: Map 2D detections from multiple cameras to 3D world coordinates
using triangulation (DLT or midpoint method). Supports stereo and multi-camera setups.

Implements:
- DLT (Direct Linear Transform) triangulation
- Midpoint triangulation (simpler, less sensitive to noise)
- Camera projection utilities
- Coordinate frame transformations
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass


@dataclass
class CameraConfig:
    camera_id: str
    width: int
    height: int
    K: np.ndarray
    dist_coeffs: np.ndarray
    R: np.ndarray
    t: np.ndarray

    @property
    def P(self) -> np.ndarray:
        RT = np.hstack([self.R, self.t.reshape(3, 1)])
        return self.K @ RT

    @property
    def projection_matrix(self) -> np.ndarray:
        return self.P


class Triangulator:
    def __init__(self, camera_configs: List[CameraConfig], method: str = "DLT"):
        self.cameras = {c.camera_id: c for c in camera_configs}
        self.method = method

    def triangulate(
        self, points_2d: Dict[str, Tuple[float, float]]
    ) -> Optional[np.ndarray]:
        if len(points_2d) < 2:
            return None

        cam_ids = list(points_2d.keys())
        pts = [points_2d[cid] for cid in cam_ids]
        P_matrices = [self.cameras[cid].P for cid in cam_ids]

        if self.method == "DLT":
            return self._triangulate_dlt(pts, P_matrices)
        elif self.method == "midpoint":
            return self._triangulate_midpoint(pts, P_matrices)
        else:
            raise ValueError(f"Unknown method: {self.method}")

    def _triangulate_dlt(
        self, points_2d: List[Tuple[float, float]], P_matrices: List[np.ndarray]
    ) -> np.ndarray:
        n = len(points_2d)
        A = np.zeros((2 * n, 4))

        for i, ((u, v), P) in enumerate(zip(points_2d, P_matrices)):
            A[2 * i] = u * P[2] - P[0]
            A[2 * i + 1] = v * P[2] - P[1]

        _, _, Vt = np.linalg.svd(A)
        X_homo = Vt[-1]
        X = X_homo[:3] / X_homo[3]

        return X

    def _triangulate_midpoint(
        self, points_2d: List[Tuple[float, float]], P_matrices: List[np.ndarray]
    ) -> np.ndarray:
        rays = []
        for (u, v), P in zip(points_2d, P_matrices):
            M = P[:, :3]
            p4 = P[:, 3]
            center = -np.linalg.inv(M) @ p4
            direction = np.linalg.inv(M) @ np.array([u, v, 1.0])
            direction = direction / np.linalg.norm(direction)
            rays.append((center, direction))

        if len(rays) == 2:
            c1, d1 = rays[0]
            c2, d2 = rays[1]
            return self._closest_point_between_rays(c1, d1, c2, d2)
        else:
            points = []
            for i in range(len(rays)):
                for j in range(i + 1, len(rays)):
                    pt = self._closest_point_between_rays(
                        rays[i][0], rays[i][1], rays[j][0], rays[j][1]
                    )
                    points.append(pt)
            return np.mean(points, axis=0)

    @staticmethod
    def _closest_point_between_rays(
        c1: np.ndarray, d1: np.ndarray, c2: np.ndarray, d2: np.ndarray
    ) -> np.ndarray:
        n = np.cross(d1, d2)
        n_norm = np.linalg.norm(n)

        if n_norm < 1e-10:
            return (c1 + c2) / 2.0

        n1 = np.cross(d1, n)
        n2 = np.cross(d2, n)

        c1_term = c1 + np.dot(c2 - c1, n2) / np.dot(d1, n2) * d1
        c2_term = c2 + np.dot(c1 - c2, n1) / np.dot(d2, n1) * d2

        return (c1_term + c2_term) / 2.0

    def project_3d_to_2d(
        self, point_3d: np.ndarray, camera_id: str
    ) -> Tuple[float, float]:
        cam = self.cameras[camera_id]
        X_homo = np.append(point_3d, 1.0)
        uv_homo = cam.P @ X_homo
        u = uv_homo[0] / uv_homo[2]
        v = uv_homo[1] / uv_homo[2]
        return float(u), float(v)

    def reprojection_error(
        self, point_3d: np.ndarray, points_2d: Dict[str, Tuple[float, float]]
    ) -> float:
        total_error = 0.0
        for cam_id, (u_obs, v_obs) in points_2d.items():
            u_proj, v_proj = self.project_3d_to_2d(point_3d, cam_id)
            total_error += np.sqrt((u_obs - u_proj) ** 2 + (v_obs - v_proj) ** 2)
        return total_error / len(points_2d)


class CoordinateTransformer:
    def __init__(self, T_cam_to_world: Optional[np.ndarray] = None):
        self.T_cam_to_world = (
            T_cam_to_world if T_cam_to_world is not None else np.eye(4)
        )

    def cam_to_world(self, point_cam: np.ndarray) -> np.ndarray:
        p_homo = np.append(point_cam, 1.0)
        p_world_homo = self.T_cam_to_world @ p_homo
        return p_world_homo[:3]

    def world_to_cam(self, point_world: np.ndarray) -> np.ndarray:
        T_world_to_cam = np.linalg.inv(self.T_cam_to_world)
        p_homo = np.append(point_world, 1.0)
        p_cam_homo = T_world_to_cam @ p_homo
        return p_cam_homo[:3]

    def update_transform(self, T_new: np.ndarray):
        self.T_cam_to_world = T_new


class StereoDepthEstimator:
    def __init__(self, baseline: float, focal_length: float, cx: float = 0.0):
        self.baseline = baseline
        self.focal_length = focal_length
        self.cx = cx

    def disparity_to_depth(self, disparity: float) -> float:
        if abs(disparity) < 1e-6:
            return float("inf")
        return self.baseline * self.focal_length / abs(disparity)

    def stereo_to_3d(
        self, u_left: float, v_left: float, u_right: float, v_right: float
    ) -> np.ndarray:
        disparity = u_left - u_right
        depth = self.disparity_to_depth(disparity)

        x = (u_left - self.cx) * depth / self.focal_length
        y = (v_left - self.cx) * depth / self.focal_length
        z = depth

        return np.array([x, y, z])
