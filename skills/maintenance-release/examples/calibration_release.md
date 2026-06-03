# 维护发布示例

```python
from maintenance_release import calibration_checksum, parse_semver

checksum = calibration_checksum({"camera": "cam0", "fx": 800.0})
version = parse_semver("1.2.3")
```

发布包应包含模型参数、标定文件、固件版本、测试报告和回滚路径。

