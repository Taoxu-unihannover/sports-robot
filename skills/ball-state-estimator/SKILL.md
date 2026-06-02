---
name: ball-state-estimator
description: 用于球类运动的状态估计与速度估计，对含噪 2D/3D 观测做时域平滑并估计速度/加速度。支持 CV（恒速）、CA（恒加速）、EKF（含空气阻力）三种 Kalman 滤波模型，以及 SlidingWindowVelocity（滑窗平均速度）和 PositionHistoryVelocity（位置历史隐式估计）三种速度估计路线。适用于用户需要实现 Kalman 滤波、状态估计、速度估计、轨迹预测、EKF；不用于信号处理中的频域滤波或图像滤波。
when_to_use: 用户提到 Kalman 滤波、状态估计、速度估计、轨迹预测、EKF、ball filter、motion model、恒速模型、滑窗平均速度、velocity estimation 时触发。
version: 2.0.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [measurement]
  properties:
    measurement:
      type: array
      description: 2D [x, y] 或 3D [x, y, z] 观测值
    dt:
      type: number
      description: 时间步长，默认 0.008 (125Hz)
    model:
      type: string
      enum: [CV, CA, EKF, sliding_window, position_history]
      description: 速度估计模型，默认 CV
output_schema:
  type: object
  required: [x, y, z, vx, vy, vz]
  properties:
    x: { type: number }
    y: { type: number }
    z: { type: number }
    vx: { type: number }
    vy: { type: number }
    vz: { type: number }
    ax: { type: number }
    ay: { type: number }
    az: { type: number }
---

# 球类状态估计与速度估计

## 何时使用

当用户需要对含噪的球类位置观测做时域平滑，并估计无法直接观测的速度/加速度时使用。典型场景：

- 平滑检测器输出的抖动 2D/3D 坐标
- 估计球的飞行速度用于击球时机预测
- 在短暂遮挡期间用运动模型外推位置
- 融合多传感器观测（视觉 + IMU）
- 对比不同速度估计方法（KF 内隐 vs 滑窗平均 vs 位置历史）

不适用于：信号频域滤波、图像平滑滤波、非时序数据去噪。

## 输入约束

- 观测为 2D [x, y] 或 3D [x, y, z] 数值数组
- 需要合理的 dt（时间步长）匹配实际帧率
- CV 模型适用于匀速运动（乒乓球飞行中段）
- CA 模型适用于变速运动（羽毛球受空气阻力）
- EKF 适用于非线性运动（含空气阻力和重力）
- SlidingWindowVelocity 需要至少 N 帧历史位置
- PositionHistoryVelocity 需要策略网络配合，不独立输出速度

## 执行步骤

### 步骤 1：预测（Predict）

- 动作：用运动模型从上一时刻状态预测当前状态
- 输入：上一时刻状态 x_{k-1}，协方差 P_{k-1}
- 成功标准：输出预测状态 x_{k|k-1} 和预测协方差 P_{k|k-1}
- 失败处理：未初始化时使用初始状态（零均值，大协方差）

### 步骤 2：更新（Update）

- 动作：用新观测修正预测值，计算 Kalman 增益
- 输入：观测 z_k，预测状态 x_{k|k-1}
- 成功标准：输出后验状态 x_{k|k}，协方差 P_{k|k} 减小
- 失败处理：观测缺失时跳过更新，仅做预测

### 步骤 3：外推预测

- 动作：用当前状态预测未来 t 秒后的位置
- 输入：当前状态 x，预测时间 t
- 成功标准：输出未来位置
- 失败处理：未初始化时返回 None

## 输出格式

```json
{
  "x": 1.23, "y": -0.45, "z": 2.10,
  "vx": 3.5, "vy": -1.2, "vz": -0.8,
  "ax": 0.0, "ay": 0.0, "az": 0.0
}
```

## 可用方法与代表性系统

速度估计是球类机器人感知链路中的关键环节。有限差分 $\hat{\mathbf{v}}_t = (\mathbf{p}_t - \mathbf{p}_{t-1})/\Delta t$ 的噪声方差为 $\sigma_v^2 = 2\sigma_p^2 / \Delta t^2$，在高动态球类中不可接受。实际系统采用以下三种路线：

### 方法一：Kalman Filter 内隐速度估计 — DeepMind / ETH 路线

Kalman Filter 的状态向量直接包含速度 $\mathbf{x} = [\mathbf{p}, \mathbf{v}]$，速度不是通过差分显式计算的，而是通过预测-更新循环隐式估计的：

- **预测步**：$\hat{\mathbf{x}}_{k|k-1} = \mathbf{F}\hat{\mathbf{x}}_{k-1|k-1}$，状态转移矩阵 $\mathbf{F}$ 编码运动模型（恒速 CV 或含阻力的非线性模型）
- **更新步**：$\hat{\mathbf{x}}_{k|k} = \hat{\mathbf{x}}_{k|k-1} + \mathbf{K}_k(\mathbf{z}_k - \mathbf{H}\hat{\mathbf{x}}_{k|k-1})$，Kalman 增益 $\mathbf{K}_k$ 自动将位置残差分配到位置和速度两个状态分量上

**DeepMind 案例**：CV Kalman Filter，状态向量 $[\mathbf{p}, \mathbf{v}]$，恒速运动模型。125 Hz 感知频率，速度估计噪声由协方差矩阵 $\mathbf{P}$ 控制。检测丢失时预测步仍可外推。

**ETH 案例**：EKF（Extended Kalman Filter），状态向量 $[\mathbf{p}, \mathbf{v}]$，预测步使用含空气阻力和重力的非线性运动模型。EKF 以 400 Hz 运行，远高于感知的 60 Hz，在检测丢失时靠预测步维持状态估计。

**适用**：需要实时速度估计、检测丢失时需要外推、追求估计可解释性的场景。

### 方法二：滑窗平均速度 — LATENT 路线

LATENT 系统使用 4 帧滑动窗口平均速度：

$$\hat{\mathbf{v}}_t = \frac{1}{N-1} \sum_{i=1}^{N-1} \frac{\mathbf{p}_{t-i+1} - \mathbf{p}_{t-i}}{\Delta t}, \quad N=4$$

噪声方差降低为单帧差分的 $1/(N-1) = 1/3$。代价是引入约 $(N-1)\Delta t / 2 = 30$ ms 的额外延迟，且平均操作会平滑掉真实的加速度变化。

**LATENT 案例**：4 帧滑窗，50 Hz planner/control 循环中使用平均速度作为策略输入。当 $\Delta t = 20$ ms、位置噪声 $\sigma_p = 5$ mm 时，速度噪声从 0.35 m/s 降至约 0.20 m/s。

**适用**：需要简单有效的速度估计、不需要外推能力、可容忍少量延迟的场景。

### 方法三：位置历史隐式恢复速度 — ETH prediction-free 路线

ETH 的 prediction-free 策略不显式输出速度，而是把最近若干帧的位置历史 $\{\mathbf{p}_{t}, \mathbf{p}_{t-1}, \ldots, \mathbf{p}_{t-N+1}\}$ 直接作为策略网络的输入。策略网络（MLP 或小型 Transformer）在训练中自动学会从位置序列中提取速度和趋势信息——本质上是数据驱动的速度估计。

**ETH prediction-free 案例**：位置历史作为策略输入，网络隐式学习"可微分的差分+滤波"操作。优势是免手动调参（$\mathbf{Q}$、$\mathbf{R}$ 矩阵），劣势是速度估计质量难以独立评估和调试。

**适用**：端到端学习框架、不需要独立速度输出、有充足训练数据的场景。

### 方法对比

| 维度 | KF 内隐 (DeepMind/ETH) | 滑窗平均 (LATENT) | 位置历史 (ETH p-free) |
|------|----------------------|-------------------|---------------------|
| 速度估计方式 | 预测-更新循环隐式 | 多帧差分取平均 | 网络隐式学习 |
| 噪声抑制 | 协方差 $\mathbf{P}$ 控制 | $1/(N-1)$ 降低 | 数据驱动自适应 |
| 检测丢失外推 | ✅ 靠运动模型 | ❌ 需要连续帧 | ❌ 需要连续帧 |
| 额外延迟 | 无 | ~30 ms (N=4) | 取决于网络推理 |
| 可解释性 | 高（可检查 $\mathbf{P}$） | 中 | 低（嵌入隐层） |
| 调参需求 | $\mathbf{Q}$、$\mathbf{R}$ 矩阵 | 窗口大小 N | 无（数据驱动） |
| 训练数据需求 | 无 | 无 | 需要大量数据 |

## 可用方案（Recipes）

| Recipe | 适用球类 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [deepmind-cv-kf](recipes/deepmind-cv-kf/RECIPE.md) | 乒乓球 | CV Kalman Filter (DeepMind) | beginner | 否 | 125Hz，可外推 |
| [eth-ekf-badminton](recipes/eth-ekf-badminton/RECIPE.md) | 羽毛球 | EKF 含空气阻力 (ETH) | intermediate | 否 | 400Hz 估计，60Hz 感知 |
| [latent-sliding-window](recipes/latent-sliding-window/RECIPE.md) | 乒乓球/羽毛球 | 滑窗平均 (LATENT) | beginner | 否 | 噪声降至1/3，延迟30ms |

选择建议：
- 通用实时系统 → KF 内隐估计（CV/CA/EKF）
- 简单快速验证 → 滑窗平均速度
- 端到端学习框架 → 位置历史隐式估计

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 未初始化 | initialized == False | 使用初始状态做预测 |
| 观测缺失 | measurement is None | 跳过 update，仅 predict |
| 协方差发散 | P 矩阵对角元过大 | 重置滤波器 |
| 模型不匹配 | 残差异常大 | 增大 measurement_noise 或切换模型 |
| 历史帧不足 | len(history) < N | 降级为有限差分 |
