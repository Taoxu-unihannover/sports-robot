"""
Module 1: Single-Frame Ball Detector

Responsibility: Discover and re-localize the ball in each frame independently.
No temporal dependency - suitable for initialization and recovery after tracking loss.

Supports:
- YOLOv8 (Ultralytics) - default, best for badminton/table tennis
- ONNX runtime export for deployment
- Custom trained model loading
"""

import numpy as np
from typing import Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class DetectionResult:
    x: float
    y: float
    confidence: float
    bbox: Tuple[float, float, float, float]


class BallDetector:
    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        input_size: int = 1024,
        confidence_threshold: float = 0.25,
        max_det: int = 1,
        device: str = "cpu",
    ):
        self.input_size = input_size
        self.confidence_threshold = confidence_threshold
        self.max_det = max_det
        self.device = device
        self.model = None
        self.model_path = model_path

    def load_model(self):
        from ultralytics import YOLO

        self.model = YOLO(self.model_path)
        if self.device != "cpu":
            self.model.to(self.device)

    def detect(self, image: np.ndarray) -> Optional[DetectionResult]:
        if self.model is None:
            self.load_model()

        h, w = image.shape[:2]
        results = self.model(
            image,
            imgsz=self.input_size,
            conf=self.confidence_threshold,
            max_det=self.max_det,
            verbose=False,
        )

        if len(results) == 0 or results[0].boxes is None:
            return None

        boxes = results[0].boxes
        if len(boxes) == 0:
            return None

        best = boxes[0]
        x1, y1, x2, y2 = best.xyxy[0].tolist()
        conf = float(best.conf[0])

        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0

        return DetectionResult(x=cx, y=cy, confidence=conf, bbox=(x1, y1, x2, y2))

    def detect_batch(self, images: List[np.ndarray]) -> List[Optional[DetectionResult]]:
        return [self.detect(img) for img in images]


class ONNXBallDetector:
    def __init__(
        self,
        onnx_path: str,
        input_size: int = 1024,
        confidence_threshold: float = 0.25,
    ):
        import onnxruntime as ort

        self.input_size = input_size
        self.confidence_threshold = confidence_threshold
        self.session = ort.InferenceSession(onnx_path)
        self.input_name = self.session.get_inputs()[0].name

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        import cv2
        h, w = image.shape[:2]
        scale = min(self.input_size / h, self.input_size / w)
        new_h, new_w = int(h * scale), int(w * scale)
        resized = cv2.resize(image, (new_w, new_h))

        canvas = np.zeros((self.input_size, self.input_size, 3), dtype=np.float32)
        canvas[:new_h, :new_w] = resized / 255.0

        canvas = canvas.transpose(2, 0, 1)
        canvas = np.expand_dims(canvas, axis=0).astype(np.float32)
        return canvas

    def detect(self, image: np.ndarray) -> Optional[DetectionResult]:
        input_tensor = self._preprocess(image)
        outputs = self.session.run(None, {self.input_name: input_tensor})
        return self._postprocess(outputs, image.shape[:2])

    def _postprocess(
        self, outputs: list, original_shape: Tuple[int, int]
    ) -> Optional[DetectionResult]:
        predictions = outputs[0][0]
        best_conf = 0.0
        best_box = None

        for pred in predictions:
            conf = float(pred[4])
            if conf > best_conf and conf >= self.confidence_threshold:
                best_conf = conf
                best_box = pred[:4]

        if best_box is None:
            return None

        oh, ow = original_shape
        x1 = float(best_box[0]) * ow / self.input_size
        y1 = float(best_box[1]) * oh / self.input_size
        x2 = float(best_box[2]) * ow / self.input_size
        y2 = float(best_box[3]) * oh / self.input_size

        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0

        return DetectionResult(x=cx, y=cy, confidence=best_conf, bbox=(x1, y1, x2, y2))


class HSVColorDetector:
    def __init__(
        self,
        lower_hsv: Tuple[int, int, int] = (30, 50, 50),
        upper_hsv: Tuple[int, int, int] = (90, 255, 255),
        min_area: int = 10,
        max_area: int = 5000,
    ):
        self.lower_hsv = np.array(lower_hsv)
        self.upper_hsv = np.array(upper_hsv)
        self.min_area = min_area
        self.max_area = max_area

    def detect(self, image: np.ndarray) -> Optional[DetectionResult]:
        import cv2
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_hsv, self.upper_hsv)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        best = None
        best_area = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if self.min_area <= area <= self.max_area and area > best_area:
                best_area = area
                best = cnt

        if best is None:
            return None

        M = cv2.moments(best)
        if M["m00"] == 0:
            return None

        cx = M["m10"] / M["m00"]
        cy = M["m01"] / M["m00"]
        x, y, w, h = cv2.boundingRect(best)

        return DetectionResult(
            x=cx, y=cy, confidence=min(1.0, best_area / 500.0), bbox=(x, y, x + w, y + h)
        )
