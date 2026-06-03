# 电源与 BMS 示例

```python
from power_bms import PowerBudget, BatteryState

budget = PowerBudget(voltage=48.0)
budget.add_load("arm", current_a=12.0)
budget.add_load("compute", current_a=4.0)
state = BatteryState(voltage=49.5, current=-10.0, capacity_ah=20.0, remaining_ah=12.0)
```

电源链路要同时关注平均功率、峰值电流、欠压保护和温升。

