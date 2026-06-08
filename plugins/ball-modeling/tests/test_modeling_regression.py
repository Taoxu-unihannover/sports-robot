"""ball-modeling plugin regression tests."""

import os
import sys
import importlib.util

import numpy as np

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, SCRIPTS_DIR)


def load_pipeline():
    spec = importlib.util.spec_from_file_location("ball_modeling_pipeline", os.path.join(SCRIPTS_DIR, "pipeline.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ModelingPipeline = load_pipeline().ModelingPipeline


def config_path():
    return os.path.join(os.path.dirname(__file__), "..", "assets", "config.yaml")


def test_pipeline_initializes():
    pipeline = ModelingPipeline(config_path())
    assert pipeline.arm.dof == 3


def test_predict_hit_schema():
    pipeline = ModelingPipeline(config_path())
    result = pipeline.predict_hit([0.1, -0.2, 0.3], [0, 0, 1], [5, 0, 0], [1, 0, 0], [-1, 0, 0])
    assert {"contact_pose", "outgoing_velocity", "states", "risk"} <= set(result)
    assert len(result["states"]) == 51
    assert np.linalg.norm(result["outgoing_velocity"]) > 0
    assert 0.0 <= result["risk"] <= 1.0


def test_predict_with_bounces():
    pipeline = ModelingPipeline(config_path())
    result = pipeline.predict_with_bounces(
        {"position": [0, 0, 1.0], "velocity": [2, 0, 0]},
        dt=0.001, duration=0.5, table_height=0.0, restitution=0.9,
    )
    assert len(result["trajectory"]) > 0


def test_align_observation():
    pipeline = ModelingPipeline(config_path())
    result = pipeline.align_observation([1.0, 0.5, 0.3], 0.500)
    assert "position_world" in result
    assert "true_timestamp" in result


def test_evaluate_model_switch():
    pipeline = ModelingPipeline(config_path())
    result = pipeline.evaluate_model_switch(0.01, 0.01, 1.0)
    assert "current_model" in result
    assert "risk_level" in result


def test_surface_bounce():
    pipeline = ModelingPipeline(config_path())
    v_after = pipeline.surface_bounce([1, 0, -5], [0, 0, 1], contact_type="table")
    assert v_after[2] > 0


def test_compute_inverse_dynamics():
    pipeline = ModelingPipeline(config_path())
    tau = pipeline.compute_inverse_dynamics([0.1, -0.2, 0.3], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0])
    assert tau.shape == (3,)
