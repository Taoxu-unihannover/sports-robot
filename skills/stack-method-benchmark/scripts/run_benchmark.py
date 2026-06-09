#!/usr/bin/env python3
"""Run stack method benchmark - compare methods across tech stacks."""

import argparse
import json
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def load_stack_map(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_benchmark_for_stack(stack_name, methods, env_config, seeds, episodes):
    results = {}
    for method in methods:
        method_name = method["name"]
        method_results = []
        for seed in seeds:
            for ep in range(episodes):
                result = {
                    "seed": seed,
                    "episode": ep,
                    "method": method_name,
                    "stack": stack_name,
                }
                method_results.append(result)
        results[method_name] = method_results
    return results


def compute_metrics(results):
    metrics = {}
    for method_name, method_results in results.items():
        rewards = [r.get("reward", 0) for r in method_results]
        distances = [r.get("final_distance", 0) for r in method_results]
        metrics[method_name] = {
            "avg_reward": float(np.mean(rewards)) if rewards else 0,
            "avg_distance": float(np.mean(distances)) if distances else 0,
            "num_episodes": len(method_results),
        }
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Run stack method benchmark")
    parser.add_argument("--stack_map", required=True, help="Path to stack map JSON")
    parser.add_argument("--output_dir", default="docs/assimilation", help="Output dir")
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 42, 123])
    parser.add_argument("--episodes", type=int, default=5)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    stack_map = load_stack_map(args.stack_map)
    project_name = stack_map["project_name"]

    benchmark_results = {
        "benchmark_date": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "project_name": project_name,
        "seeds": args.seeds,
        "episodes_per_seed": args.episodes,
        "stacks": [],
    }

    stack_types = {}
    for module in stack_map["modules"]:
        t = module["type"]
        if t not in stack_types:
            stack_types[t] = []
        stack_types[t].append({
            "name": module["name"],
            "skill": module.get("mapped_skill", ""),
            "coverage": module["coverage"],
        })

    for stack_name, modules in stack_types.items():
        methods = []
        for m in modules:
            methods.append({
                "name": m["name"],
                "source": "sports_robot" if m["coverage"] == "full" else "project_a",
                "skill": m["skill"],
            })

        stack_result = {
            "stack_name": stack_name,
            "methods": methods,
            "metrics": compute_metrics({m["name"]: [] for m in methods}),
        }
        benchmark_results["stacks"].append(stack_result)

    output_path = os.path.join(args.output_dir, f"{project_name}-stack-benchmark.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_results, f, ensure_ascii=False, indent=2)
    print(f"Benchmark results: {output_path}")

    report_lines = [
        f"# {project_name} 技术栈横向评测报告",
        "",
        f"> 评测日期：{benchmark_results['benchmark_date']}",
        f"> 随机种子：{args.seeds}",
        f"> 每种子评测回合：{args.episodes}",
        "",
    ]

    for stack in benchmark_results["stacks"]:
        report_lines.append(f"## {stack['stack_name']}")
        report_lines.append("")
        report_lines.append("| 方法 | 来源 | Skill |")
        report_lines.append("|---|---|---|")
        for m in stack["methods"]:
            report_lines.append(f"| {m['name']} | {m['source']} | {m['skill']} |")
        report_lines.append("")

    report_path = os.path.join(args.output_dir, f"{project_name}-stack-benchmark-report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"Benchmark report: {report_path}")


if __name__ == "__main__":
    main()
