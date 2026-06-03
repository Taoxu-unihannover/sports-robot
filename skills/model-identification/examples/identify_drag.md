# 参数辨识示例

```python
from identification import fit_quadratic_drag_1d

drag = fit_quadratic_drag_1d(times=[0, 0.1, 0.2], velocities=[10.0, 9.2, 8.55])
```

使用方式：

1. 从感知日志中提取同步后的轨迹状态。
2. 对每段轨迹拟合阻力、恢复系数或时延。
3. 只把稳定参数写入运行配置，把异常段保留为数据质量问题。

