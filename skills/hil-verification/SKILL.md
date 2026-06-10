---
name: hil-verification
description: 用于球类机器人的硬件在环（HIL）验证，覆盖日志回放、仿真-实机对比、回归测试和安全验证。适用于用户需要实现 HIL 测试、日志回放、回归测试、仿真对比；不用于在线控制或感知。
when_to_use: 用户提到 HIL、硬件在环、日志回放、回归测试、仿真对比、验证、verification、log replay 时触发。
version: 1.1.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [test_type, test_data]
  properties:
    test_type:
      type: string
      enum: [log_replay, sim_comparison, regression, safety_validation]
      description: 测试类型
    test_data:
      type: object
      description: 测试数据
      properties:
        log_file: { type: string, description: 日志文件路径 }
        scenario: { type: string, description: 测试场景 }
        expected_results: { type: object }
        safety_requirements: { type: array }
    system_under_test:
      type: string
      description: 被测系统标识
output_schema:
  type: object
  required: [test_result, metrics]
  properties:
    test_result:
      type: string
      enum: [pass, fail, error, skipped]
    metrics:
      type: object
      description: 测试指标
      properties:
        position_error_rmse: { type: number }
        velocity_error_rmse: { type: number }
        timing_accuracy: { type: number }
        safety_compliance: { type: boolean }
    details:
      type: array
      description: 详细测试结果
    recommendations:
      type: array
      description: 改进建议
---

# 硬件在环验证

## 何时使用

当用户需要在硬件在环环境中验证球类机器人系统时使用。典型场景：

- 日志回放验证（用历史数据测试新算法）
- 仿真-实机对比（验证仿真保真度）
- 回归测试（确保新版本不引入问题）
- 安全验证（验证安全功能正确性）

不适用于：在线控制、感知算法开发。

## 输入约束

- 日志文件必须包含完整的时间戳和数据
- 测试场景必须覆盖关键工况
- 安全验证必须覆盖所有安全功能
- 回归测试必须有明确的通过/失败标准

## 执行步骤

### 步骤 1：测试准备

- 动作：加载测试数据和环境配置
- 输入：test_type, test_data
- 成功标准：测试环境就绪
- 失败处理：数据缺失时跳过测试

### 步骤 2：执行测试

- 动作：根据测试类型执行验证
- 输入：测试配置 + 被测系统
- 成功标准：测试完成，结果可评估
- 失败处理：执行异常时标记 error

### 步骤 3：结果评估

- 动作：评估测试结果并生成报告
- 输入：测试输出 + 期望结果
- 成功标准：所有指标在可接受范围内
- 失败处理：指标超限时标记 fail 并给出建议

## 输出格式

```json
{
  "test_result": "pass",
  "metrics": {
    "position_error_rmse": 0.012,
    "velocity_error_rmse": 0.15,
    "timing_accuracy": 0.998,
    "safety_compliance": true
  },
  "details": [
    {"scenario": "normal_hit", "result": "pass", "error": 0.008},
    {"scenario": "edge_case", "result": "pass", "error": 0.015}
  ],
  "recommendations": []
}
```

## 可用方法与代表性系统

### 日志回放验证

用历史数据验证新算法：

1. **数据采集**：记录完整的传感器数据和控制输出
2. **回放**：按时间戳回放传感器数据到新算法
3. **对比**：比较新算法输出与历史输出
4. **指标**：位置/速度 RMSE、时序精度、安全合规

### 仿真-实机对比

验证仿真保真度：

1. **相同输入**：在仿真和实机上施加相同输入
2. **输出对比**：比较两者的输出轨迹
3. **一致性指标**：归一化均方误差、相关系数
4. **边界场景**：重点对比极端工况

### 安全验证

验证安全功能：

1. **正常场景**：安全功能不应误触发
2. **异常场景**：安全功能应正确触发
3. **边界场景**：安全功能应在阈值处正确切换
4. **恢复场景**：安全功能应能正确恢复

## 可用方案（Recipes）

| Recipe | 适用场景 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [log-replay-hil](recipes/log-replay-hil/RECIPE.md) | 日志回放 | 日志回放验证 | intermediate | 否 | 位置RMSE < 1cm |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 数据缺失 | 日志不完整 | 跳过测试，标记 skipped |
| 执行异常 | 被测系统崩溃 | 标记 error，记录异常 |
| 指标超限 | RMSE > 阈值 | 标记 fail，给出改进建议 |
| 安全违规 | 安全功能未触发 | 标记 fail，高优先级修复 |
| 时序异常 | 延迟超限 | 标记 fail，优化时序 |
