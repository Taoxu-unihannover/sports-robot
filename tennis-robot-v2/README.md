# tennis-robot-v2

基于 MuJoCo 仿真 + Gymnasium 环境封装 + Stable-Baselines3 强化学习的网球机器人导航项目 v2。

v2 是 `ball-project-assimilator` 插件对 `dynamic-tennis` 执行吸收与超越流程的产物，相比 v1 的关键改进：

1. **预测性导航奖励**：从 `dynamic-tennis` 沉淀的拦截点计算和速度对齐奖励
2. **改进的 XML 加载**：优先使用 `from_xml_string` 避免临时目录 I/O
3. **对齐的奖励参数**：与 `dynamic-tennis` 一致的 `distance_incentive`、`velocity_alignment` 权重

## 项目结构

```
tennis-robot-v2/
├── pyproject.toml
├── configs/
│   ├── env.yaml                 # 环境配置
│   └── train_sac.yaml           # SAC 训练配置
├── assets/mujoco/tennis_world/
│   ├── tennis_world_mecanum.xml # MuJoCo 场景
│   └── assets/                  # 资产文件
├── tennis_robot_v2/
│   ├── __init__.py
│   └── envs/
│       ├── __init__.py
│       ├── registration.py       # Gymnasium 环境注册
│       └── tennis_navigation_v2_env.py  # 核心环境类
├── scripts/
│   ├── smoke_test.py            # 冒烟测试
│   ├── train.py                 # 训练入口
│   └── evaluate.py              # 评估入口
├── saved_models/                # 保存的模型
├── evaluation_results/          # 评估结果
├── runs/                        # TensorBoard 日志
└── docs/
    ├── development-log.md       # 开发日志
    ├── tennis-robot-v2-baseline-metrics.json
    └── tennis-robot-v2-metrics.json
```

## 快速开始

### 1. 环境安装

```bash
cd tennis-robot-v2
pip install -e .
```

### 2. 冒烟测试

```bash
python scripts/smoke_test.py
```

### 3. 训练

```bash
# 短训练 (smoke test)
python scripts/train.py --algorithm SAC --total_timesteps 5000

# 完整训练 (建议 GPU)
python scripts/train.py --algorithm SAC --total_timesteps 1000000 --device cuda
```

### 4. 评估

```bash
python scripts/evaluate.py --model_path saved_models/baseline/tennis_robot_v2_SAC_final --algorithm SAC --episodes 50
```

## 技术规格

### 环境规格

| 属性 | 值 |
|------|-----|
| 观测空间 | Box(12,) float64 |
| 动作空间 | Box(3,) float64, [-1, 1] |
| frame_skip | 20 |
| max_episode_steps | 1000 |
| 网球场尺寸 | 11.885m × 8.23m (单打半场) |
| 目标容差 | 0.2m |

### 观测向量 (12维)

| 索引 | 内容 | 归一化 |
|------|------|--------|
| 0 | 目标距离 (归一化) | / diagonal_length |
| 1 | 目标角度 (归一化) | / 2π |
| 2 | 相对角度 (归一化) | / π |
| 3 | 偏航角 (归一化) | / 2π |
| 4-6 | 机器人线速度 | / max_vel |
| 7-9 | 机器人角速度 | / max_ang_vel |
| 10-11 | 网球速度 | / max_vel |

### 动作向量 (3维)

| 索引 | 内容 | 说明 |
|------|------|------|
| 0 | x_move | 前进/后退 |
| 1 | y_move | 左右平移 |
| 2 | rotate | 旋转 |

### 奖励函数

```
reward = distance_incentive × (prev_distance - curr_distance)
       + terminal_payoff (success: +10000, failure: -10000)
       + inTimeCost × (t_accepted - elapsed_time)  [if reached]
       - control_cost × Σ(action²)
```

### 终止条件

- **success**: 机器人到网球距离 ≤ 0.2m
- **failure**: 机器人或网球超出边界 (|x| > 8 or |y| > 8)
- **truncated**: 达到 max_episode_steps (1000)

## v1 vs v2 vs dynamic-tennis 对比

| 改进项 | v1 | v2 | dynamic-tennis |
|--------|----|----|----------------|
| 奖励函数 | 基础距离奖励 | 预测性导航奖励 | 预测性导航奖励 |
| XML 加载 | 临时目录拷贝 | from_xml_string 优先 | 直接加载 |
| velocity_alignment | 无 | ✅ (weight=500) | ✅ (weight=500) |
| relative_speed | 无 | ✅ (weight=20) | ✅ (weight=20) |
| 拦截点计算 | 无 | ✅ | ✅ |
| control_cost | 0.001 | 0.0005 | 0.0005 |
| step_penalty | 无 | -0.3 | -0.3 |

## 性能验证结果

### 训练配置

| 参数 | 值 |
|------|-----|
| 算法 | SAC |
| 训练步数 | 1,000,000 |
| 学习率 | 5e-4 |
| buffer_size | 3,000,000 |
| batch_size | 512 |
| 网络架构 | [1024, 512] |
| 并行环境 | 2 |
| GPU | RTX 5090 |

### 评估结果 (50 episodes)

| 指标 | 值 |
|------|-----|
| 平均奖励 | -20149.18 |
| 平均步数 | 172.4 |
| 平均最终距离 | 7.36m |
| 成功率 | 4% |
| 训练吞吐 | 137.4 steps/sec |

### 与 baseline 对比

| 指标 | dynamic-tennis (5K steps) | tennis-robot-v2 (1M steps) | 判定 |
|------|---------------------------|---------------------------|------|
| check_env | PASS | PASS | ✅ |
| 训练吞吐 | 19.9 steps/sec | 137.4 steps/sec | ✅ 提升 6.9x |
| 成功率 | 0% | 4% | ✅ |

**注意**: 由于训练步数不同（5K vs 1M），直接比较奖励和成功率意义有限。v2 的 4% 成功率表明策略已开始学习。

## 技术栈来源

### 通过 sports-robot Skills/Plugins 生成的模块

| 模块 | 使用的 Skill/Plugin |
|------|---------------------|
| MuJoCo 场景 | mujoco-tennis-world-builder |
| Gymnasium 环境 | gymnasium-mujoco-env-builder |
| 训练入口 | sb3-rl-training-runner |
| 评估入口 | mujoco-policy-evaluator |
| 技术栈拆解 | ball-project-assimilator + open-project-skill-distiller |

### 关键改进（来自 dynamic-tennis 吸收）

| 改进项 | 来源 | 说明 |
|--------|------|------|
| 预测性导航奖励 | dynamic-tennis | 拦截点计算引导策略 |
| velocity_alignment | dynamic-tennis | 速度对齐奖励 |
| from_xml_string | sports-robot | 避免临时目录 I/O |

## 优化方向

| 优先级 | 优化项 | 预期效果 |
|--------|--------|----------|
| P0 | 继续长训练 (10M+ 步) | 策略收敛，成功率提升 |
| P1 | 调整奖励权重 | 更快的收敛速度 |
| P2 | 多环境并行训练 | 提升训练吞吐 |
| P2 | 添加域随机化 | 提升泛化能力 |

## 文档

- [开发日志](docs/development-log.md) - 完整的开发历程和测试记录
- [基线指标 JSON](docs/tennis-robot-v2-baseline-metrics.json) - 5K 步训练基线
- [评估指标 JSON](docs/tennis-robot-v2-metrics.json) - 1M 步训练评估结果

---

*项目通过 ball-project-assimilator 生成于 2026-06-09*