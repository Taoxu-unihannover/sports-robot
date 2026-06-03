# Ball Modeling 示例：预测一次击球

```python
import sys
sys.path.insert(0, "plugins/ball-modeling/scripts")

from pipeline import ModelingPipeline

pipeline = ModelingPipeline("plugins/ball-modeling/assets/config.yaml")
result = pipeline.predict_hit(
    q=[0.1, -0.2, 0.3],
    incoming_position=[0.0, 0.0, 1.0],
    incoming_velocity=[5.0, 0.0, 0.0],
    paddle_velocity=[1.0, 0.0, 0.0],
    paddle_normal=[-1.0, 0.0, 0.0],
)
```

输出包含接触位姿、出球速度、预测轨迹和风险分数。
