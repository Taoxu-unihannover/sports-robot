"""Small ROS2/RTOS lifecycle and QoS reference helpers."""

from dataclasses import dataclass


@dataclass
class QosProfile:
    deadline_ms: float
    reliable: bool
    history_depth: int


def qos_profile(deadline_ms: float, reliable: bool, history_depth: int = 1) -> QosProfile:
    if deadline_ms <= 0 or history_depth <= 0:
        raise ValueError("deadline and history_depth must be positive")
    return QosProfile(float(deadline_ms), bool(reliable), int(history_depth))


class LifecycleNodeState:
    VALID = {
        "unconfigured": {"inactive"},
        "inactive": {"active", "finalized"},
        "active": {"inactive", "finalized"},
        "finalized": set(),
    }

    def __init__(self):
        self.state = "unconfigured"

    def transition(self, target: str):
        if target not in self.VALID[self.state]:
            raise ValueError(f"invalid transition {self.state}->{target}")
        self.state = target

    def configure(self):
        self.transition("inactive")

    def activate(self):
        self.transition("active")

    def deactivate(self):
        self.transition("inactive")

    def shutdown(self):
        self.transition("finalized")

