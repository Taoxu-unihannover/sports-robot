import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from safety_supervisor import SafetyLimits, SafetySupervisor, clamp_velocity


def test_accepts_safe_command():
    supervisor = SafetySupervisor(SafetyLimits(1.0, 2.0, 0.1))
    ok, reason = supervisor.check([0.5, 0, 0], [1, 0, 0], 0.2)
    assert ok and reason == "ok"


def test_rejects_workspace_limit():
    supervisor = SafetySupervisor(SafetyLimits(1.0, 2.0, 0.1))
    ok, reason = supervisor.check([2, 0, 0], [1, 0, 0], 0.2)
    assert not ok and reason == "workspace_limit"


def test_clamp_velocity():
    v = clamp_velocity([3, 4, 0], 2.0)
    assert abs(np.linalg.norm(v) - 2.0) < 1e-12

