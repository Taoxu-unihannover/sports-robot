---
name: mujoco-policy-evaluator
description: 加载训练好的 RL 策略模型并评估性能，输出成功率、平均奖励、目标距离、轨迹数据、推理延迟和截图/视频。适用于用户需要测试策略性能、导出评估报告、对比不同模型；不用于训练过程或环境定义。
---

# MuJoCo 策略评估器

## 用途

加载 Stable-Baselines3 训练的模型，在 MuJoCo 仿真环境中运行评估 episode，收集性能指标并输出评估报告。支持 GUI 可视化、轨迹记录、截图和 Web 可视化数据导出。

## 输入

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| model_path | string | 是 | 模型文件路径 (.zip) |
| env_id | string | 是 | 环境ID |
| episodes | int | 否 | 评估 episode 数，默认 5 |
| max_steps | int | 否 | 每 episode 最大步数，默认 2000 |
| deterministic | bool | 否 | 是否确定性策略，默认 True |
| gui | bool | 否 | 是否显示 GUI，默认 False |
| export_web | bool | 否 | 是否导出 Web 可视化数据，默认 False |

## 输出

| 产物 | 路径 | 说明 |
|---|---|---|
| 评估脚本 | scripts/evaluate_policy.py | 评估入口 |
| 评估指标 | web_viz_data/ | JSON 格式的 episode 数据 |
| 轨迹图 | evaluation_results/ | Matplotlib 轨迹图 |
| 评估报告 | evaluation_results/report.json | 汇总指标 |

## 执行步骤

### 步骤 1：加载模型和环境

```python
from stable_baselines3 import SAC
model = SAC.load(model_path)
env = gym.make(env_id)
```

### 步骤 2：运行评估 episode

```python
results = []
for ep in range(episodes):
    obs, info = env.reset()
    episode_data = {"trajectory": [], "rewards": [], "steps": 0}
    done = False
    while not done and episode_data["steps"] < max_steps:
        action, _ = model.predict(obs, deterministic=deterministic)
        obs, reward, terminated, truncated, info = env.step(action)
        episode_data["trajectory"].append(env.unwrapped.data.qpos[7:9].copy().tolist())
        episode_data["rewards"].append(reward)
        episode_data["steps"] += 1
        done = terminated or truncated
    episode_data["success"] = env.unwrapped.reached
    episode_data["final_distance"] = info.get("positional_error", float("inf"))
    results.append(episode_data)
```

### 步骤 3：计算指标

| 指标 | 计算方式 |
|---|---|
| 成功率 | success_count / total_episodes |
| 平均 episode reward | mean(sum(rewards)) |
| 平均步数 | mean(steps) |
| 平均最终距离 | mean(final_distance) |
| 推理延迟 | mean(prediction_time) |

### 步骤 4：导出数据

- JSON episode 数据（轨迹、成功/失败、球场参数）
- Matplotlib 轨迹图
- 汇总报告

## 失败处理

| 失败场景 | 处理策略 |
|---|---|
| 模型加载失败 | 检查路径和算法类型 |
| 环境不匹配 | 检查观测/动作空间维度 |
| GUI 不可用 | 降级为无头模式 |

## 验证方式

1. 评估 3 episodes 无崩溃
2. 输出 JSON 和轨迹图
3. 指标格式正确

## 可选 Recipes

| Recipe | 说明 |
|---|---|
| mecanum-navigation-eval | 麦克纳姆导航评估 |
