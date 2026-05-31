"""
ball-detector 单元测试

运行：python -m pytest tests/test_detector.py -v --tb=short
"""

import sys
import os
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from detector import BallDetector, DetectionResult, HSVColorDetector


class TestDetector:
    def test_yolo_init(self):
        d = BallDetector(model_path="yolov8n.pt", input_size=640, device="cpu")
        assert d.input_size == 640
        assert d.confidence_threshold == 0.25
        assert d.max_det == 1

    def test_detection_result_fields(self):
        r = DetectionResult(x=100.0, y=200.0, confidence=0.95, bbox=(90, 190, 110, 210))
        assert r.x == 100.0
        assert r.y == 200.0
        assert r.confidence == 0.95

    def test_hsv_detect_empty(self):
        pytest.importorskip("cv2", reason="opencv-python not installed")
        d = HSVColorDetector()
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        result = d.detect(img)
        assert result is None

    def test_hsv_detect_with_color(self):
        cv2 = pytest.importorskip("cv2", reason="opencv-python not installed")
        d = HSVColorDetector(lower_hsv=(30, 50, 50), upper_hsv=(90, 255, 255))
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[200:220, 300:320] = [0, 200, 0]
        result = d.detect(img)
        assert result is not None
        assert 295 < result.x < 325
        assert 195 < result.y < 225
