---
name: control-safety-supervisor
description: 用于球类机器人控制层的安全状态机、降级策略、last-safe trajectory 回退、碰撞检查、时延/丢包处理和急停协调。适用于用户需要实现安全回退、状态机、E-stop、降级控制、watchdog；不用于正常控制算法设计或感知层安全。
when_to_use: 用户提到安全回退、状态机、E-stop、degraded、last-safe、watchdog、碰撞预测、丢包、时延异常、安全监督时触发。
version: 1.1.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [system_health, control_command]
  properties:
    system_health:
      type: object
      description: 系统健康状态
      properties:
        observation_age_ms: { type: number }
        solver_status: { type: string }
        collision_risk: { type: boolean }
        hardware_fault: { type: boolean }
        communication_ok: { type: boolean }
    control_command:
      type: object
      description: 待审批的控制命令
      properties:
        joint_commands: { type: array }
        mode: { type: string }
output_schema:
  type: object
  required: [decision, safety_state]
  properties:
    decision:
      type: string
      enum: [execute, modify, fallback, safe_stop, estop]
    modified_command:
      type: object
      description: 修改后的命令（若 decision=modify）
    safety_state:
      type: string
      enum: [normal, guarded, degraded, safe_stop, estop]
    reason:
      type: string
      description: 决策原因
---

# 控制安全监督

## 何时使用

当用户需要设计或实现球类机器人控制层的安全监督机制时使用。典型场景：

- 安全状态机设计（Normal → Guarded → Degraded → Safe Stop → E-stop）
- 观测过期/丢包时的降级策略
- 求解失败时的 last-safe trajectory 回退
- 碰撞风险检测和急停协调
- 异常恢复流程设计

不适用于：正常控制算法设计、感知层安全、硬件级安全功能（用 servo-drive-safety）。

## 输入约束

- system_health 必须包含完整的健康指标
- 急停命令优先级高于所有其他命令
- 安全状态转换必须记录原因和时间戳
- 从 Safe Stop/E-stop 恢复必须经过自检和时钟同步

## 执行步骤

### 步骤 1：健康状态评估

- 动作：检查系统健康指标，判断当前安全状态
- 输入：system_health
- 成功标准：所有指标在正常范围
- 失败处理：指标异常时升级安全状态（Normal→Guarded→Degraded）

### 步骤 2：命令审批

- 动作：根据安全状态审批控制命令
- 输入：control_command + safety_state
- 成功标准：命令在当前安全状态下可执行
- 失败处理：不可执行时修改命令或回退到 last-safe

### 步骤 3：安全状态转换

- 动作：执行安全状态转换并记录
- 输入：转换目标状态 + 原因
- 成功标准：状态转换完成，所有相关模块收到通知
- 失败处理：转换失败时进入最高安全级别

## 输出格式

```json
{
  "decision": "execute",
  "modified_command": null,
  "safety_state": "normal",
  "reason": "all_health_indicators_ok"
}
```

## 可用方法与代表性系统

### 五态安全状态机

推荐的安全状态机设计：

| 状态 | 触发条件 | 行为 |
|------|---------|------|
| Normal | 所有指标正常 | 正常执行控制命令 |
| Guarded | 观测延迟增加/求解收敛率下降 | 降低控制增益，增加安全裕度 |
| Degraded | 观测丢失/求解频繁失败 | 执行 last-safe trajectory，放弃击球 |
| Safe Stop | 碰撞风险/硬件报警 | 减速停止，保持当前位置 |
| E-stop | 硬件故障/通信断开 | 立即断电，STO 触发 |

### 关键策略

- **数据过期**：模型外推 + 协方差增大，超过阈值进入 Degraded
- **求解失败**：执行 last-safe trajectory，连续失败进入 Safe Stop
- **碰撞风险**：取消击球并复位，高风险进入 Safe Stop
- **硬件报警**：进入 Safe Stop 或 E-stop
- **异常恢复**：必须重新自检和时钟同步才能回到 Normal

## 可用方案（Recipes）

| Recipe | 适用场景 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [ace-last-safe-reset](recipes/ace-last-safe-reset/RECIPE.md) | 安全回退 | last-safe trajectory + 五态状态机 | intermediate | 否 | 碰撞检测+急停协调 |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 观测过期 | data_age > threshold | 进入 Guarded，使用预测值 |
| 观测丢失 | 连续 N 帧无数据 | 进入 Degraded，执行 last-safe |
| 求解失败 | solver_status=failed | 执行 last-safe，连续失败进入 Safe Stop |
| 碰撞风险 | collision_risk=true | 取消击球，执行复位 |
| 硬件故障 | hardware_fault=true | 进入 E-stop |
| 通信断开 | communication_ok=false | 进入 E-stop |
| 恢复失败 | 自检未通过 | 保持 Safe Stop，人工介入 |
