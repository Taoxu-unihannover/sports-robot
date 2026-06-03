"""Reference launcher command mapping."""

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass
class LauncherCommand:
    wheel_left: float
    wheel_right: float
    yaw: float
    pitch: float


class LauncherModel:
    def __init__(self, speed_gain: float, yaw_gain: float, pitch_gain: float, spin_gain: float = 0.0):
        self.speed_gain = float(speed_gain)
        self.yaw_gain = float(yaw_gain)
        self.pitch_gain = float(pitch_gain)
        self.spin_gain = float(spin_gain)

    def command_for_velocity(self, velocity: Iterable[float], side_spin: float = 0.0) -> LauncherCommand:
        v = np.asarray(list(velocity), dtype=float)
        speed = float(np.linalg.norm(v))
        wheel_base = speed / max(self.speed_gain, 1e-12)
        yaw = float(np.arctan2(v[1], v[0]) / max(self.yaw_gain, 1e-12))
        pitch = float(np.arctan2(v[2], max(np.linalg.norm(v[:2]), 1e-12)) / max(self.pitch_gain, 1e-12))
        spin_delta = side_spin * self.spin_gain
        return LauncherCommand(wheel_left=wheel_base - spin_delta, wheel_right=wheel_base + spin_delta, yaw=yaw, pitch=pitch)

    def estimate_exit_speed(self, command: LauncherCommand) -> float:
        return 0.5 * (command.wheel_left + command.wheel_right) * self.speed_gain

