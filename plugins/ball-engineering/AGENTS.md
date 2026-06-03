# Ball Engineering — 球类工程开发 Team

> 工程层开发环境。含 5 个专业 Skill、3 个 Agent、实时/电源/HIL/发布验证 pipeline。

## 架构概览

```
ball-engineering/
├── plugin.json
├── AGENTS.md
├── quickstart.md
├── init.sh
├── assets/config.yaml
├── agents/
│   ├── engineering-architect.md
│   ├── engineering-developer.md
│   └── engineering-reviewer.md
├── scripts/pipeline.py
├── tests/regression.py
├── references/papers.md
├── examples/engineering_validation.md
└── workflows/
```

## 五模块 Skills

| Skill | 职责 | 输入 | 输出 |
|-------|------|------|------|
| `realtime-system-integration` | 实时预算和 watchdog | 延迟配置 | 总延迟、超时状态 |
| `ros2-rtos-middleware` | 生命周期与 QoS | 节点配置 | lifecycle/QoS |
| `power-electronics-bms` | 电源与 BMS | 电压、电流、容量 | 功率、SOC、欠压 |
| `hil-verification` | HIL/日志回放验证 | 日志指标 | RMSE、延迟统计 |
| `maintenance-release` | 维护发布 | 版本、标定配置 | checksum、兼容性 |

## 三 Agent 分工

### Engineering Architect

- 职责：系统拓扑、实时预算、中间件、电源、验证与发布策略。
- 输出：`DESIGN.md` + `PLAN.md`。

### Engineering Developer

- 职责：实现配置校验、HIL、日志回放、发布辅助工具和测试。
- 输出：工程 pipeline、配置、测试报告。

### Engineering Reviewer

- 职责：审查上线条件、日志覆盖、回滚路径和现场运维风险。
- 输出：`REVIEW.md`、发布检查清单。

## 工作流

```
Step 1: Architect 冻结系统拓扑和上线标准
Step 2: Developer 实现实时/电源/HIL/发布校验
Step 3: Developer 运行工程回归测试
Step 4: Reviewer 审查发布与回滚风险
```
