---
name: ball-spin-estimator
description: 用于球类运动的旋转（角速度）估计，从事件相机、球面标记或飞行轨迹推断球的角速度。支持 EventCameraSpin（事件相机光流回归）、MarkerPoseSpin（带标记球几何姿态估计）和 TrajectoryMagnusSpin（轨迹倒推 Magnus 效应）三种方法。适用于用户需要实现旋转估计、角速度估计、spin estimation、Magnus 效应、事件相机旋转、球面标记检测；不用于一般光流估计或 6-DoF 姿态估计。
when_to_use: 用户提到旋转估计、角速度、spin、Magnus 效应、事件相机旋转、球面标记、角速度估计、angular velocity、spin estimation、event camera spin、ball rotation 时触发。
version: 1.0.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [method]
  properties:
    method:
      type: string
      enum: [event_camera, marker_pose, trajectory_magnus]
      description: 旋转估计方法
    events:
      type: array
      description: 事件流 [(x, y, t, polarity), ...]，event_camera 方法使用
    positions_3d:
      type: array
      description: 3D 位置历史 [[x,y,z], ...]，trajectory_magnus 方法使用
    timestamps:
      type: array
      description: 对应时间戳 [t0, t1, ...]
    marker_points_2d:
      type: array
      description: 球面标记点 2D 坐标 [[u,v], ...]，marker_pose 方法使用
    marker_points_3d:
      type: array
      description: 球面标记点 3D 模型坐标 [[x,y,z], ...]，marker_pose 方法使用
    camera_matrix:
      type: array
      description: 3x3 相机内参矩阵，marker_pose 方法使用
    ball_radius:
      type: number
      description: 球半径（米），默认 0.02（乒乓球）
    dt:
      type: number
      description: 时间步长（秒），默认 0.008 (125Hz)
output_schema:
  type: object
  required: [wx, wy, wz]
  properties:
    wx: { type: number, description: 角速度 X 分量 (rad/s) }
    wy: { type: number, description: 角速度 Y 分量 (rad/s) }
    wz: { type: number, description: 角速度 Z 分量 (rad/s) }
    spin_rpm: { type: number, description: 总转速 (RPM) }
    confidence: { type: number, description: 估计置信度 [0, 1] }
    method: { type: string, description: 使用的方法名 }
---

# 球类旋转估计

## 何时使用

当用户需要估计球的旋转（角速度）时使用。旋转无法从单帧位置直接观测，必须依赖时序信息或球的表面特征。典型场景：

- 乒乓球旋转检测（上旋/下旋/侧旋），用于策略决策
- 羽毛球旋转估计，用于弹跳预测
- 网球旋转估计，用于轨迹预测
- 事件相机实时旋转估计
- 带标记球的旋转标定和验证

不适用于：一般光流估计、6-DoF 物体姿态估计（非球类）、非旋转相关的运动分析。

## 输入约束

### EventCameraSpin 方法
- 需要事件相机输出的事件流 (x, y, t, polarity)
- 事件流需聚焦在球表面区域（需先检测球位置）
- 时间精度需达微秒级
- 依赖事件相机硬件（如 DVS、Prophesee）

### MarkerPoseSpin 方法
- 需要球面上可见的标记点（logo、品牌文字等）
- 需要标记点在球面上的 3D 模型坐标（已知球半径和标记布局）
- 需要相机内参矩阵
- 至少需要 4 个非共面标记点才能可靠估计姿态
- 正式比赛用球通常不允许添加额外标记

### TrajectoryMagnusSpin 方法
- 需要高精度 3D 轨迹（位置噪声 < 5 mm）
- 需要足够长的轨迹段（至少 5–10 帧）
- 需要知道球的物理参数（半径、质量、空气密度）
- Magnus 力相对重力很小，信噪比低
- 更适合作为辅助验证手段，而非主要旋转估计方法

## 执行步骤

### 步骤 1：方法选择与输入校验

- 动作：根据可用输入数据选择旋转估计方法
- 输入：events / marker_points / positions_3d
- 成功标准：至少一种方法的输入数据满足要求
- 失败处理：输入不足时返回 `insufficient_data`

### 步骤 2：旋转估计计算

- 动作：根据选定方法计算角速度
- 输入：方法相关数据
- 成功标准：输出三维角速度 (wx, wy, wz)
- 失败处理：方法失败时降级到其他可用方法或返回 None

### 步骤 3：置信度评估

- 动作：评估旋转估计的可靠性
- 输入：角速度估计 + 方法内部指标
- 成功标准：输出置信度 [0, 1]
- 失败处理：低置信度时标记为 unreliable

## 输出格式

```json
{
  "wx": 52.36,
  "wy": -10.5,
  "wz": 3.14,
  "spin_rpm": 500.0,
  "confidence": 0.85,
  "method": "event_camera"
}
```

## 可用方法与代表性系统

旋转估计是球类感知中最具挑战性的模块。旋转（角速度 $\boldsymbol{\omega}$）无法从单帧位置直接观测，必须依赖时序信息或球的表面特征。当前主流路线可分为三类：

### 方法一：事件相机旋转估计 — Tübingen / Ace 路线

传统帧相机在捕捉高速旋转时面临两个根本性障碍：一是运动模糊——乒乓球转速可达 3000 rpm（50 rev/s），在 125 FPS 相机的 8 ms 曝光时间内球已转过约 1.4 圈，logo 完全模糊不可辨；二是带宽瓶颈——要捕捉旋转需要极高帧率，但高帧率意味着每帧曝光时间更短、噪声更大。

事件相机从根本上绕过了这两个障碍。它不输出整帧图像，而是对每个像素独立输出"亮度变化超过阈值"的异步事件流 $(x, y, t, \text{polarity})$，时间精度达微秒级。估计链路：

1. **Ordinal Time Surface**：将事件流编码为"时间面"——每个像素记录最近一次事件的时间戳，形成一张时间图。旋转的球表面纹理会产生特定的时间梯度模式
2. **事件光流提取**：从时间面的梯度中计算事件光流（event-based optical flow），即球表面每个点的表观运动方向和速度
3. **角速度回归**：球表面光流场与角速度 $\boldsymbol{\omega}$ 之间存在几何约束关系 $\mathbf{v}_{\text{flow}} = \boldsymbol{\omega} \times \mathbf{r}$（其中 $\mathbf{r}$ 是球面点到球心的向量），通过最小二乘或神经网络回归得到 $\boldsymbol{\omega}$

**Ace 案例**：3 套事件视觉 gaze-control system 各自包含可转镜面、可调焦镜头和事件传感器。两套算法并行运行：
- **低延迟 CNN**：将事件流累积为短时窗（约 1 ms）的事件帧，送入轻量 CNN 直接回归角速度，延迟约 2–3 ms
- **高精度 CMax**：基于对比度最大化（Contrast Maximization）框架，搜索使事件对齐最优的旋转参数，精度更高但计算量更大（约 10 ms）
- 系统根据实时置信度在两种算法间切换，角速度估计频率可达 400–700 Hz

**适用**：需要高频率、低延迟旋转估计、有事件相机硬件的场景。

### 方法二：带标记球几何姿态估计 — SpinDOE 路线

不依赖事件相机，而是利用球表面的标记点（logo、品牌文字等）做几何姿态估计：

1. **球面点模式识别**：在检测到球之后，进一步检测球面上的标记点（如三星 logo 的三个角点）。这些标记点在球面上的相对位置是已知的（球的直径 40mm，logo 尺寸可测量），构成一个已知的 3D 点模式
2. **点身份匹配**：将图像中检测到的 2D 标记点与 3D 模型中的已知点做匹配（Perspective-n-Point, PnP 问题）。难点是遮挡——球在旋转过程中 logo 可能部分不可见，需要鲁棒的匹配算法
3. **相邻姿态回归**：从连续两帧的球姿态 $\mathbf{R}_t$ 和 $\mathbf{R}_{t+1}$ 计算相对旋转 $\Delta\mathbf{R} = \mathbf{R}_{t+1}\mathbf{R}_t^{-1}$，再转换为角速度 $\boldsymbol{\omega} = \text{axis}(\Delta\mathbf{R}) \cdot \text{angle}(\Delta\mathbf{R}) / \Delta t$

**SpinDOE 案例**：开放了 CAD stencil（用于制作带已知标记的测试球）和轨迹数据集，非常适合作为研发阶段的高质量监督源。但正式比赛用球通常不允许添加额外标记，且商业球的 logo 位置和大小不统一。

**适用**：研发阶段的旋转标定和验证、有标记球的离线分析。

### 方法三：轨迹倒推旋转 — Magnus 效应路线

当球表面没有可见标记、也没有事件相机时，只能从球的飞行轨迹间接推断旋转。核心物理原理是 Magnus 效应：旋转的球在空气中运动时，表面气流的不对称会产生侧向力：

$$\mathbf{F}_{\text{Magnus}} = C_L \cdot \frac{4}{3}\pi r^3 \rho \cdot \boldsymbol{\omega} \times \mathbf{v}$$

其中 $C_L$ 是升力系数，$r$ 是球半径，$\rho$ 是空气密度。这个力使球的轨迹产生可观测的弯曲——上旋球下坠更快，下旋球漂浮更久，侧旋球横向偏移。

估计步骤：
1. **精确轨迹重建**：用多目系统或高帧率相机获取高精度 3D 轨迹
2. **物理拟合**：将轨迹拟合到含 Magnus 力的飞行模型 $\mathbf{a} = \mathbf{g} + \mathbf{a}_{\text{drag}} + \mathbf{a}_{\text{Magnus}}$
3. **反解角速度**：从拟合得到的 Magnus 加速度反推 $\boldsymbol{\omega}$
4. **弹跳辅助**：旋转的球在弹跳时会产生切向速度变化（上旋球弹跳后加速，下旋球减速），通过比较弹跳前后的速度变化可以估计旋转分量

**根本局限**：Magnus 力相对重力和阻力来说很小（乒乓球 Magnus 加速度通常 < 1 m/s²，而重力加速度为 9.8 m/s²），因此轨迹弯曲量很小，需要极高的位置精度才能可靠检测。当位置误差为 5 mm 时，Magnus 效应的信号可能被噪声淹没。

**适用**：无事件相机和标记球时的辅助旋转估计、弹跳旋转推断。

### 方法对比

| 维度 | 事件相机 (Tübingen/Ace) | 标记球 (SpinDOE) | 轨迹倒推 (Magnus) |
|------|------------------------|-----------------|-------------------|
| 估计频率 | 400–700 Hz | 与帧率相同 | 与轨迹采样率相同 |
| 延迟 | 2–10 ms | 与帧率相关 | 需要多帧累积 |
| 精度 | 高（微秒级时间分辨率） | 高（几何约束） | 低（Magnus 信号弱） |
| 硬件需求 | 事件相机 | 标记球 + 帧相机 | 多目系统 |
| 比赛可用 | ✅（Ace 已验证） | ❌（需标记球） | ✅（无额外硬件） |
| 遮挡鲁棒 | 中（需球在视野内） | 低（标记需可见） | 高（仅需轨迹） |
| 部署难度 | 高（事件相机硬件） | 中（标记检测） | 低（仅需轨迹） |
| 信噪比 | 高 | 高 | 低 |

## 可用方案（Recipes）

| Recipe | 适用球类 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [event-camera-spin](recipes/event-camera-spin/RECIPE.md) | 乒乓球 | EventCameraSpin (CNN + CMax) | advanced | 是 | 400–700 Hz，延迟 2–10 ms |
| [spindoe-marker-pose](recipes/spindoe-marker-pose/RECIPE.md) | 乒乓球 | MarkerPoseSpin (PnP) | intermediate | 否 | 与帧率相同，需标记球 |
| [trajectory-magnus-spin](recipes/trajectory-magnus-spin/RECIPE.md) | 乒乓球/网球 | TrajectoryMagnusSpin | beginner | 否 | 精度低，适合辅助验证 |

选择建议：
- 高精度实时旋转 → 事件相机方案（需硬件支持）
- 研发标定与验证 → 标记球方案（SpinDOE）
- 无额外硬件时的辅助估计 → 轨迹倒推方案（Magnus 效应）

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 事件流为空 | len(events) == 0 | 返回 `insufficient_data: no_events` |
| 标记点不足 | len(marker_points_2d) < 4 | 返回 `insufficient_data: insufficient_markers` |
| 轨迹太短 | len(positions_3d) < 5 | 返回 `insufficient_data: short_trajectory` |
| PnP 求解失败 | cv2.solvePnP 返回 False | 返回 None |
| Magnus 拟合不收敛 | 残差未下降 | 返回 `unreliable: magnus_fit_failed` |
| 置信度过低 | confidence < 0.3 | 标记 unreliable，仍返回结果 |
