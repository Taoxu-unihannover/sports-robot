---
name: ball-kinematic-model
description: 用于球类机器人的运动学建模与求解，覆盖正/逆运动学、雅可比计算、工作空间分析、奇异处理和运动链配置。适用于用户需要实现运动学建模、IK/FK、雅可比、工作空间、Pinocchio；不用于动力学建模或控制。
when_to_use: 用户提到运动学、IK、FK、雅可比、工作空间、奇异、DH参数、Pinocchio、运动链、kinematic model 时触发。
version: 1.1.0
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
      enum: [forward_kinematics, inverse_kinematics, jacobian, workspace_analysis]
      description: 运动学任务
    joint_values:
      type: array
      description: 关节值（FK/雅可比需要）
    target_pose:
      type: object
      description: 目标位姿（IK 需要）
      properties:
        position: { type: array }
        orientation: { type: array }
    ik_parameters:
      type: object
      description: IK 求解参数
      properties:
        initial_guess: { type: array }
        tolerance: { type: number }
        max_iterations: { type: integer }
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
    singularity_proximity:
      type: number
      description: 奇异接近度 [0, 1]
    manipulability:
      type: number
      description: 可操作度指标
---

# 运动学建模与求解

## 何时使用

当用户需要建立或求解机器人的运动学模型时使用。典型场景：

- 正运动学（FK）：从关节角计算末端位姿
- 逆运动学（IK）：从目标位姿计算关节角
- 雅可比计算：用于力/速度映射和奇异分析
- 工作空间分析：评估可达范围

不适用于：动力学建模（用 mpc-controller）、控制设计。

## 输入约束

- robot_description 必须是有效的 URDF/MJCF
- IK 需要合理初值（否则可能陷入局部极小）
- 关节值必须在关节限位内
- 奇异附近 IK 解不稳定，需要正则化

## 执行步骤

### 步骤 1：模型加载与验证

- 动作：加载 URDF/MJCF 并构建运动学树
- 输入：robot_description
- 成功标准：模型加载成功，自由度正确
- 失败处理：模型无效时返回 model_error

### 步骤 2：运动学求解

- 动作：根据 task 类型执行 FK/IK/雅可比/工作空间分析
- 输入：task + 相关参数
- 成功标准：求解收敛且结果合理
- 失败处理：IK 不收敛时尝试不同初值或返回失败

### 步骤 3：奇异与可操作度分析

- 动作：计算奇异接近度和可操作度
- 输入：关节值 + 雅可比
- 成功标准：可操作度 > 阈值
- 失败处理：接近奇异时标记并建议避开

## 输出格式

```json
{
  "result": {
    "joint_values": [0.1, -0.5, 0.3, 0.2, -0.1],
    "end_effector_pose": [1.2, 0.3, 0.8, 0.0, 0.0, 0.0, 1.0]
  },
  "success": true,
  "singularity_proximity": 0.15,
  "manipulability": 0.82
}
```

## 可用方法与代表性系统

### Pinocchio 刚体动力学库

Pinocchio 是推荐的 Lie 群运动学库：

1. **FK**：$T_{0n} = \prod_{i=1}^{n} \exp(\hat{\xi}_i q_i)$
2. **雅可比**：$J = \partial x / \partial q$，支持 body 和 spatial 两种表示
3. **IK**：Levenberg-Marquardt 或 damped least squares
4. **奇异处理**：阻尼最小二乘 + 可操作度梯度

### 方法对比

| 维度 | DH 参数法 | Pinocchio (Lie群) |
|------|----------|-------------------|
| 建模复杂度 | 中 | 低 |
| 数值稳定性 | 中 | 高 |
| 奇异处理 | 需要额外处理 | 内置阻尼 |
| 速度 | 中 | 快（模板化） |
| 生态 | 传统 | 现代（ROS/Drake） |

## 可用方案（Recipes）

| Recipe | 适用平台 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [pinocchio-lie-kinematics](recipes/pinocchio-lie-kinematics/RECIPE.md) | 通用 | Pinocchio Lie群 | intermediate | 否 | FK < 0.1ms |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 模型加载失败 | URDF/MJCF 无效 | 返回 model_error |
| IK 不收敛 | 迭代超限 | 尝试不同初值或返回失败 |
| 接近奇异 | manipulability < threshold | 增加阻尼或避开奇异位形 |
| 关节超限 | 解超出限位 | 钳位并重新求解 |
| 目标不可达 | 超出工作空间 | 返回最近可达点 |
