"""
ball-spin-estimator 单元测试

运行：python -m pytest tests/test_spin_estimator.py -v --tb=short
"""

import sys
import os
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from spin_estimator import (
    EventCameraSpinEstimator,
    MarkerBasedSpinEstimator,
    TrajectoryBasedSpinEstimator,
    SpinResult,
)


class TestSpinResult:
    def test_omega_property(self):
        r = SpinResult(omega_x=1.0, omega_y=2.0, omega_z=3.0, spin_rpm=0.0, confidence=0.9, method="test")
        assert np.allclose(r.omega, [1.0, 2.0, 3.0])

    def test_spin_axis(self):
        r = SpinResult(omega_x=0.0, omega_y=0.0, omega_z=10.0, spin_rpm=0.0, confidence=0.9, method="test")
        assert np.allclose(r.spin_axis, [0.0, 0.0, 1.0])

    def test_zero_omega_axis(self):
        r = SpinResult(omega_x=0.0, omega_y=0.0, omega_z=0.0, spin_rpm=0.0, confidence=0.9, method="test")
        assert np.allclose(r.spin_axis, [0.0, 0.0, 1.0])


class TestEventCameraSpinEstimator:
    def test_init(self):
        est = EventCameraSpinEstimator(ball_radius=0.02)
        assert est.ball_radius == 0.02
        assert est.min_events == 100

    def test_insufficient_events(self):
        est = EventCameraSpinEstimator(min_events=10)
        events = [(100.0, 200.0, 0.001, 1), (101.0, 201.0, 0.002, 1)]
        result = est.estimate(events)
        assert result is None

    def test_with_events(self):
        est = EventCameraSpinEstimator(ball_radius=0.02, min_events=50)
        np.random.seed(42)
        events = []
        cx, cy = 320.0, 240.0
        radius_px = 50.0
        for i in range(500):
            angle = i * 0.02
            x = cx + radius_px * np.cos(angle) + np.random.normal(0, 0.5)
            y = cy + radius_px * np.sin(angle) + np.random.normal(0, 0.5)
            t = i * 0.00005
            p = 1
            events.append((x, y, t, p))
        result = est.estimate(events, ball_center_2d=(cx, cy), ball_radius_px=radius_px)
        assert result is not None
        assert result.method == "event_camera"
        assert result.confidence > 0.0

    def test_empty_events(self):
        est = EventCameraSpinEstimator()
        result = est.estimate([])
        assert result is None


class TestMarkerBasedSpinEstimator:
    def test_init(self):
        est = MarkerBasedSpinEstimator(ball_radius=0.02)
        assert est.ball_radius == 0.02
        assert est.prev_rotation is None

    def test_insufficient_markers(self):
        est = MarkerBasedSpinEstimator(min_markers=4)
        points_2d = np.array([[100.0, 100.0], [200.0, 200.0]])
        points_3d = np.array([[0.01, 0.0, 0.0], [0.0, 0.01, 0.0]])
        K = np.eye(3)
        result = est.estimate(points_2d, points_3d, K)
        assert result is None

    def test_reset(self):
        est = MarkerBasedSpinEstimator()
        est.prev_rotation = np.eye(3)
        est.prev_timestamp = 0.1
        est.reset()
        assert est.prev_rotation is None
        assert est.prev_timestamp is None

    def test_rotation_to_omega(self):
        angle = 0.1
        R = np.array([
            [np.cos(angle), -np.sin(angle), 0],
            [np.sin(angle), np.cos(angle), 0],
            [0, 0, 1],
        ])
        omega = MarkerBasedSpinEstimator._rotation_to_omega(R, 0.01)
        assert abs(omega[2] - angle / 0.01) < 1.0


class TestTrajectoryBasedSpinEstimator:
    def test_init(self):
        est = TrajectoryBasedSpinEstimator(ball_radius=0.02)
        assert est.ball_radius == 0.02
        assert est.min_trajectory_length == 10

    def test_short_trajectory(self):
        est = TrajectoryBasedSpinEstimator(min_trajectory_length=10)
        traj = np.random.randn(5, 3)
        ts = np.linspace(0, 0.1, 5)
        result = est.estimate(traj, ts)
        assert result is None

    def test_no_spin_trajectory(self):
        est = TrajectoryBasedSpinEstimator(
            ball_radius=0.02, ball_mass=0.0027, min_trajectory_length=5
        )
        n = 50
        dt = 0.002
        ts = np.arange(n) * dt
        traj = np.zeros((n, 3))
        for i in range(1, n):
            traj[i, 0] = traj[i - 1, 0] + 5.0 * dt
            traj[i, 2] = traj[i - 1, 2] + 3.0 * dt - 0.5 * 9.81 * dt ** 2
        result = est.estimate(traj, ts)
        if result is not None:
            assert result.method == "trajectory_based"
            assert result.confidence >= 0.0

    def test_with_spin_trajectory(self):
        est = TrajectoryBasedSpinEstimator(
            ball_radius=0.02, ball_mass=0.0027, drag_coefficient=0.0, min_trajectory_length=5
        )
        n = 100
        dt = 0.002
        ts = np.arange(n) * dt
        traj = np.zeros((n, 3))
        v0 = np.array([5.0, 0.0, 3.0])
        magnus_accel = np.array([0.0, 0.5, 0.0])
        for i in range(1, n):
            a = np.array([0.0, 0.0, -9.81]) + magnus_accel
            traj[i] = traj[i - 1] + v0 * dt + 0.5 * a * dt ** 2
            v0 = v0 + a * dt
        result = est.estimate(traj, ts)
        if result is not None:
            assert result.method == "trajectory_based"
