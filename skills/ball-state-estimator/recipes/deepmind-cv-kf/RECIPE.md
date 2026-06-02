---
name: deepmind-cv-kf
skill: ball-state-estimator
description: DeepMind 乒乓球系统的 CV Kalman Filter 方案，恒速模型 + 125Hz 感知频率，速度通过预测-更新循环隐式估计。
source:
  paper: "D'Ambrosio et al., Achieving Human Level Competitive Robot Table Tennis (DeepMind, 2024, arXiv:2408.03906)"
  paper_url: https://arxiv.org/abs/2408.03906
  project_page: https://sites.google.com/view/competitive-robot-table-tennis
code_availability:
  deepmind: "DeepMind 乒乓球系统闭源，论文仅描述系统架构和性能指标，无公开代码。CV Kalman Filter 是标准算法，可按论文参数独立实现。"
sport: [table_tennis]
difficulty: beginner
requires_training: false
dependencies:
  - numpy>=1.20
stages:
  - id: configure_kf
    description: "配置 CV Kalman Filter 参数（dt, Q, R）"
  - id: predict_update_loop
    description: "125Hz 预测-更新循环"
  - id: handle_detection_loss
    description: "检测丢失时仅做预测外推"
performance:
  estimation_hz: 125
  note: "速度估计噪声由协方差 P 控制，检测丢失时可外推"
---

# DeepMind CV KF — 恒速 Kalman Filter 方案

## 来源

本 Recipe 来自 Google DeepMind 的乒乓球系统，使用 CV（Constant Velocity）Kalman Filter 做状态估计。状态向量 $[\mathbf{p}, \mathbf{v}]$，速度通过预测-更新循环隐式估计。

## 适用场景

- 球的飞行中段（近似匀速运动）
- 需要实时速度估计
- 检测丢失时需要外推
- 追求估计可解释性（可检查协方差矩阵 P）

## 不适用场景

- 高变速运动（应使用 CA 或 EKF）
- 非线性运动（含空气阻力和重力，应使用 EKF）

## 完整工作流（三阶段）

### 阶段一：配置 KF 参数

| 参数 | DeepMind 配置 | 说明 |
|------|-------------|------|
| dt | 1/125 = 0.008s | 125Hz 感知频率 |
| model | CV | 恒速模型 |
| process_noise (Q) | 系统辨识 | 控制预测步信任度 |
| measurement_noise (R) | 基于实测 | 控制观测步信任度 |

### 阶段二：预测-更新循环

1. **预测步**：$\hat{\mathbf{x}}_{k|k-1} = \mathbf{F}\hat{\mathbf{x}}_{k-1|k-1}$
   - 状态转移矩阵 F 编码恒速运动模型
   - 预测步给出的速度估计是上一时刻速度的延续
2. **更新步**：$\hat{\mathbf{x}}_{k|k} = \hat{\mathbf{x}}_{k|k-1} + \mathbf{K}_k(\mathbf{z}_k - \mathbf{H}\hat{\mathbf{x}}_{k|k-1})$
   - 观测仅包含位置
   - Kalman 增益自动将位置残差分配到位置和速度

### 阶段三：检测丢失处理

1. 检测丢失时跳过更新步，仅做预测
2. 协方差 P 持续增大（不确定性增加）
3. 预测步仍可给出合理的位置和速度外推
4. 检测恢复后 P 重新收敛

## 使用方式

```python
from filter import BallKalmanFilter

kf = BallKalmanFilter(
    dt=1.0/125.0,
    dim=3,
    model="CV",
    process_noise=1.0,
    measurement_noise=10.0,
)

for position_3d in trajectory:
    kf.predict()
    if position_3d is not None:
        state = kf.update_3d(*position_3d)
    else:
        state = kf.predict()

    print(f"位置: ({state.x:.3f}, {state.y:.3f}, {state.z:.3f})")
    print(f"速度: ({state.vx:.2f}, {state.vy:.2f}, {state.vz:.2f})")
```

## 性能基准

| 指标 | 值 |
|------|-----|
| 感知频率 | 125 Hz |
| 速度估计方式 | KF 内隐（预测-更新） |
| 检测丢失外推 | ✅ |
| 可解释性 | 高（可检查 P 矩阵） |
| 调参需求 | Q、R 矩阵 |

## 设计亮点

| 设计决策 | 做法 | 动机 |
|----------|------|------|
| CV 模型 | 恒速运动假设 | 乒乓球飞行中段近似匀速 |
| 内隐速度 | 预测-更新循环 | 速度噪声由 P 控制，非差分放大 |
| 检测丢失外推 | 仅 predict 不 update | 维持状态估计连续性 |
| 协方差监控 | 检查 P 对角元 | 判断估计是否可靠 |
