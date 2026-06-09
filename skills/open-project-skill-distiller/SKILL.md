name: open-project-skill-distiller
description: 拆解开源球类机器人项目的技术栈，生成技术栈图谱、skill 缺口报告和标准 skill 模板。适用于用户需要分析开源项目结构、将项目能力沉淀为 sports-robot 标准 skills；不用于直接运行训练或评估。
---

# 开源项目技能蒸馏器

## 用途

扫描任意球类机器人开源项目，识别其技术栈（仿真、感知、建模、控制、执行、工程），生成技术栈图谱，匹配 sports-robot 已有 skills，输出缺口报告和新 skill 候选。

## 输入

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| source_project_path | string | 是 | 开源项目本地路径 |
| target_domain | string | 否 | 球类领域：tennis, badminton, pingpong, baseball, soccer |
| license_policy | string | 否 | 许可证策略：allow_all / gpl_only / mit_only |
| allow_asset_reuse | bool | 否 | 是否允许复用项目专有资产（mesh/权重/数据集） |
| target_skills_dir | string | 否 | 输出 skills 目录，默认 skills/ |
| target_plugins_dir | string | 否 | 输出 plugins 目录，默认 plugins/ |

## 输出

| 产物 | 路径 | 说明 |
|---|---|---|
| 技术栈图谱 | stack_map.md | 项目结构、模块、依赖、数据流、skill 映射 |
| 缺口报告 | skill_gap_report.md | 已覆盖/部分覆盖/未覆盖 skills |
| skill 模板 | {skill_name}/SKILL.md | 新 skill 候选定义 |
| 复现计划 | reproduction_plan.md | 调用哪些 skills、顺序、配置、验证命令 |

## 执行步骤

### 步骤 1：扫描项目结构

识别关键目录和文件模式：

| 文件模式 | 识别为 | 映射 skill |
|---|---|---|
| `*.xml` (MuJoCo) | 仿真场景 | mujoco-tennis-world-builder |
| `*.urdf` / `*.xacro` | 机器人模型 | mujoco-tennis-world-builder |
| `gym.Env` / `gymnasium.Env` | RL 环境 | gymnasium-mujoco-env-builder |
| `spaces.Box` / `spaces.Discrete` | 观测/动作空间 | truth-state-policy-input |
| `SAC/PPO/DDPG/TD3` | RL 训练 | sb3-rl-training-runner |
| `model.predict` / `model.load` | 策略评估 | mujoco-policy-evaluator |
| `render` / `imshow` / `matplotlib` | 可视化 | robot-trajectory-web-visualizer |
| `Camera` / `rgb_array` / `image` | 感知输入 | sim-camera-perception-input |
| `Mecanum` / `differential` / `omni` | 底盘控制 | mobile-base-executor |
| `MPC` / `QP` / `IK` | 控制器 | mpc-controller |
| `YOLO` / `detect` / `HSV` | 检测 | ball-detector |
| `Kalman` / `EKF` / `UKF` | 状态估计 | ball-state-estimator |
| `*.yaml` / `*.json` (config) | 配置 | 工程栈 |

### 步骤 2：提取技术栈图谱

对每个识别的模块生成：

```yaml
module_name:
  type: simulation | perception | modeling | control | execution | engineering
  source_files: [list]
  dependencies: [list]
  inputs: [schema]
  outputs: [schema]
  metrics: [list]
  mapped_skill: skill_name | null
  coverage: full | partial | none
  notes: string
```

### 步骤 3：匹配已有 skills

对每个模块：
- **已覆盖**：记录 skill 名称与覆盖比例
- **部分覆盖**：记录需要补充的 schema、脚本、recipe
- **未覆盖**：生成新 skill 候选

### 步骤 4：生成缺口报告

```markdown
## Skill Gap Report

### 已覆盖 (N)
| 模块 | Skill | 覆盖率 | 说明 |
|---|---|---|---|

### 部分覆盖 (N)
| 模块 | Skill | 缺失部分 | 补充方案 |
|---|---|---|---|

### 未覆盖 (N)
| 模块 | 候选 Skill 名称 | 优先级 | 说明 |
|---|---|---|---|
```

### 步骤 5：生成复现计划

记录：
- 调用哪些 skills、顺序
- 每个 skill 的配置参数
- 验证命令和指标
- 预期性能目标

## 验证方式

1. 技术栈图谱覆盖项目所有关键模块
2. 缺口报告明确标注每个模块的覆盖状态
3. 新 skill 候选有合理名称和描述
4. 复现计划可通过 sports-robot skills 执行
