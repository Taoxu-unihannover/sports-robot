# 时空对齐与标定补偿参考

- Kalibr: Unified temporal and spatial calibration for multi-sensor systems.
  - 参考代码: https://github.com/ethz-asl/kalibr
  - 适合相机-IMU 外参和时间偏置联合标定。

- Furgale et al., "Unified Temporal and Spatial Calibration for Multi-Sensor Systems."
  - Robotics Research, 2013.
  - Kalibr 的理论基础论文。

- DeepMind robotic table tennis system.
  - 在仿真中注入真实感知延迟和噪声，使策略看到的状态分布接近实机。
  - 延迟建模是该系统的核心建模贡献之一。

- ETH legged badminton robot.
  - ZED X 双目视觉约 60 Hz 输出，需要与 IMU 和关节编码器时间对齐。
  - 强调感知噪声和延迟的显式建模。
