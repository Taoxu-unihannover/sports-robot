# Ball Execution — 球类执行开发 Team

> 执行层开发环境。含 5 个专业 Skill、3 个 Agent、硬件命令预览和安全检查 pipeline。

## 架构概览

```
ball-execution/
├── plugin.json
├── AGENTS.md
├── quickstart.md
├── init.sh
├── assets/config.yaml
├── agents/
│   ├── execution-architect.md
│   ├── execution-developer.md
│   └── execution-reviewer.md
├── scripts/pipeline.py
├── tests/regression.py
├── references/papers.md
├── examples/execution_preview.md
└── workflows/
```

## 五模块 Skills

| Skill | 职责 | 输入 | 输出 |
|-------|------|------|------|
| `ball-launcher-executor` | 发球机命令映射 | 目标速度、旋转 | 轮速、俯仰、偏航 |
| `high-speed-manipulator` | 高速机械臂轨迹 | 位移、速度/加速度约束 | 轨迹点 |
| `mobile-base-executor` | 移动底盘跟踪 | 底盘位姿、路径点 | 线速度、角速度 |
| `whole-body-executor` | 全身任务分配 | 任务位移、权重 | 底盘/手臂分配 |
| `servo-drive-safety` | 伺服安全检查 | 位置、速度、力矩、温度 | ok/unsafe + reason |

## 三 Agent 分工

### Execution Architect

- 职责：硬件拓扑、命令接口、限幅和联锁设计。
- 输出：`DESIGN.md` + `PLAN.md`。

### Execution Developer

- 职责：实现设备映射、轨迹预览、驱动安全和回归测试。
- 输出：执行 pipeline、配置、测试报告。

### Execution Reviewer

- 职责：审查硬件边界、急停链路、驱动故障和现场测试计划。
- 输出：`REVIEW.md`、安全检查清单。

## 工作流

```
Step 1: Architect 冻结设备参数和联锁策略
Step 2: Developer 实现 launcher/arm/base/whole-body/servo
Step 3: Developer 运行回归测试和命令预览
Step 4: Reviewer 审查安全与现场联调风险
```
