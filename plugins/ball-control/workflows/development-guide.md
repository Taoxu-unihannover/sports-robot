# Ball Control 开发规范

## 模块边界

控制层负责从预测轨迹选择击球计划，并输出经过安全监督的目标命令。

## 接口约定

```
PredictionBundle -> HitPlanner -> SkillPolicy / MPC -> SafetySupervisor -> ExecutionCommand
```

## 测试标准

- 击球规划要覆盖无可达窗口、可达窗口和目标速度计算。
- MPC 基线要验证控制方向和限幅。
- 技能策略要验证场景路由和低余量拒绝。
- 安全监督要验证 workspace、speed、too_late 三类拒绝。
