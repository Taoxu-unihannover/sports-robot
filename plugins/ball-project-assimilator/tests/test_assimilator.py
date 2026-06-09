import pytest
import os
import json
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def test_scan_project_script_exists():
    script_path = os.path.join(
        PROJECT_ROOT, "plugins", "ball-project-assimilator", "scripts", "scan_project.py"
    )
    assert os.path.isfile(script_path)


def test_plugin_json_valid():
    import json
    plugin_path = os.path.join(
        PROJECT_ROOT, "plugins", "ball-project-assimilator", "plugin.json"
    )
    with open(plugin_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["name"] == "ball-project-assimilator"
    assert "open-project-skill-distiller" in data["skills"]
    assert "stack-method-benchmark" in data["skills"]
    assert "best-stack-composer" in data["skills"]


def test_schemas_exist():
    schema_dir = os.path.join(
        PROJECT_ROOT, "plugins", "ball-project-assimilator", "assets"
    )
    expected = [
        "stack_map.schema.yaml",
        "skill_gap.schema.yaml",
        "benchmark.schema.yaml",
        "best_stack.schema.yaml",
        "performance_report.schema.yaml",
    ]
    for name in expected:
        assert os.path.isfile(os.path.join(schema_dir, name)), f"Missing schema: {name}"


def test_skills_exist():
    skills_dir = os.path.join(PROJECT_ROOT, "skills")
    expected = [
        "open-project-skill-distiller",
        "stack-method-benchmark",
        "best-stack-composer",
    ]
    for name in expected:
        skill_path = os.path.join(skills_dir, name, "SKILL.md")
        assert os.path.isfile(skill_path), f"Missing skill: {name}"


def test_agents_exist():
    agents_dir = os.path.join(
        PROJECT_ROOT, "plugins", "ball-project-assimilator", "agents"
    )
    expected = [
        "assimilation-architect.md",
        "assimilation-developer.md",
        "assimilation-reviewer.md",
    ]
    for name in expected:
        assert os.path.isfile(os.path.join(agents_dir, name)), f"Missing agent: {name}"
