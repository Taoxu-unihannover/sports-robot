# 示例：滑动窗口轨迹平滑

## 场景

对连续帧的检测结果做时序平滑，消除单帧抖动。

## 代码

```python
from skills.ball_tracker.scripts.tracker import TrajectoryTracker

tracker = TrajectoryTracker(
    window_size=5,
    max_gap=3,
    max_velocity=500.0,
    use_prediction=True,
)

# 模拟连续帧输入
detections = [
    (320.0, 240.0, 0.000),
    (322.5, 241.3, 0.008),
    (321.8, 240.9, 0.016),
    (None, None, 0.024),     # 检测丢失
    (323.1, 242.0, 0.032),   # 恢复
]

for x, y, ts in detections:
    result = tracker.update(x, y, ts)
    if result:
        print(f"平滑后: ({result.x:.1f}, {result.y:.1f})")
    else:
        print("跟踪丢失")

# 预测下一帧位置
next_pos = tracker.predict_next()
if next_pos:
    print(f"预测下一帧: ({next_pos[0]:.1f}, {next_pos[1]:.1f})")
```

## 示例：TrackNet 风格热图跟踪

```python
from skills.ball_tracker.scripts.tracker import TrackNetStyleTracker

tracker = TrackNetStyleTracker(
    input_frames=3,
    heatmap_sigma=2.5,
    device="cpu",
)

for frame in frames:
    tracker.add_frame(frame)
    result = tracker.track()
    if result:
        cx, cy, conf = result
        print(f"球心: ({cx:.1f}, {cy:.1f}), 置信度: {conf:.2f}")
```
