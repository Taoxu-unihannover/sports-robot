---
name: sb3-rl-training-runner
description: 统一 Stable-Baselines3 的 SAC/PPO/DDPG/TD3 训练入口，支持并行环境、checkpoint 保存、TensorBoard 日志、继续训练和自定义回调。适用于用户需要训练 RL 策略、配置超参数、管理训练过程；不用于环境定义或策略评估。
---

# SB3 强化学习训练运行器

## 用途

提供统一的 Stable-Baselines3 训练入口脚本，支持 SAC/PPO/DDPG/TD3 算法选择、并行环境创建、模型保存与加载、TensorBoard 日志、继续训练和自定义回调。

## 输入

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| env_id | string | 是 | Gymnasium 环境ID或环境类 |
| algorithm | string | 是 | SAC, PPO, DDPG, TD3 |
| total_timesteps | int | 是 | 总训练步数 |
| config | dict | 否 | 超参数配置 |
| resume_from | string | 否 | 继续训练的模型路径 |
| n_envs | int | 否 | 并行环境数，默认 2 |
| save_dir | string | 否 | 模型保存目录 |
| save_frequency | int | 否 | 保存频率（迭代次数），默认 50 |

## 输出

| 产物 | 路径 | 说明 |
|---|---|---|
| 训练脚本 | scripts/train_sb3.py | 统一训练入口 |
| 模型文件 | saved_models/ | .zip 格式的模型 checkpoint |
| TensorBoard 日志 | runs/ | 训练曲线和指标 |
| 训练配置 | assets/train_config.yaml | 可复现的超参数 |

## 执行步骤

### 步骤 1：环境注册与创建

```python
from gymnasium.envs.registration import register
from stable_baselines3.common.vec_env import SubprocVecEnv

register(id="MyEnv-v1", entry_point="envs.my_env:MyEnv", max_episode_steps=2000)

def make_env(rank, seed=0):
    def _init():
        env = gym.make("MyEnv-v1")
        env.reset(seed=seed + rank)
        return env.unwrapped
    set_random_seed(seed)
    return _init

env = SubprocVecEnv([make_env(i) for i in range(n_envs)])
```

### 步骤 2：算法选择与配置

| 算法 | 适用场景 | 推荐超参 |
|---|---|---|
| SAC | 连续控制，探索性强 | lr=5e-4, buffer=3M, batch=512, net=[1024,512] |
| PPO | 稳定训练，on-policy | lr=3e-4, batch=256, net=[256,256] |
| TD3 | 确定性策略，低方差 | lr=5e-4, buffer=1M, batch=256 |
| DDPG | 简单连续控制 | lr=1e-3, buffer=1M, batch=256 |

### 步骤 3：训练循环

```python
for i in range(save_frequency):
    model.learn(
        total_timesteps=timesteps_per_iter,
        reset_num_timesteps=False,
        tb_log_name=experiment_name,
        callback=callback,
    )
    model.save(os.path.join(save_path, f"{experiment_name}_{i}"))
```

### 步骤 4：自定义回调

标准回调模式：

```python
class MetricsCallback(BaseCallback):
    def _on_rollout_end(self):
        try:
            info = self.model.env.unwrapped.get_attr("datatoplot")[0]
            self.logger.record("rollout/goal_distance", info["goal_distance"])
            self.logger.record("rollout/positional_error", info["positional_error"])
        except Exception:
            pass

    def _on_step(self):
        return True
```

### 步骤 5：继续训练

```python
model = SAC.load(resume_from, env=env, tensorboard_log=logdir)
model.learn(total_timesteps=additional_steps, reset_num_timesteps=False)
```

## 失败处理

| 失败场景 | 处理策略 |
|---|---|
| 环境注册失败 | 检查 entry_point 路径和模块导入 |
| OOM | 减少 buffer_size、batch_size 或 n_envs |
| 训练不收敛 | 调整学习率、奖励权重或观测归一化 |
| 模型加载失败 | 检查算法类型匹配和 SB3 版本 |

## 验证方式

1. 短训练 1000 steps 无崩溃
2. 模型保存和加载正常
3. TensorBoard 日志可查看
4. 训练曲线显示 reward 趋势

## 可选 Recipes

| Recipe | 说明 |
|---|---|
| sac-mecanum-navigation | SAC 训练麦克纳姆导航 |
| ppo-arm-reacher | PPO 训练机械臂到达 |
