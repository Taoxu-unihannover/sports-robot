name: best-stack-composer
description: 组合各技术栈最优方法形成整体系统，检查兼容性，验证能否超过原项目性能。适用于用户需要将单项最优方法组合为完整系统；不用于单项评测或技能蒸馏。
---

# 最优技术栈组合器

## 用途

将 stack-method-benchmark 输出的各技术栈最优方法组合成整体系统，检查组合兼容性（schema、频率、延迟、坐标系），运行整体评测，验证能否超过原项目 A 的性能。

## 输入

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| best_method_per_stack | dict | 是 | 每个技术栈的最优方法 {stack: {method, skill, config}} |
| compatibility_schema | dict | 是 | 兼容性检查规则 |
| baseline_metrics | dict | 是 | 项目 A 的 baseline 指标 |
| target_improvement | float | 否 | 目标超越比例，默认 0.05 (5%) |

## 输出

| 产物 | 路径 | 说明 |
|---|---|---|
| 最优组合配置 | best_stack.yaml | 每个技术栈选择的 skill、方法、版本、参数 |
| 兼容性报告 | compatibility_report.md | schema/频率/延迟/坐标系/安全检查结果 |
| 增强项目计划 | enhanced_project_plan.md | 增强项目的生成计划 |
| 超越报告 | plus_performance_report.md | 与项目 A、复现版的整体性能对比 |

## 执行步骤

### 步骤 1：生成最优组合配置

```yaml
# best_stack.yaml
simulation:
  skill: mujoco-tennis-world-builder
  method: from_xml_with_temp_dir
  version: "1.0"
  config:
    xml_template: tennis_world.xml
    frame_skip: 20

perception:
  skill: truth-state-policy-input
  method: mecanum-12d-observation
  version: "1.0"
  config:
    observation_dim: 12

training:
  skill: sb3-rl-training-runner
  method: sac-mecanum-navigation
  version: "1.0"
  config:
    algorithm: SAC
    learning_rate: 5e-4
    buffer_size: 3000000
    batch_size: 512
```

### 步骤 2：检查组合兼容性

| 检查项 | 说明 | 通过条件 |
|---|---|---|
| 输入输出 schema | 上游输出 = 下游输入 | 维度、类型、范围一致 |
| 控制频率 | 感知→控制→执行频率匹配 | 延迟 < 控制周期 |
| 坐标系 | 所有模块使用同一坐标系 | 一致或有明确转换 |
| 单位 | 距离(m)、速度(m/s)、角度(rad) | 一致 |
| 安全边界 | 安全监督覆盖所有执行器 | 无盲区 |

### 步骤 3：处理组合冲突

单项最优 ≠ 整体最优。若组合后退化：

1. 记录冲突原因（延迟、schema 不匹配等）
2. 尝试次优方法替代
3. 若仍退化，记录为 tradeoff

### 步骤 4：生成增强项目

基于最优组合配置，通过 sports-robot skills 生成增强项目。

### 步骤 5：运行整体评测

同时对比三个版本：
- 项目 A baseline
- sports-robot 复现版
- 增强版

### 步骤 6：输出超越报告

| 指标 | 项目 A | 复现版 | 增强版 | 增强版 vs A |
|---|---|---|---|---|
| 成功率 | ... | ... | ... | +X% |
| 平均 reward | ... | ... | ... | +X% |
| 最终距离 | ... | ... | ... | -X% |

## 超越标准

- 核心任务指标超过项目 A baseline 至少 5%
- 不允许安全性、稳定性、可运行性退化
- 允许部分非核心指标小幅下降，但必须在报告中解释代价

## 验证方式

1. 兼容性检查覆盖所有模块对
2. 增强项目可运行
3. 评测使用与 baseline 相同的条件
4. 报告同时对比三个版本
