# Ball Execution 示例：预览硬件命令

```python
import sys
sys.path.insert(0, "plugins/ball-execution/scripts")

from pipeline import ExecutionPipeline

pipeline = ExecutionPipeline("plugins/ball-execution/assets/config.yaml")
result = pipeline.execute_preview(
    target_velocity=[6.0, 0.0, 1.0],
    arm_distance=0.5,
    base_pose=[0.0, 0.0, 0.0],
    waypoint=[1.0, 0.0],
)
```

输出包含发球机命令、机械臂轨迹、底盘命令、全身分配和伺服安全状态。
