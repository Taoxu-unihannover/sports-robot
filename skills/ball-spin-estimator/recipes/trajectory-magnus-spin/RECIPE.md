---
name: trajectory-magnus-spin
skill: ball-spin-estimator
description: 基于飞行轨迹和 Magnus 效应的旋转估计方案，通过物理拟合反解角速度。无需额外硬件，但精度有限，适合辅助验证。
source:
  method: "Magnus effect trajectory inversion + bounce velocity analysis"
  reference: "Wang et al., A Novel Trajectory-Based Ball Spin Estimation Method for Table Tennis Robot (IEEE TIE 2024)"
  reference_url: https://ieeexplore.ieee.org/document/10342178
code_availability:
  magnus_inversion: "基于物理模型的通用方法，无特定开源代码。本 Recipe 提供完整实现。"
  wang_trajectory_spin: "Wang et al. 2024 论文提出基于轨迹的旋转估计方法，代码未公开。"
sport: [table_tennis, tennis, badminton]
difficulty: beginner
requires_training: false
dependencies:
  - numpy>=1.20
  - scipy>=1.7
stages:
  - id: reconstruct_trajectory
    description: "获取高精度 3D 轨迹"
  - id: fit_flight_model
    description: "拟合含 Magnus 力的飞行模型"
  - id: invert_omega
    description: "从 Magnus 加速度反解角速度"
  - id: bounce_auxiliary
    description: "（可选）弹跳前后速度变化辅助估计"
performance:
  note: "精度低，Magnus 信号弱，适合辅助验证而非主要方法"
---

# Trajectory Magnus Spin — 轨迹倒推旋转方案

## 来源

本方案基于 Magnus 效应的物理原理，从球的飞行轨迹间接推断旋转。是唯一不需要额外硬件（事件相机或标记球）的旋转估计方法，但精度有限。

## 适用场景

- 无事件相机和标记球时的辅助旋转估计
- 弹跳旋转推断（上旋球弹跳后加速，下旋球减速）
- 离线轨迹分析中的旋转趋势估计
- 作为其他旋转估计方法的交叉验证

## 不适用场景

- 需要高精度旋转估计
- 位置噪声较大（> 5 mm）
- 短轨迹段（< 5 帧）
- 需要实时旋转反馈

## 完整工作流（四阶段）

### 阶段一：轨迹重建

1. 用多目系统或高帧率相机获取高精度 3D 轨迹
2. 位置精度需 < 5 mm（Magnus 信号才不被淹没）
3. 至少需要 5–10 帧连续轨迹

### 阶段二：飞行模型拟合

将轨迹拟合到含 Magnus 力的飞行模型：

$$\mathbf{a} = \mathbf{g} + \mathbf{a}_{\text{drag}} + \mathbf{a}_{\text{Magnus}}$$

其中：
- $\mathbf{a}_{\text{drag}} = -\frac{1}{2} C_D \rho A |\mathbf{v}| \mathbf{v} / m$
- $\mathbf{a}_{\text{Magnus}} = C_L \frac{4}{3}\pi r^3 \rho (\boldsymbol{\omega} \times \mathbf{v}) / m$

### 阶段三：反解角速度

1. 从轨迹中估计加速度（二阶差分或滤波后差分）
2. 减去重力和阻力加速度，得到 Magnus 加速度
3. 从 $\mathbf{a}_{\text{Magnus}} \propto \boldsymbol{\omega} \times \mathbf{v}$ 反解 $\boldsymbol{\omega}$
4. 使用梯度下降优化拟合

### 阶段四：弹跳辅助

旋转的球在弹跳时会产生切向速度变化：

1. 上旋球弹跳后水平速度增大
2. 下旋球弹跳后水平速度减小
3. 侧旋球弹跳后产生横向速度
4. 通过比较弹跳前后的速度变化估计旋转分量

## 使用方式

```python
from spin import TrajectoryMagnusSpin
import numpy as np

estimator = TrajectoryMagnusSpin(
    ball_radius=0.02,
    ball_mass=0.0027,
    lift_coefficient=0.2,
)

result = estimator.estimate(positions_3d, timestamps)

result = estimator.estimate_from_bounce(
    velocity_before=v_before,
    velocity_after=v_after,
    surface_normal=np.array([0.0, 0.0, 1.0]),
)
```

## 性能基准

| 指标 | 值 |
|------|-----|
| 精度 | 低（Magnus 信号弱） |
| 位置精度需求 | < 5 mm |
| 最小轨迹长度 | 5–10 帧 |
| 硬件需求 | 多目系统（已有） |
| 比赛可用 | ✅ |

## 根本局限

Magnus 力相对重力和阻力来说很小：
- 乒乓球 Magnus 加速度通常 < 1 m/s²
- 重力加速度为 9.8 m/s²
- 当位置误差为 5 mm 时，Magnus 效应的信号可能被噪声淹没
- 更适合作为辅助验证手段，而非主要旋转估计方法

## 设计亮点

| 设计决策 | 做法 | 动机 |
|----------|------|------|
| 物理拟合 | 含 Magnus 力的飞行模型 | 从轨迹物理约束反解旋转 |
| 弹跳辅助 | 弹跳前后速度差 | 独立于 Magnus 效应的旋转信息 |
| 梯度下降 | 数值优化 omega | 避免解析求解的奇异性 |
| 无额外硬件 | 仅需轨迹数据 | 零硬件成本的旋转估计 |
