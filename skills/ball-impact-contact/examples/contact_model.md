# 接触模型示例

```python
from impact_contact import PaddleImpactModel

model = PaddleImpactModel(restitution=0.86, tangential_damping=0.12)
out_velocity = model.impact(
    ball_velocity=[5.0, 0.2, -1.0],
    paddle_velocity=[1.0, 0.0, 0.0],
    paddle_normal=[-1.0, 0.0, 0.0],
)
```

输出可直接作为击球后飞行模型初值，用于验证击球规划是否能把球送到目标落点。

