---
name: eth-stereo-depth
skill: ball-geometry
description: ETH 腿足羽毛球系统的双目深度方案，使用 ZED X 硬件深度图直接获取 3D 坐标，免外参标定，适合移动平台机载实时运行。
source:
  paper: "Dipner et al., One-Shot Badminton Shuttle Detection for Mobile Robots (ETH RSL, 2026, arXiv:2603.06691)"
  paper_url: https://arxiv.org/abs/2603.06691
  project_page: https://sites.google.com/leggedrobotics.com/shuttlecockfinder
code_availability:
  shuttlecockfinder: "ETH RSL 开源了羽毛球检测数据集和 YOLOv8 检测模型（project page 可下载）。EKF 状态估计和深度图定位部分未开源，但可按论文复现。"
sport: [badminton]
difficulty: beginner
requires_training: false
dependencies:
  - numpy>=1.20
  - pyzed (ZED SDK)
  - opencv-python>=4.5
stages:
  - id: setup_zed
    description: "ZED X 双目相机初始化 + 深度模式配置"
  - id: detect_2d_hsv
    description: "HSV 颜色过滤检测球 2D 位置"
  - id: read_depth
    description: "从深度图读取 3D 坐标"
  - id: transform_to_map
    description: "相机坐标系 → map frame 转换"
performance:
  accuracy_cm: "1-3"
  depth_fps: 30
  note: "精度不如多目 DLT，但部署简便"
---

# ETH Stereo Depth — 双目深度图方案

## 来源

本 Recipe 来自 ETH Zurich RSL 的腿足羽毛球系统，面向移动平台，利用 Stereolabs ZED X 双目相机的硬件深度图直接获取 3D 坐标。

## 适用场景

- 移动机器人机载感知
- 快速部署（免外参标定）
- 机载计算（Jetson AGX Orin）
- 精度要求 1–3 cm 的场景

## 不适用场景

- 需要毫米级精度
- 远距离目标（> 5m，深度精度下降）
- 高速运动模糊严重

## 完整工作流（四阶段）

### 阶段一：ZED X 初始化

1. 连接 ZED X 双目相机
2. 配置深度模式（NEURAL / ULTRA / QUALITY）
3. 设置分辨率和帧率（默认 640x480 @ 30 FPS 深度）
4. 内置立体匹配，无需手动标定外参

### 阶段二：HSV 颜色检测

1. 用 HSV 颜色阈值过滤检测黄色羽毛球
2. HSV 方法延迟 < 2 ms
3. 输出球的 2D 像素坐标
4. 受控光照下效果良好，换场地需重新标定颜色范围

### 阶段三：深度读取

1. 从 ZED X 深度图中读取球位置对应的深度值
2. 结合 2D 像素坐标和相机内参，计算 3D 坐标
3. 深度精度约 1–3 cm（取决于距离和光照）

### 阶段四：坐标系转换

1. 利用机器人里程计将 3D 点从相机坐标系转换到 map frame
2. 为下游 EKF 状态估计提供 map frame 下的 3D 观测

## 使用方式

```python
from geometry import StereoDepthEstimator, CoordinateTransformer
import numpy as np

sd = StereoDepthEstimator(baseline=0.12, focal_length=800.0, cx=320.0)
depth = sd.disparity_to_depth(disparity_value)
point_3d = sd.stereo_to_3d(u_left, v_left, u_right, v_right)

T_cam_to_world = np.eye(4)
ct = CoordinateTransformer(T_cam_to_world)
point_world = ct.cam_to_world(point_3d)
```

## 性能基准

| 指标 | 值 |
|------|-----|
| 3D 精度 | 1–3 cm |
| 深度帧率 | 30 FPS |
| HSV 检测延迟 | < 2 ms |
| 总感知延迟 | 60–160 ms |
| 标定需求 | 内置（免外参标定） |
| 硬件成本 | 低（1 台 ZED X） |

## 设计亮点

| 设计决策 | 做法 | 动机 |
|----------|------|------|
| 硬件深度图 | ZED X 内置立体匹配 | 免外参标定，部署简便 |
| HSV 检测 | 颜色阈值过滤 | 延迟 < 2ms，适合机载 |
| 里程计转换 | cam → map frame | 统一到全局坐标系 |
| 机载计算 | Jetson AGX Orin | 移动平台实时运行 |
