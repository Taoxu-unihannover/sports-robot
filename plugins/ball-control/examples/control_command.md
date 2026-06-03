# Ball Control 示例：生成击球命令

```python
import sys
sys.path.insert(0, "plugins/ball-control/scripts")

from pipeline import ControlPipeline
from hit_planner import BallSample

pipeline = ControlPipeline("plugins/ball-control/assets/config.yaml")
result = pipeline.command(
    samples=[BallSample(0.2, [0.4, 0.0, 0.8], [-2, 0, 0])],
    target_landing=[1.5, 0.0, 0.0],
    context={"side": "right", "workspace_margin": 0.3},
)
```

输出包含状态、安全原因、选中技能、击球规划和限幅后的速度。
