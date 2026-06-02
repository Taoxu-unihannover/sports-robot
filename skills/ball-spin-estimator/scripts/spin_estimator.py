"""
Module 5: Ball Spin Estimator

Responsibility: Estimate ball angular velocity (spin) from event streams,
surface markers, or flight trajectory. Spin is unobservable from single-frame
position and requires temporal or surface information.

Implements:
- EventCameraSpinEstimator - event camera + optical flow + angular velocity regression
- MarkerBasedSpinEstimator - surface marker PnP + relative rotation
- TrajectoryBasedSpinEstimator - Magnus effect trajectory inversion
"""

import numpy as np
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass


@dataclass
class SpinResult:
    omega_x: float
    omega_y: float
    omega_z: float
    spin_rpm: float
    confidence: float
    method: str

    @property
    def omega(self) -> np.ndarray:
        return np.array([self.omega_x, self.omega_y, self.omega_z])

    @property
    def spin_axis(self) -> np.ndarray:
        norm = np.linalg.norm(self.omega)
        if norm < 1e-10:
            return np.array([0.0, 0.0, 1.0])
        return self.omega / norm


class EventCameraSpinEstimator:
    """
    Estimate spin from event camera data.

    Pipeline: Event stream → Time Surface → Event Optical Flow → Angular Velocity Regression

    The geometric constraint between surface optical flow and angular velocity is:
        v_flow = omega x r
    where r is the vector from ball center to surface point.

    Reference: Tübingen CVPRW 2024; Sony Ace (Nature 2026)
    """

    def __init__(
        self,
        ball_radius: float = 0.02,
        focal_length: float = 800.0,
        time_surface_decay: float = 0.05,
        min_events: int = 100,
    ):
        self.ball_radius = ball_radius
        self.focal_length = focal_length
        self.time_surface_decay = time_surface_decay
        self.min_events = min_events

    def estimate(
        self,
        events: List[Tuple[float, float, float, int]],
        ball_center_2d: Optional[Tuple[float, float]] = None,
        ball_radius_px: Optional[float] = None,
    ) -> Optional[SpinResult]:
        if len(events) < self.min_events:
            return None

        if ball_center_2d is None or ball_radius_px is None:
            ball_center_2d, ball_radius_px = self._estimate_ball_params(events)

        time_surface = self._build_time_surface(events)
        flow_vectors = self._compute_event_flow(time_surface, events)

        if len(flow_vectors) < 10:
            return None

        omega = self._regress_angular_velocity(
            flow_vectors, ball_center_2d, ball_radius_px
        )

        if omega is None:
            return None

        spin_rpm = np.linalg.norm(omega) * 60.0 / (2.0 * np.pi)
        confidence = min(len(flow_vectors) / 500.0, 1.0)

        return SpinResult(
            omega_x=float(omega[0]),
            omega_y=float(omega[1]),
            omega_z=float(omega[2]),
            spin_rpm=float(spin_rpm),
            confidence=float(confidence),
            method="event_camera",
        )

    def _build_time_surface(
        self, events: List[Tuple[float, float, float, int]]
    ) -> Dict[Tuple[int, int], float]:
        time_surface = {}
        for x, y, t, p in events:
            ix, iy = int(x), int(y)
            time_surface[(ix, iy)] = t
        return time_surface

    def _compute_event_flow(
        self,
        time_surface: Dict[Tuple[int, int], float],
        events: List[Tuple[float, float, float, int]],
    ) -> List[Tuple[float, float, float, float]]:
        flow_vectors = []
        for x, y, t, p in events:
            ix, iy = int(x), int(y)
            dt_dx = 0.0
            dt_dy = 0.0
            neighbors = 0

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = ix + dx, iy + dy
                if (nx, ny) in time_surface:
                    dt = time_surface[(nx, ny)] - t
                    if dx != 0:
                        dt_dx += dt / dx
                    if dy != 0:
                        dt_dy += dt / dy
                    neighbors += 1

            if neighbors >= 2 and (abs(dt_dx) > 1e-10 or abs(dt_dy) > 1e-10):
                vx = 1.0 / dt_dx if abs(dt_dx) > 1e-10 else 0.0
                vy = 1.0 / dt_dy if abs(dt_dy) > 1e-10 else 0.0
                flow_vectors.append((x, y, vx, vy))

        return flow_vectors

    def _regress_angular_velocity(
        self,
        flow_vectors: List[Tuple[float, float, float, float]],
        ball_center: Tuple[float, float],
        ball_radius_px: float,
    ) -> Optional[np.ndarray]:
        cx, cy = ball_center
        A_rows = []
        b_rows = []

        for x, y, vx, vy in flow_vectors:
            rx = (x - cx) / ball_radius_px * self.ball_radius
            ry = (y - cy) / ball_radius_px * self.ball_radius
            rz = np.sqrt(max(self.ball_radius ** 2 - rx ** 2 - ry ** 2, 0.0))

            A_rows.append([0.0, rz, -ry, -rz, 0.0, rx])
            b_rows.append(vx)
            A_rows.append([-rz, 0.0, rx, ry, -rx, 0.0])
            b_rows.append(vy)

        if len(A_rows) < 6:
            return None

        A = np.array(A_rows)
        b = np.array(b_rows)
        try:
            result, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
            omega = result[:3]
            return omega
        except np.linalg.LinAlgError:
            return None

    def _estimate_ball_params(
        self, events: List[Tuple[float, float, float, int]]
    ) -> Tuple[Tuple[float, float], float]:
        xs = [e[0] for e in events]
        ys = [e[1] for e in events]
        cx = np.mean(xs)
        cy = np.mean(ys)
        radius = max(np.std(xs), np.std(ys)) * 2.0
        return (cx, cy), max(radius, 10.0)


class MarkerBasedSpinEstimator:
    """
    Estimate spin from surface marker points using geometric pose estimation.

    Pipeline: Detect 2D markers → PnP matching → Relative rotation → Angular velocity

    Reference: SpinDOE (UZH RPG, 2024)
    """

    def __init__(
        self,
        ball_radius: float = 0.02,
        min_markers: int = 4,
    ):
        self.ball_radius = ball_radius
        self.min_markers = min_markers
        self.prev_rotation: Optional[np.ndarray] = None
        self.prev_timestamp: Optional[float] = None

    def estimate(
        self,
        points_2d: np.ndarray,
        points_3d: np.ndarray,
        camera_matrix: np.ndarray,
        dist_coeffs: Optional[np.ndarray] = None,
        timestamp: Optional[float] = None,
    ) -> Optional[SpinResult]:
        if len(points_2d) < self.min_markers:
            return None

        if dist_coeffs is None:
            dist_coeffs = np.zeros(5)

        try:
            cv2 = __import__("cv2")
        except ImportError:
            return None

        success, rvec, _ = cv2.solvePnP(
            points_3d, points_2d, camera_matrix, dist_coeffs
        )

        if not success:
            return None

        R, _ = cv2.Rodrigues(rvec)

        if self.prev_rotation is not None and timestamp is not None and self.prev_timestamp is not None:
            dt = timestamp - self.prev_timestamp
            if dt > 1e-10:
                delta_R = R @ self.prev_rotation.T
                omega = self._rotation_to_omega(delta_R, dt)
                spin_rpm = np.linalg.norm(omega) * 60.0 / (2.0 * np.pi)
                confidence = min(len(points_2d) / 8.0, 1.0)

                self.prev_rotation = R
                self.prev_timestamp = timestamp

                return SpinResult(
                    omega_x=float(omega[0]),
                    omega_y=float(omega[1]),
                    omega_z=float(omega[2]),
                    spin_rpm=float(spin_rpm),
                    confidence=float(confidence),
                    method="marker_based",
                )

        self.prev_rotation = R
        self.prev_timestamp = timestamp
        return None

    @staticmethod
    def _rotation_to_omega(delta_R: np.ndarray, dt: float) -> np.ndarray:
        angle = np.arccos(np.clip((np.trace(delta_R) - 1.0) / 2.0, -1.0, 1.0))
        if abs(angle) < 1e-10:
            return np.zeros(3)

        axis = np.array([
            delta_R[2, 1] - delta_R[1, 2],
            delta_R[0, 2] - delta_R[2, 0],
            delta_R[1, 0] - delta_R[0, 1],
        ]) / (2.0 * np.sin(angle))

        return axis * angle / dt

    def reset(self):
        self.prev_rotation = None
        self.prev_timestamp = None


class TrajectoryBasedSpinEstimator:
    """
    Estimate spin from flight trajectory by inverting the Magnus effect.

    Pipeline: 3D trajectory → Physics model fitting (gravity + drag + Magnus) → Angular velocity

    The Magnus force is:
        F_Magnus = C_L * (4/3) * pi * r^3 * rho * (omega x v)

    This method is limited by the small magnitude of Magnus force relative
    to gravity (typically < 1 m/s^2 vs 9.8 m/s^2 for table tennis),
    requiring very high position accuracy.

    Reference: General physics-based approach used in ball sports analysis
    """

    def __init__(
        self,
        ball_radius: float = 0.02,
        ball_mass: float = 0.0027,
        air_density: float = 1.225,
        lift_coefficient: float = 0.4,
        drag_coefficient: float = 0.01,
        min_trajectory_length: int = 10,
    ):
        self.ball_radius = ball_radius
        self.ball_mass = ball_mass
        self.air_density = air_density
        self.lift_coefficient = lift_coefficient
        self.drag_coefficient = drag_coefficient
        self.min_trajectory_length = min_trajectory_length

    def estimate(
        self,
        trajectory_3d: np.ndarray,
        timestamps: np.ndarray,
    ) -> Optional[SpinResult]:
        if len(trajectory_3d) < self.min_trajectory_length:
            return None

        velocities = self._compute_velocities(trajectory_3d, timestamps)
        accelerations = self._compute_accelerations(velocities, timestamps)

        gravity = np.array([0.0, 0.0, -9.81])
        magnus_accelerations = []
        velocity_samples = []

        for i in range(len(accelerations)):
            v = velocities[min(i, len(velocities) - 1)]
            speed = np.linalg.norm(v)
            if speed < 0.1:
                continue

            drag_accel = -self.drag_coefficient * speed * v
            expected_gravity_drag = gravity + drag_accel
            magnus_accel = accelerations[i] - expected_gravity_drag
            magnus_accelerations.append(magnus_accel)
            velocity_samples.append(v)

        if len(magnus_accelerations) < 3:
            return None

        avg_magnus = np.mean(magnus_accelerations, axis=0)
        avg_velocity = np.mean(velocity_samples, axis=0)

        volume = (4.0 / 3.0) * np.pi * self.ball_radius ** 3
        magnus_coeff = (
            self.lift_coefficient * volume * self.air_density / self.ball_mass
        )

        speed = np.linalg.norm(avg_velocity)
        if speed < 0.1:
            return None

        v_hat = avg_velocity / speed
        magnus_perp = avg_magnus - np.dot(avg_magnus, v_hat) * v_hat

        magnus_perp_norm = np.linalg.norm(magnus_perp)
        if magnus_perp_norm < 1e-6:
            return SpinResult(
                omega_x=0.0, omega_y=0.0, omega_z=0.0,
                spin_rpm=0.0, confidence=0.3, method="trajectory_based",
            )

        magnus_dir = magnus_perp / magnus_perp_norm
        omega_magnitude = magnus_perp_norm / (magnus_coeff * speed)
        spin_axis = np.cross(v_hat, magnus_dir)
        spin_axis_norm = np.linalg.norm(spin_axis)
        if spin_axis_norm < 1e-10:
            return None
        spin_axis = spin_axis / spin_axis_norm

        omega = spin_axis * omega_magnitude
        spin_rpm = omega_magnitude * 60.0 / (2.0 * np.pi)

        fit_residual = np.std([np.linalg.norm(m) for m in magnus_accelerations])
        confidence = max(0.1, min(1.0 - fit_residual / max(magnus_perp_norm, 0.01), 0.9))

        return SpinResult(
            omega_x=float(omega[0]),
            omega_y=float(omega[1]),
            omega_z=float(omega[2]),
            spin_rpm=float(spin_rpm),
            confidence=float(confidence),
            method="trajectory_based",
        )

    @staticmethod
    def _compute_velocities(
        trajectory: np.ndarray, timestamps: np.ndarray
    ) -> np.ndarray:
        n = len(trajectory)
        velocities = np.zeros_like(trajectory)
        for i in range(n):
            if i == 0:
                dt = timestamps[1] - timestamps[0]
                velocities[i] = (trajectory[1] - trajectory[0]) / dt
            elif i == n - 1:
                dt = timestamps[-1] - timestamps[-2]
                velocities[i] = (trajectory[-1] - trajectory[-2]) / dt
            else:
                dt = timestamps[i + 1] - timestamps[i - 1]
                velocities[i] = (trajectory[i + 1] - trajectory[i - 1]) / dt
        return velocities

    @staticmethod
    def _compute_accelerations(
        velocities: np.ndarray, timestamps: np.ndarray
    ) -> np.ndarray:
        n = len(velocities)
        accelerations = np.zeros_like(velocities)
        for i in range(1, n - 1):
            dt = timestamps[i + 1] - timestamps[i - 1]
            if dt > 1e-10:
                accelerations[i] = (velocities[i + 1] - velocities[i - 1]) / dt
        if n > 1:
            accelerations[0] = accelerations[1]
            accelerations[-1] = accelerations[-2]
        return accelerations
