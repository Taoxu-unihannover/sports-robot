# 发球机执行示例

```python
from launcher_executor import LauncherModel

launcher = LauncherModel(speed_gain=0.032, yaw_gain=0.01, pitch_gain=0.01)
command = launcher.command_for_velocity([6.0, 0.5, 1.2])
```

执行层应记录轮速、角度、实际落点和感知反推速度，用于后续标定速度映射。

