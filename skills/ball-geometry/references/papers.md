# 3D 几何重建参考论文

## 三角化方法

- **Hartley & Zisserman** (2004): Multiple View Geometry in Computer Vision
  - DLT (Direct Linear Transform) 三角化
  - Midpoint 三角化
  - 对极几何基础

## 代表性系统案例

- **DeepMind Table Tennis** (2024): Google DeepMind
  - DLT 双目三角化 + 递归 Kalman filter
  - 两台 Ximea 高速相机 125 FPS，硬件同步触发
  - 27k 参数时序 CNN，Raw Bayer 输入（跳过 demosaicing 节省 ~1 ms）
  - 对侧相机放置（基线 2.74m = 乒乓球台宽度），减少三角化偏差约 10x
  - DLT 本身 < 0.1 ms，3D 定位精度约 3 mm
  - 代码: https://arxiv.org/abs/2309.03315

- **Ace: An Elite Badminton Robot** (2026): Sony AI / Nature
  - 9 台 APS 全局快门相机 200 Hz 同步采集，DLT 多视角三角化
  - 9 相机冗余设计，遮挡鲁棒
  - 3D 定位精度 3.0 mm，感知延迟 10.2 ms
  - 代码: https://www.nature.com/articles/s41586-026-10338-5

- **ETH Legged Badminton** (2025): ETH Zurich RSL
  - ZED X 双目硬件深度图，免外参标定
  - HSV 颜色过滤 → ZED X 深度 → map frame 转换 → EKF
  - 双目深度精度约 1–3 cm，30 FPS 深度图
  - 机载 Jetson AGX Orin 实时运行
  - 代码: https://github.com/leggedrobotics/shuttle_detection

## 其他球类应用

- **Myongji University Tennis** (2023): Myongji University
  - 网侧视觉 + 机器人视觉双视觉结构
  - 神经网络检测 + 双目三角定位
  - 检测准确率 81.4%

- **Kyushu Institute Tennis** (2025): Kyushu Institute of Technology
  - 双相机位置估计
  - 面向球场辅助机器人
  - 位置估计精度 97.76%

## 立体视觉

- **ZED X Stereo Camera**: Stereolabs
  - 机载双目，内置立体匹配
  - ETH Legged Badminton 使用
  - 基于真实相机数据拟合感知噪声模型
