---
name: ball-state-estimator
description: 用于球类机器人的球状态估计，覆盖 CV/EKF/UKF 滤波、多传感器融合、延迟补偿和协方差管理。适用于用户需要实现球状态估计、卡尔曼滤波、EKF、UKF、传感器融合、延迟补偿；不用于飞行预测或旋转估计。
when_to_use: 用户提到状态估计、卡尔曼、EKF、UKF、传感器融合、延迟补偿、ball state、filtering、observation delay 时触发。
version: 1.1.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [observation, filter_state]
  properties:
    observation:
      type: object
      description: 观测数据
      properties:
        position_3d: { type: array }
        timestamp: { type: number }
        confidence: { type: number }
        sensor_id: { type: string }
    filter_state:
      type: object
      description: 当前滤波器状态
      properties:
        state: { type: array }
        covariance: { type: array }
        last_update_time: { type: number }
    filter_type:
      type: string
      enum: [cv, ekf, ukf]
      description: 滤波器类型，默认 ekf
    process_model:
      type: string
      enum: [constant_velocity, drag_model, drag_magnus]
      description: 过程模型，默认 drag_model
output_schema:
  type: object
  required: [state, covariance, innovation]
  properties:
    state:
      type: array
      description: 估计状态 [px,py,pz,vx,vy,vz] 或含旋转
    covariance:
      type: array
      description: 状态协方差矩阵
    innovation:
      type: object
      description: 新息（观测-预测差）
      properties:
        value: { type: array }
        mahalanobis_distance: { type: number }
    filter_health:
      type: string
      enum: [healthy, degraded, diverged]
---

# 球状态估计

## 何时使用

当用户需要从噪声观测中估计球的当前状态（位置、速度、旋转）时使用。典型场景：

- 从 3D 定位结果估计球速度
- 多传感器融合（多相机、IMU）
- 观测延迟补偿
- 为飞行预测提供初始状态

不适用于：飞行预测（用 ball-flight-model）、旋转估计（用 ball-spin-estimator）。

## 输入约束

- 观测必须包含时间戳和置信度
- 协方差矩阵必须对称正定
- 延迟补偿需要准确的延迟模型
- 新息门限用于剔除异常观测

## 执行步骤

### 步骤 1：延迟补偿

- 动作：将观测回溯到滤波器时间
- 输入：observation + delay_model
- 成功标准：补偿后时间戳与滤波器对齐
- 失败处理：延迟过大时标记 degraded

### 步骤 2：预测-更新

- 动作：执行 EKF/UKF/CV 的预测和更新步骤
- 输入：补偿后的观测 + filter_state
- 成功标准：新息在门限内，协方差合理
- 失败处理：新息超门限时拒绝观测

### 步骤 3：健康检查

- 动作：检查滤波器健康状态
- 输入：新息序列 + 协方差演化
- 成功标准：滤波器健康
- 失败处理：发散时重置滤波器

## 输出格式

```json
{
  "state": [1.2, 0.3, 0.8, 3.0, -1.0, -2.0],
  "covariance": [[0.001, 0, 0, 0, 0, 0], [0, 0.001, 0, 0, 0, 0], [0, 0, 0.002, 0, 0, 0], [0, 0, 0, 0.1, 0, 0], [0, 0, 0, 0, 0.1, 0], [0, 0, 0, 0, 0, 0.15]],
  "innovation": {
    "value": [0.02, -0.01, 0.03],
    "mahalanobis_distance": 1.2
  },
  "filter_health": "healthy"
}
```

## 可用方法与代表性系统

### 方法一：CV + KF — DeepMind 路线

DeepMind 使用最简单的恒速模型 + 卡尔曼滤波：

1. **过程模型**：$\dot p = v, \dot v = 0$（恒速假设）
2. **优势**：简单、快速、无需物理参数
3. **局限**：无法捕捉空气阻力和旋转效应
4. **适用**：乒乓球低速场景

### 方法二：EKF + 阻力模型 — ETH 路线

ETH 使用 EKF + 阻力模型估计羽毛球状态：

1. **过程模型**：含阻力的非线性动力学
2. **延迟补偿**：显式建模观测延迟
3. **性能**：400Hz 状态估计
4. **适用**：羽毛球高速场景

### 方法三：滑动窗口优化 — LATENT 路线

LATENT 使用滑动窗口优化：

1. **方法**：在时间窗口内联合优化状态序列
2. **优势**：更平滑、更准确
3. **局限**：计算量更大
4. **适用**：离线分析或低频场景

### 方法对比

| 维度 | CV+KF (DeepMind) | EKF+阻力 (ETH) | 滑动窗口 (LATENT) |
|------|-----------------|---------------|-------------------|
| 精度 | 低 | 高 | 最高 |
| 实时性 | 高 | 高 | 中 |
| 物理建模 | 无 | 阻力 | 完整 |
| 延迟补偿 | 简单 | 显式 | 隐式 |
| 适用频率 | 125Hz | 400Hz | < 100Hz |

## 可用方案（Recipes）

| Recipe | 适用球类 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [deepmind-cv-kf](recipes/deepmind-cv-kf/RECIPE.md) | 乒乓球 | CV+KF | beginner | 否 | 125Hz 简单滤波 |
| [eth-ekf-badminton](recipes/eth-ekf-badminton/RECIPE.md) | 羽毛球 | EKF+阻力 | intermediate | 否 | 400Hz 状态估计 |
| [latent-sliding-window](recipes/latent-sliding-window/RECIPE.md) | 乒乓球 | 滑动窗口 | advanced | 否 | 离线高精度 |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 观测延迟过大 | delay > threshold | 标记 degraded，使用预测值 |
| 新息超门限 | Mahalanobis > threshold | 拒绝观测，仅预测 |
| 协方差发散 | 对角元超限 | 重置滤波器 |
| 滤波器发散 | 健康检查失败 | 重置到上一可靠状态 |
| 多传感器冲突 | 融合结果不一致 | 降低冲突传感器权重 |
| 缺少观测 | 长时间无数据 | 仅预测，协方差增大 |
