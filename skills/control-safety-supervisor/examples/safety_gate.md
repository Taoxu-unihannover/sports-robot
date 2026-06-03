# 控制安全监督示例

```python
from safety_supervisor import SafetySupervisor, SafetyLimits

supervisor = SafetySupervisor(SafetyLimits(workspace_radius=1.5, max_speed=4.0, min_time_to_impact=0.08))
ok, reason = supervisor.check(position=[0.5, 0, 0.8], velocity=[1, 0, 0], time_to_impact=0.2)
```

安全监督应位于控制输出到执行器之间，所有命令都必须经过边界、速度和时序检查。

