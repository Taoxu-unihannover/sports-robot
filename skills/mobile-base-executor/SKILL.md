---
name: mobile-base-executor
description: 用于轮式移动底盘的粗定位、底盘-上肢协同、场地覆盖和功率预算管理。适用于用户需要实现移动平台定位、底盘+机械臂分工、全场覆盖规划；不用于固定基座系统或纯腿足平台。
when_to_use: 用户提到底盘、移动平台、轮式机器人、Hamlet、底盘定位、粗细分工、全场覆盖、mobile base、omni-directional 时触发。
version: 1.1.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [target_position, current_state]
  properties:
    target_position:
      type: array
      items: { type: number }
      description: 目标底盘位置 [x, y, theta]
    current_state:
      type: object
      description: 当前底盘状态
      properties:
        position: { type: array }
        velocity: { type: array }
        arm_capability: { type: object }
    coordination_mode:
      type: string
      enum: [coarse_fine, simultaneous, base_only]
      description: 协同模式，默认 coarse_fine
output_schema:
  type: object
  required: [base_command, coordination_status]
  properties:
    base_command:
      type: object
      description: 底盘速度/位置指令
    arm_budget:
      type: object
      description: 上肢可用裕度
    coordination_status:
      type: string
      enum: [coarse_positioning, fine_alignment, holding, error]
---

# 移动底盘与上肢协同

## 何时使用

当球类机器人使用轮式移动底盘+上肢机械臂的架构时使用。典型场景：

- 底盘负责大位移粗定位，上肢负责最后几十毫秒的精确修正
- 全场覆盖的移动击球
- 底盘-上肢的力/运动协同
- 移动中的动态稳定性维护

不适用于：固定基座系统、纯腿足平台、无移动需求的桌面级系统。

## 输入约束

- target_position 必须在底盘可达范围内
- 底盘定位精度通常为 cm 级，不能替代上肢精确调整
- 底盘必须回传当前能力裕度（剩余位移、速度、加速度余量）
- 底盘-上肢协同需要统一时间戳和坐标链

## 执行步骤

### 步骤 1：粗定位规划

- 动作：根据击球目标计算底盘目标位置
- 输入：target_position, current_state
- 成功标准：底盘轨迹在时间和功率预算内可执行
- 失败处理：目标不可达时建议调整击球策略或放弃

### 步骤 2：底盘-上肢任务分配

- 动作：将击球任务分解为底盘位移和上肢动作
- 输入：击球需求 + 底盘能力裕度 + 上肢能力裕度
- 成功标准：分解后的任务在各自能力范围内
- 失败处理：无法分解时切换为 base_only 模式

### 步骤 3：协同执行与裕度回传

- 动作：底盘执行粗定位，同时回传实时裕度给上肢
- 输入：底盘轨迹 + 上肢需求
- 成功标准：底盘到位精度满足上肢补偿范围
- 失败处理：底盘到位偏差过大时上肢调整策略

## 输出格式

```json
{
  "base_command": {
    "velocity": [0.5, 0.0, 0.1],
    "position_target": [1.2, 0.5, 0.0]
  },
  "arm_budget": {
    "position_margin": [0.05, 0.03, 0.02],
    "velocity_margin": [1.0, 0.8, 0.5]
  },
  "coordination_status": "fine_alignment"
}
```

## 可用方法与代表性系统

### Hamlet 移动操作平台

Hamlet 是移动底盘+上肢协同的代表性系统：

1. **底盘**：全向轮式平台，负责大位移粗定位
2. **上肢**：6-DoF 机械臂，负责精确击球
3. **协同策略**：底盘先到位，上肢再精确调整——"粗细分工"
4. **关键设计**：底盘回传当前能力裕度，上肢据此调整补偿策略
5. **功率预算**：底盘驱动功率 $P_{drv} \approx (ma + C_{rr}mg + 0.5\rho C_d A v^2)v / \eta$

## 可用方案（Recipes）

| Recipe | 适用平台 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [hamlet-mobile-manipulator](recipes/hamlet-mobile-manipulator/RECIPE.md) | 轮式+臂 | Hamlet 粗细分工 | intermediate | 否 | 全向底盘+6DoF臂 |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 目标不可达 | 超出底盘工作空间 | 建议调整击球策略或放弃 |
| 底盘到位偏差大 | 位置误差 > 上肢补偿范围 | 延长定位时间或降低击球精度 |
| 功率不足 | 电流/功率超限 | 降低底盘速度或暂停击球 |
| 协同超时 | 底盘未在截止时间内到位 | 上肢执行保守击球或放弃 |
| 轮子打滑 | 里程计与实际位移不匹配 | 降低加速度，增加定位裕度 |
