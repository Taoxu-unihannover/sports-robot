"""
球类项目技能蒸馏脚本

从已有球类机器人项目中分析代码结构、提取可复用模式，生成标准 skill 模板和配置。
支持自动识别 MuJoCo 场景、Gymnasium 环境、训练脚本、评估脚本等组件，将其抽象为可复用的 skill 模板。

Usage:
    python distill.py <project_dir> [--output_dir OUTPUT_DIR]
"""

import os
import json
import argparse
from typing import Dict, List, Tuple

# Skill 模式定义：匹配项目中的文件和目录
SKILL_PATTERNS = {
    "mujoco-tennis-world-builder": {
        "file_patterns": [".xml"],
        "dir_patterns": ["mujoco", "robots", "description", "assets"],
        "key_names": ["world", "scene", "robot", "actuator"],
        "description": "MuJoCo 仿真世界构建，用于生成网球/乒乓球机器人的仿真场景",
    },
    "gymnasium-mujoco-env-builder": {
        "file_patterns": ["_env.py", "environment.py"],
        "dir_patterns": ["envs", "environments"],
        "key_names": ["gym", "MujocoEnv", "observation_space", "action_space"],
        "description": "Gymnasium 环境封装，用于将 MuJoCo 仿真封装为标准 Gymnasium 环境",
    },
    "sb3-rl-training-runner": {
        "file_patterns": ["train", "training"],
        "dir_patterns": ["scripts", "training"],
        "key_names": ["SAC", "PPO", "DDPG", "TD3", "learn", "total_timesteps"],
        "description": "Stable-Baselines3 训练入口，用于强化学习策略训练",
    },
    "mujoco-policy-evaluator": {
        "file_patterns": ["test", "eval", "evaluate"],
        "dir_patterns": ["scripts", "evaluation"],
        "key_names": ["predict", "episode", "success_rate"],
        "description": "策略评估器，用于加载训练好的模型并评估性能",
    },
    "robot-trajectory-web-visualizer": {
        "file_patterns": ["visual", "viz", "plot"],
        "dir_patterns": ["visualization", "web"],
        "key_names": ["trajectory", "canvas", "html"],
        "description": "轨迹可视化器，用于生成 Web 可视化的轨迹数据",
    },
    "truth-state-policy-input": {
        "file_patterns": ["observation", "obs"],
        "dir_patterns": ["envs"],
        "key_names": ["_get_obs", "normalize", "qpos", "qvel"],
        "description": "真值状态观测，用于从仿真直接获取状态信息作为策略输入",
    },
    "sim-camera-perception-input": {
        "file_patterns": ["camera", "perception", "vision"],
        "dir_patterns": ["perception", "vision"],
        "key_names": ["render", "detect", "image"],
        "description": "仿真相机感知，用于从 MuJoCo 渲染图像模拟真实相机感知",
    },
}


def scan_project(project_dir: str) -> Dict[str, Dict]:
    """
    扫描项目目录，识别与各 skill 相关的文件和目录。

    Args:
        project_dir: 项目根目录

    Returns:
        findings: 每个 skill 的匹配结果
    """
    findings = {skill: {"files": [], "dirs": [], "matches": []} for skill in SKILL_PATTERNS}

    for root, dirs, files in os.walk(project_dir):
        # 跳过隐藏目录和常见不需要扫描的目录
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', '.git']]

        rel_root = os.path.relpath(root, project_dir)

        for f in files:
            filepath = os.path.join(root, f)
            rel_path = os.path.join(rel_root, f)

            for skill_name, patterns in SKILL_PATTERNS.items():
                # 检查文件扩展名
                for fp in patterns["file_patterns"]:
                    if fp.lower() in f.lower():
                        if rel_path not in findings[skill_name]["files"]:
                            findings[skill_name]["files"].append(rel_path)
                        break

                # 检查目录名
                for dp in patterns["dir_patterns"]:
                    if dp.lower() in rel_root.lower():
                        if rel_root not in findings[skill_name]["dirs"]:
                            findings[skill_name]["dirs"].append(rel_root)
                        break

                # 检查文件内容中的关键字
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


def generate_distill_report(findings: Dict, project_dir: str, output_dir: str) -> Tuple[Dict, str]:
    """
    生成技能蒸馏报告。

    Args:
        findings: 扫描结果
        project_dir: 项目目录
        output_dir: 输出目录

    Returns:
        report: 报告数据
        report_path: 报告文件路径
    """
    report = {
        "source_project": project_dir,
        "scan_timestamp": None,  # 可以在调用处添加
        "skills": {},
    }

    for skill_name, data in findings.items():
        # 计算相关性得分
        relevance_score = len(data["files"]) + len(data["dirs"]) + len(data["matches"])

        # 生成技能详情
        report["skills"][skill_name] = {
            "relevance_score": relevance_score,
            "matched_files": data["files"],
            "matched_dirs": list(set(data["dirs"])),
            "key_name_matches": data["matches"],
            "recommended": relevance_score >= 2,
            "description": SKILL_PATTERNS[skill_name]["description"],
        }

    # 保存报告
    report_path = os.path.join(output_dir, "distill_report.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report, report_path


def extract_references(report: Dict, project_dir: str, output_dir: str) -> List[str]:
    """
    从源项目提取参考代码到 output_dir/references/ 目录。

    Args:
        report: 蒸馏报告
        project_dir: 项目目录
        output_dir: 输出目录

    Returns:
        extracted_files: 提取的文件列表
    """
    references_dir = os.path.join(output_dir, "references")
    os.makedirs(references_dir, exist_ok=True)

    extracted_files = []

    for skill_name, data in report["skills"].items():
        if not data["recommended"]:
            continue

        skill_ref_dir = os.path.join(references_dir, skill_name)
        os.makedirs(skill_ref_dir, exist_ok=True)

        for src_file in data["key_name_matches"]:
            src_path = os.path.join(project_dir, src_file)
            if os.path.exists(src_path) and os.path.isfile(src_path):
                dst_path = os.path.join(skill_ref_dir, os.path.basename(src_file))
                try:
                    with open(src_path, "r", encoding="utf-8", errors="ignore") as sf:
                        content = sf.read()
                    with open(dst_path, "w", encoding="utf-8") as df:
                        df.write(f"# Source: {src_file}\n")
                        df.write(f"# Project: {project_dir}\n")
                        df.write(f"# Skill: {skill_name}\n\n")
                        df.write(content)
                    extracted_files.append(dst_path)
                except Exception as e:
                    print(f"Warning: Could not copy {src_file}: {e}")

    return extracted_files


def distill_project(project_dir: str, output_dir: str = None, project_type: str = None) -> Dict:
    """
    执行完整的项目蒸馏流程。

    Args:
        project_dir: 源项目目录
        output_dir: 输出目录，默认在项目根目录下创建 distiller_output/
        project_type: 项目类型（可选）

    Returns:
        report: 蒸馏报告
    """
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(project_dir), f"{os.path.basename(project_dir)}_distilled")

    print(f"=" * 60)
    print(f"球类项目技能蒸馏器")
    print(f"=" * 60)
    print(f"扫描项目: {project_dir}")
    print(f"输出目录: {output_dir}")

    # 扫描项目
    print(f"\n[1/3] 扫描项目结构...")
    findings = scan_project(project_dir)

    # 生成报告
    print(f"[2/3] 生成蒸馏报告...")
    report, report_path = generate_distill_report(findings, project_dir, output_dir)
    print(f"蒸馏报告已保存: {report_path}")

    # 提取参考代码
    print(f"[3/3] 提取参考代码...")
    extracted_files = extract_references(report, project_dir, output_dir)
    print(f"已提取 {len(extracted_files)} 个参考文件")

    # 打印推荐技能
    print(f"\n推荐提取的技能:")
    recommended = [s for s, d in report["skills"].items() if d["recommended"]]
    if recommended:
        for skill in recommended:
            data = report["skills"][skill]
            print(f"  - {skill} (得分: {data['relevance_score']})")
            print(f"    {data['description']}")
    else:
        print("  (未找到相关性足够高的技能)")

    # 打印完整技能覆盖
    print(f"\n技能覆盖情况:")
    for skill, data in report["skills"].items():
        status = "✅" if data["recommended"] else "⚪"
        print(f"  {status} {skill}: 文件={len(data['files'])}, 目录={len(data['dirs'])}, 匹配={len(data['matches'])}")

    print(f"\n{'=' * 60}")
    print(f"蒸馏完成!")
    print(f"=" * 60)

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="球类项目技能蒸馏器 - 从开源项目提取可复用的技能模式"
    )
    parser.add_argument(
        "project_dir",
        type=str,
        help="源项目根目录路径"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="输出目录，默认在项目根目录下创建 distiller_output/"
    )
    parser.add_argument(
        "--project_type",
        type=str,
        default=None,
        help="项目类型：tennis, badminton, tabletennis 等（可选）"
    )

    args = parser.parse_args()

    if not os.path.isdir(args.project_dir):
        print(f"错误: 目录不存在或不是有效目录: {args.project_dir}")
        exit(1)

    report = distill_project(args.project_dir, args.output_dir, args.project_type)