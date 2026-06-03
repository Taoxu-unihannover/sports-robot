# 高速机械臂执行示例

```python
from manipulator_executor import trapezoid_profile

profile = trapezoid_profile(distance=0.8, max_velocity=2.0, max_acceleration=6.0, dt=0.01)
```

该脚本用于快速检查击球前轨迹是否满足速度/加速度边界。

