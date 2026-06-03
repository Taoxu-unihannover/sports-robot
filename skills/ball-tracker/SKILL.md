---
name: ball-tracker
description: 用于球类机器人的多帧球跟踪，覆盖卡尔曼跟踪、匈牙利匹配、轨迹管理和遮挡恢复。适用于用户需要实现球跟踪、多目标跟踪、轨迹关联、遮挡恢复；不用于单帧检测或状态估计。
when_to_use: 用户提到球跟踪、多目标跟踪、轨迹关联、匈牙利匹配、遮挡恢复、ball tracking、track management、data association 时触发。
version: 1.1.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [detections, tracks]
  properties:
    detections:
      type: array
      description: 当前帧检测结果
      items:
        type: object
        properties:
          position_2d: { type: array }
          confidence: { type: number }
          timestamp: { type: number }
    tracks:
      type: array
      description: 当前活跃轨迹
      items:
        type: object
        properties:
          track_id: { type: integer }
          state: { type: array }
          covariance: { type: array }
          age: { type: integer }
          missed_frames: { type: integer }
    max_missed_frames:
      type: integer
      description: 最大丢失帧数，默认 5
output_schema:
  type: object
  required: [updated_tracks, assignments]
  properties:
    updated_tracks:
      type: array
      description: 更新后的轨迹列表
    assignments:
      type: array
      description: 检测-轨迹分配结果
    new_tracks:
      type: array
      description: 新创建的轨迹
    deleted_tracks:
      type: array
      description: 被删除的轨迹ID
---

# 多帧球跟踪

## 何时使用

当用户需要在连续帧之间跟踪球并维护轨迹时使用。典型场景：

- 单球/多球的连续跟踪
- 检测-轨迹关联（匈牙利匹配）
- 遮挡后的轨迹恢复
- 轨迹生命周期管理

不适用于：单帧检测（用 ball-detector）、状态估计（用 ball-state-estimator）。

## 输入约束

- 检测结果必须包含时间戳
- 轨迹状态必须包含协方差
- 匹配距离门限应根据球速设定
- 丢失帧数阈值应根据帧率设定

## 执行步骤

### 步骤 1：预测

- 动作：用运动模型预测现有轨迹到当前时刻
- 输入：tracks + dt
- 成功标准：预测状态合理
- 失败处理：预测发散时重置轨迹

### 步骤 2：数据关联

- 动作：用匈牙利算法匹配检测和轨迹
- 输入：detections + 预测轨迹 + 距离门限
- 成功标准：匹配结果合理
- 失败处理：无匹配时创建新轨迹或增加丢失计数

### 步骤 3：轨迹管理

- 动作：更新匹配轨迹、创建新轨迹、删除过期轨迹
- 输入：匹配结果
- 成功标准：轨迹列表更新完成
- 失败处理：轨迹异常时标记或删除

## 输出格式

```json
{
  "updated_tracks": [
    {"track_id": 1, "state": [1.2, 0.3, 3.0, -1.0], "age": 15, "missed_frames": 0}
  ],
  "assignments": [
    {"track_id": 1, "detection_idx": 0, "distance": 0.5}
  ],
  "new_tracks": [],
  "deleted_tracks": [2]
}
```

## 可用方法与代表性系统

### 卡尔曼跟踪 + 匈牙利匹配

标准的检测-跟踪框架：

1. **预测**：卡尔曼滤波预测轨迹到当前时刻
2. **关联**：匈牙利算法最小化总匹配代价
3. **更新**：匹配的轨迹用观测更新，未匹配的增加丢失计数
4. **管理**：丢失超限的轨迹删除，未匹配的检测创建新轨迹

### 遮挡恢复策略

| 策略 | 描述 | 适用场景 |
|------|------|---------|
| 预测维持 | 丢失期间仅预测 | 短暂遮挡 |
| 协方差膨胀 | 增大搜索范围 | 中等遮挡 |
| 外观重识别 | 用外观特征匹配 | 长时间遮挡 |

## 可用方案（Recipes）

| Recipe | 适用球类 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [deepmind-cv-kf](../ball-state-estimator/recipes/deepmind-cv-kf/RECIPE.md) | 乒乓球 | CV+KF+匈牙利 | intermediate | 否 | 125Hz 跟踪 |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 预测发散 | 状态超限 | 重置轨迹 |
| 匹配失败 | 无有效匹配 | 创建新轨迹 |
| ID 切换 | 匹配不稳定 | 增加门限或使用外观特征 |
| 遮挡过长 | 丢失帧超限 | 删除轨迹 |
| 误检 | 低置信度检测 | 提高检测阈值 |
