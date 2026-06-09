---
name: ball-project-distiller
description: 从已有球类机器人项目（如 dynamic-tennis）中提取可复用的技能模式，生成标准 skill 模板和配置。适用于用户需要将现有项目代码沉淀为可复用技能、为新项目自举提供技能基础；不用于直接运行训练或评估。
---

# 球类项目技能蒸馏器

## 用途

从已有球类机器人项目中分析代码结构、提取可复用模式，生成标准 skill 定义和配置文件。支持自动识别 MuJoCo 场景、Gymnasium 环境、训练脚本、评估脚本等组件，将其抽象为可复用的 skill 模板。

## 输入

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| project_dir | string | 是 | 源项目根目录 |
| project_type | string | 否 | 项目类型：dynamic-tennis, dynamic-badminton 等 |
| output_dir | string | 否 | 输出目录，默认 skills/ |

## 输出

| 产物 | 路径 | 说明 |
|---|---|---|
| 技能分析报告 | distill_report.json | 提取的技能清单和映射 |
| SKILL.md 模板 | {skill_name}/SKILL.md | 生成的技能定义 |
| 参考代码 | {skill_name}/references/ | 提取的参考实现 |

## 执行步骤

### 步骤 1：扫描项目结构

识别关键目录和文件：
- MuJoCo XML 文件 → mujoco-tennis-world-builder
- Gymnasium 环境类 → gymnasium-mujoco-env-builder
- 训练脚本 → sb3-rl-training-runner
- 评估脚本 → mujoco-policy-evaluator
- 可视化代码 → robot-trajectory-web-visualizer
- 观测构造 → truth-state-policy-input
- 相机/感知 → sim-camera-perception-input

### 步骤 2：提取模式

从源代码中提取：
- 观测空间定义和归一化模式
- 动作空间定义和逆运动学模式
- 奖励函数组件和权重
- 终止条件逻辑
- MuJoCo 模型结构
- 训练超参数

### 步骤 3：生成技能模板

将提取的模式写入标准 SKILL.md 格式，包含：
- 输入/输出定义
- 执行步骤
- 代码模板
- 验证方式

### 步骤 4：生成参考实现

将源代码关键片段复制到 references/ 目录，标注来源和用途。

## 验证方式

1. 蒸馏报告包含所有识别的技能
2. SKILL.md 格式符合标准
3. 参考代码可追溯至源项目
