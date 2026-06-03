# Ball Engineering 快速开始

> 5 分钟验证工程层 pipeline。

## 环境要求

- Python >= 3.8
- pip
- Git

## 安装

```bash
cd plugins/ball-engineering
python -m pip install -r requirements.txt
```

## 验证安装

```bash
python -m pytest tests/test_engineering_regression.py -v
```

## 第一个工程 pipeline

```python
import sys
sys.path.insert(0, "plugins/ball-engineering/scripts")

from pipeline import EngineeringPipeline

pipeline = EngineeringPipeline("plugins/ball-engineering/assets/config.yaml")
result = pipeline.validate(actual_runtime="1.0.0")
print(result["status"], result["latency_ms"], result["power_w"])
```

## 下一步

- 阅读 `AGENTS.md` 了解 Team 分工。
- 阅读 `workflows/development-guide.md` 了解工程验证规范。
- 查看 `skills/hil-verification/SKILL.md` 和 `skills/maintenance-release/SKILL.md`。
