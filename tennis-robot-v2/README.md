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
│   ├── env.yaml
│   └── train_sac.yaml
├── assets/mujoco/tennis_world/
│   ├── tennis_world.xml
│   └── assets/
├── tennis_robot_v2/
│   ├── __init__.py
│   └── envs/
│       ├── __init__.py
│       ├── registration.py
│       └── tennis_navigation_v2_env.py
├── scripts/
│   ├── smoke_test.py
│   ├── train.py
│   └── evaluate.py
├── docs/
│   └── development-log.md
├── saved_models/
├── evaluation_results/
└── runs/
```

## 快速开始

### 冒烟测试

```bash
python scripts/smoke_test.py
```

### 训练

```bash
python scripts/train.py --algorithm SAC --total_timesteps 5000 --version baseline
```

### 评估

```bash
python scripts/evaluate.py --model_path saved_models/baseline/tennis_robot_v2_SAC_final --algorithm SAC --episodes 5
```

## v1 vs v2 vs dynamic-tennis 对比

| 改进项 | v1 | v2 | dynamic-tennis |
|---|---|---|---|
| 奖励函数 | 基础距离奖励 | 预测性导航奖励 | 预测性导航奖励 |
| XML 加载 | 临时目录拷贝 | from_xml_string 优先 | 直接加载 |
| velocity_alignment | 无 | ✅ (weight=500) | ✅ (weight=500) |
| relative_speed | 无 | ✅ (weight=20) | ✅ (weight=20) |
| 拦截点计算 | 无 | ✅ | ✅ |
| control_cost | 0.001 | 0.0005 | 0.0005 |
| step_penalty | 无 | -0.3 | -0.3 |
