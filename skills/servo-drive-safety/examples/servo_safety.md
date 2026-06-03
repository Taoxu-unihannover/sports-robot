# 伺服驱动安全示例

```python
from servo_safety import ServoLimit, check_servo_command

limit = ServoLimit(position_min=-1.5, position_max=1.5, velocity_max=3.0, torque_max=20.0)
ok, reason = check_servo_command(position=0.2, velocity=1.0, torque=5.0, limit=limit)
```

真实系统中该检查应和驱动器报警、急停链路、温度/电流保护共同工作。

