---
name: kalibr-camera-imu
skill: sensor-calibration-alignment
description: 使用 Kalibr 进行相机-IMU 空间-时间联合标定，估计外参 T_CI 和时间偏置 delta_t。
source:
  docs: https://github.com/ethz-asl/kalibr
  report: docs/tech-report/002-建模层.md
sport: [table_tennis, badminton, tennis]
difficulty: intermediate
requires_training: false
---

# Kalibr 相机-IMU 联合标定 Recipe

## 目标

使用 Kalibr 工具箱估计相机与 IMU 之间的空间变换 $T_{CI}$ 和时间偏置 $\delta_t$，为建模层时空对齐提供标定参数。

## 工作流

1. 准备标定板（AprilTag 或棋盘格），打印并测量实际尺寸。
2. 采集标定数据：手持传感器组在标定板前做 6 自由度运动，录制 rosbag。
3. 运行 Kalibr `calibrate_imu_camera`，输出 $T_{CI}$、$\delta_t$、内参和 IMU 偏置。
4. 验证标定质量：重投影误差 < 0.5 像素，时间偏置收敛。
5. 将标定结果写入 `extrinsics.yaml` 和 `delay_profile.yaml`。

## 关键参数

| 参数 | 建议值 | 说明 |
|---|---|---|
| 标定板类型 | AprilTag 36h11 | 比棋盘格更鲁棒 |
| 采集时长 | 60–120 秒 | 覆盖充分运动 |
| 运动范围 | 全 6 自由度 | 确保激励充分 |
| 时间偏置初值 | 0 ms | Kalibr 自动估计 |

## 验收指标

| 指标 | 建议 |
|---|---|
| 重投影误差 | < 0.5 像素 |
| 时间偏置标准差 | < 1 ms |
| 外参平移误差 | < 1 mm（与 CAD 对比） |
| 外参旋转误差 | < 0.5 度 |
