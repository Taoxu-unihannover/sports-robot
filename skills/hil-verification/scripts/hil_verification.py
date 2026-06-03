"""HIL and log replay verification metrics."""

from typing import Iterable

import numpy as np


def rmse(actual: Iterable[float], expected: Iterable[float]) -> float:
    a = np.asarray(list(actual), dtype=float)
    e = np.asarray(list(expected), dtype=float)
    if a.shape != e.shape:
        raise ValueError("actual and expected must have same shape")
    return float(np.sqrt(np.mean((a - e) ** 2)))


def replay_latency_stats(latencies_ms: Iterable[float]) -> dict:
    values = np.asarray(list(latencies_ms), dtype=float)
    if len(values) == 0:
        raise ValueError("latencies cannot be empty")
    return {"mean": float(np.mean(values)), "p95": float(np.percentile(values, 95)), "max": float(np.max(values))}


def pass_fail(metric: float, threshold: float) -> bool:
    return metric <= threshold

