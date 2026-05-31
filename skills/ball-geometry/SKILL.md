---
name: ball-geometry
description: 用于球类运动的 3D 几何重建，从多视角 2D 坐标通过三角化恢复球的 3D 位置。支持 DLT（直接线性变换）和 Midpoint（中点法）两种方法，支持任意数量相机。适用于用户需要实现 3D 重建、多视角三角化、相机标定、立体视觉；不用于单目深度估计或 SLAM。
when_to_use: 用户提到 3D 重建、三角化、多视角、DLT、triangulation、3D position、立体视觉、相机标定、ball geometry 时触发。
version: 1.0.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [points_2d, projection_matrices]
  properties:
    points_2d:
      type: array
      description: 各相机视角的 2D 坐标 [[x0,y0], [x1,y1], ...]
    projection_matrices:
      type: array
      description: 各相机的 3x4 投影矩阵 [P0, P1, ...]
    method:
      type: string
      enum: [DLT, midpoint]
      description: 三角化方法，默认 DLT
output_schema:
  type: object
  required: [x, y, z]
  properties:
    x: { type: number, description: 3D X 坐标 }
    y: { type: number, description: 3D Y 坐标 }
    z: { type: number, description: 3D Z 坐标 }
    reprojection_error: { type: number, description: 重投影误差 }
---

# 球类 3D 几何重建

## 何时使用

当用户需要从多视角 2D 坐标恢复球的 3D 空间位置时使用。典型场景：

- 双目/多目相机系统的 3D 定位
- 球类运动轨迹的 3D 可视化
- 击球点空间位置分析
- 为机器人控制提供 3D 目标位置

不适用于：单目深度估计、SLAM、点云配准。

## 输入约束

- 至少 2 个视角的 2D 坐标
- 每个视角需要对应的 3x4 投影矩阵 P = K[R|t]
- 投影矩阵需预先通过相机标定获得
- 2D 坐标需来自同一时刻的同步帧

## 执行步骤

### 步骤 1：输入校验

- 动作：检查视角数 >= 2，投影矩阵维度正确
- 输入：points_2d, projection_matrices
- 成功标准：视角数 >= 2，矩阵维度 (3, 4)
- 失败处理：视角不足返回 `calibration_missing: insufficient_views`

### 步骤 2：三角化计算

- 动作：根据 method 选择 DLT 或 Midpoint 算法
- 输入：2D 坐标 + 投影矩阵
- 成功标准：输出 3D 坐标 (x, y, z)
- 失败处理：矩阵奇异返回 None

### 步骤 3：重投影校验

- 动作：将 3D 点反投影到各视角，计算重投影误差
- 输入：3D 坐标 + 投影矩阵 + 原始 2D 坐标
- 成功标准：重投影误差 < 阈值（默认 5 像素）
- 失败处理：误差过大标记为低置信度

## 输出格式

```json
{
  "x": 1.23,
  "y": -0.45,
  "z": 2.10,
  "reprojection_error": 1.2
}
```

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 视角不足 | len(points_2d) < 2 | 返回 `calibration_missing: insufficient_views` |
| 矩阵维度错误 | P.shape != (3,4) | 返回 `config_error: invalid_projection_matrix` |
| 矩阵奇异 | SVD 失败 | 返回 None |
| 重投影误差过大 | error > threshold | 标记 low_confidence，仍返回结果 |
