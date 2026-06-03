"""Power electronics and battery budget helpers."""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class PowerBudget:
    voltage: float
    loads: Dict[str, float] = field(default_factory=dict)

    def add_load(self, name: str, current_a: float):
        if current_a < 0:
            raise ValueError("current must be non-negative")
        self.loads[name] = float(current_a)

    def total_current(self) -> float:
        return float(sum(self.loads.values()))

    def total_power(self) -> float:
        return self.voltage * self.total_current()


@dataclass
class BatteryState:
    voltage: float
    current: float
    capacity_ah: float
    remaining_ah: float

    def soc(self) -> float:
        if self.capacity_ah <= 0:
            raise ValueError("capacity must be positive")
        return max(0.0, min(1.0, self.remaining_ah / self.capacity_ah))

    def undervoltage(self, min_voltage: float) -> bool:
        return self.voltage < min_voltage

