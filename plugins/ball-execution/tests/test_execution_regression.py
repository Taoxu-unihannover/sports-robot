"""ball-execution plugin regression tests."""

import os
import sys
import importlib.util

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, SCRIPTS_DIR)


def load_pipeline():
    spec = importlib.util.spec_from_file_location("ball_execution_pipeline", os.path.join(SCRIPTS_DIR, "pipeline.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ExecutionPipeline = load_pipeline().ExecutionPipeline


def config_path():
    return os.path.join(os.path.dirname(__file__), "..", "assets", "config.yaml")


def test_pipeline_initializes():
    pipeline = ExecutionPipeline(config_path())
    assert pipeline.launcher.speed_gain > 0


def test_execute_preview_schema():
    pipeline = ExecutionPipeline(config_path())
    result = pipeline.execute_preview([6, 0, 1], 0.5, [0, 0, 0], [1, 0])
    assert result["status"] in ("ok", "unsafe")
    assert {"launcher", "arm_profile", "base_command", "base_delta", "arm_delta"} <= set(result)
    assert len(result["arm_profile"]) > 1
