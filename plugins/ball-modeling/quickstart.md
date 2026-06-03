# Ball Modeling 快速开始

> 5 分钟验证建模层 pipeline。

## 环境要求

- Python >= 3.8
- pip
- Git

## 安装

```bash
cd plugins/ball-modeling
python -m pip install -r requirements.txt
```

## 验证安装

```bash
python -m pytest tests/test_modeling_regression.py -v
```

## 第一个建模 pipeline

```python
import sys
sys.path.insert(0, "plugins/ball-modeling/scripts")

from pipeline import ModelingPipeline

pipeline = ModelingPipeline("plugins/ball-modeling/assets/config.yaml")
result = pipeline.predict_hit(
    q=[0.1, -0.2, 0.3],
    incoming_position=[0.0, 0.0, 1.0],
    incoming_velocity=[5.0, 0.0, 0.0],
    paddle_velocity=[1.0, 0.0, 0.0],
    paddle_normal=[-1.0, 0.0, 0.0],
)
print(result["risk"], len(result["states"]))
```

## 下一步

- 阅读 `AGENTS.md` 了解 Team 分工。
- 阅读 `workflows/development-guide.md` 了解开发规范。
- 查看 `skills/ball-flight-model/SKILL.md` 等 Skill 文档。
