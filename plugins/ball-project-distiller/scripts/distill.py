import os
import json
import re
import yaml


SKILL_PATTERNS = {
    "mujoco-tennis-world-builder": {
        "file_patterns": [".xml"],
        "dir_patterns": ["mujoco", "robots", "description", "assets"],
        "key_names": ["world", "scene", "robot", "actuator"],
    },
    "gymnasium-mujoco-env-builder": {
        "file_patterns": ["_env.py", "environment.py"],
        "dir_patterns": ["envs", "environments"],
        "key_names": ["gym", "MujocoEnv", "observation_space", "action_space"],
    },
    "sb3-rl-training-runner": {
        "file_patterns": ["train", "training"],
        "dir_patterns": ["scripts", "training"],
        "key_names": ["SAC", "PPO", "DDPG", "TD3", "learn", "total_timesteps"],
    },
    "mujoco-policy-evaluator": {
        "file_patterns": ["test", "eval", "evaluate"],
        "dir_patterns": ["scripts", "evaluation"],
        "key_names": ["predict", "episode", "success_rate"],
    },
    "robot-trajectory-web-visualizer": {
        "file_patterns": ["visual", "viz", "plot"],
        "dir_patterns": ["visualization", "web"],
        "key_names": ["trajectory", "canvas", "html"],
    },
    "truth-state-policy-input": {
        "file_patterns": ["observation", "obs"],
        "dir_patterns": ["envs"],
        "key_names": ["_get_obs", "normalize", "qpos", "qvel"],
    },
    "sim-camera-perception-input": {
        "file_patterns": ["camera", "perception", "vision"],
        "dir_patterns": ["perception", "vision"],
        "key_names": ["render", "detect", "image"],
    },
}


def scan_project(project_dir):
    findings = {skill: {"files": [], "dirs": [], "matches": []} for skill in SKILL_PATTERNS}

    for root, dirs, files in os.walk(project_dir):
        rel_root = os.path.relpath(root, project_dir)

        for f in files:
            filepath = os.path.join(root, f)
            rel_path = os.path.join(rel_root, f)

            for skill_name, patterns in SKILL_PATTERNS.items():
                for fp in patterns["file_patterns"]:
                    if fp.lower() in f.lower():
                        findings[skill_name]["files"].append(rel_path)
                        break

                for dp in patterns["dir_patterns"]:
                    if dp.lower() in rel_root.lower():
                        findings[skill_name]["dirs"].append(rel_root)
                        break

                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read()
                        for kn in patterns["key_names"]:
                            if kn in content:
                                if rel_path not in findings[skill_name]["matches"]:
                                    findings[skill_name]["matches"].append(rel_path)
                                break
                except Exception:
                    pass

    return findings


def generate_distill_report(findings, project_dir, output_dir):
    report = {
        "source_project": project_dir,
        "skills": {},
    }

    for skill_name, data in findings.items():
        relevance_score = len(data["files"]) + len(data["dirs"]) + len(data["matches"])
        report["skills"][skill_name] = {
            "relevance_score": relevance_score,
            "matched_files": data["files"],
            "matched_dirs": list(set(data["dirs"])),
            "key_name_matches": data["matches"],
            "recommended": relevance_score >= 2,
        }

    report_path = os.path.join(output_dir, "distill_report.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report, report_path


def distill_project(project_dir, output_dir=None, project_type=None):
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")

    print(f"Scanning project: {project_dir}")
    findings = scan_project(project_dir)

    report, report_path = generate_distill_report(findings, project_dir, output_dir)
    print(f"Distill report saved to: {report_path}")

    recommended = [s for s, d in report["skills"].items() if d["recommended"]]
    print(f"\nRecommended skills to extract: {recommended}")

    for skill_name in recommended:
        skill_dir = os.path.join(output_dir, skill_name, "references")
        os.makedirs(skill_dir, exist_ok=True)
        for src_file in report["skills"][skill_name]["key_name_matches"]:
            src_path = os.path.join(project_dir, src_file)
            if os.path.exists(src_path):
                dst_path = os.path.join(skill_dir, os.path.basename(src_file))
                try:
                    with open(src_path, "r", encoding="utf-8", errors="ignore") as sf:
                        content = sf.read()
                    with open(dst_path, "w", encoding="utf-8") as df:
                        df.write(f"# Source: {src_file}\n# Project: {project_dir}\n\n")
                        df.write(content)
                except Exception as e:
                    print(f"Warning: Could not copy {src_file}: {e}")

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir", type=str)
    parser.add_argument("--output_dir", type=str, default=None)
    args = parser.parse_args()
    distill_project(args.project_dir, args.output_dir)
