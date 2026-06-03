# ROS2 / RTOS 中间件示例

```python
from ros2_rtos_middleware import LifecycleNodeState, qos_profile

profile = qos_profile(deadline_ms=5, reliable=False)
state = LifecycleNodeState()
state.configure()
state.activate()
```

该 skill 用于把机器人模块组织成可启动、可停机、可追踪的生命周期节点。

