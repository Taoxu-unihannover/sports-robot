# 时空对齐示例

本示例展示如何用 `scripts/calibration_alignment.py` 为球类机器人建立时空对齐管线。

```python
from calibration_alignment import (
    CalibrationParams,
    Extrinsics,
    SpatiotemporalAligner,
)

T_WC = np.eye(4)
T_WC[:3, 3] = [0.1, -0.5, 1.2]

calib = CalibrationParams(
    extrinsics=Extrinsics(T=T_WC),
    time_offset=0.015,
)

aligner = SpatiotemporalAligner(calib)

result = aligner.full_compensate(
    position_camera=[0.3, 0.2, 0.5],
    timestamp=0.300,
)

print(f"世界坐标: {result['position_world']}")
print(f"真实时刻: {result['true_timestamp']}")
```

典型接入流程：

1. 部署前用 Kalibr 标定外参和时间偏置，写入 `extrinsics.yaml`。
2. 在线运行时，每帧观测经过 `full_compensate` 统一到世界系和系统时钟。
3. 定期用 `update_bias` 补偿外参漂移（热胀冷缩、振动等）。
4. 用 `residual_diagnostics` 监控标定质量，残差偏大时触发重新标定。
