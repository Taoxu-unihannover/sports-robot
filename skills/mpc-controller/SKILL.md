---
name: mpc-controller
description: 用于球类机器人的模型预测控制（MPC）、最优控制（OCP）和约束优化，包括轨迹生成、击球终端约束、实时迭代求解和安全回退。适用于用户需要实现 MPC/NMPC/OCP/QP 轨迹优化、acados RTI-SQP、击球约束规划；不用于无约束 LQR 或纯 PID 控制。
when_to_use: 用户提到 MPC、NMPC、OCP、QP、acados、RTI、iLQR、trajectory optimization、约束优化、FHMPC、终端约束时触发。
version: 1.1.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [current_state, reference_trajectory]
  properties:
    current_state:
      type: object
      description: 当前机器人状态
      properties:
        q: { type: array, items: { type: number } }
        dq: { type: array, items: { type: number } }
    reference_trajectory:
      type: object
      description: 参考轨迹（来自 hit-planner）
      properties:
        hit_time: { type: number }
        hit_state: { type: object }
        paddle_target: { type: object }
    constraints:
      type: object
      description: 约束集合
    horizon:
      type: integer
      description: 预测时域步数，默认 20
    deadline_ms:
      type: number
      description: 求解截止时间（ms），默认 10
output_schema:
  type: object
  required: [control_sequence, solve_status]
  properties:
    control_sequence:
      type: array
      description: 优化后的控制序列
    solve_time_ms:
      type: number
      description: 实际求解时间
    solve_status:
      type: string
      enum: [optimal, feasible, suboptimal, failed]
    kkt_residual:
      type: number
      description: KKT 残差
    active_constraints:
      type: array
      description: 活跃约束集合
---

# 约束优化与 MPC 控制

## 何时使用

当用户需要在满足关节限位、力矩限制和安全约束的前提下，实时求解最优击球轨迹时使用。典型场景：

- 击球轨迹的实时优化（含终端击球约束）
- 多约束下的轨迹跟踪控制
- 约束满足比全局最优更重要的实时场景
- 需要显式处理安全边界的控制问题

不适用于：无约束 LQR、纯 PID 控制、离线轨迹规划（无实时性要求）。

## 输入约束

- current_state 必须包含完整的关节状态
- reference_trajectory 必须来自 hit-planner 或等效规划器
- deadline_ms 必须小于来球剩余可操作时间
- 求解器必须有 warm-start 和 fallback 机制

## 执行步骤

### 步骤 1：问题构建

- 动作：将击球任务构建为约束优化问题
- 输入：current_state, reference_trajectory, constraints
- 成功标准：构建有效的 OCP（含动力学约束、终端约束、路径约束）
- 失败处理：约束冲突时放宽软约束或报告 infeasible

### 步骤 2：实时求解

- 动作：用 RTI-SQP / iLQR / QP 求解器求解
- 输入：OCP 问题 + warm-start + deadline
- 成功标准：在截止时间内返回 feasible 或 optimal 解
- 失败处理：超时返回 suboptimal（当前迭代解），求解失败返回 failed

### 步骤 3：安全校验与下发

- 动作：校验求解结果是否满足硬约束
- 输入：control_sequence + 安全限制
- 成功标准：所有硬约束满足
- 失败处理：硬约束违反时回退到 last-safe trajectory

## 输出格式

```json
{
  "control_sequence": [[0.1], [-0.2], [0.05]],
  "solve_time_ms": 3.2,
  "solve_status": "optimal",
  "kkt_residual": 0.000001,
  "active_constraints": ["joint_limit_3", "torque_limit_2"]
}
```

## 可用方法与代表性系统

### 方法一：FHMPC — MIT 路线

MIT 轻量乒乓球平台采用 Fixed-Horizon MPC（FHMPC），核心设计：

1. **固定时域**：预测时域固定为击球时刻，终端约束为拍面位置/法向/速度
2. **求解器**：acados RTI-SQP，每步只做一次 SQP 迭代
3. **性能**：平均求解时间 3.2 ms，99.5% 收敛率
4. **对比**：FHMPC 优于 SHMPC（Shrinking Horizon MPC，平均 6.7 ms），因为固定时域的 QP 规模不随时间变化，warm-start 更有效
5. **关键工程**：必须 warm-start、必须有 deadline、必须有 last-safe fallback

### 方法二：全身 QP + RL — HITTER 路线

HITTER 系统将 MPC 思想与 RL 结合：

1. **RL 策略**输出"期望末端加速度 + 躯干加速度"
2. **全身 QP** 将期望加速度映射到关节力矩，同时满足力矩限制、接触约束和摩擦锥约束
3. **优势**：QP 保证约束始终满足，RL 负责高层决策
4. **代价**：QP 求解引入额外延迟（约 1-2 ms）

### 方法对比

| 维度 | FHMPC (MIT) | 全身QP (HITTER) |
|------|-------------|-----------------|
| 求解时间 | 3.2 ms | 1-2 ms |
| 收敛率 | 99.5% | QP 总有解 |
| 约束处理 | 完整OCP约束 | 力矩+接触约束 |
| 适用自由度 | 低（5-DoF） | 高（全身） |
| 优化目标 | 击球精度+能量 | 跟踪RL输出 |
| warm-start | 必须 | 不需要 |

## 可用方案（Recipes）

| Recipe | 适用平台 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [acados-rti-mpc](recipes/acados-rti-mpc/RECIPE.md) | 固定基座 | FHMPC (MIT) | advanced | 否 | 3.2ms, 99.5%收敛 |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 求解超时 | solve_time > deadline | 返回当前迭代解（suboptimal） |
| 求解失败 | QP/NLP 无解 | 回退 last-safe trajectory |
| 约束不可行 | 初始状态违反约束 | 放宽软约束或报告 infeasible |
| KKT 残差过大 | residual > threshold | 标记 suboptimal，增加迭代次数 |
| warm-start 失效 | 上一轮解不可用 | 冷启动求解，延长 deadline |
| 硬约束违反 | 安全校验失败 | 丢弃求解结果，执行安全回退 |
