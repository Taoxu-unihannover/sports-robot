---
name: ball-flight-model
description: 球/羽毛球飞行动力学、空气阻力、Magnus 旋转、反弹前预测和击球点外推 Skill。覆盖乒乓球、网球、羽毛球的在线降阶飞行模型。适用于用户需要实现球路预测、空气阻力建模、Magnus 效应、击球点预测；不用于碰撞建模或状态估计。
when_to_use: 用户提到球路预测、空气阻力、Magnus、飞行模型、羽毛球指数衰减、落点预测、击球点预测、trajectory prediction 时触发。
version: 1.1.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [state]
  properties:
    state:
      type: array
      description: 当前球状态 [px,py,pz,vx,vy,vz] 或含旋转 [px,py,pz,vx,vy,vz,wx,wy,wz]
    sport:
      type: string
      enum: [table_tennis, badminton, tennis]
      description: 球类，默认 table_tennis
    dt:
      type: number
      description: 积分步长（秒），默认 0.001
    predict_duration:
      type: number
      description: 预测时长（秒），默认 1.0
output_schema:
  type: object
  required: [predicted_trajectory, hit_candidates]
  properties:
    predicted_trajectory:
      type: array
      description: 预测轨迹点序列
    hit_candidates:
      type: array
      description: 候选击球点（时刻、位置、速度）
    bounce_points:
      type: array
      description: 弹跳点
    model_residual:
      type: number
      description: 模型残差（用于参数辨识反馈）
---

# 球路飞行与击球点预测

## 何时使用

当用户需要预测球的飞行轨迹和击球点时使用。典型场景：

- 从当前球状态预测未来飞行轨迹
- 计算候选击球时刻和位置
- 评估不同球类的空气动力学效应
- 为击球规划提供预测输入

不适用于：碰撞建模（用 ball-impact-contact）、状态估计（用 ball-state-estimator）。

## 输入约束

- state 必须包含至少位置和速度（6维），旋转为可选（9维）
- sport 决定使用哪种空气动力学模型
- dt 应小于飞行特征时间的 1/100
- 预测时长不应超过模型有效范围（通常 < 2 秒）

## 执行步骤

### 步骤 1：模型选择与初始化

- 动作：根据 sport 选择飞行模型和参数
- 输入：state, sport
- 成功标准：模型参数加载成功
- 失败处理：未知球类返回 `unsupported_sport`

### 步骤 2：轨迹积分

- 动作：按固定步长积分未来轨迹
- 输入：state + 模型参数 + dt + predict_duration
- 成功标准：积分完成，轨迹点数量合理
- 失败处理：积分发散时缩短预测时长或增大 dt

### 步骤 3：弹跳检测与击球点提取

- 动作：检测弹跳点，提取候选击球窗口
- 输入：预测轨迹 + 机器人可达域
- 成功标准：至少一个候选击球点
- 失败处理：无候选时返回空列表

## 输出格式

```json
{
  "predicted_trajectory": [[1.0, 0.5, 2.0], [1.1, 0.48, 1.95]],
  "hit_candidates": [
    {"time": 0.35, "position": [1.2, 0.3, 0.8], "velocity": [3.0, -1.0, -2.0]}
  ],
  "bounce_points": [{"time": 0.2, "position": [1.1, 0.4, 0.0]}],
  "model_residual": 0.003
}
```

## 可用方法与代表性系统

### 核心模型

球体飞行灰盒模型：

$$\dot p = v, \quad m\dot v = mg - k_d\|v\|v + k_m(\omega \times v)$$

羽毛球采用高阻力指数衰减模型，不直接照搬球体 Magnus 模型。

### 方法选择

| 场景 | 推荐模型 |
|---|---|
| 乒乓球飞行中段 | CV/EKF + lumped drag |
| 乒乓/网球旋转明显 | 阻力 + Magnus + 旋转衰减 |
| 羽毛球平抽/低平球 | 高阻力指数/分段模型 + EKF/UKF |
| 首版控制基线 | 简化飞行模型 + 离线辨识参数 |

## 可用方案（Recipes）

| Recipe | 适用球类 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [mit-lumped-drag](recipes/mit-lumped-drag/RECIPE.md) | 乒乓球 | MIT lumped drag | beginner | 否 | 简化飞行+离线辨识 |
| [eth-shuttle-aero](recipes/eth-shuttle-aero/RECIPE.md) | 羽毛球 | ETH 高阻力模型 | intermediate | 否 | 指数衰减+EKF |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 未知球类 | sport 不在枚举中 | 返回 unsupported_sport |
| 积分发散 | 速度/位置超限 | 缩短预测时长或增大 dt |
| 无候选击球点 | 轨迹不经过可达域 | 返回空列表 |
| 参数缺失 | 模型参数未加载 | 使用默认参数并标记 |
| 弹跳检测失败 | 高度穿越判断异常 | 跳过弹跳处理 |
