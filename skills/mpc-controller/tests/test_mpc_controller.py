import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from mpc_controller import LinearMPCTracker, double_integrator, finite_horizon_lqr


def test_lqr_returns_horizon_gains():
    A, B = double_integrator(0.01)
    gains = finite_horizon_lqr(A, B, np.eye(2), np.eye(1) * 0.1, 5)
    assert len(gains) == 5
    assert gains[0].shape == (1, 2)


def test_tracker_drives_toward_reference():
    A, B = double_integrator(0.1)
    tracker = LinearMPCTracker(A, B, np.diag([10, 1]), np.eye(1), 10, u_limit=5)
    u = tracker.control([1, 0], [0, 0])
    assert u[0] < 0

