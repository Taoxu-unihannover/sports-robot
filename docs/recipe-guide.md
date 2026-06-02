# Recipes：从推理到构建的完整方案

## 核心概念

Skill 定义"**能做什么**"（推理能力），Recipe 定义"**怎么做到**"（从数据到训练到部署的完整构建方案）。一个 Skill 可以有多种 Recipe，每种 Recipe 代表一种经过验证的具体做法。

```
Skill (推理能力)                    Recipe (构建方案)
┌─────────────────┐               ┌──────────────────────────┐
│ ball-detector   │               │ eth-shuttle-detection    │
│ scripts/        │  ← 产出权重 ←  │   autogen_labels.py      │
│ detector.py     │               │   convert_labels.py      │
│                 │               │   train.py               │
│ detect(image)   │  ← 加载权重 ←  │   eval.py               │
│ → (x, y, conf)  │               │   predict.py             │
└─────────────────┘               └──────────────────────────┘
                                  ┌──────────────────────────┐
                                  │ hsv-quickstart           │
                                  │   detect_hsv.py          │
                                  │   (无需训练，即开即用)      │
                                  └──────────────────────────┘
```

## Skill Recipe 与 Plugin Recipe

**Skill Recipe**（单模块方案）解决：**单个模块**怎么从数据到部署（如"怎么训练一个羽毛球检测器"）。

**Plugin Recipe**（系统级方案）解决：**整个系统**怎么把各模块的 Recipe 组合起来（如"怎么用 ETH 方案搭完整感知系统"）。

```
┌──────────────────────────────────────────────────────┐
│  Plugin Recipe: eth-badminton-perception              │
│  "用 ETH 方案搭建完整羽毛球感知系统"                     │
│                                                       │
│  引用各 Skill 的 Recipe：                               │
│    → ball-detector/recipes/eth-shuttle-detection      │
│    → ball-tracker (默认方案)                            │
│    → ball-state-estimator (默认方案)                    │
│    → ball-geometry (默认方案)                           │
│                                                       │
│  额外提供：Docker 编排、端到端评测、系统集成配置           │
└──────────────────────┬───────────────────────────────┘
                       │ 引用
           ┌───────────┼───────────┬──────────────┐
           ▼           ▼           ▼              ▼
     ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
     │Detector  │ │Tracker   │ │Filter    │ │Geometry  │
     │Recipe    │ │(默认)    │ │(默认)    │ │(默认)    │
     └──────────┘ └──────────┘ └──────────┘ └──────────┘
```

## 当前可用 Recipe

| Recipe | 层级 | 适用球类 | 需要训练 | 性能基准 |
|--------|------|---------|---------|---------|
| [eth-shuttle-detection](../skills/ball-detector/recipes/eth-shuttle-detection/RECIPE.md) | Skill | 羽毛球 | 是 | F1=0.86（相似场景）/ 0.70（未知场景） |
| [hsv-quickstart](../skills/ball-detector/recipes/hsv-quickstart/RECIPE.md) | Skill | 乒乓球/网球 | 否 | < 2ms 延迟，依赖颜色标定 |
| [eth-badminton-perception](../plugins/ball-perception/recipes/eth-badminton-perception/RECIPE.md) | Plugin | 羽毛球 | 是 | 端到端 < 20ms |

## Recipe 与 Agent 的协作

Recipe 不是替代 Agent，而是为 Agent 提供具体的实现指南：

| Agent 工作流步骤 | Recipe 的作用 |
|-----------------|-------------|
| Step 1: Architect 方案设计 | 查阅各 Skill 的 Recipe 索引，决定用哪个方案 |
| Step 3: Developer 代码实现 | 遵循选定的 Recipe 执行具体步骤（自动标注→训练→评测） |
| Step 6: Reviewer 精度验证 | 对照 Recipe 中的性能基准做对比评测 |

## Recipe 与现有架构的关系

| 层 | 一句话 | 例子 |
|----|--------|------|
| **Skill** | "我能检测球"——定义**能力** | `detector.py` 的 `detect()` 方法 |
| **Skill Recipe** | "用 ETH 的方法，我可以从数据训练出一个能检测球的模型"——定义**做法** | `eth-shuttle-detection/` 的五阶段流水线 |
| **Plugin** | "我们团队能搭感知系统"——定义**团队和流程** | Architect + Developer + Reviewer 的 6 步工作流 |
| **Plugin Recipe** | "用 ETH 方案搭完整羽毛球感知系统，这是具体步骤"——定义**系统级做法** | `eth-badminton-perception/` 的 Docker 编排 + 端到端评测 |

## 如何新增 Recipe

### 新增 Skill Recipe

1. 在 `skills/{skill}/recipes/` 下创建目录
2. 编写 `RECIPE.md`（含 YAML frontmatter 元数据 + 方案说明）
3. 实现各阶段脚本（autogen → convert → train → eval → predict）
4. 在 `skills/{skill}/SKILL.md` 的 Recipe 索引表中添加条目
5. 在 `.claude-plugin/marketplace.json` 的对应 skill 中注册 Recipe 路径

### 新增 Plugin Recipe

1. 在 `plugins/{plugin}/recipes/` 下创建目录
2. 编写 `RECIPE.md`（含 `skill_recipes` 字段引用各 Skill Recipe）
3. 提供系统级编排文件（docker-compose.yml、端到端评测脚本等）
4. 在 `plugins/{plugin}/plugin.json` 的 `recipes` 字段中注册
5. 在 `.claude-plugin/marketplace.json` 的对应 plugin 中注册 Recipe 路径

### RECIPE.md 标准 Frontmatter

```yaml
---
name: recipe-name
skill: ball-detector          # 所属 Skill（Skill Recipe 必填）
# 或
plugin: ball-perception       # 所属 Plugin（Plugin Recipe 必填）

description: 一句话描述
source:
  paper: "论文标题 (年份)"
  repo: https://github.com/...
  license: BSD-3-Clause

sport: [badminton]            # 适用球类
difficulty: advanced          # beginner / intermediate / advanced
requires_training: true       # 是否需要训练数据

dependencies:                 # 额外依赖（超出 Skill 基础依赖）
  - ultralytics>=8.0
  - docker

stages:                       # 构建阶段（Skill Recipe）
  - id: autogen
    script: autogen_labels.py
    description: "阶段描述"
  - id: train
    script: train.py
    description: "阶段描述"

skill_recipes:                # 引用的 Skill Recipe（Plugin Recipe）
  detector: eth-shuttle-detection
  tracker: default
  filter: default
  geometry: default

performance:                  # 性能基准
  f1: 0.86
  latency_ms: 8
---
```
