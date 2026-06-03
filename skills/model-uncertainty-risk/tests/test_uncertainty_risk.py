import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from uncertainty_risk import chi_square_gate, mahalanobis_squared, propagate_linear, risk_score


def test_linear_propagation_adds_process_noise():
    p = propagate_linear(np.eye(2), np.eye(2), np.eye(2) * 0.1)
    assert np.allclose(p, np.eye(2) * 1.1)


def test_chi_square_gate():
    assert chi_square_gate([0.1, 0.0], np.eye(2), threshold=1.0)
    assert not chi_square_gate([2.0, 0.0], np.eye(2), threshold=1.0)


def test_risk_increases_when_time_is_short():
    assert risk_score(0.05, 0.01, 1.0) > risk_score(1.0, 0.01, 1.0)

