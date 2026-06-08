---
name: robot-dynamics-model
description: 用于球类机器人刚体动力学建模与求解，覆盖前向动力学(ABA)、逆动力学(RNEA)、质量矩阵(CRBA)、科里奥利力、重力项、关节摩擦和浮基系统动力学。适用于用户需要实现机器人动力学、ABA、RNEA、CRBA、前馈力矩、惯量矩阵、Pinocchio 动力学；不用于运动学求解或飞行预测。
when_to_use: 用户提到机器人动力学、ABA、RNEA、CRBA、前向动力学、逆动力学、质量矩阵、科里奥利力、前馈力矩、惯量矩阵、robot dynamics、rigid body dynamics 时触发。
version: 1.0.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [robot_description, task]
  properties:
    robot_description:
      type: string
      description: URDF 或 MJCF 模型路径
    task:
      type: string
      enum: [forward_dynamics, inverse_dynamics, mass_matrix, coriolis_gravity, torque_feasibility]
      description: 动力学任务
    state:
      type: object
      description: 机器人状态
      properties:
        q: { type: array, description: 关节位置 }
        qd: { type: array, description: 关节速度 }
        qdd: { type: array, description: 关节加速度（逆动力学需要） }
    tau:
      type: array
      description: 关节力矩（前向动力学需要）
    friction_params:
      type: object
      description: 摩擦参数
      properties:
        viscous: { type: array, description: 粘滞摩擦系数 }
        coulomb: { type: array, description: 库仑摩擦力矩 }
output_schema:
  type: object
  required: [result, success]
  properties:
    result:
      type: object
      description: 求解结果（根据 task 类型不同）
    success:
      type: boolean
      description: 求解是否成功
    torque_margin:
      type: number
      description: 力矩裕度（剩余力矩占比）
    energy_cost:
      type: number
      description: 能量代价
---

# 机器人刚体动力学建模与求解

## 何时使用

当用户需要建立或求解机器人的动力学模型时使用。典型场景：

- 前向动力学（ABA）：给定力矩，计算加速度，用于轨迹预测
- 逆动力学（RNEA）：给定期望运动，计算所需力矩，用于前馈控制
- 质量矩阵（CRBA）：计算 $M(q)$，用于控制律设计和力矩可行性检查
- 科里奥利+重力：计算 $C(q,\dot q)\dot q + g(q)$，用于重力补偿和前馈
- 力矩可行性：检查所需力矩是否在电机能力范围内

不适用于：运动学求解（用 ball-kinematic-model）、飞行预测（用 ball-flight-model）。

## 输入约束

- robot_description 必须是有效的 URDF/MJCF
- q, qd 维数必须与模型自由度一致
- 力矩必须在物理合理范围内
- 浮基系统需要额外处理（6 自由度浮基 + 关节自由度）
- 摩擦参数应从辨识实验获得，不可随意设定

## 执行步骤

### 步骤 1：模型加载与验证

- 动作：加载 URDF/MJCF 并构建动力学树
- 输入：robot_description
- 成功标准：模型加载成功，质量属性正确
- 失败处理：模型无效时返回 model_error

### 步骤 2：动力学求解

- 动作：根据 task 类型执行 ABA/RNEA/CRBA/科里奥利+重力/力矩可行性
- 输入：task + state + 相关参数
- 成功标准：求解结果合理（加速度有限、力矩在范围内）
- 失败处理：力矩超限时标记并建议降低运动要求

### 步骤 3：力矩裕度与能量评估

- 动作：计算力矩裕度和能量代价
- 输入：所需力矩 + 电机限制
- 成功标准：力矩裕度 > 0
- 失败处理：裕度不足时建议调整轨迹或降低速度

## 输出格式

```json
{
  "result": {
    "qdd": [0.5, -1.2, 0.3, 0.1, -0.8],
    "tau": [2.1, -5.3, 1.8, 0.5, -3.2]
  },
  "success": true,
  "torque_margin": 0.35,
  "energy_cost": 12.5
}
```

## 可用方法与代表性系统

### 运动方程

机器人刚体动力学标准形式：

$$M(q)\ddot q + C(q,\dot q)\dot q + g(q) + \tau_f(\dot q) = \tau$$

其中：
- $M(q)$：广义质量矩阵（对称正定，CRBA 计算）
- $C(q,\dot q)\dot q$：科里奥利力和离心力
- $g(q)$：重力项
- $\tau_f(\dot q)$：摩擦力矩（粘滞 + 库仑）
- $\tau$：关节力矩

### 前向动力学 — ABA

铰接体算法（ABA）直接计算加速度：

$$\ddot q = \text{ABA}(q, \dot q, \tau)$$

复杂度 $O(n)$，对 6-7 自由度机械臂单次调用微秒级，满足 1 kHz 伺服环。

### 逆动力学 — RNEA

递推牛顿-欧拉算法（RNEA）计算所需力矩：

$$\tau = \text{RNEA}(q, \dot q, \ddot q)$$

用于前馈力矩计算和力矩可行性检查。

### 摩擦模型

关节摩擦通常采用粘滞+库仑模型：

$$\tau_f = F_v \dot q + F_c \cdot \text{sign}(\dot q)$$

参数需从 PRBS/扫频激励实验辨识。

### 方法对比

| 维度 | ABA (前向) | RNEA (逆) | CRBA (质量矩阵) |
|------|-----------|----------|----------------|
| 输入 | $q, \dot q, \tau$ | $q, \dot q, \ddot q$ | $q$ |
| 输出 | $\ddot q$ | $\tau$ | $M(q)$ |
| 复杂度 | $O(n)$ | $O(n)$ | $O(n^2)$ |
| 典型用途 | 轨迹预测 | 前馈控制 | 控制律设计 |
| 实时性 | μs 级 | μs 级 | 10-100 μs |

## 可用方案（Recipes）

| Recipe | 适用平台 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [pinocchio-rnea-aba](recipes/pinocchio-rnea-aba/RECIPE.md) | 通用 | Pinocchio ABA/RNEA | intermediate | 否 | ABA < 5 μs |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 模型加载失败 | URDF/MJCF 无效 | 返回 model_error |
| 力矩超限 | tau > tau_max | 标记并建议降低运动要求 |
| 质量矩阵奇异 | det(M) ≈ 0 | 检查模型质量和惯量参数 |
| 摩擦参数缺失 | friction_params 为空 | 使用零摩擦模型并标记 |
| 浮基欠驱动 | 力矩维数 < 状态维数 | 确保浮基部分力矩为零 |
