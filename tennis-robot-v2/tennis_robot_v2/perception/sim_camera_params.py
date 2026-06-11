#!/usr/bin/env python3
"""
Camera parameters for simulation camera rendering.

Absorbed from dynamic-tennis-v2/tennis_tracker/binocular_camera/sim_camera_params.py
"""
import numpy as np

# Camera baseline (distance between two cameras)
CAMERA_BASELINE = 0.24  # meters

# Camera intrinsics (will be extracted from MuJoCo model at runtime)
# These are placeholder values - actual values come from MuJoCo camera calibration
CAM1_POS = np.array([-0.12, -0.18, 0.18])   # tennis_cam1 world position
CAM2_POS = np.array([0.12, -0.18, 0.18])    # tennis_cam2 world position

# Camera rotation (looking in -Y direction)
# xyaxes = "-1 0 0 0 0 1" means:
#   Camera right (X) = -X world
#   Camera up (Y) = +Z world
#   Camera forward (Z) = -Y world
CAM1_ROTATION = np.array([[-1, 0, 0], [0, 0, 1], [0, -1, 0]])  # rotation matrix
CAM2_ROTATION = CAM1_ROTATION.copy()

# Camera extrinsics (transform from camera to base_link)
# Camera is mounted on cargo_box at z=0.18m
# Base to camera transform
T_BASE_CAM = np.array([
    [0, 0, 1, 0.18],   # camera looks in -Y, so MuJoCo +Z -> camera -Y
    [-1, 0, 0, 0.12],  # MuJoCo -X -> camera +X (right)
    [0, -1, 0, 0.18],  # MuJoCo -Y -> camera +Z (up)
    [0, 0, 0, 1]
])

# Image dimensions
DEFAULT_WIDTH = 320
DEFAULT_HEIGHT = 240

# Stereo matching parameters
STEREO_MAX_DISPARITY = 128
STEREO_BLOCK_SIZE = 5