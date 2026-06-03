# Ball Engineering 示例：工程有效性检查

```python
import sys
sys.path.insert(0, "plugins/ball-engineering/scripts")

from pipeline import EngineeringPipeline

pipeline = EngineeringPipeline("plugins/ball-engineering/assets/config.yaml")
result = pipeline.validate(actual_runtime="1.0.0")
```

输出包含延迟预算、电源功率、QoS、生命周期状态、标定 checksum 和版本兼容性。
