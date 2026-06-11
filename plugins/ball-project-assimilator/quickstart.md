# Ball Project Assimilator Quickstart

> 球类机器人开源项目吸收与超越插件。支持完整四阶段流程（拆解→复现→评测→超越）和简化两阶段流程（拆解→复现）。

## 工作模式

### 模式 A：简化版（快速复现）

适用于只需要快速复现开源项目，不需要横向对比和超越的场景。

```bash
# 扫描并蒸馏项目
python plugins/ball-project-assimilator/scripts/distill.py \
  /path/to/dynamic-tennis \
  --output_dir output/

# 查看蒸馏报告
cat output/distill_report.json
```

### 模式 B：完整版（吸收+超越）

适用于需要完整吸收、复现、横向评测和超越的场景。

## 简化版工作流（模式 A）

### 1. 扫描项目

```bash
python plugins/ball-project-assimilator/scripts/distill.py \
  /path/to/dynamic-tennis \
  --output_dir output/
```

### 2. 查看技术栈覆盖

```bash
cat output/distill_report.json
```

### 3. 基于 skills 自举项目

使用以下 skills 自举新项目：

| Skill | 用途 |
|---|---|
| `mujoco-tennis-world-builder` | 生成 MuJoCo 场景 |
| `gymnasium-mujoco-env-builder` | 生成 Gymnasium 环境 |
| `sb3-rl-training-runner` | 生成训练入口 |
| `mujoco-policy-evaluator` | 生成评估脚本 |
| `truth-state-policy-input` | 生成观测构建 |
| `sim-camera-perception-input` | 生成感知模块 |

## 完整版工作流（模式 B）

### 1. 扫描项目

```bash
python plugins/ball-project-assimilator/scripts/scan_project.py \
  --project_path dynamic-tennis \
  --domain tennis \
  --output_dir docs/assimilation
```

### 2. 查看技术栈图谱

```bash
cat docs/assimilation/dynamic-tennis-stack-map.md
```

### 3. 查看 Skill 缺口

```bash
cat docs/assimilation/dynamic-tennis-skill-gap.md
```

### 4. 运行复现

根据 reproduction_plan.md 中的步骤，通过 sports-robot skills 生成复现项目。

### 5. 运行横向评测

```bash
python plugins/ball-project-assimilator/scripts/run_stack_benchmark.py \
  --stack_map docs/assimilation/dynamic-tennis-stack-map.json \
  --output_dir docs/assimilation
```

### 6. 组合最优方法

```bash
python plugins/ball-project-assimilator/scripts/compose_best_stack.py \
  --best_method docs/assimilation/best_method_per_stack.json \
  --baseline docs/assimilation/dynamic-tennis-baseline-metrics.json \
  --output_dir docs/assimilation
```

## 工作流对比

| 阶段 | 简化版 (A) | 完整版 (B) |
|---|---|---|
| 技术栈拆解 | ✅ distill.py | ✅ scan_project.py |
| 技能提取 | ✅ | ✅ |
| 项目复现 | ✅ | ✅ |
| 横向评测 | ❌ | ✅ |
| 最优组合 | ❌ | ✅ |
| 超越验证 | ❌ | ✅ |

## 四阶段工作流（完整版）

| 阶段 | 命令 | 输出 |
|---|---|---|
| 技术栈拆解 | scan_project.py | stack_map + skill_gap |
| 项目复现 | sports-robot skills | reproduction project |
| 横向评测 | run_stack_benchmark.py | benchmark_report |
| 最优组合 | compose_best_stack.py | best_stack + plus_report |
