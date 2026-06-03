# Ball Execution 快速开始

> 5 分钟验证执行层 pipeline。

## 环境要求

- Python >= 3.8
- pip
- Git

## 安装

```bash
cd plugins/ball-execution
python -m pip install -r requirements.txt
```

## 验证安装

```bash
python -m pytest tests/test_execution_regression.py -v
```

## 第一个执行 pipeline

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
print(result["status"], len(result["arm_profile"]))
```

## 下一步

- 阅读 `AGENTS.md` 了解 Team 分工。
- 阅读 `workflows/development-guide.md` 了解执行层安全规范。
- 查看 `skills/servo-drive-safety/SKILL.md`。
