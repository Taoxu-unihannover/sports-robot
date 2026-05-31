"""
Ball Perception Pipeline

Four-module architecture for ball sports perception:
  1. detector  - Single-frame ball detection (YOLO/HSV)
  2. tracker   - Short trajectory temporal smoothing
  3. filter    - Kalman filter state estimation
  4. geometry  - 3D triangulation and coordinate transforms
"""

from .detector import BallDetector, HSVColorDetector, ONNXBallDetector, DetectionResult
from .tracker import TrajectoryTracker, SlidingWindowTracker, TrackNetStyleTracker, TrackPoint
from .filter import BallKalmanFilter, ExtendedBallKalmanFilter, BallState
from .geometry import Triangulator, CameraConfig, CoordinateTransformer, StereoDepthEstimator
from .pipeline import PerceptionPipeline

__all__ = [
    "BallDetector",
    "HSVColorDetector",
    "ONNXBallDetector",
    "DetectionResult",
    "TrajectoryTracker",
    "SlidingWindowTracker",
    "TrackNetStyleTracker",
    "TrackPoint",
    "BallKalmanFilter",
    "ExtendedBallKalmanFilter",
    "BallState",
    "Triangulator",
    "CameraConfig",
    "CoordinateTransformer",
    "StereoDepthEstimator",
    "PerceptionPipeline",
]
