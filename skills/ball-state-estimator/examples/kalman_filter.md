# 示例：CV 模型 Kalman 滤波

## 场景

对含噪的 2D 球位置观测做 Kalman 滤波，估计平滑位置和速度。

## 代码

```python
from skills.ball_state_estimator.scripts.filter import BallKalmanFilter

kf = BallKalmanFilter(
    dt=0.008,          # 125Hz
    dim=2,             # 2D 跟踪
    model="CV",        # 恒速模型
    process_noise=1.0,
    measurement_noise=10.0,
)

# 模拟含噪观测
observations = [
    (320.0, 240.0),
    (322.5, 241.3),
    (325.1, 242.8),
    (327.8, 244.5),
]

for x, y in observations:
    kf.predict()
    state = kf.update_2d(x, y)
    print(f"位置: ({state.x:.1f}, {state.y:.1f}), "
          f"速度: ({state.vx:.1f}, {state.vy:.1f})")

# 预测未来 0.1 秒后的位置
future_pos = kf.predict_future(0.1)
print(f"预测 0.1s 后位置: ({future_pos[0]:.1f}, {future_pos[1]:.1f})")
```

## 示例：CA 模型（恒加速）

```python
kf = BallKalmanFilter(
    dt=0.008,
    dim=2,
    model="CA",        # 恒加速模型（适合羽毛球）
    process_noise=0.5,
    measurement_noise=5.0,
)
```

## 示例：EKF（含空气阻力）

```python
from skills.ball_state_estimator.scripts.filter import ExtendedBallKalmanFilter

ekf = ExtendedBallKalmanFilter(
    dt=0.008,
    process_noise=1.0,
    measurement_noise=10.0,
    drag_coefficient=0.01,  # 空气阻力系数
)

ekf.predict()
state = ekf.update([1.23, -0.45, 2.10])
print(f"3D 位置: ({state.x:.2f}, {state.y:.2f}, {state.z:.2f})")
print(f"3D 速度: ({state.vx:.2f}, {state.vy:.2f}, {state.vz:.2f})")
```
