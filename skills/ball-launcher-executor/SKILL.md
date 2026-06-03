---
name: ball-launcher-executor
description: 用于球类发球机/发射器的标定与控制，覆盖发球参数映射、弹道校准、转速控制和多模式发球。适用于用户需要实现发球机标定、发球控制、Aimy、弹道校准；不用于机器人击球执行或球检测。
when_to_use: 用户提到发球机、发射器、Aimy、发球标定、弹道校准、转速控制、launcher、ball thrower 时触发。
version: 1.1.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [launch_request]
  properties:
    launch_request:
      type: object
      description: 发球请求
      properties:
        target_speed: { type: number, description: 目标球速 (m/s) }
        target_spin: { type: number, description: 目标转速 (rpm) }
        target_landing: { type: array, description: 目标落点 [x, y] }
        mode: { type: string, enum: [topspin, backspin, sidespin, flat] }
    calibration_params:
      type: object
      description: 标定参数（电机转速→球速映射）
output_schema:
  type: object
  required: [motor_commands, predicted_trajectory]
  properties:
    motor_commands:
      type: object
      description: 电机控制指令
      properties:
        top_wheel_rpm: { type: number }
        bottom_wheel_rpm: { type: number }
        elevation_angle: { type: number }
        azimuth_angle: { type: number }
    predicted_trajectory:
      type: object
      description: 预测弹道
      properties:
        landing_point: { type: array }
        flight_time: { type: number }
    calibration_confidence:
      type: number
      description: 标定置信度 [0, 1]
---

# 发球机标定与控制

## 何时使用

当用户需要控制球类发球机进行自动化训练时使用。典型场景：

- 发球机参数标定（电机转速→球速/转速映射）
- 按目标弹道自动计算发球参数
- 多模式发球（上旋/下旋/侧旋/平击）
- 弹道校准和精度验证

不适用于：机器人击球执行（用 high-speed-manipulator）、球检测（用 ball-detector）。

## 输入约束

- 发球请求必须包含目标球速或目标落点（至少一个）
- 标定参数必须基于实际测量数据
- 电机转速不能超过额定值
- 连续发球间隔必须满足散热需求

## 执行步骤

### 步骤 1：参数映射

- 动作：将目标球速/转速映射到电机转速
- 输入：launch_request + calibration_params
- 成功标准：映射后的电机转速在额定范围内
- 失败处理：超出范围时钳位并标记

### 步骤 2：弹道预测

- 动作：预测发球后的弹道
- 输入：映射参数 + 飞行模型
- 成功标准：预测落点在目标附近
- 失败处理：偏差过大时调整参数

### 步骤 3：执行与校准

- 动作：执行发球并收集反馈数据
- 输入：电机指令
- 成功标准：实际弹道与预测一致
- 失败处理：偏差大时更新标定参数

## 输出格式

```json
{
  "motor_commands": {
    "top_wheel_rpm": 3000,
    "bottom_wheel_rpm": 2500,
    "elevation_angle": 15.0,
    "azimuth_angle": 0.0
  },
  "predicted_trajectory": {
    "landing_point": [2.5, 0.0],
    "flight_time": 0.8
  },
  "calibration_confidence": 0.92
}
```

## 可用方法与代表性系统

### Aimy 智能发球机

Aimy 是球类机器人研究常用的智能发球机：

1. **双轮设计**：上下两个轮子独立控制转速，实现旋转控制
2. **参数映射**：电机转速差 → 转速，电机转速均值 → 球速
3. **标定**：用高速相机测量实际球速，拟合映射关系
4. **精度**：球速误差 < 5%，落点误差 < 10 cm

## 可用方案（Recipes）

| Recipe | 适用球类 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [aimy-ball-launcher](recipes/aimy-ball-launcher/RECIPE.md) | 乒乓球 | Aimy 双轮 | intermediate | 否 | 球速误差 < 5% |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 电机转速超限 | 映射值 > 额定 | 钳位并标记 |
| 标定参数缺失 | 无映射关系 | 使用默认参数并标记 |
| 弹道偏差大 | 实测与预测不一致 | 更新标定参数 |
| 连续发球过热 | 温度超限 | 增加间隔时间 |
| 球卡住 | 传感器异常 | 停止发球，检查机械 |
