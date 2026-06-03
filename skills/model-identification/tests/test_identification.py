import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from identification import RecursiveLeastSquares, fit_linear_map, fit_quadratic_drag_1d


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

