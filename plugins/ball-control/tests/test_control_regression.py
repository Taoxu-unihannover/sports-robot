"""ball-control plugin regression tests."""

import os
import sys
import importlib.util

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, SCRIPTS_DIR)


def load_pipeline():
    spec = importlib.util.spec_from_file_location("ball_control_pipeline", os.path.join(SCRIPTS_DIR, "pipeline.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_pipeline = load_pipeline()
BallSample = _pipeline.BallSample
ControlPipeline = _pipeline.ControlPipeline


def config_path():
    return os.path.join(os.path.dirname(__file__), "..", "assets", "config.yaml")


def test_pipeline_initializes():
    pipeline = ControlPipeline(config_path())
    assert len(pipeline.library.skills) == 2


def test_command_schema_ok():
    pipeline = ControlPipeline(config_path())
    result = pipeline.command([BallSample(0.2, [0.4, 0, 0.8], [-2, 0, 0])], [1.5, 0, 0], {"side": "right", "workspace_margin": 0.3})
    assert result["status"] in ("ok", "unsafe")
    assert {"status", "reason", "skill", "plan", "velocity"} <= set(result)


def test_no_plan_when_outside_workspace():
    pipeline = ControlPipeline(config_path())
    result = pipeline.command([BallSample(0.2, [3.0, 0, 0.8], [-2, 0, 0])], [1.5, 0, 0], {"side": "right", "workspace_margin": 0.3})
    assert result["status"] == "no_plan"
