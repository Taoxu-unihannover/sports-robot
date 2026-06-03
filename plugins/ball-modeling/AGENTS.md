# Ball Modeling — 球类建模开发 Team

> 端到端建模层开发环境。含 5 个专业 Skill、3 个 Agent、完整工作流和可运行预测 pipeline。

## 架构概览

```
ball-modeling/
├── plugin.json
├── AGENTS.md
├── quickstart.md
├── init.sh
├── assets/config.yaml
├── agents/
│   ├── modeling-architect.md
│   ├── modeling-developer.md
│   └── modeling-reviewer.md
├── scripts/pipeline.py
├── tests/regression.py
├── references/papers.md
├── examples/predict_hit.md
└── workflows/
```

## 五模块 Skills

| Skill | 职责 | 输入 | 输出 |
|-------|------|------|------|
| `ball-kinematic-model` | 机械臂/球拍运动学 | 关节角、结构参数 | 球拍位姿、雅可比、工作空间余量 |
| `ball-flight-model` | 球飞行预测 | 位置、速度、旋转 | 未来轨迹、平面穿越点 |
| `ball-impact-contact` | 球拍/地面接触 | 入射速度、球拍速度、法向 | 出射速度 |
| `model-identification` | 参数辨识 | 轨迹日志、控制日志 | 阻力、映射、在线参数 |
| `model-uncertainty-risk` | 不确定性风险 | 残差、协方差、时序 | 门控结果、风险分数 |

## 三 Agent 分工

### Modeling Architect

- 职责：模型选型、坐标系与接口设计、参数来源规划。
- 输出：`DESIGN.md` + `PLAN.md`。
- 调用时机：建模层新建、物理模型变更、跨层接口冻结。

### Modeling Developer

- 职责：实现模型、配置、参数辨识、预测 pipeline 和测试。
- 输出：Python 模块、配置文件、回归测试报告。
- 调用时机：设计确定后、模型误差修复、参数更新。

### Modeling Reviewer

- 职责：审查物理一致性、数值稳定性、实时性和控制接口风险。
- 输出：`REVIEW.md`、风险清单、上线检查项。
- 调用时机：代码提交前、参数发布前、系统联调前。

## 工作流

```
Step 1: 需求分析 -> Architect 输出 DESIGN.md + PLAN.md
Step 2: 参数来源确认 -> Developer 建立配置和辨识路径
Step 3: 代码实现 -> Developer 实现预测/接触/风险接口
Step 4: 回归测试 -> Developer 运行 tests/regression.py
Step 5: 模型审查 -> Reviewer 检查误差、边界和跨层接口
```
