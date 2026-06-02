---
name: ball-geometry
description: 用于球类运动的 3D 几何重建，从多视角 2D 坐标或双目深度恢复球的 3D 位置。支持 DLT（直接线性变换）、Midpoint（中点法）和 StereoDepth（双目深度图）三种方法，支持任意数量相机。适用于用户需要实现 3D 重建、多视角三角化、双目深度、相机标定、立体视觉；不用于单目深度估计或 SLAM。
when_to_use: 用户提到 3D 重建、三角化、多视角、DLT、triangulation、3D position、立体视觉、相机标定、双目深度、ball geometry、stereo depth 时触发。
version: 2.0.0
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
      enum: [DLT, midpoint, stereo_depth]
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

当用户需要从多视角 2D 坐标或双目深度恢复球的 3D 空间位置时使用。典型场景：

- 双目/多目相机系统的 3D 定位
- 球类运动轨迹的 3D 可视化
- 击球点空间位置分析
- 为机器人控制提供 3D 目标位置
- 移动机器人机载双目深度感知

不适用于：单目深度估计、SLAM、点云配准。

## 输入约束

- DLT / Midpoint 方法：至少 2 个视角的 2D 坐标，每个视角需要对应的 3x4 投影矩阵 P = K[R|t]
- StereoDepth 方法：需要双目相机的基线距离、焦距参数，以及左右图的视差值
- 投影矩阵需预先通过相机标定获得
- 2D 坐标需来自同一时刻的同步帧

## 执行步骤

### 步骤 1：输入校验

- 动作：检查视角数 >= 2（DLT/Midpoint）或视差有效（StereoDepth），投影矩阵维度正确
- 输入：points_2d, projection_matrices
- 成功标准：视角数 >= 2，矩阵维度 (3, 4)
- 失败处理：视角不足返回 `calibration_missing: insufficient_views`

### 步骤 2：三角化计算

- 动作：根据 method 选择 DLT / Midpoint / StereoDepth 算法
- 输入：2D 坐标 + 投影矩阵（DLT/Midpoint）或视差 + 相机参数（StereoDepth）
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

## 可用方法与代表性系统

本 Skill 的三种方法分别对应球类机器人领域三大代表性系统的 3D 定位路线：

### 方法一：DLT 三角化 — DeepMind 路线

DeepMind 乒乓球系统采用两台 Ximea 高速相机（125 FPS），硬件同步触发。2D 检测使用 27k 参数时序 CNN（Raw Bayer 输入），三角化用经典 DLT：

1. 对每个 2D 检测点 $(u_i, v_i)$，根据投影矩阵 $\mathbf{P}_i = \mathbf{K}_i[\mathbf{R}_i | \mathbf{t}_i]$ 构建线性约束 $\mathbf{A}\mathbf{X} = 0$
2. 对 $\mathbf{A}$ 做 SVD 分解，取最小奇异值对应的右奇异向量作为 3D 点齐次坐标
3. DLT 本身 < 0.1 ms，瓶颈在 2D 检测 CNN 推理

**关键设计**：对侧相机放置（基线 2.74m = 乒乓球台宽度），减少三角化偏差约 10x。3D 定位精度约 3 mm。

**适用**：固定安装、严格标定、追求最高精度的场景。

### 方法二：DLT 多目冗余三角化 — Ace 路线

Sony Ace 系统使用 9 台 APS 全局快门相机（200 Hz 同步），覆盖整个球场。每台相机独立做 2D 检测，多视角 2D 点通过 DLT 三角化得到 3D 位置。9 台相机的冗余设计使得即使部分相机遮挡或检测丢失，仍能维持稳定定位。

**关键设计**：9 相机冗余 → 遮挡鲁棒；3D 定位精度 3.0 mm，感知延迟 10.2 ms。

**适用**：广域覆盖、多相机冗余、高可靠性要求的场景。代价是硬件成本极高（9 相机 + FPGA + 专用计算）。

### 方法三：双目深度图 — ETH 路线

ETH 腿足羽毛球系统面向移动平台，利用 Stereolabs ZED X 双目相机的硬件深度图，直接从 2D 检测点读取 3D 坐标，而非通过 DLT 三角化。ZED X 内置立体匹配，输出 30 FPS 深度图，省去了手动标定外参的步骤。

**关键设计**：HSV 颜色过滤 → ZED X 硬件深度 → map frame 转换 → EKF。双目深度精度约 1–3 cm，不如多目 DLT（约 3 mm），但部署简便，适合机载实时运行。

**适用**：移动平台、机载计算、快速部署的场景。

### 方法对比

| 维度 | DLT 双目 (DeepMind) | DLT 多目 (Ace) | 双目深度 (ETH) |
|------|---------------------|----------------|----------------|
| 精度 | ~3 mm | 3.0 mm | 1–3 cm |
| 相机数 | 2 | 9 | 1（双目） |
| 标定要求 | 严格外参标定 | 严格外参标定 | 内置标定 |
| 遮挡鲁棒 | 低 | 高（9 路冗余） | 低 |
| 部署难度 | 中 | 极高 | 低 |
| 硬件成本 | 中 | 极高 | 低 |
| 适合平台 | 固定安装 | 固定安装 | 移动机载 |

## 可用方案（Recipes）

| Recipe | 适用球类 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [deepmind-dlt-triangulation](recipes/deepmind-dlt-triangulation/RECIPE.md) | 乒乓球 | DLT 双目 (DeepMind) | intermediate | 否 | 3mm 精度，DLT <0.1ms |
| [ace-multi-camera-dlt](recipes/ace-multi-camera-dlt/RECIPE.md) | 羽毛球 | DLT 9目 (Ace) | advanced | 否 | 3mm 精度，10.2ms 延迟 |
| [eth-stereo-depth](recipes/eth-stereo-depth/RECIPE.md) | 羽毛球 | 双目深度 (ETH) | beginner | 否 | 1-3cm 精度，30FPS 深度 |

选择建议：
- 固定安装 + 高精度 → DLT 双目/多目
- 移动平台 + 快速部署 → 双目深度 (ZED X)
- 广域覆盖 + 高可靠 → DLT 多目冗余 (9+ 相机)

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 视角不足 | len(points_2d) < 2 | 返回 `calibration_missing: insufficient_views` |
| 矩阵维度错误 | P.shape != (3,4) | 返回 `config_error: invalid_projection_matrix` |
| 矩阵奇异 | SVD 失败 | 返回 None |
| 重投影误差过大 | error > threshold | 标记 low_confidence，仍返回结果 |
| 视差为零 | disparity ≈ 0 | 返回 `config_error: zero_disparity` |
