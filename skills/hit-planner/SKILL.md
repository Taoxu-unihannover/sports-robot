---
name: hit-planner
description: 用于球类机器人的击球点、击球时刻、拍面目标状态和击球窗口规划，把球路预测转化为可执行终端约束。适用于用户需要实现击球规划、拦截点计算、hit time/pose 规划、终端约束生成；不用于飞行预测或底层轨迹跟踪。
when_to_use: 用户提到击球规划、拦截点、hit time、hit pose、paddle normal、terminal constraint、OCP 终端约束、击球窗口时触发。
version: 1.1.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [ball_prediction, robot_capability]
  properties:
    ball_prediction:
      type: object
      description: 球路预测结果
      properties:
        trajectory: { type: array }
        covariance: { type: array }
        hit_candidates: { type: array }
    robot_capability:
      type: object
      description: 机器人可达域和力矩/速度限制
      properties:
        reachability: { type: object }
        max_paddle_speed: { type: number }
        max_paddle_acceleration: { type: number }
    strategy:
      type: string
      enum: [aggressive, balanced, conservative, defensive]
      description: 击球策略，默认 balanced
output_schema:
  type: object
  required: [hit_time, hit_state, paddle_target, feasibility]
  properties:
    hit_time:
      type: number
      description: 候选击球时刻
    hit_state:
      type: object
      description: 球在击球时刻的位置和速度
    paddle_target:
      type: object
      description: 拍面目标状态（位置、法向、速度）
    hit_window:
      type: object
      description: 可行击球窗口
    feasibility:
      type: string
      enum: [feasible, marginal, infeasible]
---

# 击球事件规划

## 何时使用

当用户需要将球路预测转化为具体的击球目标时使用。典型场景：

- 计算候选击球时刻和位置
- 确定拍面法向和击球速度
- 评估击球窗口的可行性
- 为 IK/OCP/MPC 生成终端约束

不适用于：飞行预测（用 ball-flight-model）、底层轨迹跟踪（用 mpc-controller）。

## 输入约束

- ball_prediction 必须来自 ball-flight-model 的预测结果
- robot_capability 必须包含准确的可达域和力矩/速度限制
- 击球窗口必须考虑协方差（不确定度大的候选应降低优先级）
- 策略选择影响拍面法向和速度目标

## 执行步骤

### 步骤 1：候选击球点筛选

- 动作：将球路预测与机器人可达域求交，生成候选击球窗口
- 输入：ball_prediction.trajectory, robot_capability.reachability
- 成功标准：至少一个候选击球窗口
- 失败处理：无候选窗口时输出防守/复位/放弃击球

### 步骤 2：拍面目标计算

- 动作：根据策略和目标落点计算拍面法向和速度
- 输入：候选击球点 + 策略 + 目标落点
- 成功标准：拍面速度在机器人能力范围内
- 失败处理：速度超限时切换保守策略

### 步骤 3：可行性评估

- 动作：评估击球窗口的可行性（时间裕度、速度裕度、协方差）
- 输入：拍面目标 + 机器人能力 + 不确定度
- 成功标准：feasibility 为 feasible 或 marginal
- 失败处理：infeasible 时建议放弃击球或切换防守

## 输出格式

```json
{
  "hit_time": 0.35,
  "hit_state": {
    "position": [1.2, 0.3, 0.8],
    "velocity": [3.0, -1.0, -2.0]
  },
  "paddle_target": {
    "position": [1.2, 0.3, 0.8],
    "normal": [0.0, 0.0, 1.0],
    "velocity": [2.0, 0.0, 1.0]
  },
  "hit_window": {
    "earliest": 0.33,
    "latest": 0.37,
    "margin_ms": 40
  },
  "feasibility": "feasible"
}
```

## 可用方法与代表性系统

### MIT 终端 OCP 规划

MIT 系统将击球规划直接并入 OCP：

1. **终端约束**：拍面位置 = 球位置，拍面法向 = 期望方向，拍面速度 = 期望速度
2. **优化目标**：最小化关节力矩 + 最大化击球后球速
3. **约束**：关节限位、力矩限制、击球时刻约束
4. **输出**：直接给 MPC 的终端约束，不需要单独的 IK 步骤

## 可用方案（Recipes）

| Recipe | 适用平台 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [mit-terminal-ocp](recipes/mit-terminal-ocp/RECIPE.md) | 固定基座 | MIT 终端OCP | advanced | 否 | FHMPC 3.2ms |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 无候选窗口 | 可达域无交集 | 输出防守/复位/放弃击球 |
| 拍面速度超限 | 超出机器人能力 | 切换保守策略 |
| 击球窗口过窄 | margin < threshold | 标记 marginal，增加不确定度 |
| 协方差过大 | 置信度不足 | 降低击球精度要求或放弃 |
| 策略冲突 | 多目标不可兼得 | 按优先级取舍 |
