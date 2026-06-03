"""Realtime integration helpers for latency budgets and watchdogs."""

from dataclasses import dataclass
from typing import Dict


class LatencyBudget:
    def __init__(self):
        self.items: Dict[str, float] = {}

    def add(self, name: str, latency_ms: float):
        if latency_ms < 0:
            raise ValueError("latency cannot be negative")
        self.items[name] = float(latency_ms)

    def total_ms(self) -> float:
        return float(sum(self.items.values()))

    def over_budget(self, limit_ms: float) -> bool:
        return self.total_ms() > limit_ms


@dataclass
class Watchdog:
    timeout_ms: float
    last_tick_ms: float = 0.0

    def tick(self, now_ms: float):
        self.last_tick_ms = float(now_ms)

    def expired(self, now_ms: float) -> bool:
        return float(now_ms) - self.last_tick_ms > self.timeout_ms

