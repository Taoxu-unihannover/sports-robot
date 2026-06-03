"""Whole-body command allocation helpers."""

from typing import Iterable, Tuple

import numpy as np


def allocate_task_delta(task_delta: Iterable[float], base_weight: float) -> Tuple[np.ndarray, np.ndarray]:
    delta = np.asarray(list(task_delta), dtype=float)
    w = max(0.0, min(1.0, float(base_weight)))
    base = delta * w
    arm = delta * (1.0 - w)
    return base, arm


def support_polygon_margin(point_xy: Iterable[float], polygon_xy: Iterable[Iterable[float]]) -> float:
    point = np.asarray(list(point_xy), dtype=float)
    polygon = np.asarray(list(polygon_xy), dtype=float)
    centroid = np.mean(polygon, axis=0)
    radius = min(np.linalg.norm(vertex - centroid) for vertex in polygon)
    return float(radius - np.linalg.norm(point - centroid))

