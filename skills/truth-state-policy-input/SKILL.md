---
name: truth-state-policy-input
description: 将 MuJoCo 仿真真值状态转换为策略观测向量，定义归一化、延迟模拟、噪声注入和缺失值处理。适用于用户需要构造 RL 策略的观测输入、对比真值输入与感知输入的性能差异；不用于图像感知或视觉估计。
---

# 真值状态策略输入

## 用途

从 MuJoCo 仿真数据中提取真值状态（球位置/速度、机器人位置/速度、目标点、距离），构造标准化的策略观测向量。支持归一化、观测延迟模拟、高斯噪声注入和缺失值处理，用于 RL 训练和 sim-to-real 性能对比。

## 输入

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| observation_schema | list | 是 | 观测向量定义 |
| mujoco_data | MjData | 是 | MuJoCo 仿真数据 |
| goal_position | array | 是 | 目标位置 |
| normalize | bool | 否 | 是否归一化，默认 True |
| noise_std | float | 否 | 高斯噪声标准差，默认 0.0 |
| delay_steps | int | 否 | 观测延迟步数，默认 0 |

## 输出

| 产物 | 路径 | 说明 |
|---|---|---|
| 观测构建器 | scripts/observation_builder.py | 观测向量构造 |
| 归一化器 | scripts/normalizer.py | 归一化/反归一化 |
| 测试 | tests/test_observation.py | 观测一致性测试 |

## 执行步骤

### 步骤 1：定义观测 Schema

标准观测 schema 格式：

```yaml
observation:
  - name: goal_distance
    source: "np.linalg.norm(goal - robot_pos)"
    normalize: diagonal_length
    type: float
  - name: goal_angle
    source: "np.arctan2(rel_y, rel_x)"
    normalize: 2*pi
    type: float
  - name: rel_angle
    source: "normalize_angle(goal_angle - yaw)"
    normalize: pi
    type: float
  - name: yaw
    source: "quat_to_euler(quat)[2]"
    normalize: 2*pi
    type: float
  - name: linear_velocity
    source: "qvel[6:9]"
    normalize: max_vel
    type: array
    shape: [3]
  - name: angular_velocity
    source: "qvel[9:12]"
    normalize: max_ang_vel
    type: array
    shape: [3]
```

### 步骤 2：实现观测构建

```python
class ObservationBuilder:
    def __init__(self, schema, config):
        self.schema = schema
        self.config = config
        self.obs_buffer = deque(maxlen=delay_steps+1) if delay_steps > 0 else None

    def build(self, data, goal):
        robot_pos = data.qpos[7:9].copy()
        robot_quat = data.qpos[10:14].copy()
        robot_vel = data.qvel[6:12].copy()
        yaw = self._quat_to_euler(robot_quat)[2]
        rel = goal - robot_pos
        goal_distance = np.linalg.norm(rel)
        goal_angle = np.arctan2(rel[1], rel[0])
        rel_angle = self._normalize_angle(goal_angle - yaw)

        obs = np.array([
            goal_distance / self.diagonal_length,
            goal_angle / (2 * np.pi),
            rel_angle / np.pi,
            yaw / (2 * np.pi),
            *(robot_vel[:3] / self.max_vel),
            *(robot_vel[3:] / self.max_ang_vel),
        ])

        if self.noise_std > 0:
            obs += np.random.normal(0, self.noise_std, obs.shape)

        if self.obs_buffer is not None:
            self.obs_buffer.append(obs)
            return self.obs_buffer[0]

        return obs
```

### 步骤 3：归一化/反归一化

```python
class Normalizer:
    def __init__(self, lows, highs):
        self.lows = np.array(lows)
        self.highs = np.array(highs)

    def normalize(self, x):
        return (x - self.lows) / (self.highs - self.lows + 1e-8)

    def denormalize(self, x):
        return x * (self.highs - self.lows) + self.lows
```

### 步骤 4：验证

- 观测向量维度与 schema 一致
- 归一化后值在合理范围
- 噪声注入后仍可训练
- 延迟模拟后观测正确

## 失败处理

| 失败场景 | 处理策略 |
|---|---|
| qpos 索引越界 | 检查模型结构和索引映射 |
| 归一化除零 | 添加 epsilon 保护 |
| 延迟缓冲区空 | 首步返回当前观测 |

## 验证方式

1. 观测维度正确
2. 归一化/反归一化可逆
3. 噪声注入后均值无偏
4. 与 dynamic-tennis 观测格式兼容

## 可选 Recipes

| Recipe | 说明 |
|---|---|
| mecanum-12d-observation | 麦克纳姆12维观测 |
| arm-7d-observation | 机械臂7维观测 |
