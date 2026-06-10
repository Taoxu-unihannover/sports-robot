---
name: ball-impact-contact
description: 用于球-拍、球-台面、球-地面接触与碰撞建模，包括恢复系数、摩擦、切向冲量、拍面速度需求和接触参数辨识。适用于用户需要实现碰撞建模、反弹预测、恢复系数辨识、拍面速度计算；不用于自由飞行建模或无接触场景。
when_to_use: 用户提到球拍接触、碰撞模型、反弹、恢复系数、摩擦、拍面速度、impact、contact、MuJoCo 接触参数、冲量模型时触发。
version: 1.1.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [pre_impact_state, contact_type]
  properties:
    pre_impact_state:
      type: object
      description: 碰撞前状态
      properties:
        ball_velocity: { type: array }
        ball_angular_velocity: { type: array }
        surface_normal: { type: array }
        surface_velocity: { type: array }
    contact_type:
      type: string
      enum: [table_bounce, paddle_hit, ground_slip]
      description: 接触类型
    contact_parameters:
      type: object
      description: 接触参数（恢复系数、摩擦系数等）
output_schema:
  type: object
  required: [post_impact_state, required_paddle_speed]
  properties:
    post_impact_state:
      type: object
      description: 碰撞后状态
      properties:
        ball_velocity: { type: array }
        ball_angular_velocity: { type: array }
    required_paddle_speed:
      type: number
      description: 达到期望出球速度所需的拍面法向速度
    energy_loss:
      type: number
      description: 碰撞能量损失比例
---

# 球拍接触与反弹建模

## 何时使用

当用户需要建模球与拍面/台面/地面的碰撞过程时使用。典型场景：

- 预测球弹跳后的速度和旋转
- 计算击球所需的拍面速度
- 辨识恢复系数和摩擦参数
- 仿真中的接触力建模

不适用于：自由飞行建模（用 ball-flight-model）、无接触场景。

## 输入约束

- pre_impact_state 必须包含完整的球速度和旋转
- contact_type 决定使用哪组接触参数
- 台面、地面、拍面三类接触参数必须分开辨识
- 恢复系数 $e_n \in [0, 1]$，摩擦系数 $\mu > 0$

## 执行步骤

### 步骤 1：碰撞前状态分析

- 动作：分解碰撞前速度为法向和切向分量
- 输入：pre_impact_state.ball_velocity, surface_normal
- 成功标准：法向和切向分量正确分解
- 失败处理：法向为零时无碰撞，返回原状态

### 步骤 2：冲量计算

- 动作：用冲量模型计算碰撞后状态
- 输入：碰撞前分量 + contact_parameters
- 成功标准：碰撞后法向速度 = $-e_n \times$ 碰撞前法向速度
- 失败处理：参数缺失时使用默认值并标记

### 步骤 3：拍面速度需求计算

- 动作：根据期望出球速度反推拍面法向速度
- 输入：期望出球速度 + 入射速度 + 恢复系数
- 成功标准：拍面速度在机器人能力范围内
- 失败处理：超限时建议降低出球速度期望

## 输出格式

```json
{
  "post_impact_state": {
    "ball_velocity": [2.5, -0.3, 3.0],
    "ball_angular_velocity": [10.0, 5.0, -2.0]
  },
  "required_paddle_speed": 1.8,
  "energy_loss": 0.15
}
```

## 可用方法与代表性系统

### 冲量模型

击球瞬间优先用冲量模型：

- 法向恢复：$v_n^+ = -e_n v_n^-$
- 拍面速度反推：$v_{r,n} = (v_{out,n} + e_n v_{in,n}) / (1 + e_n)$
- 切向摩擦：$\|\Lambda_t\| \le \mu \Lambda_n$

### MuJoCo 顺应接触

仿真中用顺应接触模型：

- 法向弹簧-阻尼器：连续可导，适合梯度优化
- 平滑摩擦近似：$\tanh$ 过渡，避免刚性切换
- `solref/solimp` 参数控制接触特性

## 可用方案（Recipes）

| Recipe | 适用球类 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [mit-paddle-impact](recipes/mit-paddle-impact/RECIPE.md) | 乒乓球 | MIT lumped参数 | intermediate | 否 | 冲量模型+参数辨识 |
| [mujoco-compliant-contact](recipes/mujoco-compliant-contact/RECIPE.md) | 乒乓球/网球/羽毛球 | MuJoCo 顺应接触 | advanced | 否 | 连续可导+OCP收敛>95% |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 法向为零 | 无碰撞 | 返回原状态 |
| 参数缺失 | contact_parameters 不完整 | 使用默认值并标记 |
| 拍面速度超限 | 超出机器人能力 | 建议降低出球速度期望 |
| 摩擦锥违反 | 切向力超限 | 钳位到摩擦锥边界 |
| 能量守恒违反 | 碰撞后能量增加 | 检查参数一致性 |
