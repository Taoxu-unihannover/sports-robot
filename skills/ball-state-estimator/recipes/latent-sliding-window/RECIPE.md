---
name: latent-sliding-window
skill: ball-state-estimator
description: LATENT 系统的滑窗平均速度方案，4 帧滑动窗口差分取平均，噪声方差降低为 1/3，实现简单有效。
source:
  paper: "LATENT: Learning Athletic Humanoid Tennis Skills from Imperfect Human Motion Data (Tsinghua / Galbot, 2026, arXiv:2603.12686)"
  paper_url: https://arxiv.org/abs/2603.12686
code_availability:
  latent: "LATENT 论文提到代码同步开源，但主要聚焦于人形机器人运动学习框架。滑窗平均速度是其中最简单的速度估计组件，本 Recipe 提供完整实现。"
sport: [table_tennis, badminton]
difficulty: beginner
requires_training: false
dependencies:
  - numpy>=1.20
stages:
  - id: configure_window
    description: "配置滑动窗口大小 N（默认 4）"
  - id: accumulate_positions
    description: "累积最近 N 帧位置"
  - id: compute_average_velocity
    description: "多帧差分取平均"
performance:
  noise_reduction: "1/(N-1) = 1/3 (N=4)"
  extra_latency_ms: "30 (N=4, dt=20ms)"
  note: "简单有效，但引入额外延迟且平滑掉加速度变化"
---

# LATENT Sliding Window — 滑窗平均速度方案

## 来源

本 Recipe 来自 LATENT 系统（清华/北大/Galbot 联合，2026），使用 4 帧滑动窗口平均速度，实现简单有效的速度估计。

## 适用场景

- 需要简单有效的速度估计
- 不需要外推能力
- 可容忍少量延迟（~30 ms）
- 50 Hz planner/control 循环

## 不适用场景

- 需要检测丢失时外推（滑窗需要连续帧）
- 需要精确的加速度信息（平均操作平滑掉加速度变化）
- 需要零延迟

## 完整工作流（三阶段）

### 阶段一：配置窗口大小

| 参数 | LATENT 配置 | 说明 |
|------|-----------|------|
| window_size (N) | 4 | 4 帧滑窗 |
| dt | 20 ms | 50 Hz 控制频率 |
| dim | 3 | 3D 位置 |

窗口大小 N 的权衡：
- N 越大 → 噪声越低（$1/(N-1)$），但延迟越大（$(N-1)\Delta t/2$）
- N=4 → 噪声降至 1/3，额外延迟 30 ms

### 阶段二：累积位置

1. 维护最近 N 帧的位置队列
2. 新位置入队，旧位置出队
3. 帧数不足 N 时降级为有限差分

### 阶段三：计算平均速度

$$\hat{\mathbf{v}}_t = \frac{1}{N-1} \sum_{i=1}^{N-1} \frac{\mathbf{p}_{t-i+1} - \mathbf{p}_{t-i}}{\Delta t}$$

等价于对最近 4 帧的逐帧差分速度取平均。

**噪声分析**：
- 单帧差分噪声方差：$\sigma_v^2 = 2\sigma_p^2 / \Delta t^2$
- N 帧平均噪声方差：$2\sigma_p^2 / ((N-1)\Delta t^2)$
- 当 $\Delta t = 20$ ms、$\sigma_p = 5$ mm 时：
  - 单帧差分：$\sigma_v \approx 0.35$ m/s
  - 4 帧平均：$\sigma_v \approx 0.20$ m/s

## 使用方式

```python
from filter import SlidingWindowVelocity
import numpy as np

swv = SlidingWindowVelocity(window_size=4, dt=0.02, dim=3)

for position_3d in trajectory:
    state = swv.update_3d(*position_3d)
    if state is not None:
        print(f"位置: ({state.x:.3f}, {state.y:.3f}, {state.z:.3f})")
        print(f"速度: ({state.vx:.2f}, {state.vy:.2f}, {state.vz:.2f})")
```

## 性能基准

| 指标 | 值 |
|------|-----|
| 噪声降低 | 1/3（N=4） |
| 额外延迟 | ~30 ms（N=4, dt=20ms） |
| 实现复杂度 | 极低 |
| 外推能力 | ❌ |
| 调参需求 | 仅窗口大小 N |

## 设计亮点

| 设计决策 | 做法 | 动机 |
|----------|------|------|
| 滑窗平均 | N=4 帧差分取平均 | 噪声降至 1/3 |
| 简单实现 | 无需矩阵运算 | 极低计算开销 |
| 降级策略 | 帧数不足时用有限差分 | 避免冷启动问题 |
| 无模型假设 | 不假设运动模型 | 适用于任意运动类型 |
