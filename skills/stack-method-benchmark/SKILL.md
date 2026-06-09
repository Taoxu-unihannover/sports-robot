name: stack-method-benchmark
description: 横向比较同一技术栈中不同方法的性能，输出方法排名和最优选择建议。适用于用户需要对比项目 A 方法与 sports-robot 已有方法的性能差异；不用于技能蒸馏或项目生成。
---

# 技术栈方法横向评测

## 用途

对同一技术栈中的多种候选方法（来自开源项目 A 和 sports-robot 已有 skills），使用统一 benchmark harness、相同数据/环境/种子进行评测，输出方法排名和最优选择建议。

## 输入

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| stack_map | dict | 是 | 技术栈图谱（来自 open-project-skill-distiller） |
| candidate_methods | list | 是 | 候选方法列表 [{name, source, skill, config}] |
| benchmark_env | string | 是 | 评测环境 ID 或配置路径 |
| metric_schema | list | 是 | 指标定义 [{name, unit, direction, weight}] |
| random_seed_set | list | 否 | 随机种子列表，默认 [0, 42, 123] |
| episodes_per_seed | int | 否 | 每个种子的评测回合数，默认 5 |

## 输出

| 产物 | 路径 | 说明 |
|---|---|---|
| 评测报告 | stack_benchmark_report.md | 每个技术栈的方法性能对比 |
| 方法排名 | method_ranking.json | 按技术栈分组的方法排名 |
| 最优方法 | best_method_per_stack.json | 每个技术栈的最优方法选择 |
| 权衡说明 | tradeoff_notes.md | 最优方法的适用范围和代价 |

## 执行步骤

### 步骤 1：建立统一 benchmark harness

为每个技术栈创建统一评测入口：

```python
def benchmark_method(method_config, env_config, seeds, episodes):
    results = []
    for seed in seeds:
        env = create_env(env_config, seed=seed)
        method = load_method(method_config)
        for ep in range(episodes):
            obs, info = env.reset(seed=seed + ep)
            done = False
            episode_reward = 0
            while not done:
                action = method.predict(obs)
                obs, reward, terminated, truncated, info = env.step(action)
                episode_reward += reward
                done = terminated or truncated
            results.append({
                "seed": seed,
                "episode": ep,
                "reward": episode_reward,
                "steps": info.get("steps", 0),
                "success": info.get("success", False),
                "final_distance": info.get("goal_distance", float("inf"))
            })
    return results
```

### 步骤 2：适配候选方法

所有候选方法必须适配同一接口：

```python
class MethodAdapter:
    def predict(self, obs: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def reset(self) -> None:
        pass
```

### 步骤 3：运行评测

- 固定随机种子和指标定义
- 对延迟、精度、稳定性、资源消耗同时记录
- 每个方法至少 3 个种子 × 5 回合

### 步骤 4：输出排名

| 技术栈 | 方法 | 来源 | 指标1 | 指标2 | ... | 综合得分 | 排名 |
|---|---|---|---|---|---|---|---|

### 步骤 5：标注适用范围

报告必须说明：
- 最优方法在什么条件下最优
- 次优方法在什么条件下可能更好
- 各方法的失败模式和边界条件

## 评测指标定义

| 技术栈 | 核心指标 | 单位 | 方向 |
|---|---|---|---|
| 仿真 | 训练吞吐 | steps/sec | 越高越好 |
| 仿真 | 物理可信度 | 1-5 评分 | 越高越好 |
| 感知 | 检测 mAP | % | 越高越好 |
| 感知 | 推理延迟 | ms | 越低越好 |
| 建模 | 预测误差 | m | 越低越好 |
| 控制 | 跟踪误差 | m | 越低越好 |
| 控制 | 计算延迟 | ms | 越低越好 |
| RL 训练 | 收敛步数 | steps | 越低越好 |
| RL 训练 | 最终 reward | - | 越高越好 |
| RL 训练 | 成功率 | % | 越高越好 |

## 验证方式

1. 所有候选方法使用同一评测入口
2. 所有评测固定随机种子
3. 报告包含原始数据和统计摘要
4. 排名有明确依据和适用范围说明
