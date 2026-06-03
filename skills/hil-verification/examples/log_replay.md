# HIL 日志回放示例

```python
from hil_verification import rmse, replay_latency_stats

error = rmse([1, 2, 3], [1.1, 1.9, 3.2])
stats = replay_latency_stats([10, 12, 11])
```

HIL 验证应复用真实日志，覆盖感知丢帧、模型预测偏差、控制超时和执行器限幅。

