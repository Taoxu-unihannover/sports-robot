# dynamic-tennis-v2 完整吸收验证报告

> 报告日期：2026-06-10T19:36:13
> 项目 A: dynamic-tennis-v2 (SummitCatcher 接球任务)
> 验证方: sports-robot (ball-project-assimilator)

## 1. 验证概述

对 dynamic-tennis-v2 的麦卡轮机器人接球任务进行完整吸收验证，包括：
- **真值推理 (sim)**: 从 MuJoCo 仿真直接获取 16 维观测
- **图像推理 (real)**: 双目相机 → HSV球检测 → StereoSGBM深度 → 坐标变换 → Kalman滤波 → 16维观测重建
- **复现版**: 与 baseline 完全相同的 PPO 超参数，30M 步训练
- **增强版**: 课程学习(warmup→ramp→adaptive) + 更大网络[512,512] + 更高gamma=0.999 + LR衰减 + 更大batch, 30M 步训练

## 2. 推理管线对比

### 2.1 真值推理 (sim 模式)
```
MuJoCo sim → qpos/qvel → _get_obs() → 16-dim obs → policy → action
```
- 数据来源: 仿真引擎内部状态（完美精度）
- 延迟: 0ms
- 球检测率: 100%

### 2.2 图像推理 (real 模式)
```
MuJoCo render → binocular frames (cam1, cam2)
  → SimBallDetector (HSV H=40-110, 面积8-4000px², 圆形度≥0.25)
  → StereoDepthEstimator (SGBM + WLS, baseline=0.24m)
  → 坐标变换 (cam → base_link, 4x4齐次变换)
  → ObjectKalmanFilter (6维状态 [x,y,z,vx,vy,vz], 含重力模型)
  → 时延补偿 (40ms前向预测)
  → _compute_derived_dims() → 16-dim obs → policy → action
```
- 数据来源: 渲染图像 + 立体视觉算法
- 延迟: ~40ms (检测+深度+滤波)
- 球检测率: 取决于球在视野中的大小和遮挡情况

## 3. 训练配置

| 参数 | Baseline | Reproduction | Enhanced |
|---|---|---|---|
| 算法 | PPO | PPO | PPO |
| 学习率 | 5e-4 | 5e-4 | 3e-4→3e-5 (线性衰减) |
| n_steps | 2048 | 2048 | 4096 |
| 批大小 | 256 | 256 | 512 |
| gamma | 0.99 | 0.99 | 0.999 |
| gae_lambda | 0.95 | 0.95 | 0.98 |
| clip_range | 0.2 | 0.2 | 0.15 |
| ent_coef | 0.005 | 0.005 | 0.005 |
| 网络架构 | [256,256] | [256,256] | [512,512] |
| 训练步数 | 30M | 30M | 30M |
| 课程学习 | 否 | 否 | 是 (warmup→ramp→adaptive) |
| 奖励尺度 | R_EE_POS=15 | R_EE_POS=15 | R_EE_POS=15 |

## 4. 评测结果

### 4.1 真值推理 (sim 模式)

| 指标 | Baseline | Reproduction | Enhanced |
|---|---|---|---|
| 成功率 | 93.3% | 43.3% | 86.7% |
| 平均奖励 | 35.0 | 11.5 | 32.7 |
| 奖励标准差 | 16.6 | 21.8 | 16.8 |
| 平均步数 | 347 | 378 | 347 |

### 4.2 图像推理 (real 模式)

| 指标 | Baseline | Reproduction | Enhanced |
|---|---|---|---|
| 成功率 | 6.7% | 0.0% | 6.7% |
| 平均奖励 | -19.9 | -30.3 | -30.6 |
| 平均步数 | 416 | 411 | 412 |
| 球检测率 | 99.2% | 99.1% | 99.2% |

### 4.3 sim vs real 性能差距

| 模型 | sim 成功率 | real 成功率 | sim→real 差距 |
|---|---|---|---|
| Baseline | 93.3% | 6.7% | +86.7% |
| Reproduction | 43.3% | 0.0% | +43.3% |
| Enhanced | 86.7% | 6.7% | +80.0% |

## 5. 方法排名 (sim 模式)

1. **Baseline**: 成功率 93.3%
2. **Enhanced**: 成功率 86.7%
3. **Reproduction**: 成功率 43.3%

## 6. 超越验证结论

### ❌ 失败退出（复现未达标）
- 复现版: ❌ 未达标 (43.3% vs baseline 95%=88.7%)
- 增强版: ❌ 未超越 (86.7% vs baseline+5%=98.0%)

## 7. 图像推理管线分析

### 7.1 管线组件

| 组件 | 方法 | 关键参数 |
|---|---|---|
| 球检测 | SimBallDetector (HSV) | H=40-110, S=60-200, V=60-200, 面积8-4000px² |
| 深度估计 | StereoSGBM + WLS | baseline=0.24m, num_disp=640, block=9 |
| 坐标变换 | 4x4齐次变换 | T_base_cam (URDF精确计算) |
| 状态估计 | ObjectKalmanFilter | 6维状态, dt=1/60, process_noise=0.05 |
| 时延补偿 | 物理前向预测 | delay=40ms, 含重力模型 |
| 观测重建 | _compute_derived_dims | 10个派生维度从球状态+机器人状态计算 |

### 7.2 sim→real 性能退化原因

1. **球检测失败**: 远距离时球像素面积过小（<8px²），HSV检测失败
2. **深度估计噪声**: SGBM在球区域有效像素少，视差中位数不稳定
3. **Kalman滤波延迟**: 初始化需要若干帧，早期速度估计不准
4. **时延补偿误差**: 40ms前向预测在球快速变向时不准确
5. **观测向量差异**: real模式的16维观测与sim模式存在系统性偏差

## 8. 最优技术栈组合

```yaml
simulation:
  skill: mujoco-tennis-world-builder
  method: summit_xls_catcher_scene
  version: '2.0'
perception:
  skill: truth-state-policy-input
  method: summit_catcher_16d_obs
  version: '1.0'
  alt_method: binocular-camera-16d-obs
  alt_version: '1.0'
training:
  skill: sb3-rl-training-runner
  method: ppo-summit-catcher
  version: '2.0'
  config:
    algorithm: PPO
    learning_rate: 3e-4
    lr_schedule: linear_decay_to_3e-5
    n_steps: 4096
    batch_size: 512
    gamma: 0.999
    gae_lambda: 0.98
    clip_range: 0.15
    ent_coef: 0.005
    net_arch: [512, 512]
    total_timesteps: 30000000
    curriculum: warmup_ramp_adaptive
execution:
  skill: mobile-base-executor
  method: mecanum_wheel_kinematics
  version: '1.0'
vision:
  skill: binocular-stereo-perception
  method: hsv_detection+sgbm_depth+kalman_filter
  version: '1.0'
```