import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from ros2_rtos_middleware import LifecycleNodeState, qos_profile


def test_qos_profile():
    profile = qos_profile(5, reliable=False)
    assert profile.deadline_ms == 5
    assert profile.history_depth == 1


def test_lifecycle_valid_path():
    node = LifecycleNodeState()
    node.configure()
    node.activate()
    node.deactivate()
    node.shutdown()
    assert node.state == "finalized"


def test_lifecycle_rejects_invalid_path():
    node = LifecycleNodeState()
    with pytest.raises(ValueError):
        node.activate()

