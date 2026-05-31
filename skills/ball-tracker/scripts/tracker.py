"""
Module 2: Short Trajectory Tracker

Responsibility: Establish temporal association across consecutive frames,
output smoothed 2D trajectory. Uses motion continuity to resist single-frame
false positives and brief occlusions.

Implements:
- Sliding window temporal smoothing (lightweight, no GPU needed)
- TrackNet-style heatmap-based tracking (PyTorch, optional)
- Simple SORT-like Kalman tracking for real-time use
"""

import numpy as np
from typing import List, Tuple, Optional, Deque
from collections import deque
from dataclasses import dataclass


@dataclass
class TrackPoint:
    x: float
    y: float
    timestamp: float
    confidence: float


class SlidingWindowTracker:
    def __init__(self, window_size: int = 5, max_gap: int = 3):
        self.window_size = window_size
        self.max_gap = max_gap
        self.history: Deque[TrackPoint] = deque(maxlen=window_size)
        self.gap_counter = 0

    def update(self, x: Optional[float], y: Optional[float],
               timestamp: float, confidence: float = 1.0) -> Optional[TrackPoint]:
        if x is not None and y is not None:
            self.history.append(TrackPoint(x=x, y=y, timestamp=timestamp,
                                           confidence=confidence))
            self.gap_counter = 0
        else:
            self.gap_counter += 1
            if self.gap_counter > self.max_gap:
                self.history.clear()

        if len(self.history) < 2:
            return self.history[-1] if self.history else None

        return self._smooth()

    def _smooth(self) -> TrackPoint:
        points = list(self.history)
        weights = np.exp(-0.5 * np.arange(len(points))[::-1])
        weights = weights / weights.sum()

        x_smooth = np.average([p.x for p in points], weights=weights)
        y_smooth = np.average([p.y for p in points], weights=weights)
        conf = np.average([p.confidence for p in points], weights=weights)

        return TrackPoint(x=x_smooth, y=y_smooth,
                          timestamp=points[-1].timestamp, confidence=conf)

    def predict_next(self) -> Optional[Tuple[float, float]]:
        if len(self.history) < 2:
            return None

        points = list(self.history)
        recent = points[-3:] if len(points) >= 3 else points

        if len(recent) < 2:
            return None

        dx = recent[-1].x - recent[0].x
        dy = recent[-1].y - recent[0].y
        dt = recent[-1].timestamp - recent[0].timestamp

        if dt == 0:
            return None

        vx = dx / dt
        vy = dy / dt

        next_t = recent[-1].timestamp + (recent[-1].timestamp - recent[-2].timestamp)
        pred_x = recent[-1].x + vx * (next_t - recent[-1].timestamp)
        pred_y = recent[-1].y + vy * (next_t - recent[-1].timestamp)

        return (pred_x, pred_y)

    def reset(self):
        self.history.clear()
        self.gap_counter = 0


class TrajectoryTracker:
    def __init__(
        self,
        window_size: int = 5,
        max_gap: int = 3,
        max_velocity: float = 500.0,
        use_prediction: bool = True,
    ):
        self.tracker = SlidingWindowTracker(window_size=window_size, max_gap=max_gap)
        self.max_velocity = max_velocity
        self.use_prediction = use_prediction
        self.last_timestamp: Optional[float] = None

    def update(
        self, x: Optional[float], y: Optional[float],
        timestamp: Optional[float] = None, confidence: float = 1.0
    ) -> Optional[TrackPoint]:
        if timestamp is None:
            import time
            timestamp = time.time()

        if x is not None and y is not None and self.last_timestamp is not None:
            dt = timestamp - self.last_timestamp
            if dt > 0 and len(self.tracker.history) > 0:
                last = self.tracker.history[-1]
                velocity = np.sqrt((x - last.x) ** 2 + (y - last.y) ** 2) / dt
                if velocity > self.max_velocity:
                    x, y = None, None

        self.last_timestamp = timestamp
        return self.tracker.update(x, y, timestamp, confidence)

    def predict_next(self) -> Optional[Tuple[float, float]]:
        return self.tracker.predict_next()

    def reset(self):
        self.tracker.reset()
        self.last_timestamp = None


class TrackNetStyleTracker:
    def __init__(
        self,
        model_path: Optional[str] = None,
        input_frames: int = 3,
        heatmap_sigma: float = 2.5,
        device: str = "cpu",
    ):
        self.input_frames = input_frames
        self.heatmap_sigma = heatmap_sigma
        self.device = device
        self.frame_buffer: Deque[np.ndarray] = deque(maxlen=input_frames)
        self.model = None
        self.model_path = model_path

    def _build_model(self):
        import torch
        import torch.nn as nn

        class LightweightTrackNet(nn.Module):
            def __init__(self, in_channels=9, out_channels=1):
                super().__init__()
                self.encoder = nn.Sequential(
                    nn.Conv2d(in_channels, 64, 3, padding=1),
                    nn.BatchNorm2d(64),
                    nn.ReLU(inplace=True),
                    nn.MaxPool2d(2),
                    nn.Conv2d(64, 128, 3, padding=1),
                    nn.BatchNorm2d(128),
                    nn.ReLU(inplace=True),
                    nn.MaxPool2d(2),
                    nn.Conv2d(128, 256, 3, padding=1),
                    nn.BatchNorm2d(256),
                    nn.ReLU(inplace=True),
                    nn.MaxPool2d(2),
                )
                self.decoder = nn.Sequential(
                    nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True),
                    nn.Conv2d(256, 128, 3, padding=1),
                    nn.BatchNorm2d(128),
                    nn.ReLU(inplace=True),
                    nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True),
                    nn.Conv2d(128, 64, 3, padding=1),
                    nn.BatchNorm2d(64),
                    nn.ReLU(inplace=True),
                    nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True),
                    nn.Conv2d(64, out_channels, 3, padding=1),
                    nn.Sigmoid(),
                )

            def forward(self, x):
                features = self.encoder(x)
                heatmap = self.decoder(features)
                return heatmap

        model = LightweightTrackNet(in_channels=self.input_frames * 3)
        if self.model_path is not None:
            import torch
            model.load_state_dict(torch.load(self.model_path, map_location=self.device))
        model.to(self.device)
        model.eval()
        return model

    def _generate_heatmap_target(self, cx: float, cy: float, h: int, w: int) -> np.ndarray:
        xs = np.arange(w)
        ys = np.arange(h)
        xx, yy = np.meshgrid(xs, ys)
        heatmap = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * self.heatmap_sigma ** 2))
        return heatmap

    def _heatmap_to_center(self, heatmap: np.ndarray) -> Tuple[float, float, float]:
        h, w = heatmap.shape
        max_idx = np.argmax(heatmap)
        cy, cx = max_idx // w, max_idx % w
        confidence = float(heatmap[cy, cx])

        if 0 < cx < w - 1 and 0 < cy < h - 1:
            dx = (heatmap[cy, cx + 1] - heatmap[cy, cx - 1]) / 2.0
            dy = (heatmap[cy + 1, cx] - heatmap[cy - 1, cx]) / 2.0
            cx += dx
            cy += dy

        return float(cx), float(cy), confidence

    def add_frame(self, frame: np.ndarray):
        import cv2
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        self.frame_buffer.append(gray)

    def track(self) -> Optional[Tuple[float, float, float]]:
        if len(self.frame_buffer) < self.input_frames:
            return None

        import torch

        if self.model is None:
            self.model = self._build_model()

        frames = list(self.frame_buffer)
        h, w = frames[0].shape

        input_tensor = np.stack(frames, axis=0)
        input_tensor = input_tensor.astype(np.float32) / 255.0
        input_tensor = torch.from_numpy(input_tensor).unsqueeze(0).to(self.device)

        with torch.no_grad():
            heatmap = self.model(input_tensor).cpu().numpy()[0, 0]

        cx, cy, conf = self._heatmap_to_center(heatmap)
        return cx, cy, conf
