# Kalman 滤波与速度估计参考论文

## 基础理论

- **Kalman, R.E.** (1960): A New Approach to Linear Filtering and Prediction Problems
  - 原始 Kalman 滤波论文

## 代表性系统案例

### KF 内隐速度估计

- **DeepMind Table Tennis** (2024): Google DeepMind
  - CV Kalman Filter，状态向量 $[\mathbf{p}, \mathbf{v}]$，恒速运动模型
  - 125 Hz 感知频率，速度估计噪声由协方差矩阵 $\mathbf{P}$ 控制
  - 检测丢失时预测步仍可外推
  - 代码: https://arxiv.org/abs/2309.03315

- **ETH Legged Badminton** (2025): ETH Zurich RSL
  - EKF in map frame: 含空气阻力和重力的非线性运动模型
  - 400 Hz 状态估计，60 Hz 感知输入
  - 系统辨识获取物理参数
  - 代码: https://github.com/leggedrobotics/shuttle_detection

### 滑窗平均速度

- **LATENT** (2026): Tsinghua / Peking / Galbot
  - 4 帧滑动窗口平均速度，噪声方差降低为 1/3
  - 50 Hz planner/control 循环
  - 当 $\Delta t = 20$ ms、$\sigma_p = 5$ mm 时，速度噪声从 0.35 m/s 降至约 0.20 m/s
  - 代码: https://arxiv.org/abs/2603.12686

### 位置历史隐式恢复

- **ETH Legged Badminton prediction-free** (2025): ETH Zurich RSL
  - 位置历史直接作为策略网络输入，网络隐式学习速度
  - 免手动调参（$\mathbf{Q}$、$\mathbf{R}$ 矩阵）
  - 速度估计质量难以独立评估和调试
  - 代码: https://github.com/leggedrobotics/shuttle_detection

## 其他球类应用

- **UESTC Shuttlecock Tracking** (2022): UESTC
  - 红外双目采集轨迹
  - UKF 滤除视觉噪声
  - RBF 网络做实时轨迹预测

## 运动模型

- **CV (Constant Velocity)**: 适合匀速飞行段（乒乓球飞行中段）
- **CA (Constant Acceleration)**: 适合变速运动（羽毛球受空气阻力）
- **EKF (Extended Kalman Filter)**: 适合非线性运动（含空气阻力和重力）
