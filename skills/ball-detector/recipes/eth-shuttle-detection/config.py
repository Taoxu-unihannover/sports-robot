"""
ETH Shuttle Detection — Configuration
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

MODEL_CONFIG = {
    "base_model": "yolov8n.pt",
    "input_size": 1024,
    "max_det": 1,
    "confidence_threshold": 0.25,
}

TRAIN_CONFIG = {
    "epochs": 100,
    "batch": 16,
    "patience": 20,
    "augmentation": {
        "mosaic": 0.5,
        "mixup": 0.1,
        "hsv_h": 0.015,
        "hsv_s": 0.7,
        "hsv_v": 0.4,
        "degrees": 0.0,
        "translate": 0.1,
        "scale": 0.5,
        "fliplr": 0.5,
    },
    "coco_negatives": 1000,
    "exclude_hard": True,
}

AUTOGEN_CONFIG = {
    "bg_history": 500,
    "bg_var_threshold": 16,
    "min_area": 5,
    "max_area": 2000,
    "seg_model": "yolov8n-seg.pt",
    "temporal_weight": 0.7,
    "area_weight": 0.3,
}

EVAL_CONFIG = {
    "distance_threshold_px": 25,
    "cv_strategy": "background",
    "n_folds_background": 11,
    "n_folds_location": 5,
}

PATHS = {
    "autogen_output": str(BASE_DIR / "autogen_output"),
    "dataset": str(BASE_DIR / "dataset"),
    "runs": str(BASE_DIR / "runs"),
}
