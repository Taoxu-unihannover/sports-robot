# 移动底盘执行示例

```python
from mobile_base_executor import pure_pursuit_command

cmd = pure_pursuit_command(pose=[0, 0, 0], waypoint=[1, 0.2], linear_speed=0.6)
```

移动底盘负责把机器人带到可击球工作空间，机械臂负责最后的高速击球动作。

