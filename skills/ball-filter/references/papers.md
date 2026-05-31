# Kalman 滤波参考论文

## 基础理论

- **Kalman, R.E.** (1960): A New Approach to Linear Filtering and Prediction Problems
  - 原始 Kalman 滤波论文

## 球类应用

- **DeepMind Table Tennis** (2024): Google DeepMind
  - 递归 Kalman filter 做 3D 球状态估计
  - 延迟建模为高斯分布注入仿真训练

- **ETH Legged Badminton** (2025): ETH Zurich RSL
  - EKF in map frame: IMU 预测 + 视觉更新
  - 400 Hz 状态估计，60 Hz 感知输入
  - 系统辨识获取物理参数

- **UESTC Shuttlecock Tracking** (2022): UESTC
  - 红外双目采集轨迹
  - UKF 滤除视觉噪声
  - RBF 网络做实时轨迹预测

## 运动模型

- **CV (Constant Velocity)**: 适合匀速飞行段（乒乓球飞行中段）
- **CA (Constant Acceleration)**: 适合变速运动（羽毛球受空气阻力）
- **EKF (Extended Kalman Filter)**: 适合非线性运动（含空气阻力和重力）
