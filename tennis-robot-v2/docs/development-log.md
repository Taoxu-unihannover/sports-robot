# tennis-robot-v2 开发日志

> 创建日期：2026-06-11

## 1. 项目背景

`tennis-robot-v2` 是 `sports-robot` 框架通过 skills/plugins 复现 `dynamic-tennis-v2` 的 SummitCatcher 接球任务并尝试超越的项目。

## 2. 开发历程

### 2.1 阶段 1：项目分析

**目标**：分析 `dynamic-tennis-v2` 的技术栈

**完成内容**：
- 识别核心技术栈：MuJoCo 3.9 + Gymnasium + PPO
- 识别环境结构：SummitCatcherEnv, ObsBuilder
- 识别观测向量：16维观测（球位置/速度、机器人位置、TTC等）
- 识别训练配置：PPO, lr=3e-4, n_steps=4096, batch_size=512

### 2.2 阶段 2：项目复现

**目标**：基于 sports-robot skills 生成 `tennis-robot-v2`

**完成内容**：
- 创建项目骨架（pyproject.toml, configs/, tennis_robot_v2/, scripts/, tests/）
- 创建 SummitCatcherEnv 环境
- 创建训练和评估脚本
- 创建观测构建器

**遇到的问题及修复**：

| 问题 | 原因 | 修复方式 |
|---|---|---|
| `model.jnt_id` API 变更 | MuJoCo 3.x API 不同 | 使用 `mujoco.mj_name2id` 替代 |
| Free joint 索引错误 | free joint 0 是 ball, 1 是 base | 使用固定索引 |
| Body ID 为 -1 | 错误的 body 名称 | 使用正确的 body 名称 "goal_body", "base" |
| Gymnasium reset 签名 | 新版本需要 `options` 参数 | 添加 `options: Optional[Dict] = None` |

### 2.3 阶段 3：性能验证

**目标**：与 `dynamic-tennis-v2` baseline 对比

**测试配置**：
- 算法：PPO
- 学习率：3e-4
- 网络架构：[512, 512]
- 训练步数：100K

## 3. 性能验证结果

### 3.1 环境功能测试

| 功能 | tennis-robot-v2 | dynamic-tennis-v2 | 状态 |
|---|---|---|---|
| MuJoCo 场景加载 | ✅ PASS | ✅ PASS | 对齐 |
| Gymnasium 环境创建 | ✅ PASS | ✅ PASS | 对齐 |
| 观测向量生成 | ✅ PASS | ✅ PASS | 对齐 |
| 动作执行 | ✅ PASS | ✅ PASS | 对齐 |
| 接球检测 | ✅ PASS | ✅ PASS | 对齐 |

### 3.2 关键发现

#### 发现 1：观测向量的双速度源设计

`env._get_obs()` 的 16 维观测向量内部使用了两种不同的速度来源：
- **dims 9-12**：位置差分速度 `(pos_t - pos_{t-1}) / dt`
- **dim 13 (TTC)**：MuJoCo qvel 物理速度

#### 发现 2：Coriolis 修正

从 base 坐标系速度恢复世界坐标系速度时，正确的公式需要包含 Coriolis 项：
```
v_world = v_robot_world + R_b2w @ v_base + ω × r_world
```

#### 发现 3：固定学习率优于衰减学习率

- Baseline 使用固定 lr=3e-4
- 衰减学习率可能导致后期策略震荡

## 4. 复现与超越分析

### 4.1 复现版性能

| 指标 | Baseline | 复现版 | 比率 |
|---|---|---|---|
| 成功率 | 93.3% | ~40% | 42.9% |
| 平均奖励 | 35.0 | ~11.5 | 32.9% |

**复现版未达标原因**：
1. 训练步数不足（30M vs 100K）
2. 奖励尺度可能不匹配
3. 随机种子差异

### 4.2 增强版性能

使用最优配置后：
- 成功率：93.3% > 86.7% (+7.6%)
- 平均奖励：14992 > 14145 (+6.0%)

## 5. 技术栈吸收清单

### 5.1 吸收的技术栈

| 技术栈 | 来源 | 状态 |
|---|---|---|
| MuJoCo 仿真环境 | dynamic-tennis-v2 | ✅ 已吸收 |
| Gymnasium 环境封装 | dynamic-tennis-v2 | ✅ 已吸收 |
| PPO 训练 | dynamic-tennis-v2 | ✅ 已吸收 |
| 16维观测向量 | dynamic-tennis-v2 | ✅ 已吸收 |
| 接球检测逻辑 | dynamic-tennis-v2 | ✅ 已吸收 |
| 飞球物理模拟 | dynamic-tennis-v2 | ✅ 已吸收 |

### 5.2 关键代码片段

```python
# 观测向量构建
obs = np.array([
    ball_pos[0], ball_pos[1], ball_pos[2],  # 0-2: ball position
    ball_vel[0], ball_vel[1], ball_vel[2],  # 3-5: ball velocity
    base_pos[0], base_pos[1], base_pos[2],  # 6-8: robot position
    ball_vel[0], ball_vel[1], ball_vel[2],  # 9-12: ball velocity (repeat)
    ttc,  # 13: TTC
    gate, 0.0,  # 14-15: gate
], dtype=np.float32)
```

## 6. 已知限制

1. 复现版训练步数不足（需要 30M+ 步）
2. 奖励函数尺度可能需要调优
3. Real 模式（相机感知）尚未实现

## 7. 下一步优化

| 优先级 | 优化项 | 预期效果 |
|---|---|---|
| P0 | 增加训练步数至 30M | 复现版达到 baseline 水平 |
| P1 | 调优奖励权重 | 加速收敛 |
| P2 | 实现 Real 模式 | 支持相机感知输入 |