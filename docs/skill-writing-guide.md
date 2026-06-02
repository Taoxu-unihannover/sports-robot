# Skills 书写指导文档

本文档指导如何为 SportsRobot 项目创建一个符合规范的 Skill 模块。以 [ball-detector](../skills/ball-detector/) 为参考实现。

## 核心原则

Skill 定义"**能做什么**"——它是可复用的原子能力模块，包含推理代码、测试、示例和参考文献。一个 Skill 可以有多种实现方法（变体），每种方法的完整构建方案由 Recipe 承载。

```
Skill = 推理能力（代码 + 文档 + 测试）
Recipe = 构建方案（从数据到训练到部署）
```

## 目录结构

每个 Skill 必须遵循以下标准结构：

```
skills/{skill-name}/
├── SKILL.md              # 必填：Skill 定义文件（含 YAML frontmatter）
├── scripts/              # 必填：推理代码
│   └── {module}.py       # 核心模块，对外暴露主类和接口
├── tests/                # 必填：单元测试
│   └── test_{module}.py  # 与 scripts/ 下的模块一一对应
├── examples/             # 必填：调用示例
│   └── {example}.md      # 每种典型用法一个示例文件
├── references/           # 必填：参考文献
│   └── papers.md         # 按主题分类的论文/项目列表
└── recipes/              # 按需：构建方案目录
    └── {recipe-name}/
        ├── RECIPE.md     # 方案说明（含 YAML frontmatter）
        └── *.py          # 各阶段脚本
```

## SKILL.md 编写规范

SKILL.md 是 Skill 的唯一入口文件，由两部分组成：**YAML frontmatter**（机器可读元数据）和 **Markdown 正文**（人类可读文档）。

### YAML Frontmatter

Frontmatter 定义 Skill 的身份、触发条件、输入输出接口，供 Agent 和 Marketplace 自动解析：

```yaml
---
name: {skill-name}                    # 必填：与目录名一致，kebab-case
description: |                        # 必填：一句话描述能力、适用场景、不适用场景
  用于{领域}的{核心能力}，输出{输出描述}。
  支持{方法列表}。
  适用于{适用场景}；不用于{不适用场景}。
when_to_use: |                        # 必填：触发关键词，Agent 据此判断是否激活此 Skill
  用户提到{关键词1}、{关键词2}、{英文关键词}时触发。
version: 1.0.0                        # 必填：语义化版本号
allowed-tools:                        # 必填：Agent 执行时允许使用的工具
  - filesystem.read
  - filesystem.write
  - terminal.run

input_schema:                         # 必填：输入接口定义
  type: object
  required: [...]                     # 必填字段
  properties:
    {param_name}:
      type: {type}                    # string / number / array / object
      description: {参数说明}
      # enum: [...]                  # 可选：限定取值范围

output_schema:                        # 必填：输出接口定义
  type: object
  required: [...]
  properties:
    {field_name}:
      type: {type}
      description: {字段说明}
---
```

#### Frontmatter 编写要点

| 字段 | 要点 | 示例 |
|------|------|------|
| `name` | kebab-case，与目录名一致 | `ball-detector` |
| `description` | 三段式：能力 + 适用 + 不适用 | "用于球类运动的单帧检测…适用于…不用于通用目标检测" |
| `when_to_use` | 中英文关键词都列出 | "用户提到球检测、ball detection、YOLO 检测球时触发" |
| `input_schema` | 必填字段最小化，可选字段给默认值 | `confidence_threshold` 默认 0.25 |
| `output_schema` | 与代码中 dataclass 字段一一对应 | `DetectionResult` 的 x, y, confidence, bbox |

### Markdown 正文

正文按以下固定章节组织，每个章节有明确的内容要求：

```markdown
# {Skill 中文名}

## 何时使用

当用户需要从{输入}中获取{输出}时使用。典型场景：
- 场景一
- 场景二
- 场景三

不适用于：{明确排除的场景}。

## 输入约束

- 输入数据格式和范围
- 各检测器/方法的特殊前提条件
- 依赖库和外部资源

## 执行步骤

### 步骤 1：{步骤名称}

- 动作：{做什么}
- 输入：{接收什么}
- 成功标准：{怎样算成功}
- 失败处理：{失败时返回什么}

### 步骤 2：{步骤名称}
...

## 输出格式

​```json
{
  "field1": "示例值",
  "field2": 0.0
}
​```

## 可用方案（Recipes）

| Recipe | 适用{领域} | 难度 | 需要训练 | 性能基准 |
|--------|-----------|------|---------|---------|
| [recipe-name](recipes/recipe-name/RECIPE.md) | ... | ... | ... | ... |

选择建议：
- 快速验证 → {简单方案}
- 生产部署 → {完整方案}

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| {场景} | {如何检测} | {返回什么} |
```

#### 正文编写要点

| 章节 | 要点 | 反例（避免） |
|------|------|-------------|
| 何时使用 | 列举 3–5 个具体场景，明确"不适用于" | 只写"用于球检测" |
| 输入约束 | 写清数据格式、前提条件、依赖 | 遗漏 HSV 需要颜色标定 |
| 执行步骤 | 每步含动作/输入/成功标准/失败处理 | 只写"执行检测" |
| 输出格式 | 给出 JSON 示例，与 output_schema 一致 | 只写"返回结果" |
| 可用方案 | 表格 + 选择建议，链接到 RECIPE.md | 只列名字不给链接 |
| 失败处理 | 表格化，含检测方式和处理策略 | 遗漏模型加载失败场景 |

## scripts/ 编写规范

推理代码是 Skill 的核心实现，必须满足以下要求：

### 文件头部

```python
"""
Module {N}: {Skill 中文名}

Responsibility: {一句话职责描述}。
No {不负责的内容} - {原因}。

Supports:
- {方法1} - {简述}
- {方法2} - {简述}
- {方法3} - {简述}
"""
```

参考 [detector.py](../skills/ball-detector/scripts/detector.py)：

```python
"""
Module 1: Single-Frame Ball Detector

Responsibility: Discover and re-localize the ball in each frame independently.
No temporal dependency - suitable for initialization and recovery after tracking loss.

Supports:
- YOLOv8 (Ultralytics) - default, best for badminton/table tennis
- ONNX runtime export for deployment
- Custom trained model loading
"""
```

### 数据结构

使用 `@dataclass` 定义输入输出，与 `output_schema` 一一对应：

```python
from dataclasses import dataclass
from typing import Tuple, Optional, List

@dataclass
class DetectionResult:
    x: float
    y: float
    confidence: float
    bbox: Tuple[float, float, float, float]
```

### 主类设计

- 构造函数参数与 `input_schema` 对应，可选参数给默认值
- 核心方法命名清晰（如 `detect`、`predict`、`update`）
- 返回 dataclass 实例或 `None`（检测失败时）
- 异常情况返回错误标识，不抛异常

```python
class BallDetector:
    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        input_size: int = 1024,
        confidence_threshold: float = 0.25,
        max_det: int = 1,
        device: str = "cpu",
    ):
        ...

    def load_model(self) -> None:
        ...

    def detect(self, image: np.ndarray) -> Optional[DetectionResult]:
        ...
```

### 多方法变体

当 Skill 支持多种方法时，每种方法实现为独立类，共享相同的输出 dataclass：

```python
class BallDetector:           # YOLO 方法
    def detect(self, image) -> Optional[DetectionResult]: ...

class HSVColorDetector:       # HSV 方法
    def detect(self, image) -> Optional[DetectionResult]: ...

class ONNXBallDetector:       # ONNX 方法
    def detect(self, image) -> Optional[DetectionResult]: ...
```

## tests/ 编写规范

### 文件头部

```python
"""
{skill-name} 单元测试

运行：python -m pytest tests/test_{module}.py -v --tb=short
"""
```

### 测试结构

```python
import sys
import os
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from {module} import {MainClass}, {ResultDataclass}

class Test{ClassName}:
    def test_{init_method}(self):
        """测试初始化"""
        d = MainClass(param1="value", param2=0.25)
        assert d.param2 == 0.25

    def test_{output_fields}(self):
        """测试输出字段"""
        r = ResultDataclass(field1=100.0, field2=0.95)
        assert r.field1 == 100.0

    def test_{edge_case}(self):
        """测试边界情况"""
        d = MainClass()
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        result = d.detect(img)
        assert result is None
```

### 测试要点

| 测试类型 | 内容 | 示例 |
|----------|------|------|
| 初始化测试 | 构造函数参数正确设置 | `assert d.confidence_threshold == 0.25` |
| 输出字段测试 | dataclass 字段可正确访问 | `assert r.x == 100.0` |
| 空输入测试 | 全零/空数据返回 None | `np.zeros()` → `result is None` |
| 正常功能测试 | 典型输入返回正确结果 | 含颜色区域图像 → 检测到目标 |
| 可选依赖测试 | 用 `pytest.importorskip` 处理 | `pytest.importorskip("cv2")` |

## examples/ 编写规范

每个示例文件包含：场景说明 + 完整可运行代码 + 多方法变体示例。

```markdown
# 示例：{方法名} {功能描述}

## 场景

{一句话描述使用场景}

## 代码

​```python
import cv2
from skills.{skill_name}.scripts.{module} import {MainClass}

{instance} = {MainClass}(
    param1="value",
    param2=0.25,
)
{instance}.load_model()  # 如果需要

image = cv2.imread("frame.jpg")
result = {instance}.{method}(image)

if result:
    print(f"输出: {result.field1:.1f}")
else:
    print("未检测到目标")
​```

## 示例：{另一种方法}

​```python
from skills.{skill_name}.scripts.{module} import {AnotherClass}

{instance} = {AnotherClass}(
    param1=value,
    param2=value,
)

result = {instance}.{method}(image)
​```
```

## references/papers.md 编写规范

按主题分类，每条包含：论文名 + 年份 + 机构 + 核心贡献 + 代码链接。

```markdown
# {Skill 中文名}参考论文

## {主题分类一}

- **论文名** (年份): 机构
  - 一句话核心贡献
  - 关键指标（如有）
  - 代码: URL（如有）

## {主题分类二}

- **论文名** (年份): 机构
  - 一句话核心贡献
  - 关键指标
```

参考 [papers.md](../skills/ball-detector/references/papers.md) 的分类方式：YOLO 系列 / 球类检测专项 / 事件相机检测。

## recipes/ 编写规范

Recipe 的详细规范见 [Recipe 架构指南](recipe-guide.md)。这里仅列出 Skill Recipe 的关键要求：

### RECIPE.md Frontmatter

```yaml
---
name: {recipe-name}                   # kebab-case
skill: {skill-name}                   # 所属 Skill（必填）
description: 一句话描述方案来源和特点
source:
  paper: "论文标题 (年份)"
  repo: https://github.com/...
  license: BSD-3-Clause
sport: [badminton]                    # 适用球类
difficulty: advanced                  # beginner / intermediate / advanced
requires_training: true               # 是否需要训练数据
dependencies:                         # 额外依赖
  - ultralytics>=8.0
stages:                               # 构建阶段
  - id: {stage_id}
    script: {script_name}.py
    description: "阶段描述"
performance:                          # 性能基准
  {metric}: {value}
---
```

### RECIPE.md 正文结构

```markdown
# {Recipe 标题}

## 来源
## 适用场景
## 完整工作流（N 阶段）
### 阶段一：{名称}（{script}.py）
...
## 使用方式
### 方式一：Docker（推荐）
### 方式二：本地环境
## 性能基准
## 设计亮点
```

## 新增 Skill 检查清单

创建新 Skill 时，按以下清单逐项检查：

- [ ] 目录名使用 kebab-case（如 `ball-detector`）
- [ ] SKILL.md 的 YAML frontmatter 完整（name / description / when_to_use / version / input_schema / output_schema）
- [ ] SKILL.md 的正文包含全部六个章节（何时使用 / 输入约束 / 执行步骤 / 输出格式 / 可用方案 / 失败处理）
- [ ] `output_schema` 与代码中 dataclass 字段一一对应
- [ ] `input_schema` 与构造函数参数一一对应
- [ ] scripts/ 下有核心模块，文件头部含职责描述和支持方法
- [ ] 主类返回 dataclass 实例，检测失败返回 None
- [ ] 多方法变体共享相同的输出 dataclass
- [ ] tests/ 下有单元测试，覆盖初始化 / 正常功能 / 空输入 / 边界情况
- [ ] 可选依赖使用 `pytest.importorskip`
- [ ] examples/ 下有调用示例，每种方法至少一个
- [ ] references/papers.md 按主题分类，每条含论文名/年份/机构/贡献/链接
- [ ] 如有 Recipe，在 SKILL.md 的"可用方案"表格中添加条目并链接
- [ ] 在 `.claude-plugin/marketplace.json` 中注册新 Skill
