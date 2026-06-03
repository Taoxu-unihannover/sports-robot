---
name: ball-spin-estimator
description: 用于球类旋转估计，覆盖轨迹反推旋转（Magnus 逆问题）、标记点姿态跟踪和事件相机旋转检测。适用于用户需要实现旋转估计、Magnus 逆推、标记点跟踪、事件相机旋转检测；不用于飞行预测或 2D 检测。
when_to_use: 用户提到旋转估计、Magnus、spin、旋转检测、标记点、事件相机、旋转反推、angular velocity 时触发。
version: 1.1.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [measurement_type, measurement_data]
  properties:
    measurement_type:
      type: string
      enum: [trajectory_magnus, marker_pose, event_camera]
      description: 测量类型
    measurement_data:
      type: object
      description: 测量数据（根据类型不同）
      properties:
        trajectory: { type: array, description: 轨迹点序列（Magnus逆推用） }
        marker_poses: { type: array, description: 标记点位姿序列 }
        event_stream: { type: array, description: 事件流 }
    prior_spin:
      type: array
      description: 先验旋转速度 [wx, wy, wz]
output_schema:
  type: object
  required: [angular_velocity, confidence]
  properties:
    angular_velocity:
      type: array
      items: { type: number }
      description: 估计的旋转速度 [wx, wy, wz] (rad/s)
    confidence:
      type: number
      description: 估计置信度 [0, 1]
    method_used:
      type: string
      description: 实际使用的估计方法
    covariance:
      type: array
      description: 旋转速度协方差矩阵
---

# 球旋转估计

## 何时使用

当用户需要估计球的旋转速度时使用。典型场景：

- 从飞行轨迹反推旋转（Magnus 逆问题）
- 从标记点跟踪旋转
- 从事件相机检测旋转
- 为飞行预测提供旋转输入

不适用于：飞行预测（用 ball-flight-model）、2D 检测（用 ball-detector）。

## 输入约束

- trajectory_magnus 需要足够长的轨迹段（至少 10 个点）
- marker_pose 需要至少 3 个非共线标记点
- event_camera 需要高时间分辨率的事件流
- 先验旋转可提高收敛速度

## 执行步骤

### 步骤 1：数据预处理

- 动作：根据测量类型预处理数据
- 输入：measurement_type, measurement_data
- 成功标准：数据质量满足方法需求
- 失败处理：数据不足时返回 insufficient_data

### 步骤 2：旋转估计

- 动作：根据测量类型选择估计方法
- 输入：预处理数据 + 先验
- 成功标准：估计收敛，置信度可接受
- 失败处理：不收敛时尝试不同初值或降低精度要求

### 步骤 3：不确定度评估

- 动作：评估旋转估计的不确定度
- 输入：估计结果 + 数据质量
- 成功标准：协方差合理
- 失败处理：不确定度过大时标记 low_confidence

## 输出格式

```json
{
  "angular_velocity": [5.0, -2.0, 10.0],
  "confidence": 0.75,
  "method_used": "trajectory_magnus",
  "covariance": [[0.5, 0.1, 0.1], [0.1, 0.3, 0.1], [0.1, 0.1, 0.8]]
}
```

## 可用方法与代表性系统

### 方法一：轨迹 Magnus 逆推

从飞行轨迹反推旋转：

1. **原理**：Magnus 力 $F_m = k_m(\omega \times v)$，已知 $v$ 和 $F_m$ 可反推 $\omega$
2. **实现**：最小二乘拟合轨迹偏差
3. **优势**：无需额外硬件
4. **局限**：需要足够长的轨迹，低旋转时信噪比差

### 方法二：标记点姿态跟踪

从球面标记点跟踪旋转：

1. **原理**：跟踪标记点的 2D 运动，用 PnP 估计 3D 姿态变化
2. **实现**：SpinDOE 方法，用标记点阵列
3. **优势**：直接测量，精度高
4. **局限**：需要标记点，远距离标记点不可见

### 方法三：事件相机旋转检测

利用事件相机的高时间分辨率：

1. **原理**：球的旋转在事件相机上产生特征性事件流
2. **优势**：微秒级时间分辨率，不受运动模糊影响
3. **局限**：需要事件相机硬件，算法复杂

### 方法对比

| 维度 | Magnus 逆推 | 标记点跟踪 | 事件相机 |
|------|------------|-----------|---------|
| 精度 | 中 | 高 | 中-高 |
| 硬件需求 | 无额外 | 标记球 | 事件相机 |
| 实时性 | 中 | 中 | 高 |
| 远距离 | 差 | 差 | 好 |
| 低旋转 | 差 | 好 | 中 |

## 可用方案（Recipes）

| Recipe | 适用球类 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [trajectory-magnus-spin](recipes/trajectory-magnus-spin/RECIPE.md) | 乒乓球/网球 | Magnus 逆推 | intermediate | 否 | 需要长轨迹段 |
| [spindoe-marker-pose](recipes/spindoe-marker-pose/RECIPE.md) | 乒乓球 | 标记点跟踪 | advanced | 否 | SpinDOE 标记阵列 |
| [event-camera-spin](recipes/event-camera-spin/RECIPE.md) | 乒乓球 | 事件相机 | advanced | 否 | 微秒级时间分辨率 |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 数据不足 | 轨迹点/标记点不够 | 返回 insufficient_data |
| 估计不收敛 | 迭代超限 | 尝试不同初值或降低精度 |
| 低信噪比 | 旋转效应微弱 | 标记 low_confidence |
| 标记点丢失 | 跟踪中断 | 使用先验或放弃 |
| 事件流异常 | 数据格式错误 | 跳过异常段 |
