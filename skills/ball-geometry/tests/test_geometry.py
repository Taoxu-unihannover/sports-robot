"""
ball-geometry 单元测试

运行：python -m pytest tests/test_geometry.py -v --tb=short
"""

import sys
import os
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from geometry import Triangulator, CameraConfig, CoordinateTransformer, StereoDepthEstimator


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
