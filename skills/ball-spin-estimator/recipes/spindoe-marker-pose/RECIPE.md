---
name: spindoe-marker-pose
skill: ball-spin-estimator
description: 基于 SpinDOE 的带标记球旋转估计方案，通过 PnP 姿态估计和相邻帧相对旋转计算角速度。无需事件相机，适合研发标定。
source:
  paper: "Gossard et al., SpinDOE: A ball spin estimation method for table tennis robot (IROS 2023, arXiv:2303.03879)"
  paper_url: https://arxiv.org/abs/2303.03879
  repo: https://github.com/Tubingen-Neuro/CognitiveSystems (课题组仓库)
code_availability:
  spindoe: "论文提到 project page 提供数据集（轨迹+旋转标注），但 SpinDOE 核心代码未完全开源。CNN 点检测 + 几何哈希 + 旋转回归的流程可按论文复现。"
  dataset: "公开数据集：乒乓球轨迹含位置和旋转标注，可在 project page 下载。"
sport: [table_tennis]
difficulty: intermediate
requires_training: false
dependencies:
  - numpy>=1.20
  - opencv-python>=4.5
stages:
  - id: prepare_marker_ball
    description: "制作带已知标记的测试球（CAD stencil）"
  - id: detect_markers
    description: "检测球面上的标记点 2D 坐标"
  - id: solve_pnp
    description: "PnP 求解球姿态 R_t"
  - id: compute_omega
    description: "相邻帧相对旋转 → 角速度"
performance:
  estimation_frequency_hz: "与帧率相同 (125-200)"
  note: "需要标记可见，遮挡时估计失败"
---

# SpinDOE Marker Pose — 带标记球旋转估计方案

## 来源

本 Recipe 来自 SpinDOE（Spin Detection and Estimation）项目，利用球表面的标记点做几何姿态估计来推断角速度。

## 适用场景

- 研发阶段的旋转标定和验证
- 离线轨迹分析中的旋转标注
- 生成旋转 ground truth 数据
- 评估其他旋转估计算法的精度

## 不适用场景

- 正式比赛（不允许额外标记）
- 球表面无可见标记
- 标记被严重遮挡

## 完整工作流（四阶段）

### 阶段一：准备标记球

1. 使用 SpinDOE 提供的 CAD stencil 制作带已知标记的测试球
2. 标记点在球面上的 3D 坐标需精确测量（球的直径 40mm，标记尺寸可测量）
3. 至少需要 4 个非共面标记点
4. 推荐使用 6–8 个标记点以获得更鲁棒的估计

### 阶段二：标记点检测

1. 在检测到球之后，进一步检测球面上的标记点
2. 可使用角点检测、模板匹配或语义分割
3. 输出每个标记点的 2D 像素坐标
4. 遮挡处理：部分标记不可见时，使用 RANSAC + PnP 鲁棒估计

### 阶段三：PnP 姿态求解

1. 将检测到的 2D 标记点与 3D 模型中的已知点做匹配
2. 使用 `cv2.solvePnP` 求解球姿态 $\mathbf{R}_t$
3. Rodrigues 向量转旋转矩阵
4. 遮挡鲁棒：使用 RANSAC 剔除误匹配

### 阶段四：角速度计算

从连续两帧的球姿态计算角速度：

1. 计算相对旋转：$\Delta\mathbf{R} = \mathbf{R}_{t+1}\mathbf{R}_t^{-1}$
2. 提取旋转轴和角度：$\text{axis}(\Delta\mathbf{R})$, $\text{angle}(\Delta\mathbf{R})$
3. 转换为角速度：$\boldsymbol{\omega} = \text{axis} \cdot \text{angle} / \Delta t$

## 使用方式

```python
from spin import MarkerPoseSpin
import numpy as np

K = np.array([[800, 0, 320], [0, 800, 240], [0, 0, 1]], dtype=float)

estimator = MarkerPoseSpin(
    ball_radius=0.02,
    camera_matrix=K,
)

for frame_idx, (pts_2d, timestamp) in enumerate(frames):
    result = estimator.update(pts_2d, marker_3d_model, timestamp)
    if result and result.confidence > 0.3:
        print(f"RPM: {result.spin_rpm:.0f}")
```

## 性能基准

| 指标 | 值 |
|------|-----|
| 估计频率 | 与帧率相同 |
| 标记点需求 | ≥ 4 个非共面 |
| 遮挡鲁棒 | 中（RANSAC 辅助） |
| 硬件需求 | 标记球 + 帧相机 |
| 比赛可用 | ❌ |

## 设计亮点

| 设计决策 | 做法 | 动机 |
|----------|------|------|
| CAD stencil | 提供标准标记模板 | 确保标记位置精确已知 |
| RANSAC + PnP | 鲁棒姿态估计 | 处理部分遮挡 |
| 相邻帧差分 | delta_R → omega | 简单有效的角速度计算 |
| 开放数据集 | 轨迹 + 旋转标注 | 作为其他方法的 ground truth |
