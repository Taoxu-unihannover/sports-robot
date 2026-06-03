"""End-to-end engineering validation pipeline."""

import argparse
import os
import sys

import yaml

_SKILLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "skills")
for _skill in ["realtime-system-integration", "ros2-rtos-middleware", "power-electronics-bms", "hil-verification", "maintenance-release"]:
    sys.path.insert(0, os.path.join(_SKILLS_DIR, _skill, "scripts"))

from hil_verification import replay_latency_stats
from maintenance_release import calibration_checksum, compatible_runtime, parse_semver
from power_bms import PowerBudget
from realtime_system import LatencyBudget, Watchdog
from ros2_rtos_middleware import LifecycleNodeState, qos_profile


class EngineeringPipeline:
    def __init__(self, config_path: str):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    def validate(self, actual_runtime: str = "1.0.0"):
        budget = LatencyBudget()
        for name, latency in self.config["latency_budget_ms"].items():
            budget.add(name, latency)
        watchdog = Watchdog(**self.config["watchdog"])
        qos = qos_profile(**self.config["qos"])
        node = LifecycleNodeState()
        node.configure()
        node.activate()
        power = PowerBudget(self.config["power"]["voltage"])
        for name, current in self.config["power"]["loads"].items():
            power.add_load(name, current)
        checksum = calibration_checksum(self.config)
        compatible = compatible_runtime(parse_semver(self.config["release"]["required_runtime"]), parse_semver(actual_runtime))
        stats = replay_latency_stats(list(self.config["latency_budget_ms"].values()))
        return {"status": "ok" if compatible and not budget.over_budget(25.0) else "warning", "latency_ms": budget.total_ms(), "qos": qos, "node_state": node.state, "power_w": power.total_power(), "checksum": checksum, "latency_stats": stats, "watchdog_expired": watchdog.expired(100.0)}


def main():
    parser = argparse.ArgumentParser(description="Ball engineering pipeline")
    parser.add_argument("--config", default=os.path.join(os.path.dirname(__file__), "..", "assets", "config.yaml"))
    args = parser.parse_args()
    result = EngineeringPipeline(args.config).validate()
    print(f"{result['status']} latency={result['latency_ms']:.1f}ms")


if __name__ == "__main__":
    main()
