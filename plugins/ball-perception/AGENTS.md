# Ball Perception — 球类感知开发 Team

> 端到端球类感知系统开发环境。含 5 个专业 Skill、3 个 Agent、完整工作流。

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

## 五模块 Skills

| Skill | 职责 | 输入 | 输出 |
|-------|------|------|------|
| `ball-detector` | 单帧球体检测 | BGR 图像 | 2D 球心坐标 + 置信度 |
| `ball-tracker` | 短轨迹时序平滑 | 连续帧 2D 坐标 | 去噪 2D 轨迹 |
| `ball-state-estimator` | Kalman 状态估计 | 含噪 2D/3D 观测 | 平滑状态 + 速度/加速度 |
| `ball-geometry` | 3D 几何重建 | 多视角 2D 坐标 + 投影矩阵 | 3D 位置 + 重投影误差 |
| `ball-spin-estimator` | 旋转（角速度）估计 | 事件流/标记点/3D 轨迹 | 三维角速度 + 置信度 |

## 三 Agent 分工

### Perception Architect（感知架构师）

- **职责**：需求分析、方案设计、技术路线决策
- **输出**：DESIGN.md + PLAN.md
- **调用时机**：新感知系统搭建、方案变更、技术选型

### Perception Developer（感知开发工程师）

- **职责**：代码实现、模块集成、测试验证
- **输出**：Python 模块代码 + 测试报告
- **调用时机**：方案确定后、Bug 修复、性能优化

### Perception Reviewer（感知审查员）

- **职责**：代码审查、精度验证、性能评估
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
