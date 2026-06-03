# 不确定性与风险门控示例

```python
from uncertainty_risk import chi_square_gate, risk_score

accepted = chi_square_gate(residual=[0.02, 0.01], covariance=[[0.01, 0], [0, 0.01]], threshold=5.99)
score = risk_score(time_to_impact=0.18, position_sigma=0.04, workspace_margin=0.2)
```

典型用途：

1. 过滤高残差观测。
2. 给击球规划提供置信度。
3. 当风险超过阈值时切换到保守轨迹或安全停机。

