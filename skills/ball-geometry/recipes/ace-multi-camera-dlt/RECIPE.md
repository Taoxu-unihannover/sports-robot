---
name: ace-multi-camera-dlt
skill: ball-geometry
description: Sony Ace 羽毛球系统的 9-APS 多目 DLT 三角化方案，9 台全局快门相机 200Hz 同步，冗余设计实现遮挡鲁棒的高精度 3D 定位。
source:
  paper: "Ace: An Elite Badminton Robot (Sony AI, Nature 2026)"
  paper_url: https://www.nature.com/articles/s41586-026-10338-5
code_availability:
  ace: "Sony Ace 系统完全闭源，Nature 论文仅描述架构和性能指标，无公开代码。9-APS 多目 DLT 可按论文描述独立实现。"
sport: [badminton]
difficulty: advanced
requires_training: false
dependencies:
  - numpy>=1.20
  - opencv-python>=4.5
  - fpga-sdk (硬件同步)
stages:
  - id: calibrate_9cam
    description: "9 台 APS 相机内外参标定 + 硬件同步"
  - id: detect_2d_per_camera
    description: "每台相机独立轻量 CNN 2D 检测"
  - id: multi_view_dlt
    description: "多视角 DLT 三角化（≥2 视角即可）"
  - id: outlier_rejection
    description: "重投影误差剔除异常视角"
performance:
  accuracy_mm: 3.0
  latency_ms: 10.2
  camera_count: 9
  note: "9 相机冗余，部分遮挡仍可定位"
---

# Ace Multi-Camera DLT — 9-APS 多目三角化方案

## 来源

本 Recipe 来自 Sony Ace 羽毛球机器人系统，使用 9 台 APS 全局快门相机（200 Hz 同步），覆盖整个球场，实现遮挡鲁棒的高精度 3D 定位。

## 适用场景

- 广域覆盖的球类场地
- 需要高可靠性的 3D 定位（部分相机遮挡仍可工作）
- 固定安装的多相机系统
- 追求最高定位精度的比赛/研究场景

## 不适用场景

- 移动机器人（9 相机无法移动）
- 预算有限（9+ 相机 + FPGA 成本极高）
- 小范围场景（2 相机已足够）

## 完整工作流（四阶段）

### 阶段一：9 相机标定

1. 9 台 APS 全局快门相机以 200 Hz 同步采集
2. 覆盖整个球场，确保任意位置至少 2 台相机可见
3. 使用大型标定结构做内外参标定
4. FPGA 硬件同步确保所有相机时间戳对齐

### 阶段二：每台相机独立 2D 检测

1. 每台相机独立运行轻量 CNN 做 2D 检测
2. 输出球的像素坐标 + 置信度
3. 部分相机可能检测失败（遮挡、球不在视野内）

### 阶段三：多视角 DLT 三角化

1. 收集所有成功检测的相机的 2D 坐标
2. 至少 2 个视角即可三角化
3. 使用所有可用视角做 DLT（更多视角 → 更高精度）
4. 9 相机冗余设计：即使部分相机遮挡或检测丢失，仍能维持稳定定位

### 阶段四：异常视角剔除

1. 计算每个视角的重投影误差
2. 剔除重投影误差过大的异常视角
3. 用剩余视角重新三角化
4. 输出最终 3D 位置 + 精度估计

## 使用方式

```python
from geometry import Triangulator, CameraConfig
import numpy as np

cameras = [CameraConfig(f"cam{i}", ...) for i in range(9)]
tri = Triangulator(cameras, method="DLT")

points_2d = {"cam0": (u0, v0), "cam2": (u2, v2), "cam5": (u5, v5)}
point_3d = tri.triangulate(points_2d)
error = tri.reprojection_error(point_3d, points_2d)
```

## 性能基准

| 指标 | 值 |
|------|-----|
| 3D 定位精度 | 3.0 mm |
| 感知延迟 | 10.2 ms |
| 相机数量 | 9 |
| 帧率 | 200 Hz |
| 遮挡鲁棒 | 高（9 路冗余） |
| 硬件成本 | 极高 |

## 设计亮点

| 设计决策 | 做法 | 动机 |
|----------|------|------|
| 9 相机冗余 | 覆盖全球场 | 遮挡鲁棒 + 精度提升 |
| 全局快门 | APS 传感器 | 无卷帘畸变 |
| FPGA 同步 | 硬件触发 | 严格时间对齐 |
| 异常剔除 | 重投影误差过滤 | 提高定位可靠性 |
