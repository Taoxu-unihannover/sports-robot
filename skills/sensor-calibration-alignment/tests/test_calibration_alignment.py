import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from calibration_alignment import (
    CalibrationParams,
    CoordinateChain,
    Extrinsics,
    Intrinsics,
    SpatiotemporalAligner,
)


def test_extrinsics_identity():
    ext = Extrinsics()
    p = ext.transform_point([1.0, 2.0, 3.0])
    assert np.allclose(p, [1.0, 2.0, 3.0])


def test_extrinsics_translation():
    T = np.eye(4)
    T[:3, 3] = [0.5, -0.3, 1.0]
    ext = Extrinsics(T=T)
    p = ext.transform_point([0.0, 0.0, 0.0])
    assert np.allclose(p, [0.5, -0.3, 1.0])


def test_extrinsics_inverse():
    T = np.eye(4)
    T[:3, 3] = [1.0, 2.0, 3.0]
    ext = Extrinsics(T=T)
    ext_inv = ext.inverse()
    p = [0.5, -0.3, 0.8]
    p_round = ext_inv.transform_point(ext.transform_point(p))
    assert np.allclose(p_round, p, atol=1e-10)


def test_temporal_align():
    calib = CalibrationParams(time_offset=0.015)
    aligner = SpatiotemporalAligner(calib)
    t_true = aligner.temporal_align(0.300)
    assert abs(t_true - 0.285) < 1e-10


def test_spatial_align():
    T = np.eye(4)
    T[:3, 3] = [1.0, 0.0, 0.0]
    calib = CalibrationParams(extrinsics=Extrinsics(T=T))
    aligner = SpatiotemporalAligner(calib)
    p_world = aligner.spatial_align([0.5, 0.3, 0.8])
    assert np.allclose(p_world, [1.5, 0.3, 0.8])


def test_full_compensate():
    T = np.eye(4)
    T[:3, 3] = [0.0, 0.0, 0.5]
    calib = CalibrationParams(extrinsics=Extrinsics(T=T), time_offset=0.020)
    aligner = SpatiotemporalAligner(calib)
    result = aligner.full_compensate([1.0, 0.5, 0.3], 0.500)
    assert np.allclose(result["position_world"], [1.0, 0.5, 0.8])
    assert abs(result["true_timestamp"] - 0.480) < 1e-10


def test_bias_drift_update():
    calib = CalibrationParams()
    aligner = SpatiotemporalAligner(calib)
    for _ in range(100):
        aligner.update_bias([1.0, 0.0, 0.0], [0.99, 0.0, 0.0], learning_rate=0.05)
    assert aligner._bias_drift[0] > 0


def test_coordinate_chain():
    chain = CoordinateChain()
    T_WB = np.eye(4)
    T_WB[:3, 3] = [0.0, 0.0, 0.0]
    chain.register("base", "world", T_WB)
    T_BC = np.eye(4)
    T_BC[:3, 3] = [0.1, 0.0, 0.5]
    chain.register("cam", "base", T_BC)
    T_result = chain.lookup("cam", "world")
    assert np.allclose(T_result[:3, 3], [0.1, 0.0, 0.5])


def test_intrinsics_undistort():
    K = np.array([[500.0, 0.0, 320.0], [0.0, 500.0, 240.0], [0.0, 0.0, 1.0]])
    D = np.zeros(5)
    intr = Intrinsics(K=K, D=D)
    result = intr.undistort_normalized([320.0, 240.0])
    assert np.allclose(result, [0.0, 0.0], atol=1e-6)
