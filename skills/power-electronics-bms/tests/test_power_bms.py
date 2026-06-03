import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from power_bms import BatteryState, PowerBudget


def test_power_budget():
    budget = PowerBudget(48)
    budget.add_load("arm", 10)
    budget.add_load("compute", 2)
    assert budget.total_current() == 12
    assert budget.total_power() == 576


def test_battery_soc_and_voltage():
    state = BatteryState(44, -5, 20, 10)
    assert state.soc() == 0.5
    assert state.undervoltage(45)

