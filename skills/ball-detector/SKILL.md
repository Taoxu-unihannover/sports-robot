---
name: ball-detector
description: 用于球类运动（乒乓球、羽毛球、网球等）的单帧球体检测，输出球的 2D 图像坐标。支持 YOLOv8、HSV 颜色过滤、ONNX 推理部署。适用于用户需要实现球类检测、目标定位、检测器选型对比；不用于通用目标检测、多目标跟踪或非球类场景。
when_to_use: 用户提到球检测、球定位、YOLO 检测球、HSV 颜色检测球、ball detection、shuttle detection、单帧检测时触发。
version: 1.0.0
allowed-tools:
  - filesystem.read
  - filesystem.write
  - terminal.run
input_schema:
  type: object
  required: [image]
  properties:
    image:
      type: object
      description: numpy array (H, W, 3) BGR 图像
    model_path:
      type: string
      description: YOLO 模型路径，默认 yolov8n.pt
    confidence_threshold:
      type: number
      description: 检测置信度阈值，默认 0.25
output_schema:
  type: object
  required: [x, y, confidence]
  properties:
    x: { type: number, description: 球心 x 坐标 }
    y: { type: number, description: 球心 y 坐标 }
    confidence: { type: number }
    bbox: { type: array, items: { type: number } }
---

# 球类单帧检测器

## 何时使用

当用户需要从单帧图像中检测球类目标的 2D 位置时使用。典型场景：

- 球类机器人感知系统的检测模块
- 从视频帧中定位乒乓球/羽毛球/网球
- 对比不同检测器（YOLO vs HSV）在球类场景下的表现
- 为跟踪模块提供初始化和重定位能力

不适用于：通用目标检测、多类别检测、语义分割。

## 输入约束

- 输入图像为 numpy array，BGR 格式，(H, W, 3)
- YOLO 模式需要 ultralytics 库和模型文件
- HSV 模式需要预先标定目标颜色范围
- ONNX 模式需要预先导出的 .onnx 模型

## 执行步骤

### 步骤 1：选择检测器类型

- 动作：根据配置选择 YOLO / HSV / ONNX 检测器
- 输入：detector_type 参数
- 成功标准：检测器实例化成功
- 失败处理：不支持的检测器类型返回 `config_error: unknown_detector_type`

### 步骤 2：执行单帧检测

- 动作：对输入图像运行检测推理
- 输入：BGR 图像 (H, W, 3)
- 成功标准：返回 DetectionResult（含 x, y, confidence, bbox）
- 失败处理：无检测目标返回 None；模型加载失败返回 `config_error: model_load_failed`

### 步骤 3：后处理

- 动作：NMS 过滤，取最高置信度检测框，计算球心坐标
- 输入：原始检测框列表
- 成功标准：输出唯一球心坐标（max_det=1）
- 失败处理：所有检测框低于阈值返回 None

## 输出格式

```json
{
  "x": 320.5,
  "y": 240.3,
  "confidence": 0.92,
  "bbox": [310, 230, 331, 251]
}
```

## 可用方案（Recipes）

Skill 定义"能做什么"（推理能力），Recipe 定义"怎么做到"（从数据到部署的完整构建方案）。

| Recipe | 适用球类 | 难度 | 需要训练 | 性能基准 |
|--------|---------|------|---------|---------|
| [eth-shuttle-detection](recipes/eth-shuttle-detection/RECIPE.md) | 羽毛球 | 高 | 是 | F1=0.86（相似场景）/ 0.70（未知场景） |
| [hsv-quickstart](recipes/hsv-quickstart/RECIPE.md) | 乒乓球/网球 | 低 | 否 | < 2ms 延迟，依赖颜色标定 |

选择建议：
- 快速验证 → `hsv-quickstart`：无需 GPU，即开即用
- 生产部署 → `eth-shuttle-detection`：需要 GPU + 训练数据，但精度和泛化能力远超 HSV

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 模型文件缺失 | 加载异常 | 返回 `config_error: model_load_failed` |
| 图像为空 | shape 检查 | 返回 None |
| 无检测目标 | 检测框为空 | 返回 None |
| 置信度过低 | 所有框 < threshold | 返回 None |
