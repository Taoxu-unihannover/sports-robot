"""
ball-filter 单元测试

运行：python -m pytest tests/test_filter.py -v --tb=short
"""

import sys
import os
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from filter import BallKalmanFilter, ExtendedBallKalmanFilter, BallState


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
