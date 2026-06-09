# tennis-robot

基于 MuJoCo 仿真 + Gymnasium 环境封装 + Stable-Baselines3 强化学习的网球机器人导航项目。

本项目由 `sports-robot` 的 skills/plugins 自举生成，不直接复制 `dynamic-tennis` 源码。

## 项目结构

```
tennis-robot/
├── pyproject.toml                          # 项目配置与依赖
├── configs/                                # 配置文件
│   ├── env.yaml                            # 环境参数
│   └── train_sac.yaml                      # SAC 训练超参
├── assets/                                 # MuJoCo 资产
│   └── mujoco/tennis_world/                # 网球世界 XML
│       ├── tennis_world.xml                # 主场景
│       └── assets/                         # 子资产
│           ├── assets.xml                  # 编译器/纹理/材质
│           ├── scene.xml                   # 地面/球场/目标/灯光
│           ├── robot.xml                   # 机器人 URDF
│           └── actuator.xml               # 执行器
├── tennis_robot/                           # 核心代码
│   ├── envs/                               # Gymnasium 环境
│   │   ├── registration.py                 # 环境注册
│   │   └── tennis_navigation_env.py        # 导航环境实现
│   ├── training/                           # 训练
│   │   └── train.py                        # SB3 训练入口
│   ├── evaluation/                         # 评估
│   │   └── evaluate.py                     # 策略评估脚本
│   ├── visualization/                      # 可视化
│   │   ├── visualizer.py                   # 轨迹可视化
│   │   └── web/                            # Web 可视化
│   │       └── server.py                   # HTTP 服务器
│   ├── perception/                         # 感知
│   │   └── vision.py                       # 仿真相机适配器
│   └── control/                            # 控制
│       └── mecanum_controller.py           # 麦克纳姆轮控制器
├── scripts/                                # 命令行入口
│   ├── train.py                            # 训练脚本
│   ├── evaluate.py                         # 评估脚本
│   └── smoke_test.py                       # 冒烟测试
├── tests/                                  # 单元测试
│   └── test_tennis_robot.py
├── docs/                                   # 文档
│   ├── development-log.md                  # 开发日志
│   ├── bootstrap-run-1.md                  # 自举验证报告
│   ├── dynamic-tennis-baseline.md          # baseline 冻结报告
│   ├── dynamic-tennis-baseline-metrics.json
│   └── tennis-robot-baseline-metrics.json
├── saved_models/                           # 训练模型
├── evaluation_results/                     # 评估结果
├── runs/                                   # TensorBoard 日志
└── web_viz_data/                           # Web 可视化数据
```

## 环境依赖

| 组件 | 版本 |
|---|---|
| Python | ≥3.10 |
| MuJoCo | ≥3.4.0 |
| Gymnasium | ≥1.2.0 |
| Stable-Baselines3 | ≥2.7.0 |
| PyTorch | ≥2.3.0 |
| NumPy | ≥1.26.0 |

安装：

```bash
pip install -e .
```

## 快速开始

### 冒烟测试

```bash
python scripts/smoke_test.py
```

### 训练

```bash
python scripts/train.py --algorithm SAC --total_timesteps 5000 --version v1 --n_envs 1
```

支持的算法：`SAC`、`PPO`、`DDPG`、`TD3`

### 评估

```bash
python scripts/evaluate.py --model_path saved_models/v1/tennis_robot_SAC_final --algorithm SAC --episodes 5
```

### Web 可视化

```bash
python -m tennis_robot.visualization.web.server --port 8080
```

## 环境规格

| 属性 | 值 |
|---|---|
| 环境ID | `TennisNavigation-v1` |
| 观测空间 | `Box(12,)` float64 |
| 动作空间 | `Box(3,)` float64, [-1, 1] |
| frame_skip | 20 |
| max_episode_steps | 2000 |
| 目标容差 | 0.5m |

### 观测向量 (12维)

| 索引 | 内容 | 归一化 |
|---|---|---|
| 0 | goal_distance | / diagonal_length |
| 1 | goal_angle | / 2π |
| 2 | rel_angle | / π |
| 3 | yaw | / 2π |
| 4-6 | vx, vy, vz | / max_vel |
| 7-9 | wx, wy, wz | / max_ang_vel |
| 10-11 | 网球 vx, vy | / max_vel |

### 动作向量 (3维, Mecanum IK)

| 索引 | 内容 | 范围 |
|---|---|---|
| 0 | x_move (前进/后退) | [-1, 1] |
| 1 | y_move (左右平移) | [-1, 1] |
| 2 | rotate (旋转) | [-1, 1] |

## 自举来源

本项目由以下 sports-robot skills/plugins 生成：

- `mujoco-tennis-world-builder` — MuJoCo 网球世界
- `gymnasium-mujoco-env-builder` — Gymnasium 环境封装
- `sb3-rl-training-runner` — SB3 训练入口
- `mujoco-policy-evaluator` — 策略评估
- `robot-trajectory-web-visualizer` — Web 可视化
- `truth-state-policy-input` — 真值状态观测
- `sim-camera-perception-input` — 仿真相机感知
- `ball-project-distiller` — 项目能力抽取
