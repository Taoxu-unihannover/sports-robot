---
name: high-speed-manipulator
description: 用于高速低惯量击球机械臂的设计与执行，包括反射惯量分析、关节带宽评估、末端拍面配置和击球执行验证。适用于用户需要设计或评估高速击球机械臂、直线平台、末端拍面、执行器选型；不用于常规工业机械臂设计或低速操作。
when_to_use: 用户提到高速机械臂、低惯量、MIT 乒乓、直线平台、拍面末端、反射惯量、执行器选型、关节带宽、击球执行时触发。
version: 1.1.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [robot_model, hit_requirements]
  properties:
    robot_model:
      type: object
      description: 机器人模型参数
      properties:
        joint_inertias: { type: array }
        joint_limits: { type: array }
        link_masses: { type: array }
        end_effector_mass: { type: number }
    hit_requirements:
      type: object
      description: 击球需求
      properties:
        max_acceleration: { type: number }
        paddle_speed: { type: number }
        reset_time: { type: number }
output_schema:
  type: object
  required: [feasibility, checks]
  properties:
    feasibility:
      type: string
      enum: [feasible, marginal, infeasible]
    checks:
      type: object
      description: 各项检查结果
    recommendations:
      type: array
      description: 改进建议
---

# 高速击球机械臂

## 何时使用

当用户需要设计或评估用于球类击球的高速机械臂时使用。典型场景：

- 评估现有机械臂是否满足击球速度/加速度需求
- 选择执行器（电机+减速器）组合
- 分析反射惯量和关节带宽
- 验证击球后复位轨迹的可行性

不适用于：常规工业机械臂设计、低速操作任务、无击球需求的机械臂选型。

## 输入约束

- robot_model 必须包含完整的惯量和限位参数
- hit_requirements 的加速度和速度需求必须来自实际击球场景分析
- 反射惯量计算需要准确的减速比和电机转子惯量
- 热分析需要连续工作时间和环境温度

## 执行步骤

### 步骤 1：反射惯量与带宽分析

- 动作：计算各关节的反射惯量，评估关节带宽
- 输入：robot_model.joint_inertias, 减速比, 电机参数
- 成功标准：反射惯量 < 负载惯量的 3 倍，带宽 > 控制频率的 5 倍
- 失败处理：反射惯量过大时建议降低减速比或换更大电机

### 步骤 2：力矩/速度需求校验

- 动作：校验峰值力矩、RMS 力矩、峰值速度是否在电机能力内
- 输入：hit_requirements + 动力学模型
- 成功标准：峰值力矩 < 最大力矩，RMS < 连续力矩，峰值速度 < 最大速度
- 失败处理：不满足时建议换电机或降低击球需求

### 步骤 3：复位轨迹验证

- 动作：验证击球后复位轨迹在时间和力矩限制内可执行
- 输入：击球后状态 + 复位时间 + 力矩限制
- 成功标准：复位轨迹可执行，TCP 重复定位 < 击球容差 1/3
- 失败处理：不可执行时建议增加复位时间或优化轨迹

## 输出格式

```json
{
  "feasibility": "feasible",
  "checks": {
    "peak_torque": {"value": 12.5, "limit": 15.0, "status": "pass"},
    "rms_torque": {"value": 4.2, "limit": 5.0, "status": "pass"},
    "peak_speed": {"value": 8.3, "limit": 10.0, "status": "pass"},
    "reflected_inertia_ratio": {"value": 2.1, "limit": 3.0, "status": "pass"},
    "tcp_repeatability": {"value": 0.8, "limit": 2.0, "status": "pass"}
  },
  "recommendations": []
}
```

## 可用方法与代表性系统

### MIT 轻量乒乓球臂

MIT 的 5-DoF 轻量臂是高速击球机械臂的典型范例：

1. **低惯量设计**：碳纤维连杆，最小化移动质量
2. **低减速比**：直驱或低减速比（< 50:1），降低反射惯量
3. **高带宽电机**：无框力矩电机，电流环 > 5 kHz
4. **末端轻量化**：3D 打印拍面支架，总末端质量 < 100 g
5. **击球性能**：末端加速度 > 50 m/s²，击球后复位 < 200 ms

## 可用方案（Recipes）

| Recipe | 适用平台 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [mit-lightweight-arm](recipes/mit-lightweight-arm/RECIPE.md) | 固定基座 | MIT 轻量臂 | advanced | 否 | 5-DoF, 加速度>50m/s² |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 反射惯量过大 | ratio > 3.0 | 建议降低减速比或换更大电机 |
| 峰值力矩不足 | tau_peak > tau_max | 建议换电机或降低击球需求 |
| RMS 过热风险 | tau_rms > tau_cont | 建议增加散热或降低工作比 |
| 带宽不足 | bandwidth < 5x control_freq | 建议降低减速比或换高带宽电机 |
| 复位不可行 | 超时或超力矩 | 建议增加复位时间或优化轨迹 |
