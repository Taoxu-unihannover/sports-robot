# 球体跟踪参考论文

## TrackNet 系列

- **TrackNetV1** (2019): VGG-16 backbone, 3-frame input, Gaussian heatmap output
  - 代码: https://github.com/yastrebksv/TrackNet

- **TrackNetV3** (2024): NYCU
  - 轨迹预测 + 轨迹修复 + 数据增强
  - Accuracy 97.51%, F1 98.56%, 25.11 FPS
  - 代码: https://github.com/NYCU-ACVLab/TrackNetV3

## 滑动窗口方法

- **DeepMind Table Tennis** (2024): Google DeepMind
  - 递归 Kalman filter 做 3D 跟踪
  - 对侧相机放置减少三角化偏差 10x

- **LATENT** (2026): Tsinghua / Peking / Galbot
  - 四帧滑动窗口平滑速度观测
  - 减轻位置噪声放大到速度估计的问题

## 多目标跟踪

- **SORT** (2016): Simple Online and Realtime Tracking
  - Kalman filter + Hungarian algorithm
  - 适合实时球类跟踪的轻量基线
