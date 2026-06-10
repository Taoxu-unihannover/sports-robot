# dynamic-tennis-v2 超越报告

> 报告日期：2026-06-10T02:16:14

## 1. 超越目标

- 复现版核心性能达到项目 A baseline 的 95% 以上
- 增强版核心指标超过项目 A baseline 至少 5%

## 2. 整体性能对比

| 指标 | 项目 A (Baseline) | 复现版 | 增强版 | 复现版 vs A | 增强版 vs A |
|---|---|---|---|---|---|
| 成功率 | 93.3% | 46.7% | 43.3% | -50.0% | -53.6% |
| 平均奖励 | 35.0 | 16.4 | 9.3 | -53.1% | -73.4% |

## 3. 差距根因分析

### 3.1 训练步数差异（主因）

| 版本 | 训练步数 | 训练时长 | 成功率 |
|---|---|---|---|
| Baseline | 30M | ~8h (GPU) | 93.3% |
| Reproduction | 10M | ~50min (CPU) | 46.7% |
| Enhanced | 10M | ~110min (CPU) | 43.3% |

Baseline 在 10M 步时成功率约 10-20%，复现版在同等步数下达到 46.7%，
说明**复现版的超参数配置实际优于 baseline 同期水平**，差距主要来自训练步数不足。

### 3.2 增强版超参数不匹配

增强版使用 [512,512] 大网络 + n_steps=4096，在小奖励尺度（R_EE_POS=15）下：
- 网络过大导致收敛慢，std 从 0.9 持续上升到 1.45
- n_steps=4096 导致 FPS 降低 56%（1480 vs 3410），有效训练量更少
- 结论：**大网络需要配合大奖励尺度或课程学习才能发挥优势**

### 3.3 环境差异

复现版直接复用 dynamic-tennis-v2 的 SummitCatcherEnv，环境完全一致。
Baseline 训练时使用了 CUDA GPU，复现版使用 CPU 训练，这影响了训练效率但不影响最终性能。

## 4. 最优技术栈组合

基于本次评测，推荐以下技术栈组合：

```yaml
# best_stack.yaml (基于当前评测结果修正)
simulation:
  skill: mujoco-tennis-world-builder
  method: summit_xls_catcher_scene
  version: '2.0'
  notes: MuJoCo 网球场场景 + 麦卡轮机器人 + 网球物理

perception:
  skill: truth-state-policy-input
  method: summit_catcher_16d_obs
  version: '1.0'
  notes: 16维观测 (base_pose, base_vel, ball_pose, ball_vel, intercept_point, ee_dist)

training:
  skill: sb3-rl-training-runner
  method: ppo-summit-catcher-v2
  version: '2.0'
  config:
    algorithm: PPO
    learning_rate: 5e-4
    n_steps: 2048
    batch_size: 256
    gamma: 0.99
    gae_lambda: 0.95
    clip_range: 0.2
    ent_coef: 0.005
    net_arch: [256, 256]
    total_timesteps: 30000000
    reward_scale:
      R_EE_POS: 15.0
      R_PRECISION: 15.0
      SUCCESS_BONUS: 10.0
      FAIL_PENALTY: -15.0

execution:
  skill: mobile-base-executor
  method: mecanum_wheel_kinematics
  version: '1.0'
  notes: 麦卡轮运动学混合 (vx, vy, wz -> 4轮速度)
```

## 5. 超越验证结论

### ⚠️ 带差距退出

- ❌ 复现版未达标: 46.7% < baseline 95%（但训练步数仅 1/3）
- ❌ 增强版未超越: 43.3% < baseline +5%（超参数需调整）

### 退出原因

1. **训练资源限制**: 10M 步训练不足以收敛到 baseline 水平
2. **增强版超参数选择失误**: 大网络 + 小奖励尺度 = 收敛困难

### 信心评估

- 复现版延长到 30M 步后，**预计可达 80-90% 成功率**（基于学习曲线外推）
- 增强版修正超参数后（使用 [256,256] 网络 + 课程学习），**预计可达 85-95% 成功率**

## 6. 下一步优化 backlog

| 优先级 | 优化项 | 预期效果 | 实施难度 |
|---|---|---|---|
| P0 | 延长复现版训练到 30M 步 | 成功率 80%+ | 低 |
| P1 | 添加课程学习 (CurriculumCallback) | 加速收敛 2-3x | 中 |
| P1 | 增大奖励尺度 (R_EE_POS=2500) | 更快收敛 | 低 |
| P2 | 学习率线性衰减 | 稳定后期训练 | 低 |
| P2 | SAC 算法对比 | 可能更样本高效 | 中 |
| P3 | 观测空间增强 (加入截击点距离) | 更精确的移动引导 | 中 |
