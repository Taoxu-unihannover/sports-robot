# 简化球类项目复现 Recipe

> 本 Recipe 是 `ball-project-assimilator` 的简化版本，只包含阶段 1-2（技术栈拆解 → 项目复现），不包含横向评测和超越。
> 
> 适用于：用户只需要快速复现开源项目，不需要横向对比和超越的场景。

## 用途

从已有球类机器人项目中提取可复用的技能模式，生成标准 skill 模板，并基于 sports-robot 自举新项目。

## 适用场景

- 用户需要将现有项目代码沉淀为可复用技能
- 用户需要快速基于 sports-robot 自举新项目
- 不需要横向对比同类方法或超越原项目

## 输入

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| project_dir | string | 是 | 源项目根目录 |
| project_type | string | 否 | 项目类型：dynamic-tennis, dynamic-badminton 等 |
| output_dir | string | 否 | 输出目录，默认项目根目录 |
| skip_skills_generation | bool | 否 | 是否跳过 skills 生成 |

## 输出

| 产物 | 路径 | 说明 |
|---|---|---|
| 技能分析报告 | distill_report.json | 提取的技能清单和映射 |
| SKILL.md 模板 | skills/{skill_name}/SKILL.md | 生成的技能定义 |
| 参考代码 | skills/{skill_name}/references/ | 提取的参考实现 |
| 自举项目 | {project_name}/ | 基于 skills 自举的新项目 |

## 执行步骤

### 步骤 1：扫描项目结构（对应阶段 1）

识别关键目录和文件：
- MuJoCo XML 文件 → `mujoco-tennis-world-builder`
- Gymnasium 环境类 → `gymnasium-mujoco-env-builder`
- 训练脚本 → `sb3-rl-training-runner`
- 评估脚本 → `mujoco-policy-evaluator`
- 可视化代码 → `robot-trajectory-web-visualizer`
- 观测构造 → `truth-state-policy-input`
- 相机/感知 → `sim-camera-perception-input`

### 步骤 2：提取模式（对应阶段 1）

从源代码中提取：
- 观测空间定义和归一化模式
- 动作空间定义和逆运动学模式
- 奖励函数组件和权重
- 终止条件逻辑
- MuJoCo 模型结构
- 训练超参数

### 步骤 3：生成技能模板（对应阶段 1）

将提取的模式写入标准 SKILL.md 格式，包含：
- 输入/输出定义
- 执行步骤
- 代码模板
- 验证方式

### 步骤 4：生成参考实现（对应阶段 1）

将源代码关键片段复制到 references/ 目录，标注来源和用途。

### 步骤 5：基于 sports-robot 自举项目（对应阶段 2）

使用以下 skills 自举新项目：

| Skill | 用途 |
|---|---|
| `mujoco-tennis-world-builder` | 生成 MuJoCo 场景 |
| `gymnasium-mujoco-env-builder` | 生成 Gymnasium 环境 |
| `sb3-rl-training-runner` | 生成训练入口 |
| `mujoco-policy-evaluator` | 生成评估脚本 |
| `truth-state-policy-input` | 生成观测构建 |
| `sim-camera-perception-input` | 生成感知模块 |

### 步骤 6：验证自举项目（对应阶段 2）

运行以下验证：
1. `python -m pytest tests/ -q` — 单元测试
2. `python scripts/train.py --total_timesteps 1000` — 短训练 smoke test
3. `python scripts/evaluate.py --episodes 3` — 评估 smoke test

## 验证方式

1. 蒸馏报告包含所有识别的技能
2. SKILL.md 格式符合标准
3. 参考代码可追溯至源项目
4. 自举项目可运行且通过 smoke test
5. 自举项目功能覆盖率达到原项目的 80%+

## 与完整版对比

| 功能 | 简化版 | 完整版 |
|---|---|---|
| 阶段 1：技术栈拆解 | ✅ | ✅ |
| 阶段 2：项目复现 | ✅ | ✅ |
| 阶段 3：横向评测 | ❌ | ✅ |
| 阶段 4：最优组合 | ❌ | ✅ |
| 超越原项目 | ❌ | ✅ |

## 使用示例

```python
from ball_project_assimilator.recipes.simple_reproduction import run_simple_reproduction

result = run_simple_reproduction(
    project_dir="path/to/dynamic-tennis",
    project_type="tennis",
    output_dir="path/to/output",
)
```

## 迁移指南

如果需要从简化版升级到完整版：
1. 使用 `open-project-skill-distiller` 重新生成技术栈图谱
2. 使用 `stack-method-benchmark` 进行横向评测
3. 使用 `best-stack-composer` 组合最优方法
4. 验证增强版是否超越原项目

---

*Recipe 版本：v1.0.0*
*对应 Plugin：ball-project-assimilator*
*来源：原 ball-project-distiller 功能整合*