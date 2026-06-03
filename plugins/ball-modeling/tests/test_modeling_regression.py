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
