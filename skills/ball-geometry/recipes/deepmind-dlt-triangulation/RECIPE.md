---
name: deepmind-dlt-triangulation
skill: ball-geometry
description: DeepMind 乒乓球系统的 DLT 双目三角化方案，两台 Ximea 高速相机硬件同步，经典 DLT SVD 求解 3D 位置。
source:
  paper: "D'Ambrosio et al., Achieving Human Level Competitive Robot Table Tennis (DeepMind, 2024, arXiv:2408.03906)"
  paper_url: https://arxiv.org/abs/2408.03906
  project_page: https://sites.google.com/view/competitive-robot-table-tennis
code_availability:
  deepmind: "DeepMind 乒乓球系统闭源，论文仅描述系统架构和性能指标，无公开代码。DLT 三角化是标准算法，可按论文参数独立实现。"
sport: [table_tennis]
difficulty: intermediate
requires_training: false
dependencies:
  - numpy>=1.20
  - opencv-python>=4.5
stages:
  - id: calibrate_cameras
    description: "双目相机外参标定（基线 2.74m 对侧放置）"
  - id: detect_2d
    description: "27k 参数时序 CNN 检测 2D 球心（Raw Bayer 输入）"
  - id: triangulate_dlt
    description: "DLT SVD 三角化得到 3D 位置"
  - id: validate_reprojection
    description: "重投影误差校验"
performance:
  accuracy_mm: 3.0
  dlt_latency_ms: 0.1
  total_latency_ms: "8-11"
  note: "瓶颈在 2D CNN 推理，DLT 本身 < 0.1ms"
---

# DeepMind DLT Triangulation — 双目 DLT 三角化方案

## 来源

本 Recipe 来自 Google DeepMind 的乒乓球系统，采用两台 Ximea 高速相机（125 FPS），硬件同步触发，DLT 三角化实现 3D 定位。

## 适用场景

- 固定安装的双目相机系统
- 追求最高 3D 定位精度（~3 mm）
- 乒乓球台等标准尺寸场景
- 有严格标定条件的实验室/比赛场地

## 不适用场景

- 移动机器人（相机位置不固定）
- 相机数量 > 2（应使用多目 DLT 方案）
- 无法做严格外参标定

## 完整工作流（四阶段）

### 阶段一：双目相机标定

1. 两台 Ximea 高速相机对侧放置，基线 2.74m（= 乒乓球台宽度）
2. 对侧放置减少三角化偏差约 10x（相比同侧放置）
3. 使用棋盘格标定板做内外参标定
4. 硬件同步触发确保两帧时间戳严格对齐

### 阶段二：2D 检测

1. 使用 27k 参数的时序 CNN
2. 直接处理 Raw Bayer 图像（跳过 demosaicing 节省约 1 ms）
3. 输出球的像素坐标 (u, v)

### 阶段三：DLT 三角化

1. 对每个 2D 检测点 $(u_i, v_i)$，根据投影矩阵 $\mathbf{P}_i = \mathbf{K}_i[\mathbf{R}_i | \mathbf{t}_i]$ 构建线性约束方程 $\mathbf{A}\mathbf{X} = 0$
2. 对 $\mathbf{A}$ 做 SVD 分解，取最小奇异值对应的右奇异向量作为 3D 点 $\mathbf{X}$ 的齐次坐标
3. DLT 本身 < 0.1 ms

### 阶段四：重投影校验

1. 将 3D 点反投影到各视角
2. 计算重投影误差
3. 误差过大时标记为低置信度

## 使用方式

```python
from geometry import Triangulator, CameraConfig
import numpy as np

cam0 = CameraConfig("cam0", 640, 480,
    K=np.array([[800, 0, 320], [0, 800, 240], [0, 0, 1]]),
    dist_coeffs=np.zeros(5), R=np.eye(3), t=np.array([0, 0, 0]))

cam1 = CameraConfig("cam1", 640, 480,
    K=np.array([[800, 0, 320], [0, 800, 240], [0, 0, 1]]),
    dist_coeffs=np.zeros(5), R=np.eye(3), t=np.array([2.74, 0, 0]))

tri = Triangulator([cam0, cam1], method="DLT")
point_3d = tri.triangulate({"cam0": (320.5, 240.3), "cam1": (315.2, 238.7)})
error = tri.reprojection_error(point_3d, {"cam0": (320.5, 240.3), "cam1": (315.2, 238.7)})
```

## 性能基准

| 指标 | 值 |
|------|-----|
| 3D 定位精度 | ~3 mm |
| DLT 延迟 | < 0.1 ms |
| 总感知延迟 | 8–11 ms |
| 相机数量 | 2 |
| 帧率 | 125 FPS |

## 设计亮点

| 设计决策 | 做法 | 动机 |
|----------|------|------|
| 对侧放置 | 基线 2.74m = 球台宽度 | 减少三角化偏差约 10x |
| Raw Bayer 输入 | 跳过 demosaicing | 节省约 1 ms |
| 硬件同步 | Ximea 触发线 | 确保时间戳严格对齐 |
| SVD 求解 | 最小奇异值对应解 | 数值稳定的 DLT 实现 |
