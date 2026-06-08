import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from uncertainty_risk import (
    DelayModel,
    ModelSwitchController,
    NoiseModel,
    chi_square_gate,
    compute_cvar,
    hit_probability,
    mahalanobis_squared,
    propagate_linear,
    risk_score,
)


def test_propagate_linear():
    P = np.eye(3) * 0.01
    F = np.eye(3)
    Q = np.eye(3) * 0.001
    P_new = propagate_linear(P, F, Q)
    assert np.allclose(P_new, np.eye(3) * 0.011)


def test_mahalanobis_squared():
    r = np.array([1.0, 0.0, 0.0])
    S = np.eye(3)
    assert abs(mahalanobis_squared(r, S) - 1.0) < 1e-9


def test_chi_square_gate():
    r = np.array([0.1, 0.0, 0.0])
    S = np.eye(3)
    assert chi_square_gate(r, S, threshold=10.0) is True
    assert chi_square_gate(np.array([10.0, 0.0, 0.0]), S, threshold=1.0) is False


def test_risk_score():
    assert risk_score(0.0, 0.01, 0.1) == 1.0
    score = risk_score(0.3, 0.02, 0.1)
    assert 0.0 < score < 1.0


def test_delay_model_position_uncertainty():
    dm = DelayModel(mean=0.015, std=0.003)
    unc = dm.position_uncertainty(ball_speed=10.0)
    assert unc > 0
    assert abs(unc - 10.0 * 0.021) < 1e-9


def test_delay_model_covariance_contribution():
    dm = DelayModel(mean=0.015, std=0.003)
    C = dm.delay_covariance_contribution(ball_speed=10.0, direction=[1.0, 0.0, 0.0])
    assert C.shape == (3, 3)
    assert C[0, 0] > 0


def test_noise_model_sigma_at_distance():
    nm = NoiseModel(near_sigma=0.005, far_sigma=0.050, transition_distance=3.0)
    assert abs(nm.sigma_at_distance(0.0) - 0.005) < 1e-9
    assert abs(nm.sigma_at_distance(3.0) - 0.050) < 1e-9
    s_mid = nm.sigma_at_distance(1.5)
    assert 0.005 < s_mid < 0.050


def test_noise_model_observation_covariance():
    nm = NoiseModel()
    R = nm.observation_covariance(1.0)
    assert R.shape == (3, 3)
    assert np.allclose(R, R.T)


def test_compute_cvar():
    samples = list(np.random.randn(1000) + 0.1)
    cvar = compute_cvar(samples, alpha=0.05)
    assert isinstance(cvar, float)


def test_compute_cvar_empty():
    assert compute_cvar([], alpha=0.05) == 0.0


def test_hit_probability_high():
    P = np.eye(3) * 0.0001
    p = hit_probability(P, paddle_radius=0.08)
    assert p > 0.5


def test_model_switch_no_switch_when_stable():
    ctrl = ModelSwitchController(covariance_trace_threshold=0.1, residual_threshold=0.05)
    result = ctrl.evaluate(covariance_trace=0.01, residual_rms=0.01, current_time=1.0)
    assert result["current_model"] == "high_fidelity"
    assert result["switched"] is False
    assert result["risk_level"] == "low"


def test_model_switch_to_reduced():
    ctrl = ModelSwitchController(covariance_trace_threshold=0.1, residual_threshold=0.05)
    result = ctrl.evaluate(covariance_trace=0.5, residual_rms=0.1, current_time=1.0)
    assert result["current_model"] == "reduced"
    assert result["switched"] is True


def test_model_switch_back_to_high_fidelity():
    ctrl = ModelSwitchController(covariance_trace_threshold=0.1, residual_threshold=0.05)
    ctrl.evaluate(covariance_trace=0.5, residual_rms=0.1, current_time=1.0)
    result = ctrl.evaluate(covariance_trace=0.01, residual_rms=0.01, current_time=2.0)
    assert result["current_model"] == "high_fidelity"


def test_model_switch_min_interval():
    ctrl = ModelSwitchController(covariance_trace_threshold=0.1, residual_threshold=0.05, min_switch_interval=1.0)
    ctrl.evaluate(covariance_trace=0.5, residual_rms=0.1, current_time=1.0)
    result = ctrl.evaluate(covariance_trace=0.01, residual_rms=0.01, current_time=1.5)
    assert result["switched"] is False
