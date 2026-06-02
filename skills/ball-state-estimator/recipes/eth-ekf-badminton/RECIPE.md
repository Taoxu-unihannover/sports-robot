---
name: eth-ekf-badminton
skill: ball-state-estimator
description: ETH 腿足羽毛球系统的 EKF 方案，含空气阻力和重力的非线性运动模型，400Hz 状态估计频率，60Hz 感知输入。
source:
  paper: "Dipner et al., One-Shot Badminton Shuttle Detection for Mobile Robots (ETH RSL, 2026, arXiv:2603.06691)"
  paper_url: https://arxiv.org/abs/2603.06691
  project_page: https://sites.google.com/leggedrobotics.com/shuttlecockfinder
code_availability:
  shuttlecockfinder: "ETH RSL 开源了羽毛球检测数据集和 YOLOv8 检测模型。EKF 状态估计部分未开源，但论文描述了运动模型和参数，可按论文复现。"
sport: [badminton]
difficulty: intermediate
requires_training: false
dependencies:
  - numpy>=1.20
stages:
  - id: system_identification
    description: "系统辨识获取物理参数（阻力系数、升力系数）"
  - id: configure_ekf
    description: "配置 EKF 参数（dt=1/400, Q, R, drag）"
  - id: high_rate_predict
    description: "400Hz 预测步（远高于 60Hz 感知）"
  - id: low_rate_update
    description: "60Hz 更新步（感知数据到达时）"
performance:
  estimation_hz: 400
  perception_hz: 60
  note: "EKF 400Hz 运行，感知 60Hz 输入，检测丢失时靠预测维持"
---

# ETH EKF Badminton — 含空气阻力 EKF 方案

## 来源

本 Recipe 来自 ETH Zurich RSL 的腿足羽毛球系统，使用 EKF（Extended Kalman Filter）做状态估计。预测步使用含空气阻力和重力的非线性运动模型，而非简单的恒速模型。

## 适用场景

- 羽毛球等高变速运动（受空气阻力显著影响）
- 需要高频率状态估计（400 Hz）
- 感知频率低于估计频率（60 Hz 感知 → 400 Hz 估计）
- 检测丢失时需要靠物理模型外推

## 不适用场景

- 近似匀速运动（CV KF 更简单高效）
- 无物理参数（需系统辨识）

## 完整工作流（四阶段）

### 阶段一：系统辨识

1. 采集大量羽毛球飞行轨迹数据
2. 拟合阻力系数 $C_D$、升力系数 $C_L$
3. 验证物理模型预测精度
4. 确定过程噪声 Q 和观测噪声 R

### 阶段二：配置 EKF

| 参数 | ETH 配置 | 说明 |
|------|---------|------|
| dt | 1/400 = 0.0025s | 400Hz 状态估计 |
| model | EKF | 含空气阻力和重力 |
| drag_coefficient | 系统辨识 | 空气阻力系数 |
| process_noise (Q) | 系统辨识 | 物理模型不确定性 |
| measurement_noise (R) | 基于实测 | ZED X 深度噪声 |

### 阶段三：高频预测步

1. EKF 以 400 Hz 运行，远高于感知的 60 Hz
2. 预测步使用非线性运动模型：
   - 位置更新：$\mathbf{p}_{k+1} = \mathbf{p}_k + \mathbf{v}_k \Delta t - \frac{1}{2}\mathbf{a}_{drag}\Delta t^2 - \frac{1}{2}\mathbf{g}\Delta t^2$
   - 速度更新：$\mathbf{v}_{k+1} = \mathbf{v}_k - \mathbf{a}_{drag}\Delta t - \mathbf{g}\Delta t$
3. Jacobian 矩阵 F 用于协方差传播

### 阶段四：低频更新步

1. 感知数据以 60 Hz 到达时执行更新步
2. 观测为 map frame 下的 3D 位置
3. Kalman 增益将位置残差分配到位置和速度
4. 检测丢失时仅做预测，靠物理模型维持状态估计

## 使用方式

```python
from filter import ExtendedBallKalmanFilter

ekf = ExtendedBallKalmanFilter(
    dt=1.0/400.0,
    process_noise=0.5,
    measurement_noise=5.0,
    drag_coefficient=0.01,
)

for i in range(400):
    ekf.predict(dt=1.0/400.0)

    if i % (400 // 60) == 0 and position_3d is not None:
        state = ekf.update(position_3d)
    else:
        state = ekf.predict()

    print(f"位置: ({state.x:.3f}, {state.y:.3f}, {state.z:.3f})")
    print(f"速度: ({state.vx:.2f}, {state.vy:.2f}, {state.vz:.2f})")
```

## 性能基准

| 指标 | 值 |
|------|-----|
| 状态估计频率 | 400 Hz |
| 感知输入频率 | 60 Hz |
| 运动模型 | 含空气阻力 + 重力 |
| 检测丢失外推 | ✅（物理模型外推） |
| 系统辨识 | 需要 |

## 设计亮点

| 设计决策 | 做法 | 动机 |
|----------|------|------|
| 非线性模型 | 含阻力 + 重力 | 羽毛球高变速运动 |
| 高频估计 | 400Hz >> 60Hz 感知 | 检测丢失时仍可外推 |
| 系统辨识 | 拟合物理参数 | 模型精度依赖参数准确性 |
| map frame | 统一全局坐标系 | 融合里程计信息 |
