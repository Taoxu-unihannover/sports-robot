---
name: event-camera-spin
skill: ball-spin-estimator
description: 基于事件相机的球体旋转估计方案，使用 Ordinal Time Surface + 事件光流 + 角速度回归，支持低延迟 CNN 和高精度 CMax 双算法切换。
source:
  paper: "Gossard et al., Table tennis ball spin estimation with an event camera (CVPRW 2024, arXiv:2404.09870); Ace: An Elite Badminton Robot (Nature 2026)"
  paper_url: https://arxiv.org/abs/2404.09870
  repo: https://www.nature.com/articles/s41586-026-10338-5
code_availability:
  tubingen_event_spin: "论文有详细方法描述和伪代码，但未公开完整源码。核心算法（Ordinal Time Surface + 光流提取 + 角速度回归）可按论文复现。"
  ace_nature: "Sony Ace 系统闭源，Nature 论文仅描述架构和性能指标，无公开代码。"
sport: [table_tennis, badminton]
difficulty: advanced
requires_training: true
dependencies:
  - numpy>=1.20
  - opencv-python>=4.5
  - torch>=1.10
  - prophesee-driver (事件相机驱动)
stages:
  - id: calibrate
    description: "事件相机内参标定 + 时间同步校准"
  - id: detect_ball_region
    description: "帧相机/事件流检测球位置，确定 ROI"
  - id: compute_time_surface
    description: "Ordinal Time Surface 编码事件流"
  - id: extract_flow
    description: "从时间面梯度提取事件光流"
  - id: regress_omega
    description: "CNN 回归或 CMax 优化得到角速度"
performance:
  estimation_frequency_hz: "400-700"
  latency_ms: "2-10"
  note: "CNN 模式 2-3ms，CMax 模式约 10ms"
---

# Event Camera Spin — 事件相机旋转估计方案

## 来源

本 Recipe 综合了 Tübingen 大学 2024 CVPRW 工作的事件相机旋转估计方法论，以及 Sony Ace 系统中系统化的双算法（CNN + CMax）架构。

## 适用场景

- 乒乓球高速旋转检测（可达 3000 RPM）
- 需要微秒级时间分辨率的旋转估计
- 有事件相机硬件（如 iniVation DVS、Prophesee）的系统
- 需要实时旋转反馈的闭环控制

## 不适用场景

- 没有事件相机硬件
- 球转速很低（< 100 RPM），帧相机已足够
- 需要绝对旋转角度（而非角速度）

## 完整工作流（五阶段）

### 阶段一：事件相机标定

1. 使用标定板（棋盘格）对事件相机做内参标定
2. 与帧相机做时间同步校准（硬件触发或软件时间戳对齐）
3. 确定事件阈值参数（对比度灵敏度）

### 阶段二：球区域检测

1. 用帧相机或事件累积帧检测球的大致 2D 位置
2. 在事件流中裁剪球表面 ROI 区域
3. Ace 方案：使用 gaze-control 可转镜面跟踪球，保持球在视野中心

### 阶段三：Ordinal Time Surface 编码

将异步事件流编码为时间面——每个像素记录最近一次事件的时间戳：

```
TS(x, y) = max{t | event at (x, y, t) exists}
```

旋转的球表面纹理会产生特定的时间梯度模式。时间面的梯度方向与球表面运动方向相关。

### 阶段四：事件光流提取

从时间面的梯度中计算事件光流：

1. 计算时间面的空间梯度 ∇TS
2. 利用时间约束：光流 v 满足 ∇TS · v = -1
3. 在球表面 ROI 内聚合多个点的光流向量

### 阶段五：角速度回归

球表面光流场与角速度的几何约束：

$$\mathbf{v}_{\text{flow}} = \boldsymbol{\omega} \times \mathbf{r}$$

两种回归算法：

**低延迟 CNN（Ace 方案）**：
- 将事件流累积为短时窗（~1 ms）的事件帧
- 送入轻量 CNN 直接回归角速度
- 延迟约 2–3 ms
- 适合实时控制

**高精度 CMax（Ace 方案）**：
- 基于对比度最大化（Contrast Maximization）框架
- 搜索使事件对齐最优的旋转参数
- 精度更高但计算量更大（约 10 ms）
- 适合需要高精度角速度的场景

系统根据实时置信度在两种算法间切换。

## 使用方式

### 方式一：使用 EventCameraSpin 类

```python
from spin import EventCameraSpin

estimator = EventCameraSpin(
    ball_radius=0.02,
    focal_length=800.0,
    accumulation_window_ms=1.0,
)

result = estimator.estimate_angular_velocity(
    events=event_array,
    ball_center_2d=(320.0, 240.0),
    ball_center_3d=np.array([1.37, 0.0, 2.0]),
    ball_radius_px=50.0,
)
```

### 方式二：自定义 CNN 模型

需要训练事件帧 → 角速度的回归网络，参考 Ace 论文中的网络架构。

## 性能基准

| 指标 | CNN 模式 | CMax 模式 |
|------|---------|----------|
| 延迟 | 2–3 ms | ~10 ms |
| 估计频率 | 400–700 Hz | 100–200 Hz |
| 精度 | 中 | 高 |
| GPU 需求 | 是 | 否 |

## 设计亮点

| 设计决策 | 做法 | 动机 |
|----------|------|------|
| 双算法切换 | CNN (快) + CMax (准) | 平衡延迟与精度 |
| Time Surface 编码 | Ordinal TS | 保留时间信息，支持光流提取 |
| Gaze-control | 可转镜面跟踪球 | 保持球在视野中心，最大化事件密度 |
| 事件帧累积 | ~1ms 窗口 | 兼顾时间分辨率和事件密度 |
