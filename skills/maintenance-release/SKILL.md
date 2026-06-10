---
name: maintenance-release
description: 用于球类机器人的运维与发布流程，覆盖 CI/CD、仿真-实机一致性校验、参数热更新、安全回滚和版本管理。适用于用户需要实现 CI/CD、仿真校验、参数更新、安全回滚、版本管理；不用于控制算法或感知算法。
when_to_use: 用户提到 CI/CD、仿真校验、sim-to-real、参数更新、热更新、回滚、版本管理、release、deployment、运维时触发。
version: 1.1.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [release_type, change_description]
  properties:
    release_type:
      type: string
      enum: [major, minor, patch, hotfix, parameter_update]
      description: 发布类型
    change_description:
      type: string
      description: 变更描述
    affected_skills:
      type: array
      description: 受影响的技能列表
    simulation_results:
      type: object
      description: 仿真验证结果
    rollback_plan:
      type: string
      description: 回滚计划
output_schema:
  type: object
  required: [release_status, validation_results]
  properties:
    release_status:
      type: string
      enum: [approved, conditional, rejected]
    validation_results:
      type: object
      description: 验证结果
      properties:
        simulation_passed: { type: boolean }
        consistency_check: { type: string, enum: [pass, warning, fail] }
        safety_review: { type: string, enum: [approved, conditional, rejected] }
    deployment_steps:
      type: array
      description: 部署步骤
    rollback_instructions:
      type: string
      description: 回滚指令
---

# 运维与发布流程

## 何时使用

当用户需要管理球类机器人系统的发布和运维时使用。典型场景：

- 新版本发布前的仿真-实机一致性校验
- 参数热更新和版本管理
- 安全回滚策略设计
- CI/CD 流程配置

不适用于：控制算法设计、感知算法设计。

## 输入约束

- major/minor 发布必须通过完整仿真验证
- hotfix 必须有明确的回滚计划
- 参数更新必须先在仿真中验证
- 所有发布必须记录变更日志

## 执行步骤

### 步骤 1：变更影响分析

- 动作：分析变更影响的技能和子系统
- 输入：change_description, affected_skills
- 成功标准：影响范围明确
- 失败处理：影响不明确时要求补充信息

### 步骤 2：仿真验证

- 动作：在仿真中验证变更
- 输入：变更 + 仿真环境 + 验证场景
- 成功标准：仿真结果与预期一致
- 失败处理：仿真不通过时拒绝发布

### 步骤 3：安全审查与部署

- 动作：安全审查后执行部署
- 输入：验证结果 + 安全审查
- 成功标准：部署完成且系统正常
- 失败处理：部署异常时执行回滚

## 输出格式

```json
{
  "release_status": "approved",
  "validation_results": {
    "simulation_passed": true,
    "consistency_check": "pass",
    "safety_review": "approved"
  },
  "deployment_steps": [
    "1. 备份当前参数",
    "2. 部署新版本到仿真环境验证",
    "3. 部署到实机",
    "4. 执行功能验证测试"
  ],
  "rollback_instructions": "回滚到 v1.0.3: ros2 launch rollback version:=1.0.3"
}
```

## 可用方法与代表性系统

### 发布流程

| 发布类型 | 仿真验证 | 安全审查 | 回滚计划 |
|---------|---------|---------|---------|
| major | 完整 | 必须 | 必须 |
| minor | 完整 | 必须 | 必须 |
| patch | 回归 | 必须 | 必须 |
| hotfix | 最小 | 必须 | 必须 |
| parameter_update | 参数相关 | 条件 | 条件 |

### 仿真-实机一致性校验

1. **参数一致性**：仿真参数与实机参数对比
2. **行为一致性**：相同输入下的输出对比
3. **性能一致性**：延迟、精度等指标对比
4. **边界一致性**：极端工况下的行为对比

### 参数热更新

- 支持运行时更新的参数：控制增益、检测阈值、QoS 配置
- 需要重启的参数：模型参数、网络权重、调度配置
- 禁止热更新的参数：安全阈值（需要完整验证）

## 可用方案（Recipes）

| Recipe | 适用场景 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [eth-sim2real-validation](recipes/eth-sim2real-validation/RECIPE.md) | 仿真校验 | ETH 一致性校验 | intermediate | 否 | 仿真-实机行为对比 |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 仿真验证失败 | 结果不符合预期 | 拒绝发布，修复后重新验证 |
| 一致性校验失败 | 仿真-实机偏差过大 | 拒绝发布，校准仿真模型 |
| 安全审查未通过 | 存在安全风险 | 拒绝发布，修复安全问题 |
| 部署异常 | 部署后系统异常 | 立即执行回滚 |
| 参数更新冲突 | 新旧参数不兼容 | 重新验证后部署 |
| 回滚失败 | 回滚后系统异常 | 进入安全模式，人工介入 |
