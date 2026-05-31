---
name: ball-filter
description: 用于球类运动的状态估计 Kalman 滤波器，对含噪 2D/3D 观测做时域平滑并估计速度/加速度。支持 CV（恒速）、CA（恒加速）模型和 EKF（含空气阻力）。适用于用户需要实现 Kalman 滤波、状态估计、轨迹预测、速度估计；不用于信号处理中的频域滤波或图像滤波。
when_to_use: 用户提到 Kalman 滤波、状态估计、速度估计、轨迹预测、EKF、ball filter、motion model、恒速模型时触发。
version: 1.0.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [measurement]
  properties:
    measurement:
      type: array
      description: 2D [x, y] 或 3D [x, y, z] 观测值
    dt:
      type: number
      description: 时间步长，默认 0.008 (125Hz)
    model:
      type: string
      enum: [CV, CA]
      description: 运动模型，默认 CV
output_schema:
  type: object
  required: [x, y, z, vx, vy, vz]
  properties:
    x: { type: number }
    y: { type: number }
    z: { type: number }
    vx: { type: number }
    vy: { type: number }
    vz: { type: number }
    ax: { type: number }
    ay: { type: number }
    az: { type: number }
---

# 球类 Kalman 滤波器

## 何时使用

当用户需要对含噪的球类位置观测做时域平滑，并估计无法直接观测的速度/加速度时使用。典型场景：

- 平滑检测器输出的抖动 2D 坐标
- 估计球的飞行速度用于击球时机预测
- 在短暂遮挡期间用运动模型外推位置
- 融合多传感器观测（视觉 + IMU）

不适用于：信号频域滤波、图像平滑滤波、非时序数据去噪。

## 输入约束

- 观测为 2D [x, y] 或 3D [x, y, z] 数值数组
- 需要合理的 dt（时间步长）匹配实际帧率
- CV 模型适用于匀速运动（乒乓球飞行中段）
- CA 模型适用于变速运动（羽毛球受空气阻力）
- EKF 适用于非线性运动（含空气阻力和重力）

## 执行步骤

### 步骤 1：预测（Predict）

- 动作：用运动模型从上一时刻状态预测当前状态
- 输入：上一时刻状态 x_{k-1}，协方差 P_{k-1}
- 成功标准：输出预测状态 x_{k|k-1} 和预测协方差 P_{k|k-1}
- 失败处理：未初始化时使用初始状态（零均值，大协方差）

### 步骤 2：更新（Update）

- 动作：用新观测修正预测值，计算 Kalman 增益
- 输入：观测 z_k，预测状态 x_{k|k-1}
- 成功标准：输出后验状态 x_{k|k}，协方差 P_{k|k} 减小
- 失败处理：观测缺失时跳过更新，仅做预测

### 步骤 3：外推预测

- 动作：用当前状态预测未来 t 秒后的位置
- 输入：当前状态 x，预测时间 t
- 成功标准：输出未来位置
- 失败处理：未初始化时返回 None

## 输出格式

```json
{
  "x": 1.23, "y": -0.45, "z": 2.10,
  "vx": 3.5, "vy": -1.2, "vz": -0.8,
  "ax": 0.0, "ay": 0.0, "az": 0.0
}
```

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 未初始化 | initialized == False | 使用初始状态做预测 |
| 观测缺失 | measurement is None | 跳过 update，仅 predict |
| 协方差发散 | P 矩阵对角元过大 | 重置滤波器 |
| 模型不匹配 | 残差异常大 | 增大 measurement_noise 或切换模型 |
