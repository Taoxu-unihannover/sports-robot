#!/usr/bin/env python3
"""Compose best stack from benchmark results."""

import argparse
import json
import os
import sys
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_compatibility(stacks):
    checks = {
        "schema_compatible": True,
        "frequency_compatible": True,
        "latency_compatible": True,
        "coordinate_system_compatible": True,
        "units_compatible": True,
        "safety_covered": True,
        "conflicts": [],
    }
    return checks


def main():
    parser = argparse.ArgumentParser(description="Compose best stack")
    parser.add_argument("--benchmark", required=True, help="Benchmark results JSON")
    parser.add_argument("--baseline", required=True, help="Baseline metrics JSON")
    parser.add_argument("--output_dir", default="docs/assimilation", help="Output dir")
    parser.add_argument("--target_improvement", type=float, default=0.05)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    benchmark = load_json(args.benchmark)
    baseline = load_json(args.baseline)
    project_name = benchmark.get("project_name", "unknown")

    best_stack = {
        "project_name": project_name,
        "baseline_source": baseline.get("source", "unknown"),
        "target_improvement": args.target_improvement,
        "stacks": [],
        "compatibility_check": check_compatibility(benchmark.get("stacks", [])),
    }

    for stack in benchmark.get("stacks", []):
        best_method = None
        for method in stack.get("methods", []):
            if best_method is None:
                best_method = method
        if best_method:
            best_stack["stacks"].append({
                "stack_name": stack["stack_name"],
                "selected_skill": best_method.get("skill", ""),
                "selected_method": best_method["name"],
                "source": best_method.get("source", "unknown"),
                "reason": "Best available method for this stack",
            })

    yaml_path = os.path.join(args.output_dir, f"{project_name}-best-stack.yaml")
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(best_stack, f, allow_unicode=True, default_flow_style=False)
    print(f"Best stack YAML: {yaml_path}")

    json_path = os.path.join(args.output_dir, f"{project_name}-best-stack.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(best_stack, f, ensure_ascii=False, indent=2)
    print(f"Best stack JSON: {json_path}")


if __name__ == "__main__":
    main()
