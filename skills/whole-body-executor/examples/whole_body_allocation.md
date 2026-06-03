# 全身执行示例

```python
from whole_body_executor import allocate_task_delta

base_delta, arm_delta = allocate_task_delta(task_delta=[1, 0, 0], base_weight=0.3)
```

全身系统通常把大范围位移分配给底盘/腿，把高速末端修正分配给手臂。

