#!/usr/bin/env python3
"""Scan an open-source ball robot project and output a tech stack map."""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime


SKILL_PATTERNS = {
    "simulation": {
        "mujoco-tennis-world-builder": [
            r"\.xml$", r"\.urdf$", r"\.xacro$", r"mujoco",
        ],
        "mujoco-policy-evaluator": [
            r"evaluate", r"test_.*navigation", r"policy.*eval",
        ],
    },
    "perception": {
        "sim-camera-perception-input": [
            r"camera", r"rgb_array", r"render.*image", r"vision",
        ],
        "truth-state-policy-input": [
            r"_get_obs", r"observation_space", r"spaces\.Box",
        ],
        "ball-detector": [
            r"yolo", r"detect", r"hsv", r"contour",
        ],
        "ball-state-estimator": [
            r"kalman", r"ekf", r"ukf", r"filter",
        ],
        "ball-tracker": [
            r"track", r"trajectory.*smooth",
        ],
    },
    "modeling": {
        "ball-flight-model": [
            r"flight", r"aero", r"drag", r"magnus",
        ],
        "ball-impact-contact": [
            r"impact", r"contact", r"bounce", r"rebound",
        ],
        "ball-kinematic-model": [
            r"kinematic", r"forward_kinematics",
        ],
    },
    "control": {
        "mpc-controller": [
            r"mpc", r"model_predictive",
        ],
        "skill-policy-controller": [
            r"skill.*policy", r"hierarchical",
        ],
        "control-safety-supervisor": [
            r"safety", r"boundary.*check",
        ],
    },
    "execution": {
        "mobile-base-executor": [
            r"mecanum", r"differential", r"omni.*wheel",
        ],
        "high-speed-manipulator": [
            r"manipulator", r"arm.*control",
        ],
    },
    "training": {
        "sb3-rl-training-runner": [
            r"SAC\(", r"PPO\(", r"DDPG\(", r"TD3\(",
            r"stable_baselines3", r"learn\(",
        ],
    },
    "engineering": {
        "robot-trajectory-web-visualizer": [
            r"visuali", r"matplotlib", r"plot.*trajectory",
        ],
    },
}


def scan_directory(project_path):
    """Scan project directory and collect file info."""
    files = []
    for root, dirs, filenames in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in {
            '__pycache__', '.git', 'node_modules', '.mypy_cache',
            'saved_models', 'runs', 'evaluation_results', 'web_viz_data',
        }]
        for f in filenames:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, project_path)
            files.append(rel_path)
    return files


def read_file_content(project_path, rel_path, max_chars=5000):
    """Read file content for pattern matching."""
    full_path = os.path.join(project_path, rel_path)
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read(max_chars)
    except Exception:
        return ""


def identify_modules(project_path, files):
    """Identify tech stack modules from project files."""
    modules = []
    file_contents_cache = {}

    for stack_type, skills in SKILL_PATTERNS.items():
        for skill_name, patterns in skills.items():
            matched_files = []
            for rel_path in files:
                if rel_path not in file_contents_cache:
                    file_contents_cache[rel_path] = read_file_content(
                        project_path, rel_path
                    )
                content = file_contents_cache[rel_path]
                for pattern in patterns:
                    if re.search(pattern, rel_path, re.IGNORECASE) or \
                       re.search(pattern, content, re.IGNORECASE):
                        matched_files.append(rel_path)
                        break
            if matched_files:
                modules.append({
                    "name": skill_name,
                    "type": stack_type,
                    "source_files": sorted(set(matched_files)),
                    "coverage": "full",
                    "mapped_skill": skill_name,
                })

    return modules


def match_skills(modules, existing_skills):
    """Match identified modules to existing sports-robot skills."""
    for module in modules:
        skill_name = module["mapped_skill"]
        if skill_name in existing_skills:
            module["coverage"] = "full"
        else:
            module["coverage"] = "none"
            module["gap_description"] = f"Skill {skill_name} not found in sports-robot"
    return modules


def get_existing_skills(skills_dir):
    """Get list of existing sports-robot skills."""
    skills = set()
    if os.path.isdir(skills_dir):
        for name in os.listdir(skills_dir):
            skill_path = os.path.join(skills_dir, name, "SKILL.md")
            if os.path.isfile(skill_path):
                skills.add(name)
    return skills


def build_stack_map(project_path, project_name, project_url, domain):
    """Build complete stack map for a project."""
    files = scan_directory(project_path)
    project_root = Path(project_path).parent.parent
    skills_dir = os.path.join(str(project_root), "skills")
    existing_skills = get_existing_skills(skills_dir)

    modules = identify_modules(project_path, files)
    modules = match_skills(modules, existing_skills)

    covered = [m for m in modules if m["coverage"] == "full"]
    partial = [m for m in modules if m["coverage"] == "partial"]
    uncovered = [m for m in modules if m["coverage"] == "none"]

    stack_map = {
        "project_name": project_name,
        "project_path": project_path,
        "project_url": project_url,
        "scan_date": datetime.now().isoformat(),
        "project_type": domain,
        "language": "python",
        "dependencies": {},
        "modules": modules,
        "summary": {
            "total_modules": len(modules),
            "covered_count": len(covered),
            "partial_count": len(partial),
            "uncovered_count": len(uncovered),
        }
    }

    return stack_map


def render_markdown(stack_map):
    """Render stack map as markdown."""
    lines = [
        f"# {stack_map['project_name']} 技术栈图谱",
        "",
        f"> 扫描日期：{stack_map['scan_date']}",
        f"> 项目类型：{stack_map['project_type']}",
        f"> 项目路径：{stack_map['project_path']}",
        f"> 项目仓库：{stack_map.get('project_url', 'N/A')}",
        "",
        "## 模块总览",
        "",
        f"| 类型 | 模块数 | 已覆盖 | 部分覆盖 | 未覆盖 |",
        f"|---|---|---|---|---|",
    ]

    type_counts = {}
    for m in stack_map["modules"]:
        t = m["type"]
        if t not in type_counts:
            type_counts[t] = {"total": 0, "full": 0, "partial": 0, "none": 0}
        type_counts[t]["total"] += 1
        type_counts[t][m["coverage"]] += 1

    for t in ["simulation", "perception", "modeling", "control", "execution", "training", "engineering"]:
        if t in type_counts:
            c = type_counts[t]
            lines.append(f"| {t} | {c['total']} | {c['full']} | {c['partial']} | {c['none']} |")

    lines.extend([
        "",
        "## 模块详情",
        "",
    ])

    for m in stack_map["modules"]:
        lines.append(f"### {m['name']} ({m['type']})")
        lines.append("")
        lines.append(f"- **覆盖状态**: {m['coverage']}")
        lines.append(f"- **映射 Skill**: {m.get('mapped_skill', 'N/A')}")
        if m.get("gap_description"):
            lines.append(f"- **缺口说明**: {m['gap_description']}")
        lines.append(f"- **源文件**: {len(m['source_files'])} 个")
        for f in m['source_files'][:10]:
            lines.append(f"  - `{f}`")
        if len(m['source_files']) > 10:
            lines.append(f"  - ... 及其他 {len(m['source_files']) - 10} 个")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Scan ball robot project")
    parser.add_argument("--project_path", required=True, help="Project path")
    parser.add_argument("--project_name", default=None, help="Project name")
    parser.add_argument("--project_url", default="", help="Project repo URL")
    parser.add_argument("--domain", default="tennis", help="Ball domain")
    parser.add_argument("--output_dir", default="docs/assimilation", help="Output dir")
    args = parser.parse_args()

    project_name = args.project_name or os.path.basename(args.project_path)
    stack_map = build_stack_map(args.project_path, project_name, args.project_url, args.domain)

    os.makedirs(args.output_dir, exist_ok=True)

    json_path = os.path.join(args.output_dir, f"{project_name}-stack-map.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(stack_map, f, ensure_ascii=False, indent=2)
    print(f"Stack map JSON: {json_path}")

    md_path = os.path.join(args.output_dir, f"{project_name}-stack-map.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(render_markdown(stack_map))
    print(f"Stack map MD: {md_path}")

    summary = stack_map["summary"]
    print(f"\nSummary: {summary['total_modules']} modules, "
          f"{summary['covered_count']} covered, "
          f"{summary['partial_count']} partial, "
          f"{summary['uncovered_count']} uncovered")


if __name__ == "__main__":
    main()
