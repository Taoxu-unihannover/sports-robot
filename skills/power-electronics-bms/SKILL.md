---
name: power-electronics-bms
description: 用于球类机器人的功率电子与电池管理系统，覆盖功率预算、电池 SoC/SoH 估算、充放电管理、热管理和配电保护。适用于用户需要实现功率预算、BMS、电池管理、SoC 估算、热管理、配电保护；不用于控制算法或感知系统。
when_to_use: 用户提到功率预算、电池、BMS、SoC、SoH、充电、放电、热管理、配电、保护、power budget、battery management 时触发。
version: 1.1.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [power_demand, battery_state]
  properties:
    power_demand:
      type: object
      description: 功率需求
      properties:
        peak_power: { type: number }
        continuous_power: { type: number }
        duration: { type: number }
    battery_state:
      type: object
      description: 电池状态
      properties:
        voltage: { type: number }
        current: { type: number }
        temperature: { type: number }
        soc: { type: number }
        soh: { type: number }
    operating_mode:
      type: string
      enum: [match, training, idle, charging]
      description: 工作模式，默认 match
output_schema:
  type: object
  required: [power_budget, thermal_status, battery_health]
  properties:
    power_budget:
      type: object
      description: 各子系统功率分配
      properties:
        compute: { type: number }
        actuation: { type: number }
        perception: { type: number }
        reserve: { type: number }
    thermal_status:
      type: string
      enum: [normal, warm, hot, critical]
    battery_health:
      type: object
      description: 电池健康评估
      properties:
        estimated_runtime: { type: number }
        cycle_life_remaining: { type: number }
        charge_recommendation: { type: string }
    power_limitation:
      type: boolean
      description: 是否需要限制功率输出
---

# 功率电子与电池管理

## 何时使用

当用户需要设计或管理球类机器人的功率系统和电池时使用。典型场景：

- 比赛功率预算规划（计算+驱动+感知的功率分配）
- 电池 SoC/SoH 估算和剩余运行时间预测
- 充放电策略和热管理
- 配电保护和故障隔离

不适用于：控制算法设计、感知系统设计。

## 输入约束

- power_demand 必须基于实际工作负载分析
- battery_state 的 SoC 必须在 [0, 1] 范围内
- 热管理阈值必须根据电池规格设定
- 功率分配必须保留安全裕度

## 执行步骤

### 步骤 1：功率需求评估

- 动作：根据工作模式评估各子系统功率需求
- 输入：power_demand, operating_mode
- 成功标准：总功率需求在电池能力范围内
- 失败处理：超出时建议降低工作负载或切换模式

### 步骤 2：功率分配与预算

- 动作：按优先级分配功率预算
- 输入：功率需求 + 电池状态 + 优先级
- 成功标准：所有关键子系统获得足够功率
- 失败处理：功率不足时降低非关键子系统功率

### 步骤 3：热管理与健康评估

- 动作：评估热状态和电池健康
- 输入：battery_state + 环境温度
- 成功标准：热状态正常，SoH 可接受
- 失败处理：过热时降低功率输出，SoH 过低时建议更换

## 输出格式

```json
{
  "power_budget": {
    "compute": 150,
    "actuation": 500,
    "perception": 50,
    "reserve": 100
  },
  "thermal_status": "normal",
  "battery_health": {
    "estimated_runtime": 45,
    "cycle_life_remaining": 300,
    "charge_recommendation": "charge_after_match"
  },
  "power_limitation": false
}
```

## 可用方法与代表性系统

### 功率预算模型

移动底盘驱动功率：$P_{drv} = (ma + C_{rr}mg + 0.5\rho C_d A v^2)v / \eta$

### SoC 估算方法

| 方法 | 精度 | 复杂度 | 适用场景 |
|------|------|--------|---------|
| 库仑计数 | 中 | 低 | 实时 |
| 开路电压 | 高 | 低 | 静止后 |
| EKF | 高 | 中 | 实时+高精度 |
| 机器学习 | 高 | 高 | 离线校准 |

### 热管理策略

| 温度范围 | 策略 |
|---------|------|
| < 45°C | 正常运行 |
| 45-55°C | 降低峰值功率 |
| 55-60°C | 仅连续功率 |
| > 60°C | 停止放电 |

## 可用方案（Recipes）

| Recipe | 适用场景 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [hamlet-power-budget](recipes/hamlet-power-budget/RECIPE.md) | 移动平台 | Hamlet 功率模型 | intermediate | 否 | 底盘+臂功率分配 |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 功率不足 | 总需求 > 电池能力 | 降低非关键子系统功率 |
| 过热 | 温度超限 | 降低功率输出或停止 |
| SoC 过低 | SoC < 10% | 进入低功耗模式 |
| SoH 过低 | 容量衰减 > 20% | 建议更换电池 |
| 充电异常 | 充电电流/电压异常 | 停止充电，报告故障 |
| 配电故障 | 短路/过流 | 熔断保护，隔离故障 |
