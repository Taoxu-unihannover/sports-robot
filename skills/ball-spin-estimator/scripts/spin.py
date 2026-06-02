"""
Module 5: Ball Spin (Angular Velocity) Estimator

Responsibility: Estimate ball angular velocity from event cameras,
surface markers, or flight trajectory (Magnus effect).
No position estimation - that is handled by ball-state-estimator.

Supports:
- EventCameraSpin - event-based optical flow regression (Tubingen/Ace)
- MarkerPoseSpin - PnP pose estimation from surface markers (SpinDOE)
- TrajectoryMagnusSpin - trajectory inversion via Magnus effect
"""

import numpy as np
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass


@dataclass
class SpinState:
    wx: float = 0.0
    wy: float = 0.0
    wz: float = 0.0
    spin_rpm: float = 0.0
    confidence: float = 0.0
    method: str = ""

    @property
    def angular_velocity(self) -> np.ndarray:
        return np.array([self.wx, self.wy, self.wz])

    @property
    def spin_direction(self) -> np.ndarray:
        w = self.angular_velocity
        norm = np.linalg.norm(w)
        if norm < 1e-8:
            return np.array([0.0, 0.0, 1.0])
        return w / norm


class EventCameraSpin:
    """
    Event camera angular velocity estimator.

    Estimates angular velocity from event stream using optical flow
    constraints on the ball surface. The geometric relationship between
    surface flow and angular velocity is:

        v_flow = omega x r

    where r is the vector from ball center to surface point.

    Reference: Tubingen CVPRW 2024, Ace (Sony AI / Nature 2026)
    """

    def __init__(
        self,
        ball_radius: float = 0.02,
        image_width: int = 640,
        image_height: int = 480,
        focal_length: float = 800.0,
        time_surface_decay: float = 0.05,
        accumulation_window_ms: float = 1.0,
    ):
        self.ball_radius = ball_radius
        self.image_width = image_width
        self.image_height = image_height
        self.focal_length = focal_length
        self.time_surface_decay = time_surface_decay
        self.accumulation_window_ms = accumulation_window_ms

    def compute_time_surface(
        self, events: np.ndarray, width: int = 0, height: int = 0
    ) -> np.ndarray:
        w = width or self.image_width
        h = height or self.image_height
        time_surface = np.zeros((h, w), dtype=np.float64)

        if len(events) == 0:
            return time_surface

        for event in events:
            x, y, t, _ = event[0], event[1], event[2], event[3]
            ix, iy = int(x), int(y)
            if 0 <= ix < w and 0 <= iy < h:
                time_surface[iy, ix] = t

        return time_surface

    def compute_event_flow(
        self, events: np.ndarray, ball_center_2d: Tuple[float, float],
        ball_radius_px: float
    ) -> Optional[np.ndarray]:
        if len(events) < 10:
            return None

        cx, cy = ball_center_2d
        r = ball_radius_px

        mask = ((events[:, 0] - cx) ** 2 + (events[:, 1] - cy) ** 2) <= r ** 2
        ball_events = events[mask]

        if len(ball_events) < 5:
            return None

        n_bins = max(2, int(self.accumulation_window_ms))
        t_min, t_max = ball_events[:, 2].min(), ball_events[:, 2].max()
        if t_max - t_min < 1e-6:
            return None

        bin_edges = np.linspace(t_min, t_max, n_bins + 1)
        flows = []

        for i in range(n_bins):
            mask_t = (ball_events[:, 2] >= bin_edges[i]) & (ball_events[:, 2] < bin_edges[i + 1])
            bin_evts = ball_events[mask_t]
            if len(bin_evts) < 2:
                continue

            dx = bin_evts[-1, 0] - bin_evts[0, 0]
            dy = bin_evts[-1, 1] - bin_evts[0, 1]
            dt = bin_evts[-1, 2] - bin_evts[0, 2]
            if abs(dt) < 1e-9:
                continue
            flows.append([dx / dt, dy / dt])

        if len(flows) == 0:
            return None

        return np.mean(flows, axis=0)

    def estimate_angular_velocity(
        self,
        events: np.ndarray,
        ball_center_2d: Tuple[float, float],
        ball_center_3d: Optional[np.ndarray] = None,
        ball_radius_px: float = 50.0,
    ) -> Optional[SpinState]:
        if len(events) < 10:
            return None

        flow = self.compute_event_flow(events, ball_center_2d, ball_radius_px)
        if flow is None:
            return None

        cx, cy = ball_center_2d
        fx = self.focal_length

        if ball_center_3d is not None:
            depth = ball_center_3d[2]
        else:
            depth = self.ball_radius * fx / max(ball_radius_px, 1.0)

        scale = depth / fx
        r_3d = np.array([
            (cx - self.image_width / 2) * scale,
            (cy - self.image_height / 2) * scale,
            self.ball_radius,
        ])

        flow_3d = np.array([flow[0] * scale, flow[1] * scale, 0.0])

        omega = np.cross(r_3d, flow_3d) / (np.dot(r_3d, r_3d) + 1e-10)

        spin_rpm = np.linalg.norm(omega) * 60.0 / (2.0 * np.pi)

        n_events = len(events)
        confidence = min(1.0, n_events / 100.0)

        return SpinState(
            wx=float(omega[0]),
            wy=float(omega[1]),
            wz=float(omega[2]),
            spin_rpm=float(spin_rpm),
            confidence=float(confidence),
            method="event_camera",
        )


class MarkerPoseSpin:
    """
    Marker-based angular velocity estimator using PnP pose estimation.

    Estimates angular velocity by solving PnP for consecutive frames
    and computing the relative rotation:

        delta_R = R_{t+1} * R_t^{-1}
        omega = axis(delta_R) * angle(delta_R) / dt

    Reference: SpinDOE (Spin Detection and Estimation, 2024)
    """

    def __init__(
        self,
        ball_radius: float = 0.02,
        camera_matrix: Optional[np.ndarray] = None,
        dist_coeffs: Optional[np.ndarray] = None,
    ):
        self.ball_radius = ball_radius
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs if dist_coeffs is not None else np.zeros(5)
        self._prev_rotation: Optional[np.ndarray] = None
        self._prev_timestamp: Optional[float] = None

    def solve_pnp(
        self,
        points_2d: np.ndarray,
        points_3d: np.ndarray,
        camera_matrix: Optional[np.ndarray] = None,
    ) -> Optional[np.ndarray]:
        K = camera_matrix if camera_matrix is not None else self.camera_matrix
        if K is None:
            raise ValueError("Camera matrix required for PnP")

        if len(points_2d) < 4 or len(points_3d) < 4:
            return None

        try:
            import cv2
            success, rvec, _ = cv2.solvePnP(
                points_3d.astype(np.float32),
                points_2d.astype(np.float32),
                K.astype(np.float32),
                self.dist_coeffs.astype(np.float32),
                flags=cv2.SOLVEPNP_ITERATIVE,
            )
            if not success:
                return None
            R, _ = cv2.Rodrigues(rvec)
            return R
        except ImportError:
            return self._solve_pnp_fallback(points_2d, points_3d, K)

    def _solve_pnp_fallback(
        self, points_2d: np.ndarray, points_3d: np.ndarray, K: np.ndarray
    ) -> Optional[np.ndarray]:
        n = min(len(points_2d), len(points_3d))
        if n < 4:
            return None

        K_inv = np.linalg.inv(K)
        rays = []
        for i in range(n):
            p_homo = np.array([points_2d[i, 0], points_2d[i, 1], 1.0])
            ray = K_inv @ p_homo
            ray = ray / np.linalg.norm(ray)
            rays.append(ray)

        best_R = np.eye(3)
        best_error = float("inf")

        for i in range(n):
            for j in range(i + 1, n):
                d3d = points_3d[j] - points_3d[i]
                d3d_norm = np.linalg.norm(d3d)
                if d3d_norm < 1e-8:
                    continue
                d3d_unit = d3d / d3d_norm

                cos_angle = np.clip(np.dot(rays[i], rays[j]), -1.0, 1.0)
                angle = np.arccos(cos_angle)
                if angle < 1e-6:
                    continue

                depth_i = d3d_norm * np.sin(angle) / max(np.sin(angle), 1e-6)
                p3d_i = rays[i] * depth_i
                p3d_j = p3d_i + d3d

                R_est = np.eye(3)
                error = np.linalg.norm(R_est @ points_3d[i] - p3d_i)
                if error < best_error:
                    best_error = error
                    best_R = R_est

        return best_R

    def update(
        self,
        marker_points_2d: np.ndarray,
        marker_points_3d: np.ndarray,
        timestamp: float,
        camera_matrix: Optional[np.ndarray] = None,
    ) -> Optional[SpinState]:
        R = self.solve_pnp(marker_points_2d, marker_points_3d, camera_matrix)
        if R is None:
            return None

        if self._prev_rotation is None:
            self._prev_rotation = R
            self._prev_timestamp = timestamp
            return SpinState(
                wx=0.0, wy=0.0, wz=0.0,
                spin_rpm=0.0, confidence=0.0, method="marker_pose",
            )

        dt = timestamp - self._prev_timestamp
        if dt < 1e-9:
            self._prev_rotation = R
            return SpinState(
                wx=0.0, wy=0.0, wz=0.0,
                spin_rpm=0.0, confidence=0.0, method="marker_pose",
            )

        delta_R = R @ self._prev_rotation.T
        omega = self._rotation_to_omega(delta_R, dt)

        self._prev_rotation = R
        self._prev_timestamp = timestamp

        n_markers = len(marker_points_2d)
        confidence = min(1.0, n_markers / 8.0)

        return SpinState(
            wx=float(omega[0]),
            wy=float(omega[1]),
            wz=float(omega[2]),
            spin_rpm=float(np.linalg.norm(omega) * 60.0 / (2.0 * np.pi)),
            confidence=float(confidence),
            method="marker_pose",
        )

    @staticmethod
    def _rotation_to_omega(R: np.ndarray, dt: float) -> np.ndarray:
        angle = np.arccos(np.clip((np.trace(R) - 1.0) / 2.0, -1.0, 1.0))
        if abs(angle) < 1e-10:
            return np.zeros(3)

        axis = np.array([
            R[2, 1] - R[1, 2],
            R[0, 2] - R[2, 0],
            R[1, 0] - R[0, 1],
        ])
        axis_norm = np.linalg.norm(axis)
        if axis_norm < 1e-10:
            return np.zeros(3)
        axis = axis / axis_norm

        return axis * angle / dt

    def reset(self):
        self._prev_rotation = None
        self._prev_timestamp = None


class TrajectoryMagnusSpin:
    """
    Trajectory-based angular velocity estimator via Magnus effect.

    Estimates angular velocity by fitting a flight model with Magnus force
    to the observed trajectory and inverting for omega:

        F_Magnus = C_L * (4/3) * pi * r^3 * rho * (omega x v)

    Also uses bounce velocity change as auxiliary spin information.

    Reference: General aerodynamics, used as auxiliary in multiple systems
    """

    def __init__(
        self,
        ball_radius: float = 0.02,
        ball_mass: float = 0.0027,
        air_density: float = 1.225,
        drag_coefficient: float = 0.47,
        lift_coefficient: float = 0.2,
        gravity: float = 9.81,
    ):
        self.ball_radius = ball_radius
        self.ball_mass = ball_mass
        self.air_density = air_density
        self.drag_coefficient = drag_coefficient
        self.lift_coefficient = lift_coefficient
        self.gravity = gravity

        self.ball_volume = (4.0 / 3.0) * np.pi * ball_radius ** 3
        self.cross_section = np.pi * ball_radius ** 2

    def _compute_acceleration(
        self, position: np.ndarray, velocity: np.ndarray, omega: np.ndarray
    ) -> np.ndarray:
        a_gravity = np.array([0.0, 0.0, -self.gravity])

        speed = np.linalg.norm(velocity)
        if speed < 1e-8:
            return a_gravity

        F_drag = -0.5 * self.drag_coefficient * self.air_density * self.cross_section * speed * velocity
        a_drag = F_drag / self.ball_mass

        F_magnus = self.lift_coefficient * self.ball_volume * self.air_density * np.cross(omega, velocity)
        a_magnus = F_magnus / self.ball_mass

        return a_gravity + a_drag + a_magnus

    def estimate(
        self,
        positions: np.ndarray,
        timestamps: np.ndarray,
        initial_omega: Optional[np.ndarray] = None,
    ) -> Optional[SpinState]:
        if len(positions) < 5 or len(timestamps) < 5:
            return None

        if initial_omega is None:
            initial_omega = np.zeros(3)

        omega, residual = self._fit_omega(positions, timestamps, initial_omega)

        if omega is None:
            return None

        spin_rpm = np.linalg.norm(omega) * 60.0 / (2.0 * np.pi)

        pos_noise_est = residual / max(len(positions) - 4, 1)
        confidence = max(0.0, min(1.0, 1.0 - pos_noise_est / 0.01))

        return SpinState(
            wx=float(omega[0]),
            wy=float(omega[1]),
            wz=float(omega[2]),
            spin_rpm=float(spin_rpm),
            confidence=float(confidence),
            method="trajectory_magnus",
        )

    def _fit_omega(
        self, positions: np.ndarray, timestamps: np.ndarray,
        initial_omega: np.ndarray, n_iterations: int = 20, lr: float = 0.01
    ) -> Tuple[Optional[np.ndarray], float]:
        omega = initial_omega.copy()

        best_residual = float("inf")
        best_omega = omega.copy()

        for _ in range(n_iterations):
            residual = self._compute_residual(positions, timestamps, omega)
            if residual < best_residual:
                best_residual = residual
                best_omega = omega.copy()

            grad = np.zeros(3)
            eps = 1e-4
            for dim in range(3):
                omega_plus = omega.copy()
                omega_plus[dim] += eps
                res_plus = self._compute_residual(positions, timestamps, omega_plus)

                omega_minus = omega.copy()
                omega_minus[dim] -= eps
                res_minus = self._compute_residual(positions, timestamps, omega_minus)

                grad[dim] = (res_plus - res_minus) / (2.0 * eps)

            grad_norm = np.linalg.norm(grad)
            if grad_norm < 1e-10:
                break

            omega = omega - lr * grad / (grad_norm + 1e-8)

        if best_residual > 1e6:
            return None, best_residual

        return best_omega, best_residual

    def _compute_residual(
        self, positions: np.ndarray, timestamps: np.ndarray, omega: np.ndarray
    ) -> float:
        n = len(positions)
        dt0 = timestamps[1] - timestamps[0]
        velocity = (positions[1] - positions[0]) / max(dt0, 1e-9)

        total_residual = 0.0
        for i in range(1, n - 1):
            dt = timestamps[i] - timestamps[i - 1]
            if dt < 1e-9:
                continue

            a = self._compute_acceleration(positions[i - 1], velocity, omega)
            predicted_pos = positions[i - 1] + velocity * dt + 0.5 * a * dt ** 2

            residual = np.linalg.norm(positions[i] - predicted_pos) ** 2
            total_residual += residual

            velocity = velocity + a * dt

        return total_residual / max(n - 2, 1)

    def estimate_from_bounce(
        self,
        velocity_before: np.ndarray,
        velocity_after: np.ndarray,
        surface_normal: np.ndarray = None,
        restitution: float = 0.9,
        friction: float = 0.3,
    ) -> Optional[SpinState]:
        if surface_normal is None:
            surface_normal = np.array([0.0, 0.0, 1.0])

        v_n_before = np.dot(velocity_before, surface_normal) * surface_normal
        v_t_before = velocity_before - v_n_before

        v_n_after = np.dot(velocity_after, surface_normal) * surface_normal
        v_t_after = velocity_after - v_n_after

        delta_v_t = v_t_after - v_t_before

        delta_v_t_norm = np.linalg.norm(delta_v_t)
        if delta_v_t_norm < 1e-6:
            return SpinState(
                wx=0.0, wy=0.0, wz=0.0,
                spin_rpm=0.0, confidence=0.0, method="trajectory_magnus",
            )

        omega_direction = np.cross(surface_normal, delta_v_t)
        omega_dir_norm = np.linalg.norm(omega_direction)
        if omega_dir_norm < 1e-8:
            return None
        omega_direction = omega_direction / omega_dir_norm

        omega_magnitude = delta_v_t_norm / (friction * self.ball_radius + 1e-10)
        omega = omega_direction * omega_magnitude

        spin_rpm = np.linalg.norm(omega) * 60.0 / (2.0 * np.pi)

        return SpinState(
            wx=float(omega[0]),
            wy=float(omega[1]),
            wz=float(omega[2]),
            spin_rpm=float(spin_rpm),
            confidence=0.3,
            method="trajectory_magnus",
        )

    def reset(self):
        pass
