"""
ball-state-estimator 单元测试

运行：python -m pytest tests/test_filter.py -v --tb=short
"""

import sys
import os
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from filter import BallKalmanFilter, ExtendedBallKalmanFilter, BallState, SlidingWindowVelocity, PositionHistoryBuffer


class TestFilter:
    def test_kf_init(self):
        kf = BallKalmanFilter(dt=0.008, dim=2, model="CV")
        assert kf.dim == 2
        assert kf.model_type == "CV"
        assert not kf.initialized

    def test_kf_predict_update_2d(self):
        kf = BallKalmanFilter(dt=0.008, dim=2, model="CV")
        kf.predict()
        state = kf.update_2d(100.0, 200.0)
        assert abs(state.x - 100.0) < 20.0
        assert abs(state.y - 200.0) < 20.0
        assert kf.initialized

    def test_kf_convergence(self):
        kf = BallKalmanFilter(dt=0.008, dim=2, model="CV", measurement_noise=1.0)
        for _ in range(50):
            kf.predict()
            kf.update_2d(100.0, 200.0)
        state = kf.predict()
        assert abs(state.x - 100.0) < 1.0
        assert abs(state.y - 200.0) < 1.0

    def test_kf_3d(self):
        kf = BallKalmanFilter(dt=0.008, dim=3, model="CV")
        kf.predict()
        state = kf.update_3d(1.0, 2.0, 3.0)
        assert abs(state.x - 1.0) < 0.5
        assert abs(state.y - 2.0) < 0.5
        assert abs(state.z - 3.0) < 0.5

    def test_kf_ca_model(self):
        kf = BallKalmanFilter(dt=0.008, dim=2, model="CA")
        kf.predict()
        state = kf.update_2d(100.0, 200.0)
        assert abs(state.ax) < 0.01
        assert abs(state.ay) < 0.01

    def test_kf_predict_future(self):
        kf = BallKalmanFilter(dt=0.008, dim=2, model="CV")
        kf.predict()
        kf.update_2d(100.0, 200.0)
        kf.x[2] = 10.0
        kf.x[3] = 5.0
        future = kf.predict_future(0.1)
        assert abs(future[0] - (kf.x[0] + 1.0)) < 0.1
        assert abs(future[1] - (kf.x[1] + 0.5)) < 0.1

    def test_kf_reset(self):
        kf = BallKalmanFilter(dt=0.008, dim=2, model="CV")
        kf.predict()
        kf.update_2d(100.0, 200.0)
        kf.reset()
        assert not kf.initialized

    def test_ekf_init(self):
        ekf = ExtendedBallKalmanFilter(dt=0.008, drag_coefficient=0.01)
        assert not ekf.initialized

    def test_ekf_predict_update(self):
        ekf = ExtendedBallKalmanFilter(dt=0.008, drag_coefficient=0.01)
        ekf.predict()
        state = ekf.update(np.array([1.0, 2.0, 3.0]))
        assert abs(state.x - 1.0) < 0.5
        assert abs(state.y - 2.0) < 0.5
        assert abs(state.z - 3.0) < 0.5

    def test_ball_state_properties(self):
        s = BallState(x=1.0, y=2.0, z=3.0, vx=4.0, vy=5.0, vz=6.0)
        assert np.allclose(s.position, [1, 2, 3])
        assert np.allclose(s.velocity, [4, 5, 6])
        assert abs(s.speed - np.sqrt(16 + 25 + 36)) < 0.01


class TestSlidingWindowVelocity:
    def test_init(self):
        swv = SlidingWindowVelocity(window_size=4, dt=0.02, dim=3)
        assert swv.window_size == 4
        assert swv.dt == 0.02
        assert len(swv.history) == 0

    def test_single_frame(self):
        swv = SlidingWindowVelocity(window_size=4, dt=0.02, dim=3)
        state = swv.update_3d(1.0, 2.0, 3.0)
        assert state is not None
        assert abs(state.x - 1.0) < 0.01

    def test_velocity_estimation(self):
        swv = SlidingWindowVelocity(window_size=4, dt=0.02, dim=3)
        swv.update_3d(0.0, 0.0, 0.0)
        swv.update_3d(1.0, 0.0, 0.0)
        state = swv.update_3d(2.0, 0.0, 0.0)
        assert state is not None
        assert abs(state.vx - 50.0) < 1.0

    def test_window_size_limit(self):
        swv = SlidingWindowVelocity(window_size=3, dt=0.02, dim=3)
        for i in range(10):
            swv.update_3d(float(i), 0.0, 0.0)
        assert len(swv.history) == 3

    def test_reset(self):
        swv = SlidingWindowVelocity(window_size=4, dt=0.02, dim=3)
        swv.update_3d(1.0, 2.0, 3.0)
        swv.reset()
        assert len(swv.history) == 0

    def test_2d_mode(self):
        swv = SlidingWindowVelocity(window_size=4, dt=0.02, dim=2)
        swv.update_2d(0.0, 0.0)
        swv.update_2d(1.0, 0.0)
        state = swv.update_2d(2.0, 0.0)
        assert state is not None
        assert abs(state.vx - 50.0) < 1.0


class TestPositionHistoryBuffer:
    def test_init(self):
        phb = PositionHistoryBuffer(window_size=10, dim=3)
        assert phb.window_size == 10
        assert len(phb.history) == 0

    def test_update_shape(self):
        phb = PositionHistoryBuffer(window_size=5, dim=3)
        buf = phb.update(np.array([1.0, 2.0, 3.0]))
        assert buf.shape == (5, 3)

    def test_buffer_fill(self):
        phb = PositionHistoryBuffer(window_size=3, dim=3)
        phb.update(np.array([1.0, 0.0, 0.0]))
        phb.update(np.array([2.0, 0.0, 0.0]))
        buf = phb.update(np.array([3.0, 0.0, 0.0]))
        assert np.allclose(buf[0], [1.0, 0.0, 0.0])
        assert np.allclose(buf[2], [3.0, 0.0, 0.0])

    def test_is_full(self):
        phb = PositionHistoryBuffer(window_size=3, dim=3)
        assert not phb.is_full
        phb.update(np.array([1.0, 0.0, 0.0]))
        phb.update(np.array([2.0, 0.0, 0.0]))
        assert not phb.is_full
        phb.update(np.array([3.0, 0.0, 0.0]))
        assert phb.is_full

    def test_window_overflow(self):
        phb = PositionHistoryBuffer(window_size=3, dim=3)
        for i in range(5):
            phb.update(np.array([float(i), 0.0, 0.0]))
        assert len(phb.history) == 3
        assert np.allclose(phb.history[0], [2.0, 0.0, 0.0])

    def test_reset(self):
        phb = PositionHistoryBuffer(window_size=5, dim=3)
        phb.update(np.array([1.0, 2.0, 3.0]))
        phb.reset()
        assert len(phb.history) == 0
