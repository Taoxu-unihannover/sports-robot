# 3D 几何重建参考论文

## 三角化方法

- **Hartley & Zisserman** (2004): Multiple View Geometry in Computer Vision
  - DLT (Direct Linear Transform) 三角化
  - Midpoint 三角化
  - 对极几何基础

## 球类应用

- **DeepMind Table Tennis** (2024): Google DeepMind
  - DLT 三角化 + 递归 Kalman filter
  - 对侧相机放置减少三角化偏差 10x
  - 2.74m 基线（乒乓球台宽度）

- **Myongji University Tennis** (2023): Myongji University
  - 网侧视觉 + 机器人视觉双视觉结构
  - 神经网络检测 + 双目三角定位
  - 检测准确率 81.4%

- **Kyushu Institute Tennis** (2025): Kyushu Institute of Technology
  - 双相机位置估计
  - 面向球场辅助机器人
  - 位置估计精度 97.76%

## 立体视觉

- **ZED X Stereo Camera**: ETH Legged Badminton 使用
  - 机载双目，Jetson AGX Orin 处理
  - 基于真实相机数据拟合感知噪声模型
