# dynamic-tennis Baseline 冻结报告

> 创建日期：2026-06-09
> 状态：基线冻结 v1.0

## 一、环境依赖

### CPU 环境

| 组件 | 版本 |
|---|---|
| Python | 3.10 |
| MuJoCo | 3.4.0 |
| Gymnasium | 1.2.3 |
| Stable-Baselines3 | 2.7.1 |
| PyTorch | 2.3.0 |
| NumPy | 1.26.4 |
| PyYAML | 6.0.3 |
| Matplotlib | 3.10.8 |
| conda env | `wtr-set` (env-cpu.yaml) |

### GPU 环境

GPU 训练使用 `env-gpu.yaml`，额外依赖 CUDA 12.x + cuDNN。

## 二、可复现命令

### 环境检查

```bash
cd dynamic-tennis
conda activate wtr-set
python -c "from envs.mecanum_navigator.mecanum_navigator_v1 import MecanumNavigatorEnv; import gymnasium as gym; from stable_baselines3.common.env_checker import check_env; env = MecanumNavigatorEnv(); check_env(env); print('check_env PASSED')"
```

### 短训练 (smoke test)

```bash
cd dynamic-tennis/scripts
python train_mecanum_navigator.py --model SAC --total_timesteps 1000 --version smoke_test
```

### 完整训练

```bash
cd dynamic-tennis/scripts
python train_mecanum_navigator.py --model SAC --total_timesteps 15000 --version vgpu_dynamic_001
```

### 评估

```bash
cd dynamic-tennis/scripts
python test_mecanum_navigation.py --model ./saved_models/mecanum_navigator/SAC_vgpu_dynamic_001/vgpu_dynamic_001_9.zip --episodes 5
```

### Web 可视化

```bash
cd dynamic-tennis/web_visualization
python launch_server.py
```

## 三、核心环境架构

### 环境继承链

```
MujocoEnv (gymnasium)
  └── WTRBlockReacherEnv (navigaterobot_v2.py)
        └── MecanumNavigatorEnv (mecanum_navigator_v1.py)
```

### MuJoCo 模型架构

```
summit_xls.xml
  ├── assets.xml (compiler, textures, materials, meshes)
  ├── basic_scene.xml (ground, goal_body/tennis_ball, court markers, light)
  ├── summit_xls.urdf.xml (base_footprint → base → 4×omni_wheel → rollers)
  └── summit_xls_actuator.xml (4×motor actuators for wheels)
```

### 关键 qpos 布局

| 索引 | 内容 | 说明 |
|---|---|---|
| qpos[0:7] | goal_body (free joint) | 网球位置 (x,y,z,qw,qx,qy,qz) |
| qpos[7:14] | base_footprint (free joint) | 机器人位置 (x,y,z,qw,qx,qy,qz) |
| qpos[14:] | 轮子关节 | 4个轮子的滚动关节 |

### 关键 qvel 布局

| 索引 | 内容 | 说明 |
|---|---|---|
| qvel[0:6] | goal_body 速度 | 网球速度 |
| qvel[6:12] | base_footprint 速度 | 机器人速度 (vx,vy,vz,wx,wy,wz) |
| qvel[12:] | 轮子关节速度 | 4个轮子角速度 |

### 执行器映射

| 执行器索引 | 关节 | 说明 |
|---|---|---|
| ctrl[0] | front_right_wheel | 右前轮 |
| ctrl[1] | front_left_wheel | 左前轮 |
| ctrl[2] | back_right_wheel | 右后轮 |
| ctrl[3] | back_left_wheel | 左后轮 |

## 四、MecanumNavigatorEnv 规格摘要

| 属性 | 值 |
|---|---|
| 观测空间 | Box(12,) float64 |
| 动作空间 | Box(3,) float64, [-1, 1] |
| frame_skip | 20 |
| max_episode_steps | 2000 |
| 网球场尺寸 | 11.885m × 8.23m (单打半场) |
| 网球半径 | 0.067m |
| 目标容差 | 0.5m |
| 对角线归一化 | 14.45m |

### 观测向量 (12维)

| 索引 | 内容 | 归一化 |
|---|---|---|
| 0 | goal_distance_norm | / diagonal_length |
| 1 | goal_angle_norm | / 2π |
| 2 | rel_angle_norm | / π |
| 3 | yaw_norm | / 2π |
| 4 | vx (前向速度) | / max_vel |
| 5 | vy (横向速度) | / max_vel |
| 6 | vz (垂直速度) | / max_vel |
| 7 | wx (滚转角速度) | / max_ang_vel |
| 8 | wy (俯仰角速度) | / max_ang_vel |
| 9 | wz (偏航角速度) | / max_ang_vel |
| 10 | 网球vx | / max_vel |
| 11 | 网球vy | / max_vel |

### 动作向量 (3维, Mecanum IK)

| 索引 | 内容 | 范围 |
|---|---|---|
| 0 | x_move (前进/后退) | [-1, 1] |
| 1 | y_move (左右平移) | [-1, 1] |
| 2 | rotate (旋转) | [-1, 1] |

Mecanum IK 映射：
- front_left  = x_move - y_move - rotate
- front_right = x_move + y_move + rotate
- back_left   = x_move + y_move - rotate
- back_right  = x_move - y_move + rotate

### 奖励函数

```
reward = distance_incentive × (prev_distance - curr_distance)
       + terminal_payoff (success: +10000, failure: -10000)
       + inTimeCost × (t_accepted - elapsed_time)  [if reached]
       - control_cost × Σ(action²)
```

### 终止条件

- **reached**: 机器人到网球距离 ≤ 0.5m
- **failed**: 机器人超出网球场边界 (x < -8 or x > 8 or y < -8 or y > 8)
- **truncated**: 达到 max_episode_steps

## 五、已有模型

| 模型路径 | 算法 | 说明 |
|---|---|---|
| saved_models/mecanum_navigator/SAC_vgpu_dynamic_001/ | SAC | 移动网球导航，9个checkpoint |

## 六、基线指标 (5000 steps SAC)

| 指标 | 值 | 采集条件 |
|---|---|---|
| check_env | PASSED | 单次运行 |
| 短训练 1000 steps | 无崩溃 | SAC, seed=0 |
| 训练吞吐 | 19.9 steps/sec | 5000 steps |
| 成功率 | 0.0% | 5 episodes |
| 平均 episode reward | 20805.8 | 5 episodes |
| 平均最终距离 | 5.82m | 5 episodes |
| 平均步数 | 209.2 | 5 episodes |

## 七、已知限制

1. 部分环境文件 (armreacher, stroke, 3Dreacher) 包含硬编码绝对路径，无法直接在其他机器运行
2. MecanumNavigatorEnv 的网球位置在 reset 时使用 time+pid 作为种子，训练时不可完全复现
3. Web 可视化依赖浏览器环境，无头环境只能导出 JSON 数据
4. 基类 WTRBlockReacherEnv 的 checkFlags 使用硬编码边界 (-8, 8)，MecanumNavigatorEnv 未覆盖此方法
5. MuJoCo 不支持中文路径，需通过临时目录拷贝解决
