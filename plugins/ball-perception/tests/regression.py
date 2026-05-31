"""
ball-perception skill 回归测试

验证：
1. 输出 schema 字段完整性
2. 各模块初始化不抛异常
3. 空输入/异常输入降级处理
4. 配置文件校验

运行：python -m pytest tests/regression.py -v --tb=short
"""

import sys
import os
import json
import tempfile
import pytest
import numpy as np
import yaml

_SKILLS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "skills")
sys.path.insert(0, os.path.join(_SKILLS_DIR, "ball-filter", "scripts"))
sys.path.insert(0, os.path.join(_SKILLS_DIR, "ball-geometry", "scripts"))
sys.path.insert(0, os.path.join(_SKILLS_DIR, "ball-detector", "scripts"))
sys.path.insert(0, os.path.join(_SKILLS_DIR, "ball-tracker", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from filter import BallKalmanFilter, ExtendedBallKalmanFilter, BallState
from geometry import Triangulator, CameraConfig, CoordinateTransformer, StereoDepthEstimator


def validate_output_schema(result):
    required = {"status", "states"}
    missing = required - set(result)
    if missing:
        raise AssertionError(f"missing keys: {missing}")
    assert result["status"] in ("ok", "no_detection", "calibration_missing", "config_error"), f"invalid status: {result['status']}"
    for state in result.get("states", []):
        for key in ("x", "y", "z", "vx", "vy", "vz", "timestamp"):
            assert key in state, f"state missing key: {key}"


class TestFilter:
    def test_kf_init(self):
        kf = BallKalmanFilter(dt=0.008, dim=2, model="CV")
        assert kf.dim == 2
        assert kf.model_type == "CV"
        assert not kf.initialized

    def test_kf_predict_update_2d(self):
        kf = BallKalmanFilter(dt=0.008, dim=2, model="CV")
        kf.predict()
        state = kf.update_2d(100.0, 200.0)
        assert abs(state.x - 100.0) < 20.0
        assert abs(state.y - 200.0) < 20.0
        assert kf.initialized

    def test_kf_convergence(self):
        kf = BallKalmanFilter(dt=0.008, dim=2, model="CV", measurement_noise=1.0)
        for _ in range(50):
            kf.predict()
            kf.update_2d(100.0, 200.0)
        state = kf.predict()
        assert abs(state.x - 100.0) < 1.0
        assert abs(state.y - 200.0) < 1.0

    def test_kf_3d(self):
        kf = BallKalmanFilter(dt=0.008, dim=3, model="CV")
        kf.predict()
        state = kf.update_3d(1.0, 2.0, 3.0)
        assert abs(state.x - 1.0) < 0.5
        assert abs(state.y - 2.0) < 0.5
        assert abs(state.z - 3.0) < 0.5

    def test_kf_ca_model(self):
        kf = BallKalmanFilter(dt=0.008, dim=2, model="CA")
        kf.predict()
        state = kf.update_2d(100.0, 200.0)
        assert abs(state.ax) < 0.01
        assert abs(state.ay) < 0.01

    def test_kf_predict_future(self):
        kf = BallKalmanFilter(dt=0.008, dim=2, model="CV")
        kf.predict()
        kf.update_2d(100.0, 200.0)
        kf.x[2] = 10.0
        kf.x[3] = 5.0
        future = kf.predict_future(0.1)
        assert abs(future[0] - (kf.x[0] + 1.0)) < 0.1
        assert abs(future[1] - (kf.x[1] + 0.5)) < 0.1

    def test_kf_reset(self):
        kf = BallKalmanFilter(dt=0.008, dim=2, model="CV")
        kf.predict()
        kf.update_2d(100.0, 200.0)
        kf.reset()
        assert not kf.initialized

    def test_ekf_init(self):
        ekf = ExtendedBallKalmanFilter(dt=0.008, drag_coefficient=0.01)
        assert not ekf.initialized

    def test_ekf_predict_update(self):
        ekf = ExtendedBallKalmanFilter(dt=0.008, drag_coefficient=0.01)
        ekf.predict()
        state = ekf.update(np.array([1.0, 2.0, 3.0]))
        assert abs(state.x - 1.0) < 0.5
        assert abs(state.y - 2.0) < 0.5
        assert abs(state.z - 3.0) < 0.5

    def test_ball_state_properties(self):
        s = BallState(x=1.0, y=2.0, z=3.0, vx=4.0, vy=5.0, vz=6.0)
        assert np.allclose(s.position, [1, 2, 3])
        assert np.allclose(s.velocity, [4, 5, 6])
        assert abs(s.speed - np.sqrt(16 + 25 + 36)) < 0.01


class TestGeometry:
    def make_cameras(self):
        K = np.array([[800, 0, 320], [0, 800, 240], [0, 0, 1]], dtype=float)
        return [
            CameraConfig("cam0", 640, 480, K.copy(), np.zeros(5), np.eye(3), np.array([0.0, 0.0, 0.0])),
            CameraConfig("cam1", 640, 480, K.copy(), np.zeros(5), np.eye(3), np.array([2.74, 0.0, 0.0])),
        ]

    def test_dlt_triangulation(self):
        cameras = self.make_cameras()
        tri = Triangulator(cameras, method="DLT")
        point_3d_true = np.array([1.37, 0.0, 2.0])
        points_2d = {}
        for cam in cameras:
            u, v = tri.project_3d_to_2d(point_3d_true, cam.camera_id)
            points_2d[cam.camera_id] = (u, v)
        result = tri.triangulate(points_2d)
        assert result is not None
        assert np.allclose(result, point_3d_true, atol=0.01)

    def test_midpoint_triangulation(self):
        cameras = self.make_cameras()
        tri = Triangulator(cameras, method="midpoint")
        point_3d_true = np.array([1.37, 0.0, 2.0])
        points_2d = {}
        for cam in cameras:
            u, v = tri.project_3d_to_2d(point_3d_true, cam.camera_id)
            points_2d[cam.camera_id] = (u, v)
        result = tri.triangulate(points_2d)
        assert result is not None
        assert np.allclose(result, point_3d_true, atol=0.01)

    def test_insufficient_cameras(self):
        cameras = self.make_cameras()
        tri = Triangulator(cameras, method="DLT")
        result = tri.triangulate({"cam0": (100.0, 200.0)})
        assert result is None

    def test_reprojection_error(self):
        cameras = self.make_cameras()
        tri = Triangulator(cameras, method="DLT")
        point_3d = np.array([1.37, 0.0, 2.0])
        points_2d = {}
        for cam in cameras:
            u, v = tri.project_3d_to_2d(point_3d, cam.camera_id)
            points_2d[cam.camera_id] = (u, v)
        error = tri.reprojection_error(point_3d, points_2d)
        assert error < 0.01

    def test_coordinate_transform(self):
        T = np.eye(4)
        T[:3, 3] = [1.0, 2.0, 3.0]
        ct = CoordinateTransformer(T)
        p_cam = np.array([0.0, 0.0, 0.0])
        p_world = ct.cam_to_world(p_cam)
        assert np.allclose(p_world, [1.0, 2.0, 3.0])
        p_back = ct.world_to_cam(p_world)
        assert np.allclose(p_back, p_cam)

    def test_stereo_depth(self):
        sd = StereoDepthEstimator(baseline=0.12, focal_length=800.0, cx=320.0)
        depth = sd.disparity_to_depth(50.0)
        assert abs(depth - 0.12 * 800.0 / 50.0) < 0.01
        p3d = sd.stereo_to_3d(370.0, 240.0, 320.0, 240.0)
        assert p3d[2] > 0


class TestTracker:
    def test_sliding_window_empty(self):
        from tracker import SlidingWindowTracker
        t = SlidingWindowTracker(window_size=5)
        result = t.update(None, None, timestamp=0.0)
        assert result is None

    def test_sliding_window_smooth(self):
        from tracker import SlidingWindowTracker
        t = SlidingWindowTracker(window_size=5)
        for i in range(10):
            t.update(float(100 + i), float(200 + i), timestamp=i * 0.016)
        result = t.update(110.0, 210.0, timestamp=0.16)
        assert result is not None
        assert abs(result.x - 110.0) < 5.0

    def test_gap_reset(self):
        from tracker import SlidingWindowTracker
        t = SlidingWindowTracker(window_size=5, max_gap=2)
        t.update(100.0, 200.0, timestamp=0.0)
        t.update(None, None, timestamp=0.016)
        t.update(None, None, timestamp=0.032)
        t.update(None, None, timestamp=0.048)
        assert len(t.history) == 0

    def test_predict_next(self):
        from tracker import SlidingWindowTracker
        t = SlidingWindowTracker(window_size=5)
        t.update(100.0, 200.0, timestamp=0.0)
        t.update(110.0, 210.0, timestamp=0.016)
        pred = t.predict_next()
        assert pred is not None
        assert pred[0] > 110.0

    def test_trajectory_tracker_velocity_filter(self):
        from tracker import TrajectoryTracker
        t = TrajectoryTracker(max_velocity=100.0)
        t.update(100.0, 200.0, timestamp=0.0)
        result = t.update(500.0, 500.0, timestamp=0.016)
        assert result is not None
        assert abs(result.x - 100.0) < 5.0
        assert abs(result.y - 200.0) < 5.0


class TestDetector:
    def test_yolo_init(self):
        from detector import BallDetector
        d = BallDetector(model_path="yolov8n.pt", input_size=640, device="cpu")
        assert d.input_size == 640
        assert d.confidence_threshold == 0.25
        assert d.max_det == 1

    def test_detection_result_fields(self):
        from detector import DetectionResult
        r = DetectionResult(x=100.0, y=200.0, confidence=0.95, bbox=(90, 190, 110, 210))
        assert r.x == 100.0
        assert r.y == 200.0
        assert r.confidence == 0.95

    def test_hsv_detect_empty(self):
        pytest.importorskip("cv2", reason="opencv-python not installed")
        from detector import HSVColorDetector
        d = HSVColorDetector()
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        result = d.detect(img)
        assert result is None

    def test_hsv_detect_with_color(self):
        cv2 = pytest.importorskip("cv2", reason="opencv-python not installed")
        from detector import HSVColorDetector
        d = HSVColorDetector(lower_hsv=(30, 50, 50), upper_hsv=(90, 255, 255))
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[200:220, 300:320] = [0, 200, 0]
        result = d.detect(img)
        assert result is not None
        assert 295 < result.x < 325
        assert 195 < result.y < 225


class TestPipeline:
    def make_dummy_config(self):
        return {
            "detector": {"type": "hsv", "hsv": {"lower": [30, 50, 50], "upper": [90, 255, 255], "min_area": 10, "max_area": 5000}},
            "tracker": {"window_size": 5, "max_gap": 3, "max_velocity": 500.0, "use_prediction": True},
            "filter": {"dt": 0.008, "dim": 2, "model": "CV", "process_noise": 1.0, "measurement_noise": 10.0, "process_noise_3d": 0.5, "measurement_noise_3d": 5.0},
            "geometry": {"method": "DLT", "T_cam_to_world": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]},
            "cameras": [
                {"id": "cam0", "width": 640, "height": 480, "K": [[800, 0, 320], [0, 800, 240], [0, 0, 1]], "dist_coeffs": [0, 0, 0, 0, 0], "R": [[1, 0, 0], [0, 1, 0], [0, 0, 1]], "t": [0, 0, 0]},
                {"id": "cam1", "width": 640, "height": 480, "K": [[800, 0, 320], [0, 800, 240], [0, 0, 1]], "dist_coeffs": [0, 0, 0, 0, 0], "R": [[1, 0, 0], [0, 1, 0], [0, 0, 1]], "t": [2.74, 0, 0]},
            ],
        }

    def make_dummy_image(self, h=480, w=640):
        return np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)

    def test_config_validation(self):
        pytest.importorskip("cv2", reason="opencv-python not installed")
        from pipeline import PerceptionPipeline
        config = self.make_dummy_config()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name
        try:
            pipeline = PerceptionPipeline(config_path)
            assert len(pipeline.detectors) == 2
            assert len(pipeline.trackers) == 2
            assert len(pipeline.filter_2d) == 2
            assert pipeline.triangulator is not None
        finally:
            os.unlink(config_path)

    def test_process_frame_no_detection(self):
        pytest.importorskip("cv2", reason="opencv-python not installed")
        from pipeline import PerceptionPipeline
        config = self.make_dummy_config()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name
        try:
            pipeline = PerceptionPipeline(config_path)
            frames = {"cam0": self.make_dummy_image(), "cam1": self.make_dummy_image()}
            state = pipeline.process_frame(frames)
            assert state is not None
            stats = pipeline.get_stats()
            assert stats["frames_processed"] == 1
        finally:
            os.unlink(config_path)

    def test_output_schema(self):
        pytest.importorskip("cv2", reason="opencv-python not installed")
        from pipeline import PerceptionPipeline
        config = self.make_dummy_config()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name
        try:
            pipeline = PerceptionPipeline(config_path)
            frames = {"cam0": self.make_dummy_image(), "cam1": self.make_dummy_image()}
            states = []
            for _ in range(5):
                state = pipeline.process_frame(frames)
                if state is not None:
                    states.append({
                        "x": state.x, "y": state.y, "z": state.z,
                        "vx": state.vx, "vy": state.vy, "vz": state.vz,
                        "timestamp": state.timestamp,
                    })
            stats = pipeline.get_stats()
            result = {
                "status": "ok" if states else "no_detection",
                "states": states,
                "stats": stats,
            }
            validate_output_schema(result)
        finally:
            os.unlink(config_path)
