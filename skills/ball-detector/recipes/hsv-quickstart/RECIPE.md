---
name: hsv-quickstart
skill: ball-detector
description: 基于 HSV 颜色空间的轻量球体检测方案，无需训练，即开即用。
source:
  method: HSV color thresholding + contour filtering
sport: [table_tennis, tennis]
difficulty: beginner
requires_training: false
dependencies:
  - opencv-python>=4.5
stages:
  - id: calibrate
    description: "标定目标球的颜色 HSV 范围"
  - id: detect
    script: detect_hsv.py
    description: "HSV 阈值分割 + 形态学滤波 + 轮廓检测"
performance:
  latency_ms: 2
  note: "依赖颜色标定质量，受光照变化影响大"
---

# HSV Quickstart — 轻量颜色检测方案

## 适用场景

- 乒乓球（橙色/白色）、网球（黄绿色）等颜色鲜明的球
- 受控光照环境（室内、均匀照明）
- 快速原型验证，不需要 GPU
- 作为 YOLO 方案之前的基线对比

## 不适用场景

- 羽毛球（颜色不鲜明、高速运动模糊）
- 光照剧烈变化的户外场景
- 背景中存在大量同色干扰物

## 使用方式

### 步骤一：标定颜色范围

```python
import cv2
import numpy as np

# 用取色器工具获取目标球的 HSV 范围
# 乒乓球（橙色）：H=10-25, S=100-255, V=100-255
# 网球（黄绿色）：H=30-90, S=50-255, V=50-255

# 交互式标定（可选）
image = cv2.imread("ball_sample.jpg")
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
# 用 cv2.createTrackbar 调参，找到最优阈值
```

### 步骤二：运行检测

```python
from detector import HSVColorDetector

detector = HSVColorDetector(
    lower_hsv=(10, 100, 100),   # 乒乓球橙色
    upper_hsv=(25, 255, 255),
    min_area=10,
    max_area=5000,
)

result = detector.detect(image)
if result:
    print(f"球心: ({result.x:.1f}, {result.y:.1f}), 置信度: {result.confidence:.2f}")
```

## 性能特征

| 指标 | 值 |
|------|-----|
| 单帧延迟 | < 2 ms (CPU) |
| GPU 需求 | 无 |
| 训练数据 | 无需 |
| 颜色标定 | 需要 |
| 光照鲁棒性 | 低 |
| 运动模糊鲁棒性 | 中 |

## 与 YOLO 方案对比

| 维度 | HSV Quickstart | ETH Shuttle Detection |
|------|---------------|----------------------|
| 部署难度 | 极低 | 高（需 Docker/GPU） |
| 精度 | 中（依赖标定） | 高（F1=0.86） |
| 泛化能力 | 低（换场景需重标定） | 高（交叉验证验证） |
| 适用球类 | 乒乓球/网球 | 羽毛球 |
| 延迟 | 2 ms | 8 ms |
