# SportsRobot — 球类机器人技术栈

> 以 Marketplace + Plugin + Skill + Agent + Recipe 架构构建乒乓球、羽毛球、网球机器人全技术栈。当前已落地**感知层**、**控制层**（强化学习训练）、**工程层**（项目自举），后续将逐步覆盖建模层、执行层。

## 项目理念

球类机器人落地不是"检测模型 + 机械臂"这么简单，而是一条跨越**高频感知、状态估计、球路建模、决策规划、关节控制、执行机构、系统总线、数据闭环**的全链条工程。本项目将每一层技术栈以 **Marketplace Plugin** 的形式组织，每个 Plugin 包含：

- **Skills**：可复用的原子能力模块（含代码、文档、测试）
- **Recipes**：经过验证的完整构建方案（从数据到训练到部署）
- **Agents**：专业 AI Agent（架构师、开发工程师、审查员）
- **Workflows**：标准化开发流程（设计→串讲→实现→审查→验证）
- **Hooks**：生命周期钩子（环境初始化、上下文注入）
- **Templates**：文档与代码模板

完整技术栈分析见 [技术报告](docs/tech-report/000-tech-report.md)。

## 核心能力

### 🟢 已落地：感知层 + 控制层 + 工程层

| 层级 | Plugin | 能力 | 状态 |
|------|--------|------|------|
| **感知层** | `ball-perception` | 双目相机感知、球检测、跟踪、3D 重建 | ✅ 已落地 |
| **感知层** | `ball-project-assimilator` | 开源项目吸收、复现、超越 | ✅ 已落地 |
| **控制层** | `ball-control` | 强化学习训练、PPO/SAC/DDPG/TD3 | ✅ 已落地 |
| **工程层** | `ball-engineering` | MuJoCo 仿真、Gymnasium 环境、项目工程化 | ✅ 已落地 |
| **工程层** | `ball-project-distiller` | 项目能力抽取、自举新项目 | ✅ 已落地 |

### 🆕 新增项目

| 项目 | 说明 | 源自 | 性能 |
|------|------|------|------|
| [tennis-robot](tennis-robot/) | 基于 MuJoCo + Gymnasium + SB3 的网球机器人导航项目 | skill 自举 | PASS_WITH_GAP |
| [tennis-robot-v2](tennis-robot-v2/) | 基于 dynamic-tennis-v2 接球任务的重现项目 | 项目吸收 | ✅ Sim 模式超越成功 |

### 🆕 新增 Skills

| Skill | 用途 |
|-------|------|
| `mujoco-world-builder` | MuJoCo 网球世界构建 |
| `gymnasium-env-builder` | Gymnasium + MuJoCo 环境封装 |
| `sb3-rl-training-runner` | Stable-Baselines3 训练入口 |
| `mujoco-policy-evaluator` | 策略评估与指标输出 |
| `trajectory-visualizer` | Web 可视化导出 |
| `truth-state-policy-input` | 真值状态观测构建 |
| `sim-camera-input` | 仿真相机感知 |
| `open-project-skill-distiller` | 开源项目技术栈拆解 |
| `stack-method-benchmark` | 同技术栈方法横向评测 |
| `best-stack-composer` | 最优技术栈组合 |

## 项目结构

```
sports-robot/
├── .claude-plugin/
│   └── marketplace.json          # 根级 Marketplace 注册表
├── skills/                       # 独立 Skill 模块（可单独对外呈现）
│   ├── ball-detector/            # 单帧球体检测
│   │   ├── scripts/              # 推理代码
│   │   ├── tests/                # 推理测试
│   │   ├── examples/             # 调用示例
│   │   ├── references/           # 论文引用
│   │   └── recipes/              # 🆕 构建/训练方案
│   │       ├── eth-shuttle-detection/  # ETH YOLOv8 羽毛球方案
│   │       └── hsv-quickstart/        # HSV 轻量快速方案
│   ├── ball-tracker/             # 短轨迹时序平滑
│   ├── ball-state-estimator/    # 状态估计与速度估计
│   └── ball-geometry/            # 3D 几何重建
├── plugins/                     # 官方 Plugin（含 Agent + Workflow + Recipe）
│   └── ball-perception/          # 🟢 感知层（已落地）
│       ├── agents/               # 3 个专业 Agent
│       ├── workflows/            # 开发规范 + 任务提示 + 模板
│       ├── hooks/                # 生命周期钩子
│       ├── scripts/              # 流水线脚本 + 回归测试
│       ├── tests/                # 回归测试用例
│       ├── assets/               # 配置文件模板
│       ├── references/           # 数学公式 + 论文汇总
│       ├── examples/             # 使用示例
│       ├── recipes/              # 🆕 跨 Skill 系统级方案
│       │   └── eth-badminton-perception/  # ETH 羽毛球感知系统方案
│       ├── AGENTS.md             # Team 总览
│       ├── quickstart.md         # 快速开始
│       └── init.sh               # 环境初始化
├── docs/
│   ├── tech-report/              # 技术报告与参考资料
│   └── todo/                     # 待办事项与审查报告
```

## 技术栈全景

```
┌─────────────────────────────────────────────────────────┐
│                    球类机器人全技术栈                       │
├───────────┬───────────┬───────────┬───────────┬─────────┤
│  感知层    │  建模层    │  控制层    │  执行层    │  工程层  │
│  🟢 已落地  │  ⬜ 规划中  │  ⬜ 规划中  │  ⬜ 规划中  │  ⬜ 规划中 │
├───────────┼───────────┼───────────┼───────────┼─────────┤
│ 多相机标定 │ 飞行物理   │ 分层策略   │ 机械臂    │ 实时通信 │
│ 球体检测   │ 碰撞弹跳   │ 轨迹规划   │ 轮式底盘  │ 仿真闭环 │
│ 短时跟踪   │ 贝叶斯滤波 │ IK/MPC    │ 腿足系统  │ 数据管线 │
│ 3D 定位    │ 轨迹预测   │ 强化学习   │ 类人平台  │ 安全监控 │
│ 速度估计   │ 混合模型   │ 全身控制   │ 发球机    │ 自动评测 │
│ 旋转估计   │ 残差学习   │ 模仿学习   │ 伺服驱动  │ CI/CD   │
└───────────┴───────────┴───────────┴───────────┴─────────┘
```

## 已落地：感知层 Agent

### 概述

**ball-perception** 是球类感知端到端开发 Team，覆盖乒乓球/羽毛球/网球的感知全流程：

```
Camera → Detector → Tracker → Filter → Geometry → 3D State
         (检测)     (跟踪)    (滤波)    (重建)      (x,y,z,vx,vy,vz)
```

### 四模块 Skills

> 每个 Skill 支持多种方法实现，可独立选型、组合、迭代。未来将持续扩充方法库与版本。

| Skill | 路径 | 职责 | 可用方法 / 变体 |
|-------|------|------|--------|
| `ball-detector` | [skills/ball-detector/](skills/ball-detector/) | 单帧球体检测 | `YOLOv8` · `HSVColorDetector` · `ONNXBallDetector` |
| `ball-tracker` | [skills/ball-tracker/](skills/ball-tracker/) | 短轨迹时序平滑 | `SlidingWindowTracker` · `TrajectoryTracker` · `TrackNetStyleTracker` |
| `ball-state-estimator` | [skills/ball-state-estimator/](skills/ball-state-estimator/) | 状态估计与速度估计 | `CV` (恒速) · `CA` (恒加速) · `EKF` (扩展 Kalman) · `SlidingWindow` (滑窗平均) · `PositionHistory` (位置历史) |
| `ball-geometry` | [skills/ball-geometry/](skills/ball-geometry/) | 3D 几何重建 | `DLT` (直接线性变换) · `Midpoint` (中点法) · `StereoDepthEstimator` |

### Recipes：从推理到构建的完整方案
Skill 定义"**能做什么**"（推理能力），Recipe 定义"**怎么做到**"（从数据到训练到部署的完整构建方案）。一个 Skill 可以有多种 Recipe，每种代表一种经过验证的具体做法；Plugin Recipe 则组合各 Skill Recipe 形成系统级方案。详见 [Recipe 架构指南](docs/recipe-guide.md)。

#### 当前可用 Recipe

| Recipe | 层级 | 适用球类 | 需要训练 | 性能基准 |
|--------|------|---------|---------|---------|
| [eth-shuttle-detection](skills/ball-detector/recipes/eth-shuttle-detection/RECIPE.md) | Skill | 羽毛球 | 是 | F1=0.86（相似场景）/ 0.70（未知场景） |
| [hsv-quickstart](skills/ball-detector/recipes/hsv-quickstart/RECIPE.md) | Skill | 乒乓球/网球 | 否 | < 2ms 延迟，依赖颜色标定 |
| [eth-badminton-perception](plugins/ball-perception/recipes/eth-badminton-perception/RECIPE.md) | Plugin | 羽毛球 | 是 | 端到端 < 20ms |

### 三 Agent 分工

| Agent | 文件 | 职责 | 输出 |
|-------|------|------|------|
| **Perception Architect** | [agents/perception-architect.md](plugins/ball-perception/agents/perception-architect.md) | 需求分析、方案设计、技术选型 | DESIGN.md + PLAN.md |
| **Perception Developer** | [agents/perception-developer.md](plugins/ball-perception/agents/perception-developer.md) | 代码实现、模块集成、测试验证 | Python 代码 + 测试报告 |
| **Perception Reviewer** | [agents/perception-reviewer.md](plugins/ball-perception/agents/perception-reviewer.md) | 代码审查、精度验证、性能评估、**跨方法/跨版本对比评测** | REVIEW.md + 精度报告 + 对比基准 |

### 开发工作流

```
Step 1: 需求分析    → Architect 输出 DESIGN.md + PLAN.md
Step 2: 设计串讲    → Developer 审查设计，输出 WALKTHROUGH.md
Step 3: 代码实现    → Developer 实现四模块代码
Step 4: 集成测试    → Developer 运行回归测试
Step 5: 代码审查    → Reviewer 审查代码，输出 REVIEW.md
Step 6: 精度验证    → Reviewer 运行精度测试，输出精度报告
                        └─ 含方法间横向对比（如 YOLO vs HSV vs ONNX）
                        └─ 含版本间纵向对比（如 v1.0 → v1.1 精度变化）
                        └─ 含综合性能排名与选型建议
```

---

## 快速开始

### 环境要求

- Python >= 3.8
- pip
- Git

### 安装

```bash
git clone https://github.com/Taoxu-unihannover/sports-robot.git
cd sports-robot

# 初始化感知插件环境
cd plugins/ball-perception
bash init.sh

# 安装 Python 依赖
pip install -r requirements.txt
```

### 验证安装

```bash
# 运行回归测试（23 个测试用例）
cd plugins/ball-perception
python -m pytest tests/regression.py -v

# 预期输出：28 passed
```

### 使用感知 Agent

#### 方式一：直接调用 Skill 模块

```python
import sys
sys.path.insert(0, "skills/ball-detector/scripts")
sys.path.insert(0, "skills/ball-tracker/scripts")
sys.path.insert(0, "skills/ball-state-estimator/scripts")
sys.path.insert(0, "skills/ball-geometry/scripts")

# 检测器
from detector import BallDetector
detector = BallDetector(model_path="yolov8n.pt", confidence_threshold=0.25)
detector.load_model()
result = detector.detect(image)  # → DetectionResult(x, y, confidence, bbox)

# 跟踪器
from tracker import TrajectoryTracker
tracker = TrajectoryTracker(window_size=5, max_gap=3, max_velocity=500.0)
track_point = tracker.update(x=320.5, y=240.3, timestamp=0.016)

# 滤波器
from filter import BallKalmanFilter
kf = BallKalmanFilter(dt=0.008, dim=2, model="CV")
kf.predict()
state = kf.update_2d(x=320.5, y=240.3)  # → BallState(x, y, vx, vy)

# 几何重建
from geometry import Triangulator, CameraConfig
triangulator = Triangulator(camera_configs=[cam0, cam1], method="DLT")
point_3d = triangulator.triangulate({"cam0": (320, 240), "cam1": (315, 238)})
```

#### 方式二：通过 Agent 驱动开发

在支持 Agent 的 IDE（如 Trae / Claude Code）中，直接描述需求即可触发对应 Agent：

```
# 触发 Perception Architect（方案设计）
"我想搭建一个乒乓球感知系统，双目相机，需要实时输出球的 3D 位置和速度"

# 触发 Perception Developer（代码实现）
"请根据 DESIGN.md 实现检测器模块，使用 YOLOv8，置信度阈值 0.3"

# 触发 Perception Reviewer（代码审查）
"请审查 ball-detector 模块的代码质量和精度指标"
```

Agent 会根据 [task-prompts.md](plugins/ball-perception/workflows/task-prompts.md) 中定义的调用参数自动执行对应任务。

#### 方式三：完整流水线

```python
import sys
sys.path.insert(0, "plugins/ball-perception/scripts")
sys.path.insert(0, "skills/ball-detector/scripts")
sys.path.insert(0, "skills/ball-tracker/scripts")
sys.path.insert(0, "skills/ball-state-estimator/scripts")
sys.path.insert(0, "skills/ball-geometry/scripts")

from pipeline import PerceptionPipeline

pipeline = PerceptionPipeline("plugins/ball-perception/assets/config.yaml")
result = pipeline.run("input_video.mp4", display=True)

# result.states  → 每帧的 3D 状态 [BallState, ...]
# result.stats   → 性能统计 {frames_processed, avg_latency_ms, ...}
```

配置文件模板见 [config.yaml](plugins/ball-perception/assets/config.yaml)。

### 精度基准

> 每个 Skill 的多种方法在同一测试集上独立评测，形成可对比的精度矩阵。Reviewer 在 Step 6 输出横向/纵向对比报告。

| 模块 | 指标 | 目标值 | 评测方法 |
|------|------|--------|----------|
| Detector | mAP@0.5 | > 0.8 | YOLOv8 / HSV / ONNX 分别评测 |
| Detector | 单帧延迟 | < 10 ms | 各方法独立计时 |
| Tracker | 平滑度提升 | > 30% | SlidingWindow / Trajectory / TrackNet 对比 |
| Filter | 位置 RMSE | < 5 px | CV / CA / EKF 分别评测 |
| Filter | 速度 RMSE | < 50 px/s | 同上 |
| Geometry | 重投影误差 | < 2 px | DLT / Midpoint / StereoDepth 对比 |
| Geometry | 3D 位置误差 | < 5 cm | 同上 |
| Pipeline | 端到端延迟 | < 20 ms | 最优方法组合 vs 基线组合 |

---

## 路线图

### 已落地

- [x] **感知层** — ball-perception Plugin（4 Skills + 3 Agents + 完整工作流）
- [x] **控制层** — ball-control Plugin（SB3 训练 + 强化学习策略）
- [x] **工程层** — ball-engineering Plugin（MuJoCo + Gymnasium + 项目工程化）
- [x] **项目自举** — ball-project-distiller Plugin（从 skills 自举新项目）
- [x] **项目吸收** — ball-project-assimilator Plugin（吸收开源项目 + 复现 + 超越）
- [x] **tennis-robot** — 自举生成的网球机器人导航项目
- [x] **tennis-robot-v2** — 吸收 dynamic-tennis-v2 的接球任务重现（Sim 模式 93.3% > 86.7%）
- [x] **验证报告** — [docs/verification/two-tasks-verification-report.md](docs/verification/two-tasks-verification-report.md) 任务完成度分析
- [x] Marketplace 架构 — 根级 + 插件级 marketplace.json
- [x] 技术报告 — 全技术栈详尽分析（乒乓球/羽毛球/网球）

### 规划中

- [ ] **建模层** — ball-modeling Plugin
  - 飞行物理模型（重力、阻力、Magnus 效应）
  - 碰撞/弹跳模型
  - 轨迹预测（物理外推 + 数据驱动 + 混合）
  - 旋转/翻转建模
- [ ] **执行层** — ball-actuation Plugin
  - 机械臂运动学/动力学
  - 发球机控制接口
  - 移动平台（轮式/腿足）
  - 类人本体集成

---

## 参考资源

| 资源 | 路径 |
|------|------|
| Recipe 架构指南 | [docs/recipe-guide.md](docs/recipe-guide.md) |
| 全技术栈报告 | [docs/tech-report/000-tech-report.md](docs/tech-report/000-tech-report.md) |
| 感知层设计 | [docs/tech-report/001-感知层.md](docs/tech-report/001-感知层.md) |
| 感知 Agent 总览 | [plugins/ball-perception/AGENTS.md](plugins/ball-perception/AGENTS.md) |
| 快速开始指南 | [plugins/ball-perception/quickstart.md](plugins/ball-perception/quickstart.md) |
| 开发规范 | [plugins/ball-perception/workflows/development-guide.md](plugins/ball-perception/workflows/development-guide.md) |
| Agent 调用参数 | [plugins/ball-perception/workflows/task-prompts.md](plugins/ball-perception/workflows/task-prompts.md) |
| 设计模板 | [plugins/ball-perception/workflows/templates/design-template.md](plugins/ball-perception/workflows/templates/design-template.md) |
| 开发计划模板 | [plugins/ball-perception/workflows/templates/plan-template.md](plugins/ball-perception/workflows/templates/plan-template.md) |
| 数学公式推导 | [plugins/ball-perception/references/formulas.md](plugins/ball-perception/references/formulas.md) |
| 相关论文汇总 | [plugins/ball-perception/references/papers.md](plugins/ball-perception/references/papers.md) |

---

## 贡献指南

本项目采用 Marketplace + Plugin + Agent + Recipe 架构，新增技术栈的标准流程：

1. 在 `skills/` 下创建独立 Skill 模块（含 SKILL.md + scripts/）
2. 在 `skills/{skill}/recipes/` 下创建 Recipe（含 RECIPE.md + 训练/评测脚本）
3. 在 `plugins/` 下创建 Plugin 目录（含 agents/ + workflows/ + hooks/）
4. 在 `plugins/{plugin}/recipes/` 下创建跨 Skill 系统级 Recipe
5. 在 `.claude-plugin/marketplace.json` 中注册新 Plugin 和 Recipe
6. 更新本 README 的路线图

详细规范见 [development-guide.md](plugins/ball-perception/workflows/development-guide.md)。
