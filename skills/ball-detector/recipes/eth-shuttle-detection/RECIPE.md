---
name: eth-shuttle-detection
skill: ball-detector
description: ETH Zurich RSL 的 YOLOv8 羽毛球检测方案，从自动标注到训练评测的完整闭环。
source:
  paper: "One-Shot Badminton Shuttle Detection for Mobile Robots (2026)"
  repo: https://github.com/leggedrobotics/shuttle_detection
  license: BSD-3-Clause
sport: [badminton]
difficulty: advanced
requires_training: true
dependencies:
  - ultralytics>=8.0
  - opencv-python>=4.5
  - torch>=1.10
  - docker (recommended)
stages:
  - id: autogen
    script: autogen_labels.py
    description: "GMM 背景减除 + YOLOv8-seg 对手移除 → 自动标注"
  - id: convert
    script: convert_labels.py
    description: "CVAT 标注 → YOLO 格式，按难度分级 easy/medium/hard"
  - id: train
    script: train.py
    description: "YOLOv8 fine-tune，含 COCO 负样本 + mixup 增强"
  - id: eval
    script: eval.py
    description: "背景级/地点级交叉验证，距离精度指标"
  - id: deploy
    script: predict.py
    description: "加载训练权重推理，输出 CSV"
performance:
  f1_similar_scene: 0.86
  f1_novel_scene: 0.70
  latency_ms: 8
  input_resolution: 1024
  dataset_frames: 20510
  dataset_backgrounds: 11
---

# ETH Shuttle Detection — 羽毛球检测完整方案

## 来源

本 Recipe 来自 ETH Zurich RSL 的 [shuttle_detection](https://github.com/leggedrobotics/shuttle_detection) 仓库，配套论文 *"One-Shot Badminton Shuttle Detection for Mobile Robots"*（2026）。

## 适用场景

- 移动机器人视角的羽毛球检测（非广播视角）
- 需要从零构建检测数据集和训练模型
- 需要评估模型在不同环境下的泛化能力

## 完整工作流（五阶段）

### 阶段一：自动标注（autogen_labels.py）

传统标注需要人工逐帧画框，本方案实现了自动标注流水线，将人工工作量降低约 85%：

1. **GMM 背景减除**：利用 OpenCV 的 `cv2.createBackgroundSubtractorMOG2()` 对静止相机视频做前景分割，提取运动区域
2. **对手移除**：用 YOLOv8-seg 分割对手球员区域，从前景中排除——因为球员也在运动，但我们要找的是球
3. **行人过滤**：排除图像下半部分的小型连通分量（行人腿部误检）
4. **候选排序**：剩余候选按时间一致性（与前一帧检测位置的距离）和 blob 面积排序，选出最可能是球的区域
5. **输出 CVAT 归档**：生成 `.zip` 文件，可直接导入 CVAT 进行人工校验和修正

论文报告该流水线正确标注了 85.7% 的帧，8.3% 仅需微调边界框，5.9% 需手动修正。

### 阶段二：标注转换（convert_labels.py）

CVAT 导出 YOLO 格式的标注后，该脚本将其转换为 Ultralytics YOLO 标准数据集结构，并按 difficulty 分为 easy/medium/hard 三个子集。

### 阶段三：训练（train.py）

基于 Ultralytics YOLOv8 的 `model.train()` API，关键配置：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 模型 | yolov8n.pt | nano 版本，最小最快 |
| 输入分辨率 | 1024 | 论文做了 640–1408 的 sweep |
| max_det | 1 | 每帧最多一个检测 |
| 训练数据 | easy + medium | 排除 hard 噪声标签 |
| COCO 负样本 | 1000 张 | 混入无球背景图降低误检 |
| mixup | 开启 | 对 recall 提升最大（0.68 → 0.78） |

### 阶段四：评测（eval.py）

两种交叉验证策略：

- **Background-based CV**：11 折，每次留一个背景做测试——评估对相似环境的泛化
- **Location-based CV**：5 折，每次留一个地点的所有背景做测试——评估对完全未知环境的泛化

评测指标使用**距离精度**（Distance Precision Rate）：预测框中心与真值框中心的欧氏距离 ≤ 25 像素即为 True Positive。

### 阶段五：推理部署（predict.py）

加载训练好的模型权重，对任意图像文件夹做批量推理，输出 CSV 文件。

## 使用方式

### 方式一：Docker（推荐）

```bash
# 构建镜像
docker-compose build

# 自动标注
docker-compose run shuttletrack python -m shuttletrack.autogen_labels --video_dir /data/raw

# 训练
docker-compose run shuttletrack python -m shuttletrack.train

# 评测
docker-compose run shuttletrack python -m shuttletrack.eval

# 推理
docker-compose run shuttletrack python -m shuttletrack.predict --source /data/test
```

### 方式二：本地环境

```bash
pip install ultralytics opencv-python torch

# 按阶段执行
python autogen_labels.py --video_dir /path/to/videos
python convert_labels.py --input /path/to/cvat/export
python train.py
python eval.py
python predict.py --source /path/to/images
```

## 性能基准

| 指标 | 相似场景 | 未知场景 |
|------|---------|---------|
| F1 | 0.86 | 0.70 |
| Precision | 0.89 | 0.75 |
| Recall | 0.84 | 0.66 |
| 单帧延迟 | 8 ms (GPU) | — |

## 设计亮点

| 设计决策 | 做法 | 动机 |
|----------|------|------|
| Docker 化 | 所有依赖封装在容器中 | 消除环境配置差异 |
| CLI 入口 | 每阶段独立命令 | 模块解耦，可单独运行 |
| 自动标注 | GMM + YOLOv8-seg + 时序过滤 | 标注成本从数周降至数小时 |
| CVAT 集成 | 自动标注输出直接导入 CVAT | 利用成熟工具做人工校验 |
| 难度分级 | easy/medium/hard | 训练时排除 hard 噪声 |
| 交叉验证 | 背景级 + 地点级 | 系统评估泛化能力 |
| COCO 负样本 | 混入 1000 张无球图 | 降低误检 |
