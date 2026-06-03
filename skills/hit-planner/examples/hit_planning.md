# 击球规划示例

```python
from hit_planner import HitPlanner, BallSample

planner = HitPlanner(workspace_radius=1.2)
samples = [
    BallSample(t=0.10, position=[0.5, 0.0, 0.9], velocity=[-3, 0, 0]),
    BallSample(t=0.15, position=[0.35, 0.0, 0.85], velocity=[-3, 0, -0.2]),
]
plan = planner.select_hit(samples, target_landing=[1.6, 0.0, 0.0])
```

规划器输出击球时间、击球点和期望出球速度，供 MPC 或技能控制器跟踪。

