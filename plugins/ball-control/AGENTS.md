# Ball Control — 球类控制开发 Team

> 控制层开发环境。含 4 个专业 Skill、3 个 Agent、击球规划到安全监督的完整 pipeline。

## 架构概览

```
ball-control/
├── plugin.json
├── AGENTS.md
├── quickstart.md
├── init.sh
├── assets/config.yaml
├── agents/
│   ├── control-architect.md
│   ├── control-developer.md
│   └── control-reviewer.md
├── scripts/pipeline.py
├── tests/regression.py
├── references/papers.md
├── examples/control_command.md
└── workflows/
```

## 四模块 Skills

| Skill | 职责 | 输入 | 输出 |
|-------|------|------|------|
| `hit-planner` | 击球点/时间/目标速度规划 | 预测轨迹、目标落点 | HitPlan |
| `mpc-controller` | 实时跟踪控制基线 | 状态、参考、约束 | 控制输入 |
| `skill-policy-controller` | 技能路由与动作混合 | 场景上下文 | 技能选择 |
| `control-safety-supervisor` | 控制安全门控 | 目标命令、边界 | ok/unsafe + reason |

## 三 Agent 分工

### Control Architect

- 职责：控制频率分层、规划/MPC/策略选型、安全边界设计。
- 输出：`DESIGN.md` + `PLAN.md`。

### Control Developer

- 职责：实现规划器、控制器、技能策略、安全监督和回归测试。
- 输出：控制 pipeline、配置、测试报告。

### Control Reviewer

- 职责：审查可达性、实时性、限幅、fallback 和安全状态机。
- 输出：`REVIEW.md`、失败模式覆盖清单。

## 工作流

```
Step 1: Architect 冻结目标、约束、频率
Step 2: Developer 实现 planner/MPC/policy/safety
Step 3: Developer 运行回归与边界测试
Step 4: Reviewer 检查安全监督和执行层接口
```
