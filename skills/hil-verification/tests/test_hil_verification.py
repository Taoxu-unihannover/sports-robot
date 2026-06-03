import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from hil_verification import pass_fail, replay_latency_stats, rmse


def test_rmse_zero_for_match():
    assert rmse([1, 2], [1, 2]) == 0


def test_latency_stats():
    stats = replay_latency_stats([1, 2, 3, 4])
    assert stats["max"] == 4
    assert stats["p95"] >= stats["mean"]


def test_pass_fail():
    assert pass_fail(0.1, 0.2)
    assert not pass_fail(0.3, 0.2)

