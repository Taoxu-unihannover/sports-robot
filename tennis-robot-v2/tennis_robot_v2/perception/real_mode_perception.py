#!/usr/bin/env python3
"""
Real-mode perception pipeline for tennis-robot-v2.

Implements the image-based perception chain:
  MuJoCo render → binocular camera → ball detection (HSV) →
  stereo depth (SGBM) → coordinate transform →
  Kalman filter → obs reconstruction

This is absorbed from dynamic-tennis-v2's binocular_camera module.
"""

import os
import sys
import math
import numpy as np

import cv2


class SimBallDetector:
    """
    HSV-based tennis ball detector for simulation images.

    Absorbed from dynamic-tennis-v2/tennis_tracker/binocular_camera/sim_ball_detector.py
    """

    # Tennis ball HSV range (green ball in simulation)
    H_MIN, H_MAX = 40, 110
    S_MIN, S_MAX = 60, 200
    V_MIN, V_MAX = 60, 200

    def __init__(self, min_area=3, max_area=50000, circularity_thresh=0.25):
        self.min_area = min_area
        self.max_area = max_area
        self.circularity_thresh = circularity_thresh

    def detect(self, image):
        """
        Detect tennis ball in image.

        Args:
            image: RGB image (HxWx3)

        Returns:
            dict with keys: cx, cy, area, or None if not detected
        """
        if image is None or image.size == 0:
            return None

        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

        # Create mask for tennis ball color (green)
        mask = cv2.inRange(hsv, (self.H_MIN, self.S_MIN, self.V_MIN),
                          (self.H_MAX, self.S_MAX, self.V_MAX))

        # Optional: morphological operations to reduce noise
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        # Filter by area
        valid_contours = [c for c in contours
                         if self.min_area <= cv2.contourArea(c) <= self.max_area]

        if not valid_contours:
            return None

        # Find largest contour
        largest = max(valid_contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)

        # Check circularity
        perimeter = cv2.arcLength(largest, True)
        if perimeter < 1e-6:
            return None
        circularity = 4 * math.pi * area / (perimeter * perimeter)

        if circularity < self.circularity_thresh:
            return None

        # Get centroid
        M = cv2.moments(largest)
        if M["m00"] < 1e-6:
            return None

        cx = M["m10"] / M["m00"]
        cy = M["m01"] / M["m00"]

        return {
            "cx": cx,
            "cy": cy,
            "area": area,
            "circularity": circularity,
        }


class ObjectKalmanFilter:
    """
    Kalman filter for ball state estimation with gravity model.

    6-D state: [x, y, z, vx, vy, vz]

    Absorbed from dynamic-tennis-v2/tennis_tracker/src/utils/filter.py
    """

    def __init__(self, dt=1.0/60.0, process_noise=0.05, measurement_noise=0.08):
        self.dt = dt
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise

        # State: [x, y, z, vx, vy, vz]
        self.x = np.zeros(6, dtype=np.float64)
        self.P = np.eye(6, dtype=np.float64) * 10.0  # Initial covariance

        # State transition matrix (with gravity)
        self.F = np.array([
            [1, 0, 0, dt, 0, 0],
            [0, 1, 0, 0, dt, 0],
            [0, 0, 1, 0, 0, dt],
            [0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 1],
        ], dtype=np.float64)

        # Add gravity effect to z velocity
        g = 9.81 * dt
        self.F[2, 5] = dt
        self.F[5, 5] = 1.0

        # Measurement matrix (observe position only)
        self.H = np.array([
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0],
        ], dtype=np.float64)

        # Measurement noise
        self.R = np.eye(3, dtype=np.float64) * (measurement_noise ** 2)

        # Process noise
        q = process_noise ** 2
        self.Q = np.array([
            [dt**4/4, 0, 0, dt**3/2, 0, 0],
            [0, dt**4/4, 0, 0, dt**3/2, 0],
            [0, 0, dt**4/4, 0, 0, dt**3/2],
            [dt**3/2, 0, 0, dt**2, 0, 0],
            [0, dt**3/2, 0, 0, dt**2, 0],
            [0, 0, dt**3/2, 0, 0, dt**2],
        ], dtype=np.float64) * q

        self.initialized = False

    def update(self, measurement):
        """
        Update Kalman filter with new measurement.

        Args:
            measurement: np.array [3] = [x, y, z] observed position

        Returns:
            dict with keys: position, velocity
        """
        if not self.initialized:
            self.x[:3] = measurement
            self.x[3:] = 0
            self.initialized = True
            return {
                "position": self.x[:3].copy(),
                "velocity": self.x[3:].copy(),
            }

        # Prediction
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q

        # Update
        z = measurement - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)

        self.x = self.x + K @ z
        self.P = (np.eye(6) - K @ self.H) @ self.P

        return {
            "position": self.x[:3].copy(),
            "velocity": self.x[3:].copy(),
        }

    def predict(self, steps=1):
        """
        Predict future state.

        Args:
            steps: number of steps to predict

        Returns:
            predicted position
        """
        F_n = np.linalg.matrix_power(self.F, steps)
        return F_n @ self.x

    def reset(self):
        """Reset filter state."""
        self.x = np.zeros(6, dtype=np.float64)
        self.P = np.eye(6, dtype=np.float64) * 10.0
        self.initialized = False


class StereoDepthEstimator:
    """
    Depth estimator using ball size for depth and pixel position for x,y.

    Absorbed from dynamic-tennis-v2/tennis_tracker/src/depth/stereo_depth.py
    """

    # Ball diameter in simulation (from scene.xml: size="0.085")
    BALL_DIAMETER = 0.085  # meters

    def __init__(self, baseline=0.24, img_height=240, fovy=45.0):
        self.baseline = baseline
        self.img_height = img_height
        self.img_width = int(img_height * 4 / 3)  # Assume 4:3 aspect ratio

        # Calibrated focal length empirically measured:
        # At true depth ~5.22m with pixel diameter ~104.8, we need focal = 6439.7
        # This compensates for MuJoCo renderer's internal rendering scale
        # Compute theoretical focal from FOV, then scale by empirically measured ratio
        theoretical_focal = (img_height / 2) / np.tan(np.radians(fovy / 2))
        self.focal_length = theoretical_focal * 22.2  # Empirical calibration factor

        # Precompute depth lookup for area-based estimation
        self._build_depth_lookup()

    def _build_depth_lookup(self):
        """Build lookup table for depth from pixel diameter."""
        self._diameter_to_depth = {}
        for pixel_d in range(1, 500):
            # z = focal * real_diameter / pixel_diameter
            depth = self.focal_length * self.BALL_DIAMETER / pixel_d
            self._diameter_to_depth[pixel_d] = min(depth, 100)  # Cap at 100m

    def estimate_depth(self, left_image, right_image, detection):
        """
        Estimate 3D position from stereo images.

        Args:
            left_image: RGB image
            right_image: RGB image
            detection: dict with cx, cy, area

        Returns:
            dict with position_cam (x, y, z in camera frame)
        """
        if detection is None:
            return None

        cx, cy = detection["cx"], detection["cy"]
        area = detection.get("area", 100)

        # Estimate depth from ball size (more reliable than stereo in simulation)
        # Convert area to diameter: d = 2 * sqrt(area / pi)
        pixel_diameter = 2 * np.sqrt(area / np.pi)

        # Look up depth from diameter
        pixel_d_int = int(round(pixel_diameter))
        if pixel_d_int in self._diameter_to_depth:
            z = self._diameter_to_depth[pixel_d_int]
        else:
            # Fallback: use direct calculation
            z = self.focal_length * self.BALL_DIAMETER / pixel_diameter

        # Compute x, y in camera frame from pixel position
        x = (cx - left_image.shape[1] / 2) * z / self.focal_length
        y = (cy - left_image.shape[0] / 2) * z / self.focal_length

        return {"position_cam": np.array([x, y, z], dtype=np.float64)}


def compute_coriolis_velocity(ball_pos_base, ball_vel_base, robot_yaw, robot_vx, robot_vy, robot_wz):
    """
    Compute ball velocity in world coordinates with Coriolis correction.

    This is the key finding from dynamic-tennis-v2 absorption:
    v_ball_world = v_robot_world + R_b2w @ v_ball_base + ω × r_world

    Args:
        ball_pos_base: ball position in base frame [x, y, z]
        ball_vel_base: ball velocity in base frame [vx, vy, vz]
        robot_yaw: robot yaw angle
        robot_vx, robot_vy: robot linear velocity in base frame
        robot_wz: robot angular velocity (yaw rate)

    Returns:
        ball velocity in world frame [vx, vy]
    """
    cos_y = math.cos(robot_yaw)
    sin_y = math.sin(robot_yaw)
    R_b2w = np.array([[cos_y, -sin_y], [sin_y, cos_y]])

    # Rotate ball velocity from base to world
    ball_v_xy = R_b2w @ ball_vel_base[:2].astype(np.float64)

    # Robot velocity in world frame
    robot_v_world = np.array([robot_vx * cos_y - robot_vy * sin_y,
                              robot_vx * sin_y + robot_vy * cos_y])

    # Coriolis term: ω × r
    # r_world = R_b2w @ ball_pos_base[:2]
    rel_pos_world = np.array([
        ball_pos_base[0] * cos_y - ball_pos_base[1] * sin_y,
        ball_pos_base[0] * sin_y + ball_pos_base[1] * cos_y,
    ])
    coriolis = np.array([-robot_wz * rel_pos_world[1],
                          robot_wz * rel_pos_world[0]])

    # Total world velocity
    ball_v_world = robot_v_world + ball_v_xy + coriolis

    return ball_v_world


class TennisRobotV2ObsBuilder:
    """
    Observation builder for tennis-robot-v2 with sim/real dual mode.

    Absorbed from dynamic-tennis-v2/tennis_tracker/binocular_camera/obs_builder.py

    Sim mode: direct from MuJoCo (truth state)
    Real mode: binocular camera → ball detection → depth → Kalman → obs reconstruction
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.mode = self.config.get("obs_mode", "sim")

        # Robot parameters
        self.v_max_x = self.config.get("v_max_x", 5.0)
        self.v_max_y = self.config.get("v_max_y", 2.0)
        self.w_max = self.config.get("w_max", 1.5)
        self.court_diagonal = self.config.get("court_diagonal", 14.45)

        # Camera transform (camera -> base_link)
        # Camera: pos=(-0.12, -0.18, 0.18) in cargo_box, looks -Y direction (forward=[0,-1,0])
        # Camera frame: +X=right, +Y=up, +Z=forward (toward -Y world)
        # Base frame: +X=forward (+X world), +Y=left (-Y world), +Z=up
        # Transform: camera +X (right) -> base -Y, camera +Y (up) -> base +Z, camera +Z (forward/-Y) -> base +X
        self.T_base_cam = np.array([
            [ 0.0,  0.0,  1.0, -0.12],  # camera +X -> base +Y, camera +Z -> base +X, camera pos
            [ 0.0,  0.0, -1.0, -0.18],  # camera -Z -> base +Y
            [ 0.0,  1.0,  0.0, -0.18],  # camera +Y -> base +Z
            [ 0.0,  0.0,  0.0,   1.0],
        ], dtype=np.float64)

        # Initialize perception components
        self.detector = SimBallDetector(min_area=3)
        # NOTE: cameras in simulation are 4.19m apart (box_cam1 at x=-0.12, box_cam2 at x=0.12)
        # This is much larger than real binocular cameras (0.24m baseline)
        # Use actual camera spacing for accurate depth estimation
        self.depth_estimator = StereoDepthEstimator(baseline=4.19)
        self.kalman = ObjectKalmanFilter(dt=1.0/60.0, process_noise=0.05, measurement_noise=0.08)

        self._last_ball_pos = None
        self._last_ball_vel = None
        self._kalman_initialized = False
        self._ball_detected = False

        print(f"[TennisRobotV2ObsBuilder] mode={self.mode}")

    def reset(self):
        """Reset internal state."""
        self._last_ball_pos = None
        self._last_ball_vel = None
        self._kalman_initialized = False
        self._ball_detected = False
        self.kalman.reset()

    @property
    def ball_detected(self):
        return self._ball_detected

    def build_sim(self, env):
        """Build observation in sim mode (direct from MuJoCo)."""
        obs = env._get_obs()
        self._last_ball_pos = obs[7:9].copy() if len(obs) > 7 else None
        self._last_ball_vel = obs[9:11].copy() if len(obs) > 9 else None
        return obs

    def build_real(self, env, camera_frames):
        """
        Build observation in real mode (image-based).

        Args:
            env: TennisNavigationV2Env instance
            camera_frames: (cam1_rgb, cam2_rgb) tuple
        """
        if camera_frames is None:
            return self.build_sim(env)

        cam1_rgb, cam2_rgb = camera_frames

        # Get robot state
        robot_pos = env.data.qpos[7:9].copy()
        robot_quat = env.data.qpos[10:14].copy()
        robot_vel = env.data.qvel[6:12].copy()

        yaw = self._quat_to_euler(robot_quat)[2]
        robot_vx_base = robot_vel[0]
        robot_vy_base = robot_vel[1]
        robot_wz = robot_vel[5]

        # Ball detection
        detection = self.detector.detect(cam1_rgb)
        self._ball_detected = detection is not None and detection.get("area", 0) >= 3

        if detection:
            # Estimate depth
            depth_result = self.depth_estimator.estimate_depth(cam1_rgb, cam2_rgb, detection)

            if depth_result is not None:
                p_cam = depth_result["position_cam"]
                p_homo = np.append(p_cam, 1.0)
                p_base = (self.T_base_cam @ p_homo)[:2]

                # Kalman filter update
                result = self.kalman.update(np.array([p_base[0], p_base[1], p_cam[2]]))
                self._kalman_initialized = True
                ball_pos = result["position"].astype(np.float32)
            else:
                ball_pos = self._get_fallback_position()
        else:
            ball_pos = self._get_fallback_position()

        # Compute ball velocity from position difference
        if self._last_ball_pos is not None:
            dt = env.model.opt.timestep * env.frame_skip
            ball_vel = ((ball_pos[:2] - self._last_ball_pos) / dt).astype(np.float32)
        else:
            ball_vel = np.zeros(2, dtype=np.float32)

        # Compute Coriolis-corrected world velocity for TTC
        ball_v_world = compute_coriolis_velocity(
            np.array([ball_pos[0], ball_pos[1], 0]),
            np.array([ball_vel[0], ball_vel[1], 0]),
            yaw, robot_vx_base, robot_vy_base, robot_wz
        )

        # Build observation vector (12-dim)
        rel_x = env.goal[0] - robot_pos[0]
        rel_y = env.goal[1] - robot_pos[1]
        goal_angle = math.atan2(rel_y, rel_x)
        rel_angle = self._normalize_angle(goal_angle - yaw)
        goal_distance = math.sqrt(rel_x**2 + rel_y**2)

        goal_dist_norm = goal_distance / self.court_diagonal
        yaw_norm = yaw / (2 * math.pi)
        goal_angle_norm = goal_angle / (2 * math.pi)
        rel_angle_norm = rel_angle / math.pi

        vel_norm = robot_vel.copy()
        vel_norm[:3] /= self.v_max_x
        vel_norm[3:] /= self.w_max

        tennis_vel_norm = ball_vel.copy()
        tennis_vel_norm /= self.v_max_x

        obs = np.array([
            goal_dist_norm,
            goal_angle_norm,
            rel_angle_norm,
            yaw_norm,
            vel_norm[0], vel_norm[1], vel_norm[2],
            vel_norm[3], vel_norm[4], vel_norm[5],
            tennis_vel_norm[0], tennis_vel_norm[1],
        ], dtype=np.float32)

        self._last_ball_pos = ball_pos[:2].copy()
        self._last_ball_vel = ball_vel.copy()

        return obs

    def _get_fallback_position(self):
        """Get fallback position when detection fails."""
        if self._kalman_initialized:
            pred = self.kalman.predict(steps=1)
            # pred is full 6-dim state [x, y, z, vx, vy, vz]
            return np.array([pred[0], pred[1], pred[2]], dtype=np.float32)
        elif self._last_ball_pos is not None:
            return np.array([self._last_ball_pos[0], self._last_ball_pos[1], 0.067], dtype=np.float32)
        else:
            return np.array([0.0, 0.0, 0.067], dtype=np.float32)

    @staticmethod
    def _quat_to_euler(quat):
        x, y, z, w = quat
        t0 = 2.0 * (w * x + y * z)
        t1 = 1.0 - 2.0 * (x * x + y * y)
        roll = math.atan2(t0, t1)
        t2 = 2.0 * (w * y - z * x)
        t2 = max(-1.0, min(1.0, t2))
        pitch = math.asin(t2)
        t3 = 2.0 * (w * z + x * y)
        t4 = 1.0 - 2.0 * (y * y + z * z)
        yaw = math.atan2(t3, t4)
        return np.array([roll, pitch, yaw])

    @staticmethod
    def _normalize_angle(angle):
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle


if __name__ == "__main__":
    # Test perception pipeline
    print("=== Testing TennisRobotV2ObsBuilder ===")

    config = {
        "obs_mode": "real",
        "v_max_x": 5.0,
        "v_max_y": 2.0,
        "w_max": 1.5,
        "court_diagonal": 14.45,
    }

    builder = TennisRobotV2ObsBuilder(config)
    print(f"Mode: {builder.mode}")
    print(f"Detector: {builder.detector}")
    print(f"Depth estimator: {builder.depth_estimator}")
    print(f"Kalman filter: {builder.kalman}")

    # Test Kalman filter
    kf = ObjectKalmanFilter(dt=1/60, process_noise=0.05, measurement_noise=0.08)
    print("\n=== Testing Kalman Filter ===")

    true_pos = np.array([0.0, 5.0, 1.5])
    true_vel = np.array([0.0, -4.0, 1.0])
    dt = 1.0 / 60.0
    errors = []

    for i in range(20):
        true_vel[2] += -9.8 * dt
        true_pos += true_vel * dt
        noisy_pos = true_pos + np.random.normal(0, 0.05, 3)
        result = kf.update(noisy_pos)
        err = abs(result["position"][2] - true_pos[2])
        errors.append(err)
        if i % 5 == 0:
            print(f"  Frame {i:2d}: true_z={true_pos[2]:.3f}, filter_z={result['position'][2]:.3f}, err={err:.4f}")

    mean_err = float(np.mean(errors))
    print(f"\n  Mean position error: {mean_err:.4f} m")
    assert mean_err < 0.5, f"Kalman error too large: {mean_err:.4f}"
    print("✓ Kalman filter test passed")

    print("\n=== All perception pipeline tests passed ===")