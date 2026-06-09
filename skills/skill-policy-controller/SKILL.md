---
name: skill-policy-controller
description: 用于球类机器人的技能库管理、高层策略选择、RL/IL 策略训练、动作原语组合和残差学习。支持 Stable-Baselines3 (SAC/PPO/DDPG/TD3) 训练流程、Gymnasium 环境接口和 MuJoCo 仿真。适用于用户需要实现技能切换、策略训练、skill selection、残差补偿、策略安全投影；不用于底层伺服控制或纯模型预测控制。
---

# 技能策略与学习控制

## 何时使用

当用户需要用学习型策略（RL/IL）控制球类机器人，或需要管理多种击球技能的切换和组合时使用。典型场景：

- 训练 RL 策略实现端到端击球（DeepMind 路线）
- 构建技能库实现多种击球方式切换（forehand/backhand/smash）
- 用残差学习补偿模型误差（HITTER 路线）
- 用人类运动先验加速策略学习（LATENT 路线）
- 使用 SB3 (SAC/PPO/DDPG/TD3) 在 MuJoCo+Gymnasium 环境中训练策略

不适用于：纯模型预测控制（MPC）、底层伺服环、无学习需求的系统。

## SB3/MuJoCo/Gymnasium 训练流程

### 标准训练管线

```
1. 注册 Gymnasium 环境 → gym.make("MyEnv-v1")
2. 创建 SB3 模型 → SAC("MlpPolicy", env, ...)
3. 训练 → model.learn(total_timesteps=N)
4. 保存 → model.save("path")
5. 评估 → model.predict(obs, deterministic=True)
```

### 算法选择

| 算法 | 适用场景 | 推荐超参 |
|---|---|---|
| SAC | 连续控制，探索性强 | lr=5e-4, buffer=3M, batch=512, net=[1024,512] |
| PPO | 稳定训练，on-policy | lr=3e-4, batch=256, net=[256,256] |
| TD3 | 确定性策略，低方差 | lr=5e-4, buffer=1M, batch=256 |
| DDPG | 简单连续控制 | lr=1e-3, buffer=1M, batch=256 |

### 环境接口要求

策略训练环境必须满足 Gymnasium 标准接口：

- `reset() → (obs, info)`
- `step(action) → (obs, reward, terminated, truncated, info)`
- `observation_space: Box(...)`
- `action_space: Box(...)`
- 通过 `stable_baselines3.common.env_checker.check_env`

### 观测/动作空间设计

| 观测类型 | 维度 | 归一化 | 说明 |
|---|---|---|---|
| 目标距离 | 1 | / diagonal_length | 目标到机器人的欧氏距离 |
| 目标角度 | 1 | / 2π | 目标方向角 |
| 相对角度 | 1 | / π | 目标相对机器人朝向 |
| 机器人朝向 | 1 | / 2π | yaw 角 |
| 线速度 | 3 | / max_vel | vx, vy, vz |
| 角速度 | 3 | / max_ang_vel | wx, wy, wz |
| 球速度 | 2 | / max_vel | 网球 vx, vy |

动作空间：Box(-1, 1, shape=(3,))，对应 [x_move, y_move, rotate]。

## 输入约束

- observation 必须包含球状态和机器人状态
- skill_context 的 confidence 必须在 [0, 1] 范围内
- 策略输出必须经过安全投影后才能下发
- RL 策略需要仿真环境进行训练

## 执行步骤

### 步骤 1：技能选择

- 动作：根据观测和上下文选择最合适的技能
- 输入：observation, skill_context, available_skills
- 成功标准：输出有效的 skill_id
- 失败处理：无合适技能时选择默认防守技能

### 步骤 2：策略推理

- 动作：用选定技能的策略网络前向推理
- 输入：observation + skill_id
- 成功标准：输出 target_state 和 residual
- 失败处理：推理失败时回退到模型基线策略

### 步骤 3：安全投影

- 动作：将策略输出投影到安全可行域
- 输入：target_state + 关节限位 + 力矩限制 + 碰撞约束
- 成功标准：投影后输出满足所有约束
- 失败处理：无法满足约束时标记 rejected 并回退

## 输出格式

```json
{
  "skill_id": "forehand_drive",
  "target_state": {
    "paddle_position": [0.5, 0.3, 1.2],
    "paddle_normal": [0.0, 0.0, 1.0],
    "paddle_velocity": [2.0, 0.0, 1.0]
  },
  "residual": [0.01, -0.02, 0.0],
  "safety_projection": "none"
}
```

## 可用方法与代表性系统

### 方法一：端到端 RL 策略 — DeepMind 路线

DeepMind 乒乓球系统采用端到端 RL 策略，核心设计：

1. **策略结构**：MLP 策略网络，输入球状态+机器人关节状态，输出关节位置/速度指令
2. **训练方法**：PPO，在 MuJoCo 仿真中大规模并行训练
3. **延迟建模**：仿真中显式注入观测延迟，策略在训练中学会适应信息滞后
4. **域随机化**：对物理参数做随机扰动，增强 sim-to-real 鲁棒性
5. **技能库**：策略隐式包含多种击球方式（通过不同的球状态输入自然触发不同击球动作）

### 方法二：分层策略 + 全身 RL — HITTER 路线

HITTER 系统采用"模型规划 + RL 执行"的分层架构：

1. **高层**：基于模型的规划器输出拍面目标状态
2. **低层**：全身 RL 策略将拍面目标转化为全身关节指令
3. **残差学习**：RL 策略输出"期望末端加速度 + 躯干加速度"，再通过全身 QP 求解器映射到关节力矩
4. **安全保证**：QP 求解器保证力矩约束和接触约束始终满足

### 方法三：人类运动先验 + 残差 — LATENT 路线

LATENT 系统利用人类网球运动员的 MoCap 数据：

1. **运动先验**：从 MoCap 提取运动模式，作为策略的基础输出
2. **残差学习**：RL 只学习先验与实际需求之间的差异
3. **技能切换**：不同击球类型对应不同的先验模式
4. **优势**：输出更自然、训练更快、泛化更好

### 方法对比

| 维度 | 端到端RL (DeepMind) | 分层策略 (HITTER) | 人类先验 (LATENT) |
|------|---------------------|-------------------|-------------------|
| 策略输出 | 关节指令 | 末端加速度+QP | 先验+残差 |
| 训练数据 | 仅仿真 | 仅仿真 | MoCap+仿真 |
| 安全保证 | 域随机化 | QP求解器 | QP+先验约束 |
| 动作自然性 | 中 | 中 | 高 |
| 技能切换 | 隐式 | 显式 | 显式 |
| 适合平台 | 固定基座 | 人形 | 人形 |

## 可用方案（Recipes）

| Recipe | 适用平台 | 对应方法 | 难度 | 需要训练 | 性能基准 |
|--------|---------|---------|------|---------|---------|
| [deepmind-skill-library](recipes/deepmind-skill-library/RECIPE.md) | 固定基座 | 端到端RL (DeepMind) | advanced | 是 | 125Hz 闭环 |
| [hitter-wholebody-rl](recipes/hitter-wholebody-rl/RECIPE.md) | 人形 | 分层策略 (HITTER) | advanced | 是 | 全身QP+RL |

## 失败处理

| 失败场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 策略推理失败 | 网络异常/NaN | 回退到模型基线策略 |
| 安全投影失败 | 约束不可满足 | 标记 rejected，执行防守复位 |
| 技能选择冲突 | 多技能置信度接近 | 选择保守技能 |
| 观测异常 | 输入超出训练分布 | 降低策略权重，增加模型权重 |
| 延迟超限 | 观测过期 | 使用预测状态替代 |
