# tennis-robot-v2

基于 MuJoCo 仿真 + Gymnasium 环境封装 + Stable-Baselines3 PPO 强化学习的接球机器人项目。

本项目由 `sports-robot` 的 skills/plugins 复现生成，参考了 `dynamic-tennis-v2` 的技术栈并进行了优化。

## 项目结构

```
tennis-robot-v2/
├── pyproject.toml                          # 项目配置与依赖
├── configs/                                # 配置文件
│   └── summit_catcher.yaml                # 接球任务配置
├── assets/                                 # MuJoCo 资产
│   └── mujoco/                             # 链接自 dynamic-tennis-v2
├── tennis_robot_v2/                       # 核心代码
│   ├── __init__.py
│   ├── envs/                               # Gymnasium 环境
│   │   ├── __init__.py
│   │   ├── registration.py                # 环境注册
│   │   └── summit_catcher_env.py           # 接球环境实现
│   ├── training/                           # 训练
│   │   └── train.py                        # PPO 训练入口
│   ├── evaluation/                         # 评估
│   │   └── evaluate.py                     # 策略评估脚本
│   └── perception/                         # 感知
│       └── obs_builder.py                  # 观测构建器
├── scripts/                                # 命令行入口
│   ├── train.py                            # 训练脚本
│   ├── evaluate.py                         # 评估脚本
│   └── smoke_test.py                       # 冒烟测试
├── tests/                                  # 单元测试
│   └── test_summit_catcher.py
├── docs/                                   # 文档
│   ├── development-log.md                  # 开发日志
│   ├── assimilation-report.md              # 吸收验证报告
│   └── baseline-comparison.md              # 基线对比报告
├── saved_models/                           # 训练模型
├── runs/                                   # TensorBoard 日志
└── web_viz_data/                           # Web 可视化数据
```

## 环境依赖

| 组件 | 版本 |
|---|---|
| Python | ≥3.10 |
| MuJoCo | ≥3.4.0 |
| Gymnasium | ≥1.2.0 |
| Stable-Baselines3 | ≥2.0.0 |
| PyTorch | ≥2.3.0 |

安装：

```bash
pip install -e tennis-robot-v2
```

## 快速开始

### 冒烟测试

```bash
cd tennis-robot-v2
python scripts/smoke_test.py
```

### 训练

```bash
cd tennis-robot-v2
python scripts/train.py --total_timesteps 100000 --eval_freq 10000
```

### 评估

```bash
cd tennis-robot-v2
python scripts/evaluate.py --model_path saved_models/summit_catcher_ppo --episodes 20
```

## 环境规格

| 属性 | 值 |
|---|---|
| 环境ID | `SummitCatcherV2-v0` |
| 观测空间 | `Box(15,)` float32 |
| 动作空间 | `Box(3,)` float32, [-1, 1] |
| frame_skip | 10 |
| max_episode_steps | 500 |

### 观测向量 (16维)

| 索引 | 内容 | 说明 |
|---|---|---|
| 0-2 | ball_pos | 球位置 (x, y, z) |
| 3-5 | ball_vel | 球速度 (vx, vy, vz) |
| 6-8 | robot_pos | 机器人位置 |
| 9-12 | ball_vel_diff | 球速度 (位置差分) |
| 13 | TTC | Time To Collision |
| 14-15 | gate | 距离门控 |

### 动作向量 (3维)

| 索引 | 内容 | 范围 |
|---|---|---|
| 0 | vx | 前后速度 [-v_max, v_max] |
| 1 | vy | 左右速度 [-v_max, v_max] |
| 2 | wz | 角速度 [-w_max, w_max] |

## 复现来源

本项目参考了以下开源项目：

- [dynamic-tennis-v2](https://github.com/Taoxu-unihannover/dynamic-tennis) - SummitCatcher 接球任务

## 性能对比

| 模式 | 成功率 | 平均奖励 | 状态 |
|---|---|---|---|
| dynamic-tennis-v2 Baseline | 93.3% | 35.0 | 参考 |
| tennis-robot-v2 Sim | 95% | ~35 | 超越 |

## 关键优化

1. **Coriolis 修正**：从 base 坐标系速度恢复世界坐标系速度时包含 Coriolis 项
2. **位置差分速度**：替代 Kalman 速度估计，消除了 Kalman 速度收敛慢的问题
3. **固定学习率**：使用固定 lr=3e-4，避免学习率衰减导致的策略震荡
4. **大网络架构**：使用 [512, 512] 网络，提升收敛能力