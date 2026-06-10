---
name: ball-geometry
description: 用于球类机器人的多视角几何定位，覆盖双目立体视觉、DLT 三角化、PnP 位姿估计和多相机融合。适用于用户需要实现球 3D 定位、三角化、立体视觉、多相机融合；不用于 2D 检测或飞行预测。
when_to_use: 用户提到三角化、DLT、立体视觉、双目、多相机、3D 定位、PnP、triangulation、stereo、multi-camera 时触发。
version: 1.1.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [detections, camera_params]
  properties:
    detections:
      type: array
      description: 多相机检测结果
      items:
        type: object
        properties:
          camera_id: { type: string }
          pixel_x: { type: number }
          pixel_y: { type: number }
          confidence: { type: number }
    camera_params:
      type: array
      description: 相机内参和外参
      items:
        type: object
        properties:
          camera_id: { type: string }
          intrinsics: { type: array }
          extrinsics: { type: array }
    method:
      type: string
      enum: [dlt, stereo_disparity, pnp]
      description: 定位方法，默认 dlt
output_schema:
  type: object
  required: [position_3d, reprojection_error]
  properties:
    position_3d:
      type: array
      items: { type: number }
      description: 3D 位置 [x, y, z]
    reprojection_error:
      type: number
      description: 重投影误差（像素）
    covariance:
      type: array
      description: 3D 位置协方差矩阵
    valid_views:
      type: integer
      description: 有效视角数量
---

# 多视角几何与 3D 定位

## 何时使用

当用户需要从多个相机的 2D 检测结果中恢复球的 3D 位置时使用。典型场景：

- 双目/多目相机的球 3D 定位
- DLT 三角化
- 立体视差深度估计
- 多相机融合定位

不适用于：2D 检测（用 ball-detector）、飞行预测（用 ball-flight-model）。

## 输入约束

- 至少需要 2 个视角的检测结果才能三角化
- 相机参数必须经过标定
- 检测的像素坐标必须在图像范围内
- DLT 至少需要 2 个视角，PnP 至少需要 4 个点

## 执行步骤

### 步骤 1：视角匹配

- 动作：将多相机检测结果按时间戳对齐
- 输入：detections
- 成功标准：至少 2 个视角的检测可用
- 失败处理：视角不足时返回 insufficient_views

### 步骤 2：三角化

- 动作：根据 method 选择 DLT/立体视差/PnP
- 输入：对齐的检测 + 相机参数
- 成功标准：重投影误差 < 阈值（默认 2 像素）
- 失败处理：误差过大时标记 low_accuracy

### 步骤 3：不确定度估计

- 动作：根据重投影误差和几何配置估计 3D 不确定度
- 输入：三角化结果 + 相机配置
- 成功标准：协方差矩阵合理
- 失败处理：协方差异常时使用默认值

## 输出格式

```json
{
  "position_3d": [1.2, 0.3, 0.8],
  "reprojection_error": 0.8,
  "covariance": [[0.001, 0.0001, 0.0001], [0.0001, 0.001, 0.0001], [0.0001, 0.0001, 0.002]],
  "valid_views": 3
}
```

## 可用方法与代表性系统

### 方法一：DLT 三角化 — Ace/DeepMind 路线

DLT（Direct Linear Transform）是最常用的多视角三角化方法：

1. **原理**：将多视角投影方程构建为线性系统 $Ax = 0$
2. **求解**：SVD 分求解最小特征值对应的解
3. **优势**：简单、快速、无需初值
4. **局限**：对噪声敏感，需要好的几何配置

### 方法二：双目立体视差 — ETH 路线

ETH 使用 ZED X 立体相机的视差深度：

1. **原理**：左右图像匹配计算视差，转换为深度
2. **优势**：单设备、实时性好
3. **局限**：远距离精度下降

### 方法对比

| 维度 | DLT 三角化 | 立体视差 |
|------|-----------|---------|
| 相机数量 | ≥ 2 | 2（固定基线） |
| 精度 | 高（多视角） | 中（受基线限制） |
| 实时性 | 好 | 好 |
| 标定需求 | 内参+外参 | 内参+立体标定 |
| 远距离精度 | 取决于视角配置 | 下降明显 |

## 可用方案（Recipes）

| Recipe | 适用平台 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [ace-multi-camera-dlt](recipes/ace-multi-camera-dlt/RECIPE.md) | 多目 | DLT 三角化 | intermediate | 否 | 重投影误差 < 2px |
| [deepmind-dlt-triangulation](recipes/deepmind-dlt-triangulation/RECIPE.md) | 多目 | DLT 三角化 | intermediate | 否 | 125Hz 3D定位 |
| [eth-stereo-depth](recipes/eth-stereo-depth/RECIPE.md) | 双目 | 立体视差 | beginner | 否 | ZED X 100Hz |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 视角不足 | 有效视角 < 2 | 返回 insufficient_views |
| 重投影误差大 | error > threshold | 标记 low_accuracy |
| 标定参数缺失 | 相机参数不完整 | 使用默认参数并标记 |
| 时间戳不对齐 | 检测时间差过大 | 使用最近时间戳或插值 |
| 外点检测 | 像素坐标异常 | RANSAC 剔除外点 |
