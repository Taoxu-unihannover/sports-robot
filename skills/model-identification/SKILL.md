---
name: model-identification
description: 用于球类机器人的参数辨识与在线自适应，覆盖飞行阻力、反弹恢复系数、摩擦、惯量、驱动常数、轮径、延迟和噪声参数的离线批量辨识和在线递推更新。适用于用户需要实现系统辨识、参数拟合、RLS、最小二乘、sim-to-real 校准；不用于在线状态估计或控制器设计。
when_to_use: 用户提到系统辨识、参数拟合、RLS、least squares、摩擦辨识、阻力参数、sim-to-real、domain randomization、参数漂移、在线自适应时触发。
version: 1.1.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [data_source, parameter_set]
  properties:
    data_source:
      type: string
      description: 辨识数据来源（日志文件路径或在线数据流标识）
    parameter_set:
      type: string
      enum: [flight_drag, bounce, friction, inertia, drive_train, all]
      description: 待辨识参数集
    method:
      type: string
      enum: [batch_nls, rls, dual_ekf]
      description: 辨识方法，默认 batch_nls
    constraints:
      type: object
      description: 参数物理约束（上下界）
output_schema:
  type: object
  required: [parameters, residuals, confidence]
  properties:
    parameters:
      type: object
      description: 辨识得到的参数值
    residuals:
      type: object
      description: 拟合残差统计（RMSE, max_error）
    confidence:
      type: number
      description: 参数置信度 [0, 1]
    parameter_covariance:
      type: array
      description: 参数协方差矩阵
---

# 参数辨识与在线自适应

## 何时使用

当用户需要从实验数据中辨识球类机器人系统的物理参数，或需要在线修正参数漂移时使用。典型场景：

- 首次部署时的系统辨识（阻力、摩擦、恢复系数）
- 换球/换台/换场地后的参数重整定
- 在线参数漂移修正（球磨损、胶皮老化）
- sim-to-real 仿真参数校准

不适用于：在线状态估计（用 ball-state-estimator）、控制器设计（用 mpc-controller）。

## 输入约束

- 辨识数据必须包含激励充分的多组实验（持续激励条件）
- 参数必须有物理上下界约束（如 $e_n \in [0, 1]$，$\mu > 0$）
- 在线更新必须有冻结条件，避免把感知异常学成"新参数"
- 批量辨识数据应按球种、球速、转速和场地分组

## 执行步骤

### 步骤 1：数据准备与激励检验

- 动作：加载辨识数据，检查激励充分性
- 输入：data_source, parameter_set
- 成功标准：数据覆盖参数空间，条件数可接受
- 失败处理：激励不足时返回 `insufficient_excitation`，建议补充实验

### 步骤 2：参数拟合

- 动作：根据 method 选择批量 NLS / RLS / 双 EKF
- 输入：数据 + 参数初值 + 物理约束
- 成功标准：拟合收敛，残差在可接受范围
- 失败处理：不收敛时调整初值或放宽约束重试

### 步骤 3：验证与固化

- 动作：在验证集上评估辨识参数的泛化能力
- 输入：辨识参数 + 验证数据
- 成功标准：验证集误差不超过训练集误差的 2 倍
- 失败处理：泛化不足时增加训练数据或降低模型复杂度

## 输出格式

```json
{
  "parameters": {
    "k_d": 0.0045,
    "e_n_table": 0.92,
    "mu_paddle": 0.65
  },
  "residuals": {
    "rmse": 0.012,
    "max_error": 0.045
  },
  "confidence": 0.89,
  "parameter_covariance": [[0.001, 0.0001], [0.0001, 0.002]]
}
```

## 可用方法与代表性系统

### 方法一：离线批量最小二乘 — MIT 路线

MIT 轻量乒乓球平台采用最实用的 lumped 参数策略：

1. **飞行参数**：用二次阻力模型，忽略 Magnus 效应，只辨识 $k_d$
2. **弹跳参数**：用恢复系数 $e_n$ 和摩擦系数 $\mu$，不区分速度区间
3. **辨识方法**：标准非线性最小二乘（NLS），用真实轨迹数据拟合
4. **优势**：参数少、辨识快、在低自由度系统上精度足够
5. **局限**：强简化假设在高旋转或高自由度系统中可能不足

### 方法二：集成系统辨识 — ETH 路线

ETH 腿足羽毛球系统将系统辨识提升到系统级：

1. **感知噪声辨识**：在仿真中引入与真实 ZED X 相机一致的噪声模型
2. **飞行参数辨识**：用真实飞行数据辨识阻力系数和旋转衰减
3. **动力学参数辨识**：用关节编码器和力传感器辨识机器人参数
4. **统一校准**：将辨识结果统一纳入仿真器，使仿真链路与真实一致
5. **核心思想**：感知误差和模型误差在闭环中耦合，必须联合辨识

### 方法三：仿真校准 + 域随机化 — DeepMind 路线

DeepMind 采用"辨识→校准→域随机化"三步法：

1. **辨识**：用高速相机采集真实轨迹，反推物理参数
2. **校准**：将参数填入 MuJoCo，比较仿真-现实一致性
3. **域随机化**：对关键参数施加随机扰动，增强鲁棒性

### 方法对比

| 维度 | 批量NLS (MIT) | 集成辨识 (ETH) | 仿真校准 (DeepMind) |
|------|--------------|---------------|-------------------|
| 辨识范围 | 飞行+弹跳 | 全系统 | 全系统 |
| 在线能力 | 否 | 部分 | 否 |
| 精度 | 中（lumped） | 高 | 高 |
| 复杂度 | 低 | 高 | 高 |
| sim-to-real | 间接 | 直接 | 直接 |

## 可用方案（Recipes）

| Recipe | 适用球类 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [eth-system-identification](recipes/eth-system-identification/RECIPE.md) | 羽毛球 | 集成辨识 (ETH) | advanced | 否 | 全系统联合辨识 |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 激励不足 | 条件数过大 | 返回 insufficient_excitation，建议补充实验 |
| 拟合不收敛 | 残差未下降 | 调整初值或放宽约束重试 |
| 参数越界 | 超出物理约束 | 钳位到约束边界并标记 |
| 泛化不足 | 验证集误差过大 | 增加训练数据或降低模型复杂度 |
| 在线异常 | 残差突增 | 冻结参数更新，使用上一组可靠参数 |
| 数据损坏 | 格式/范围异常 | 跳过损坏数据段，使用有效段辨识 |
