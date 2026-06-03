# 实时系统集成示例

```python
from realtime_system import LatencyBudget

budget = LatencyBudget()
budget.add("perception", 10.2)
budget.add("planning", 3.0)
budget.add("control", 1.0)
assert budget.total_ms() < 20.0
```

工程层需要把感知、建模、控制、执行各模块的时间戳和延迟预算显式记录下来。

