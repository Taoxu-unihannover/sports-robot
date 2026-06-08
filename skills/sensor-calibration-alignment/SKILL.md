---
name: sensor-calibration-alignment
description: 用于球类机器人多传感器时空对齐与标定补偿，覆盖相机-IMU 外参标定、时间偏置估计、畸变校正、坐标系统一管理和在线偏置漂移补偿。适用于用户需要实现 Kalibr 标定、传感器时间同步、外参补偿、延迟校正、坐标链管理；不用于状态估计或飞行预测。
when_to_use: 用户提到时空对齐、Kalibr、标定补偿、外参、时间偏置、延迟校正、畸变校正、坐标系统一、sensor calibration、temporal alignment、extrinsics 时触发。
version: 1.0.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [observation, calibration_params]
  properties:
    observation:
      type: object
      description: 感知层原始观测
      properties:
        position_camera: { type: array, description: 相机坐标系下球位置 }
        timestamp: { type: number, description: 观测时间戳（秒） }
        sensor_id: { type: string, description: 传感器标识 }
    calibration_params:
      type: object
      description: 标定参数
      properties:
        extrinsics: { type: object, description: 外参变换 T_CI }
        time_offset: { type: number, description: 时间偏置 delta_t（秒） }
        intrinsics: { type: object, description: 内参 K, D }
    task:
      type: string
      enum: [spatial_align, temporal_align, undistort, full_compensate, update_bias]
      description: 对齐任务类型，默认 full_compensate
output_schema:
  type: object
  required: [aligned_observation, residual_diagnostics]
  properties:
    aligned_observation:
      type: object
      description: 对齐后的观测
      properties:
        position_world: { type: array, description: 世界坐标系下位置 }
        true_timestamp: { type: number, description: 校正后真实物理时刻 }
    residual_diagnostics:
      type: object
      description: 标定残差诊断
      properties:
        reprojection_error: { type: number, description: 重投影误差（像素） }
        temporal_residual: { type: number, description: 时间残差（毫秒） }
        calibration_confidence: { type: number, description: 标定置信度 [0,1] }
---

# 时空对齐与标定补偿

## 何时使用

当用户需要将多传感器观测统一到同一坐标系和时间基准时使用。典型场景：

- 空间对齐：将相机坐标系下的球位置变换到世界坐标系
- 时间对齐：补偿传感器时间偏置，还原真实物理时刻
- 畸变校正：消除镜头畸变对位置观测的影响
- 在线偏置漂移补偿：运行中持续精化外参和时间偏置
- 标定残差监控：检测标定是否过期

不适用于：状态估计（用 ball-state-estimator）、飞行预测（用 ball-flight-model）。

## 输入约束

- 外参变换必须是有效的 SE(3) 变换（4×4 齐次矩阵）
- 时间偏置通常在 ±100 ms 范围内，超出则标定可能失效
- 畸变校正需要有效的内参矩阵和畸变系数
- 坐标系命名必须统一：世界系(W)、场地系(C)、相机系(cam)、底盘系(base)、拍面系(ee)

## 执行步骤

### 步骤 1：空间对齐

- 动作：将相机坐标系下的球位置通过外参变换到世界坐标系
- 输入：position_camera, extrinsics T_WC
- 成功标准：变换后位置在合理物理范围内
- 失败处理：外参无效时返回 calibration_error

### 步骤 2：时间对齐

- 动作：将观测时间戳减去时间偏置，得到真实物理时刻
- 输入：timestamp, time_offset delta_t
- 成功标准：校正后时刻与系统时钟一致
- 失败处理：偏置过大时触发重新标定警告

### 步骤 3：畸变校正

- 动作：用内参将像素坐标反投影为归一化坐标
- 输入：pixel_position, intrinsics K, D
- 成功标准：校正后重投影误差 < 0.5 像素
- 失败处理：畸变系数无效时使用无畸变模型

### 步骤 4：残差诊断

- 动作：计算标定残差并评估标定质量
- 输入：对齐后观测 vs 预期值
- 成功标准：残差在可接受范围内
- 失败处理：残差持续偏大时触发重新标定

## 输出格式

```json
{
  "aligned_observation": {
    "position_world": [1.2, 0.5, 0.8],
    "true_timestamp": 0.2985
  },
  "residual_diagnostics": {
    "reprojection_error": 0.23,
    "temporal_residual": 1.2,
    "calibration_confidence": 0.95
  }
}
```

## 可用方法与代表性系统

### Kalibr 空间-时间联合标定

Kalibr 是 ETH ASL 开发的多传感器时空标定工具箱，核心能力：

1. **相机-IMU 外参标定**：同时估计 $T_{CI}$（相机到 IMU 变换）和时间偏置 $\delta_t$
2. **多相机外参标定**：估计相机间相对位姿 $T_{C_1C_2}$
3. **滚动快门校正**：估计滚动快门时间参数
4. **在线偏置漂移**：标定后外参仍有亚毫米级残差，需在线补偿

### 坐标系链管理

球类机器人典型坐标系链：

$$T_{W,ee} = T_{W,base} \cdot T_{base,shoulder} \cdot T_{shoulder,ee}$$

$$T_{W,cam} = T_{W,base} \cdot T_{base,cam}$$

所有坐标系显式命名，变换链通过 $T_{AB}$ 链式传递，避免隐式假设。

### 延迟建模

感知延迟不是固定值，而是一个分布：

- 均值：5–30 ms（取决于相机类型和处理管线）
- 抖动：2–5 ms（标准差）
- 1 ms 延迟在 10 m/s 球速下 = 1 cm 位置误差

### 方法对比

| 维度 | Kalibr 离线标定 | 在线偏置补偿 | 固定外参假设 |
|------|----------------|-------------|-------------|
| 精度 | 高（亚毫米级） | 中（可追踪漂移） | 低（漂移后失效） |
| 实时性 | 离线 | 在线 | 在线 |
| 适用阶段 | 部署前 | 运行中 | 仅短期 |
| 计算开销 | 大 | 小 | 无 |

## 可用方案（Recipes）

| Recipe | 适用场景 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [kalibr-camera-imu](recipes/kalibr-camera-imu/RECIPE.md) | 相机-IMU 联合标定 | Kalibr | intermediate | 否 | 重投影误差 < 0.5 px |
| [gatech-async-multi-camera](recipes/gatech-async-multi-camera/RECIPE.md) | 异步多相机融合 | Georgia Tech 异步VIO | advanced | 否 | 丢帧50%退化<15% |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 外参无效 | 变换矩阵非 SE(3) | 返回 calibration_error |
| 时间偏置过大 | abs(delta_t) > 100 ms | 触发重新标定警告 |
| 畸变校正失败 | 畸变系数异常 | 使用无畸变模型 |
| 标定过期 | 残差持续偏大 | 触发重新标定流程 |
| 坐标系不一致 | 命名冲突 | 使用统一命名规范 |
