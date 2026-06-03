# 飞行预测示例

```python
from flight_model import BallFlightModel, FlightState

model = BallFlightModel(mass=0.0027, radius=0.02, drag_coefficient=0.47)
state = FlightState(position=[0, 0, 1.2], velocity=[7, 0, 2], spin=[0, 0, 80])
future = model.rollout(state, dt=0.005, steps=100)
```

使用建议：

1. 感知层输出 3D 位置/速度/旋转估计。
2. 飞行模型做短时预测，控制层在预测轨迹上选择击球时间。
3. 如果球速较高或旋转明显，打开 Magnus 项。
4. 对羽毛球使用更高阻力或分段阻力模型，不要直接套乒乓球参数。

