import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from identification import (
    DualEKF,
    ParameterBounds,
    RecursiveLeastSquares,
    batch_nls,
    fit_linear_map,
    fit_quadratic_drag_1d,
)


def test_fit_linear_map():
    x = np.array([[1, 0], [0, 1], [1, 1], [2, 1]], dtype=float)
    w_true = np.array([[2, 0], [0, -1]], dtype=float)
    y = x @ w_true
    assert np.allclose(fit_linear_map(x, y), w_true)


def test_fit_quadratic_drag_positive():
    t = np.linspace(0, 0.4, 6)
    v = 10.0 / (1.0 + 0.3 * 10.0 * t)
    assert fit_quadratic_drag_1d(t, v) > 0.0


def test_recursive_least_squares_converges():
    rls = RecursiveLeastSquares.create(2)
    for _ in range(20):
        rls.update([1.0, 2.0], 5.0)
    assert abs(np.dot([1.0, 2.0], rls.theta) - 5.0) < 1e-2


def test_dual_ekf_state_update():
    ekf = DualEKF(state_dim=2, param_dim=1)
    F = np.eye(2)
    H = np.array([1.0, 0.0])
    for _ in range(10):
        ekf.predict_state(F, np.zeros(2))
        ekf.update_state(H, 1.0)
    assert abs(ekf.x[0] - 1.0) < 0.5


def test_dual_ekf_param_update():
    ekf = DualEKF(state_dim=2, param_dim=2)
    H = np.array([1.0, 1.0])
    for _ in range(20):
        ekf.update_params(H, 3.0)
    assert abs(np.dot(H, ekf.theta) - 3.0) < 1.0


def test_dual_ekf_freeze_condition():
    ekf = DualEKF(state_dim=2, param_dim=2)
    ekf._freeze_residual_threshold = 0.1
    ekf._freeze_rate_threshold = 1e-3
    H = np.array([1.0, 0.0])
    for _ in range(200):
        ekf.update_params(H, 0.0)
    assert ekf.frozen


def test_dual_ekf_unfreeze():
    ekf = DualEKF(state_dim=2, param_dim=2)
    ekf._frozen = True
    assert ekf.frozen
    ekf.unfreeze()
    assert not ekf.frozen


def test_parameter_bounds_clamp():
    bounds = ParameterBounds(lower=np.array([0.0, 0.5]), upper=np.array([1.0, 2.0]))
    theta = np.array([-0.5, 3.0])
    clamped = bounds.clamp(theta)
    assert np.allclose(clamped, [0.0, 2.0])


def test_batch_nls_converges():
    def model(theta, x):
        return theta[0] * x + theta[1]

    x_data = [1.0, 2.0, 3.0, 4.0]
    y_data = [2.5, 4.5, 6.5, 8.5]
    result = batch_nls(model, [1.0, 0.0], x_data, y_data, max_iterations=200, step_size=0.1)
    assert result["cost"] < 1.0
    assert result["iterations"] > 0


def test_batch_nls_with_bounds():
    def model(theta, x):
        return theta[0] * x

    bounds = ParameterBounds(lower=np.array([0.0]), upper=np.array([10.0]))
    result = batch_nls(model, [0.5], [1.0, 2.0, 3.0], [2.0, 4.0, 6.0], bounds=bounds, max_iterations=100, step_size=0.1)
    assert result["parameters"][0] >= 0.0
