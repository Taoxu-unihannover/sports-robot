# Ball Control 快速开始

> 5 分钟验证控制层 pipeline。

## 环境要求

- Python >= 3.8
- pip
- Git

## 安装

```bash
cd plugins/ball-control
python -m pip install -r requirements.txt
```

## 验证安装

```bash
python -m pytest tests/test_control_regression.py -v
```

## 第一个控制 pipeline

```python
import sys
sys.path.insert(0, "plugins/ball-control/scripts")

from hit_planner import BallSample
from pipeline import ControlPipeline

pipeline = ControlPipeline("plugins/ball-control/assets/config.yaml")
result = pipeline.command(
    samples=[BallSample(0.2, [0.4, 0.0, 0.8], [-2.0, 0.0, 0.0])],
    target_landing=[1.5, 0.0, 0.0],
    context={"side": "right", "workspace_margin": 0.3},
)
print(result["status"], result["skill"])
```

## 下一步

- 阅读 `AGENTS.md` 了解 Team 分工。
- 阅读 `workflows/development-guide.md` 了解控制开发规范。
- 查看 `skills/hit-planner/SKILL.md` 和 `skills/mpc-controller/SKILL.md`。
