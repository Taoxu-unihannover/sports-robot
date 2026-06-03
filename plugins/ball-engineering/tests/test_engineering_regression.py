"""ball-engineering plugin regression tests."""

import os
import sys
import importlib.util

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, SCRIPTS_DIR)


def load_pipeline():
    spec = importlib.util.spec_from_file_location("ball_engineering_pipeline", os.path.join(SCRIPTS_DIR, "pipeline.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EngineeringPipeline = load_pipeline().EngineeringPipeline


def config_path():
    return os.path.join(os.path.dirname(__file__), "..", "assets", "config.yaml")


def test_pipeline_validate_schema():
    result = EngineeringPipeline(config_path()).validate("1.0.0")
    assert result["status"] in ("ok", "warning")
    assert {"latency_ms", "qos", "node_state", "power_w", "checksum", "latency_stats"} <= set(result)
    assert result["node_state"] == "active"
    assert result["power_w"] > 0


def test_runtime_incompatibility_warns():
    result = EngineeringPipeline(config_path()).validate("2.0.0")
    assert result["status"] == "warning"
