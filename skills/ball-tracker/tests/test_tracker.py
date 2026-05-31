"""
ball-tracker 单元测试

运行：python -m pytest tests/test_tracker.py -v --tb=short
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from tracker import SlidingWindowTracker, TrajectoryTracker


class TestTracker:
    def test_sliding_window_empty(self):
        t = SlidingWindowTracker(window_size=5)
        result = t.update(None, None, timestamp=0.0)
        assert result is None

    def test_sliding_window_smooth(self):
        t = SlidingWindowTracker(window_size=5)
        for i in range(10):
            t.update(float(100 + i), float(200 + i), timestamp=i * 0.016)
        result = t.update(110.0, 210.0, timestamp=0.16)
        assert result is not None
        assert abs(result.x - 110.0) < 5.0

    def test_gap_reset(self):
        t = SlidingWindowTracker(window_size=5, max_gap=2)
        t.update(100.0, 200.0, timestamp=0.0)
        t.update(None, None, timestamp=0.016)
        t.update(None, None, timestamp=0.032)
        t.update(None, None, timestamp=0.048)
        assert len(t.history) == 0

    def test_predict_next(self):
        t = SlidingWindowTracker(window_size=5)
        t.update(100.0, 200.0, timestamp=0.0)
        t.update(110.0, 210.0, timestamp=0.016)
        pred = t.predict_next()
        assert pred is not None
        assert pred[0] > 110.0

    def test_trajectory_tracker_velocity_filter(self):
        t = TrajectoryTracker(max_velocity=100.0)
        t.update(100.0, 200.0, timestamp=0.0)
        result = t.update(500.0, 500.0, timestamp=0.016)
        assert result is not None
        assert abs(result.x - 100.0) < 5.0
        assert abs(result.y - 200.0) < 5.0
