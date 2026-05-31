# 示例：YOLO 单帧球体检测

## 场景

使用 YOLOv8 对单帧图像进行球体检测，输出球的 2D 坐标和置信度。

## 代码

```python
import cv2
from skills.ball_detector.scripts.detector import BallDetector

detector = BallDetector(
    model_path="yolov8n.pt",
    input_size=1024,
    confidence_threshold=0.25,
    max_det=1,
    device="cpu",
)
detector.load_model()

image = cv2.imread("frame.jpg")
result = detector.detect(image)

if result:
    print(f"球心: ({result.x:.1f}, {result.y:.1f}), 置信度: {result.confidence:.2f}")
else:
    print("未检测到球")
```

## 示例：HSV 颜色检测

```python
from skills.ball_detector.scripts.detector import HSVColorDetector

detector = HSVColorDetector(
    lower_hsv=(30, 50, 50),   # 绿色球
    upper_hsv=(90, 255, 255),
    min_area=10,
    max_area=5000,
)

result = detector.detect(image)
```

## 示例：ONNX 部署

```python
from skills.ball_detector.scripts.detector import ONNXBallDetector

detector = ONNXBallDetector(
    onnx_path="ball_detector.onnx",
    input_size=1024,
    confidence_threshold=0.25,
)

result = detector.detect(image)
```
