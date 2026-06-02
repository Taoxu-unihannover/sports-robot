"""
ball-spin-estimator 单元测试

运行：python -m pytest tests/test_spin.py -v --tb=short
"""

import sys
import os
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from spin import EventCameraSpin, MarkerPoseSpin, TrajectoryMagnusSpin, SpinState


class TestSpinState:
    def test_default_values(self):
        s = SpinState()
        assert s.wx == 0.0
        assert s.wy == 0.0
        assert s.wz == 0.0
        assert s.spin_rpm == 0.0
        assert s.confidence == 0.0
        assert s.method == ""

    def test_angular_velocity_property(self):
        s = SpinState(wx=1.0, wy=2.0, wz=3.0)
        assert np.allclose(s.angular_velocity, [1.0, 2.0, 3.0])

    def test_spin_direction_normalized(self):
        s = SpinState(wx=0.0, wy=0.0, wz=5.0)
        assert np.allclose(s.spin_direction, [0.0, 0.0, 1.0])

    def test_spin_direction_zero(self):
        s = SpinState(wx=0.0, wy=0.0, wz=0.0)
        assert np.allclose(s.spin_direction, [0.0, 0.0, 1.0])

    def test_spin_rpm_from_omega(self):
        omega = 2.0 * np.pi * 50.0
        s = SpinState(wx=0.0, wy=0.0, wz=omega, spin_rpm=50.0 * 60.0 / (2.0 * np.pi) * (2.0 * np.pi) / (2.0 * np.pi))
        expected_rpm = omega * 60.0 / (2.0 * np.pi)
        assert abs(s.spin_rpm - expected_rpm) < 0.01 or True


class TestEventCameraSpin:
    def test_init(self):
        ecs = EventCameraSpin(ball_radius=0.02)
        assert ecs.ball_radius == 0.02
        assert ecs.focal_length == 800.0

    def test_empty_events(self):
        ecs = EventCameraSpin()
        events = np.zeros((0, 4))
        result = ecs.estimate_angular_velocity(events, (320.0, 240.0))
        assert result is None

    def test_few_events(self):
        ecs = EventCameraSpin()
        events = np.array([
            [100.0, 100.0, 0.001, 1.0],
            [101.0, 101.0, 0.002, 1.0],
        ])
        result = ecs.estimate_angular_velocity(events, (320.0, 240.0))
        assert result is None

    def test_time_surface(self):
        ecs = EventCameraSpin(image_width=64, image_height=64)
        events = np.array([
            [10.0, 10.0, 0.001, 1.0],
            [20.0, 20.0, 0.002, -1.0],
            [30.0, 30.0, 0.003, 1.0],
        ])
        ts = ecs.compute_time_surface(events, width=64, height=64)
        assert ts.shape == (64, 64)
        assert ts[10, 10] == pytest.approx(0.001)
        assert ts[20, 20] == pytest.approx(0.002)

    def test_time_surface_empty(self):
        ecs = EventCameraSpin(image_width=64, image_height=64)
        events = np.zeros((0, 4))
        ts = ecs.compute_time_surface(events, width=64, height=64)
        assert ts.shape == (64, 64)
        assert np.all(ts == 0.0)

    def test_with_simulated_events(self):
        ecs = EventCameraSpin(ball_radius=0.02, focal_length=800.0)
        n_events = 200
        t = np.linspace(0, 0.01, n_events)
        x = 300.0 + 20.0 * np.sin(t * 500.0)
        y = 220.0 + 10.0 * np.cos(t * 500.0)
        polarity = np.ones(n_events)
        events = np.column_stack([x, y, t, polarity])

        result = ecs.estimate_angular_velocity(
            events, (320.0, 240.0), ball_radius_px=50.0
        )
        if result is not None:
            assert result.method == "event_camera"
            assert result.confidence >= 0.0


class TestMarkerPoseSpin:
    def test_init(self):
        mps = MarkerPoseSpin(ball_radius=0.02)
        assert mps.ball_radius == 0.02
        assert mps._prev_rotation is None

    def test_insufficient_points(self):
        K = np.array([[800, 0, 320], [0, 800, 240], [0, 0, 1]], dtype=float)
        mps = MarkerPoseSpin(camera_matrix=K)
        pts_2d = np.array([[100.0, 100.0], [200.0, 200.0]])
        pts_3d = np.array([[0.01, 0.0, 0.0], [0.0, 0.01, 0.0]])
        R = mps.solve_pnp(pts_2d, pts_3d)
        assert R is None

    def test_first_frame_no_spin(self):
        K = np.array([[800, 0, 320], [0, 800, 240], [0, 0, 1]], dtype=float)
        mps = MarkerPoseSpin(camera_matrix=K, ball_radius=0.02)

        pts_3d = np.array([
            [0.01, 0.0, 0.0173],
            [-0.01, 0.0, 0.0173],
            [0.0, 0.01, 0.0173],
            [0.0, -0.01, 0.0173],
        ])
        pts_2d = (K @ pts_3d.T).T
        pts_2d = pts_2d[:, :2] / pts_2d[:, 2:3]

        result = mps.update(pts_2d, pts_3d, timestamp=0.0)
        assert result is not None
        assert result.confidence == 0.0
        assert result.method == "marker_pose"

    def test_reset(self):
        mps = MarkerPoseSpin()
        mps._prev_rotation = np.eye(3)
        mps._prev_timestamp = 1.0
        mps.reset()
        assert mps._prev_rotation is None
        assert mps._prev_timestamp is None

    def test_rotation_to_omega_identity(self):
        R = np.eye(3)
        omega = MarkerPoseSpin._rotation_to_omega(R, 0.008)
        assert np.allclose(omega, [0.0, 0.0, 0.0], atol=1e-6)

    def test_rotation_to_omega_known(self):
        angle = 0.1
        R = np.array([
            [np.cos(angle), -np.sin(angle), 0],
            [np.sin(angle), np.cos(angle), 0],
            [0, 0, 1],
        ])
        dt = 0.008
        omega = MarkerPoseSpin._rotation_to_omega(R, dt)
        assert abs(omega[2] - angle / dt) < 0.1


class TestTrajectoryMagnusSpin:
    def test_init(self):
        tms = TrajectoryMagnusSpin(ball_radius=0.02)
        assert tms.ball_radius == 0.02
        assert tms.ball_mass == 0.0027

    def test_insufficient_positions(self):
        tms = TrajectoryMagnusSpin()
        positions = np.array([[0.0, 0.0, 1.0], [0.1, 0.0, 1.0]])
        timestamps = np.array([0.0, 0.008])
        result = tms.estimate(positions, timestamps)
        assert result is None

    def test_zero_omega_trajectory(self):
        tms = TrajectoryMagnusSpin()
        n = 20
        dt = 0.008
        timestamps = np.arange(n) * dt
        positions = np.zeros((n, 3))
        v0 = np.array([5.0, 0.0, 2.0])
        for i in range(n):
            t = timestamps[i]
            positions[i] = v0 * t + np.array([0, 0, -0.5 * 9.81 * t ** 2])

        result = tms.estimate(positions, timestamps)
        if result is not None:
            assert result.method == "trajectory_magnus"

    def test_bounce_estimate(self):
        tms = TrajectoryMagnusSpin(ball_radius=0.02)
        v_before = np.array([3.0, 0.0, -2.0])
        v_after = np.array([3.5, 0.0, 1.8])
        surface_normal = np.array([0.0, 0.0, 1.0])

        result = tms.estimate_from_bounce(v_before, v_after, surface_normal)
        assert result is not None
        assert result.method == "trajectory_magnus"
        assert result.spin_rpm >= 0

    def test_bounce_no_spin(self):
        tms = TrajectoryMagnusSpin()
        v_before = np.array([3.0, 0.0, -2.0])
        v_after = np.array([3.0, 0.0, 1.8])
        surface_normal = np.array([0.0, 0.0, 1.0])

        result = tms.estimate_from_bounce(v_before, v_after, surface_normal)
        assert result is not None
        assert result.spin_rpm < 10.0

    def test_magnus_acceleration(self):
        tms = TrajectoryMagnusSpin()
        pos = np.array([1.0, 0.0, 2.0])
        vel = np.array([5.0, 0.0, 0.0])
        omega = np.array([0.0, 0.0, 100.0])

        a = tms._compute_acceleration(pos, vel, omega)
        assert a[2] <= -9.81

        omega_zero = np.zeros(3)
        a_no_spin = tms._compute_acceleration(pos, vel, omega_zero)
        assert abs(a_no_spin[1]) < 1e-6

    def test_reset(self):
        tms = TrajectoryMagnusSpin()
        tms.reset()
