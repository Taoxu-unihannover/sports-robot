---
name: gymnasium-mujoco-env-builder
description: 生成标准 Gymnasium MuJoCo 环境，支持 reset/step/render/observation_space/action_space 接口和 check_env 验证。适用于用户需要创建自定义 Gymnasium 环境、封装 MuJoCo 仿真、定义观测/动作空间；不用于纯 MuJoCo 场景搭建或 RL 训练入口。
---

# Gymnasium MuJoCo 环境构建

## 用途

基于 MuJoCo 仿真场景生成符合 Gymnasium 标准接口的 RL 环境，支持 `stable_baselines3.common.env_checker.check_env` 验证。提供环境模板、观测/动作 schema、奖励函数模板和终止条件模板。

## 输入

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| env_name | string | 是 | 环境名称，如 TennisNavigationEnv |
| xml_file | string | 是 | MuJoCo XML 场景路径 |
| observation_schema | list | 是 | 观测向量定义 [{name, type, low, high, normalize}] |
| action_schema | list | 是 | 动作向量定义 [{name, type, low, high}] |
| reward_config | dict | 否 | 奖励函数配置 |
| termination_config | dict | 否 | 终止条件配置 |
| max_episode_steps | int | 否 | 默认 2000 |
| frame_skip | int | 否 | 默认 5 |

## 输出

| 产物 | 路径 | 说明 |
|---|---|---|
| 环境类 | scripts/{env_name}.py | 标准 Gymnasium 环境 |
| 配置模板 | assets/env_config.yaml | 环境配置文件 |
| 环境测试 | tests/test_env.py | check_env + smoke test |

## 执行步骤

### 步骤 1：定义观测空间

标准观测向量构建模式：

```python
def _get_obs(self) -> np.ndarray:
    robot_pos = self.data.qpos[robot_start:robot_start+2].copy()
    robot_quat = self.data.qpos[robot_start+3:robot_start+7].copy()
    robot_vel = self.data.qvel[robot_vel_start:robot_vel_start+6].copy()
    goal_rel = self.goal - robot_pos
    goal_distance = np.linalg.norm(goal_rel)
    goal_angle = np.arctan2(goal_rel[1], goal_rel[0])
    yaw = self._quat_to_euler(robot_quat)[2]
    rel_angle = self._normalize_angle(goal_angle - yaw)
    obs = np.array([
        goal_distance / self.diagonal_length,
        goal_angle / (2 * np.pi),
        rel_angle / np.pi,
        yaw / (2 * np.pi),
        *robot_vel[:3] / self.max_vel,
        *robot_vel[3:] / self.max_ang_vel,
    ])
    return obs
```

归一化规则：
- 距离类：除以对角线长度
- 角度类：除以 π 或 2π
- 速度类：除以最大速度限制

### 步骤 2：定义动作空间

标准动作空间模式：

| 底盘类型 | 动作维度 | 说明 |
|---|---|---|
| differential | 2 | [v, ω] |
| mecanum | 3 | [x_move, y_move, rotate] |
| arm | N | 关节角度/速度 |

动作归一化：所有动作空间为 Box(-1, 1)，通过 denormalize 映射到实际控制量。

### 步骤 3：实现 reset

```python
def reset(self, seed=None, options=None):
    super().reset(seed=seed)
    self.reached, self.failed = False, False
    self.step_count = 0
    self.data.qpos[:] = self.init_pos.copy()
    self.data.qvel[:] = np.zeros(self.model.nv)
    self.data.time = 0.0
    self._reset_goal()
    mujoco.mj_forward(self.model, self.data)
    self.prev_distance = self._compute_distance()
    observation = self._get_obs()
    info = self._get_info()
    return observation, info
```

### 步骤 4：实现 step

```python
def step(self, action):
    self.step_count += 1
    ctrl = self._action_to_ctrl(action)
    self.do_simulation(ctrl, self.frame_skip)
    self._update_dynamics()
    self._check_termination()
    reward = self._compute_reward(action)
    observation = self._get_obs()
    terminated, truncated = self.terminated, self.truncated
    info = self._get_info()
    return observation, reward, terminated, truncated, info
```

### 步骤 5：实现奖励函数

标准奖励组件：

| 组件 | 公式 | 说明 |
|---|---|---|
| distance_incentive | w_d × (prev_d - curr_d) | 接近目标奖励 |
| terminal_payoff | +R (success) / -R (failure) | 终止奖励 |
| inTimeCost | w_t × (t_accepted - elapsed) | 及时完成奖励 |
| control_cost | w_c × Σ(a²) | 控制代价 |
| step_penalty | w_s × (-1) | 步数惩罚 |

### 步骤 6：验证

```python
from stable_baselines3.common.env_checker import check_env
env = MyEnv()
check_env(env)
```

## 失败处理

| 失败场景 | 处理策略 |
|---|---|
| check_env 失败 | 检查观测/动作空间定义、reward 类型、info 格式 |
| MuJoCo 加载失败 | 检查 XML 路径和 qpos 索引 |
| 奖励发散 | 检查归一化和奖励权重 |

## 验证方式

1. `check_env(env)` 通过
2. `env.reset()` 返回 (obs, info)
3. `env.step(action)` 返回 (obs, reward, terminated, truncated, info)
4. 短训练 1000 steps 无崩溃

## 可选 Recipes

| Recipe | 说明 |
|---|---|
| mecanum-navigation-env | 麦克纳姆底盘导航环境 |
| arm-reacher-env | 机械臂到达环境 |
