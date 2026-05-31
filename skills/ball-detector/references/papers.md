# 球体检测参考论文

## YOLO 系列

- **YOLOv8** (2023): Ultralytics YOLOv8, https://github.com/ultralytics/ultralytics
  - 单阶段检测器，适合小目标球体检测
  - 支持 ONNX/TensorRT 导出部署

## 球类检测专项

- **One-Shot Badminton Shuttle Detection** (2026): ETH Zurich RSL
  - 面向移动机器人视角的 YOLOv8 单帧检测
  - 20,510 帧数据集，11 个背景场景
  - F1=0.86（相似场景）/ 0.70（未知场景）
  - 代码: https://github.com/leggedrobotics/shuttle_detection

- **Detecting the shuttlecock for a badminton robot** (2021): SMU / Shandong / I2R
  - Tiny YOLOv2 变体，针对小高速目标优化
  - 改造损失函数和网络结构

- **DeepMind Table Tennis** (2024): Google DeepMind
  - 27k 参数时序 CNN，直接处理 Raw Bayer 图像
  - 跳过 demosaicing 节省 ~1ms 延迟
  - 125 FPS Ximea 相机硬件同步

## 事件相机检测

- **Sony Ace** (2026): Sony AI
  - 9 个 APS 相机 + 3 个事件相机
  - FPGA 加速 2D 检测
  - 3.0 mm 三维定位误差，10.2 ms 感知延迟
