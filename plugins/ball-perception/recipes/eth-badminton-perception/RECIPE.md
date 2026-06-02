---
name: eth-badminton-perception
plugin: ball-perception
description: 基于 ETH RSL 方案的完整羽毛球感知系统，组合各 Skill Recipe 搭建端到端管线。
source:
  paper: "Learning coordinated badminton skills for legged manipulators (2026)"
  repo: https://github.com/leggedrobotics/shuttle_detection
sport: [badminton]
difficulty: advanced
skill_recipes:
  detector: eth-shuttle-detection
  tracker: default
  filter: default
  geometry: default
---

# ETH Badminton Perception — 羽毛球感知系统方案

## 来源

本 Recipe 组合 ETH Zurich RSL 的羽毛球检测方案与默认跟踪/滤波/重建模块，形成完整的羽毛球感知管线。

## 系统架构

```
Camera × 2 → ETH YOLOv8 Detector → SlidingWindow Tracker → CV Kalman Filter → DLT Triangulation → 3D State
              (eth-shuttle-detection)  (default)              (default)          (default)
```

## 各模块 Recipe 选择

| 模块 | Recipe | 说明 |
|------|--------|------|
| Detector | [eth-shuttle-detection](../../../skills/ball-detector/recipes/eth-shuttle-detection/RECIPE.md) | ETH YOLOv8 fine-tune 方案 |
| Tracker | 默认 SlidingWindowTracker | 无需专用 Recipe |
| Filter | 默认 CV Kalman Filter | 羽毛球飞行中段近似匀速 |
| Geometry | 默认 DLT Triangulation | 双目三角化 |

## 构建步骤

### 1. 构建检测器（核心）

```bash
cd skills/ball-detector/recipes/eth-shuttle-detection

# 阶段一：自动标注
python autogen_labels.py --video_dir /path/to/raw/videos

# 阶段二：CVAT 校验后转换
python convert_labels.py --input /path/to/cvat/export

# 阶段三：训练
python train.py

# 阶段四：评测
python eval.py
```

### 2. 配置管线

```yaml
# 参考 plugins/ball-perception/assets/config.yaml
detector:
  type: yolo
  model_path: skills/ball-detector/recipes/eth-shuttle-detection/runs/train/weights/best.pt
  input_size: 1024
  confidence_threshold: 0.25
  max_det: 1

cameras:
  - id: "cam0"
    width: 1280
    height: 1024
    K: [[800, 0, 640], [0, 800, 512], [0, 0, 1]]
    dist_coeffs: [0, 0, 0, 0, 0]
    R: [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    t: [0, 0, 0]
  - id: "cam1"
    width: 1280
    height: 1024
    K: [[800, 0, 640], [0, 800, 512], [0, 0, 1]]
    dist_coeffs: [0, 0, 0, 0, 0]
    R: [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    t: [2.74, 0, 0]
```

### 3. 运行端到端管线

```python
from pipeline import PerceptionPipeline

pipeline = PerceptionPipeline("config.yaml")
states = pipeline.process_video("badminton_match.mp4", display=True)
```

### 4. Docker 部署（可选）

```bash
docker-compose -f docker-compose.yml up
```

## 性能基准

| 模块 | 指标 | 值 |
|------|------|-----|
| Detector | F1 (相似场景) | 0.86 |
| Detector | F1 (未知场景) | 0.70 |
| Detector | 单帧延迟 | 8 ms |
| Tracker | 平滑度提升 | > 30% |
| Filter | 位置 RMSE | < 5 px |
| Geometry | 重投影误差 | < 2 px |
| Pipeline | 端到端延迟 | < 20 ms |
