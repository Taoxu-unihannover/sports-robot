# Ball Perception — 球类感知开发 Team

> 端到端球类感知系统开发环境。含 7 个专业 Skill、3 个 Agent、完整工作流，包括 MuJoCo 仿真相机感知链路。

## 架构概览

```
ball-perception/
├── plugin.json              # 插件元数据
├── AGENTS.md                # 本文件（Team 总览）
├── quickstart.md            # 快速开始指南
├── init.sh                  # 环境初始化脚本
├── agents/                  # 专业 Agent 定义
│   ├── perception-architect.md   # 感知架构师（方案设计）
│   ├── perception-developer.md   # 感知开发工程师（代码实现）
│   └── perception-reviewer.md    # 感知审查员（代码审查）
├── hooks/                   # 生命周期钩子
│   ├── hooks.json
│   └── run-hook.cmd
└── workflows/               # 工作流定义
    ├── development-guide.md      # 开发规范（单一参考源）
    ├── task-prompts.md           # Agent 调用参数详情
    └── templates/                # 文档模板
        ├── design-template.md
        └── plan-template.md
```

## 七模块 Skills

| Skill | 职责 | 输入 | 输出 |
|-------|------|------|------|
| `ball-detector` | 单帧球体检测 | BGR 图像 | 2D 球心坐标 + 置信度 |
| `ball-tracker` | 短轨迹时序平滑 | 连续帧 2D 坐标 | 去噪 2D 轨迹 |
| `ball-state-estimator` | Kalman 状态估计 | 含噪 2D/3D 观测 | 平滑状态 + 速度/加速度 |
| `ball-geometry` | 3D 几何重建 | 多视角 2D 坐标 + 投影矩阵 | 3D 位置 + 重投影误差 |
| `ball-spin-estimator` | 旋转（角速度）估计 | 事件流/标记点/3D 轨迹 | 三维角速度 + 置信度 |
| `sim-camera-perception-input` | MuJoCo 仿真相机 | MuJoCo 渲染 buffer | RGB/深度图像 + 状态估计 |
| `mujoco-policy-evaluator` | 策略评估与指标 | 训练模型 + 环境 | 成功率、奖励、轨迹 |

## MuJoCo 仿真相机感知链路

### 相机配置

MuJoCo 仿真中可配置多个虚拟相机：

```python
import mujoco

camera = mujoco.MjvCamera()
camera.type = mujoco.mjtCamera.mjCAMERA_FIXED
camera.fixedcamid = model.cam("camera_name").id

renderer = mujoco.Renderer(model, height=480, width=640)
renderer.update_scene(data, camera=camera)
image = renderer.render()
```

### 感知管线

1. **渲染**：从 MuJoCo 相机获取 RGB/深度图
2. **检测**：颜色分割/轮廓检测定位球体
3. **跟踪**：多帧关联，时序平滑
4. **状态估计**：Kalman 滤波估计位置和速度
5. **误差评估**：与真值对比，计算位置/速度误差

### 真值 vs 感知对比

| 指标 | 真值输入 | 感知输入 | 允许退化 |
|---|---|---|---|
| 位置误差 | 0 | 取决于检测精度 | ≤ 120% |
| 速度误差 | 0 | 取决于滤波延迟 | ≤ 130% |
| 推理延迟 | ~1ms | ~10ms | ≤ 150% |
| 成功率 | baseline | baseline × 0.8 | ≥ 80% |

## 三 Agent 分工

### Perception Architect（感知架构师）

- **职责**：需求分析、方案设计、技术路线决策、MuJoCo 相机配置
- **输出**：DESIGN.md + PLAN.md
- **调用时机**：新感知系统搭建、方案变更、技术选型

### Perception Developer（感知开发工程师）

- **职责**：代码实现、模块集成、测试验证、仿真相机适配器
- **输出**：Python 模块代码 + 测试报告
- **调用时机**：方案确定后、Bug 修复、性能优化

### Perception Reviewer（感知审查员）

- **职责**：代码审查、精度验证、性能评估、感知 vs 真值误差分析
- **输出**：REVIEW.md + 精度报告
- **调用时机**：代码提交前、上线前审查

## 工作流

```
Step 1: 需求分析 → Architect 输出 DESIGN.md + PLAN.md
Step 2: 设计串讲 → Developer 审查设计，输出 WALKTHROUGH.md
Step 3: 代码实现 → Developer 实现四模块代码
Step 4: 集成测试 → Developer 运行回归测试
Step 5: 代码审查 → Reviewer 审查代码，输出 REVIEW.md
Step 6: 精度验证 → Reviewer 运行精度测试，输出精度报告
```

## 快速开始

```bash
# 初始化环境
bash init.sh

# 安装依赖
pip install -r requirements.txt

# 运行回归测试
cd skills/ball-detector && python scripts/detector.py --test
cd skills/ball-tracker && python scripts/tracker.py --test
cd skills/ball-state-estimator && python scripts/filter.py --test
cd skills/ball-geometry && python scripts/geometry.py --test
cd skills/ball-spin-estimator && python scripts/spin.py --test
```
