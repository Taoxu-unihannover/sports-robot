---
name: model-uncertainty-risk
description: 用于建模不确定性量化、协方差传播、命中概率计算、风险边界评估、CVaR 和模型切换决策。把估计误差传递给控制层安全约束。适用于用户需要实现不确定性量化、风险评估、协方差传播、模型切换；不用于状态估计或参数辨识。
when_to_use: 用户提到协方差、风险、uncertainty、CVaR、命中概率、鲁棒性、Monte Carlo、模型切换、风险约束时触发。
version: 1.1.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [state_estimate, uncertainty_sources]
  properties:
    state_estimate:
      type: object
      description: 状态估计（含协方差）
      properties:
        state: { type: array }
        covariance: { type: array }
    uncertainty_sources:
      type: array
      description: 不确定性来源列表
      items:
        type: object
        properties:
          name: { type: string }
          type: { type: string, enum: [perception_noise, delay_jitter, parameter_drift, contact_mismatch, environment_change] }
          magnitude: { type: number }
    risk_threshold:
      type: number
      description: 风险阈值，默认 0.05（5%）
output_schema:
  type: object
  required: [risk_level, hit_probability, recommended_action]
  properties:
    risk_level:
      type: string
      enum: [low, medium, high, critical]
    hit_probability:
      type: number
      description: 命中概率 [0, 1]
    risk_bound:
      type: number
      description: 风险上界（CVaR 或分位数）
    recommended_action:
      type: string
      enum: [aggressive_hit, conservative_hit, defensive_reset, abort]
    model_switch_recommendation:
      type: string
      description: 模型切换建议（若有）
---

# 不确定性与风险评估

## 何时使用

当用户需要量化建模层输出的不确定性，并将风险信息传递给控制层时使用。典型场景：

- 评估击球命中的概率和风险
- 在不确定度较大时选择保守策略
- 决定是否需要切换到更简单/更鲁棒的模型
- 离线 Monte Carlo 评估策略边界

不适用于：状态估计（用 ball-state-estimator）、参数辨识（用 model-identification）。

## 输入约束

- state_estimate 必须包含协方差矩阵
- uncertainty_sources 应覆盖五类不确定性
- risk_threshold 应根据安全需求设定
- 协方差矩阵必须对称正定

## 执行步骤

### 步骤 1：不确定性分类与传播

- 动作：将不确定性分为五类并传播协方差
- 输入：state_estimate, uncertainty_sources
- 成功标准：传播后的协方差合理增长
- 失败处理：协方差发散时重置或切换模型

### 步骤 2：命中概率计算

- 动作：计算在当前不确定度下的命中概率
- 输入：传播后协方差 + 拍面大小 + 击球窗口
- 成功标准：命中概率在 [0, 1] 范围内
- 失败处理：计算失败时使用保守估计

### 步骤 3：风险决策

- 动作：根据风险等级推荐控制策略
- 输入：命中概率 + risk_threshold
- 成功标准：推荐策略与风险等级匹配
- 失败处理：风险过高时推荐放弃击球

## 输出格式

```json
{
  "risk_level": "medium",
  "hit_probability": 0.72,
  "risk_bound": 0.15,
  "recommended_action": "conservative_hit",
  "model_switch_recommendation": null
}
```

## 可用方法与代表性系统

### 协方差传播

线性化后的协方差传播：$P_{k+1} = A_k P_k A_k^\top + Q_k$

### 五类不确定性

| 类型 | 来源 | 典型量级 |
|------|------|---------|
| 感知噪声 | 相机检测误差 | 1-3 cm |
| 延迟抖动 | 观测延迟波动 | ±5 ms |
| 参数漂移 | 球磨损/环境变化 | 5-10% |
| 接触失配 | 碰撞模型简化 | 系统性偏差 |
| 环境变化 | 换场地/换球 | 可达 20% |

### 风险度量

- **命中概率**：球落在拍面范围内的概率
- **VaR**：击球偏差的 $\alpha$-分位数
- **CVaR**：最坏 $1-\alpha$ 情况下的平均偏差

## 可用方案（Recipes）

| Recipe | 适用球类 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [ace-spin-state-fusion](recipes/ace-spin-state-fusion/RECIPE.md) | 乒乓球 | Ace 旋转+状态融合 | advanced | 否 | 协方差传播+风险门控 |
| [deepmind-delay-distribution](recipes/deepmind-delay-distribution/RECIPE.md) | 乒乓球/网球/羽毛球 | DeepMind 延迟分布建模 | advanced | 否 | 协方差膨胀+策略降级 |
| [gtsam-isam2-async-fusion](recipes/gtsam-isam2-async-fusion/RECIPE.md) | 乒乓球/网球/羽毛球 | GTSAM/ISAM2 异步融合 | advanced | 否 | 增量更新<0.5ms |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 协方差发散 | 对角元超限 | 重置协方差或切换模型 |
| 命中概率极低 | < 10% | 推荐放弃击球 |
| 风险不可接受 | CVaR > 阈值 | 推荐防守复位 |
| 不确定性来源未知 | 缺少分类 | 使用最坏情况估计 |
| 模型切换频繁 | 短时间内多次切换 | 锁定当前模型，增加观测 |
