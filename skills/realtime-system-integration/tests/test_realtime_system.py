import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from realtime_system import LatencyBudget, Watchdog


def test_latency_budget():
    budget = LatencyBudget()
    budget.add("perception", 10)
    budget.add("control", 2)
    assert budget.total_ms() == 12
    assert budget.over_budget(10)


def test_watchdog():
    wd = Watchdog(timeout_ms=5)
    wd.tick(10)
    assert not wd.expired(14)
    assert wd.expired(16)

