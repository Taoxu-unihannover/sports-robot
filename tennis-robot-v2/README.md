# tennis-robot-v2

> 基于 sports-robot 的 ball-project-assimilator 插件，对 dynamic-tennis/dynamic-tennis-v2 的吸收与超越产物。

## 项目概述

tennis-robot-v2 是 sports-robot 框架执行"开源球类机器人项目吸收与超越计划"的产物，通过以下四阶段工作流生成：

1. **技术栈拆解**：扫描 dynamic-tennis-v2，输出技术栈图谱和 skill gap
2. **项目复现**：基于 sports-robot skills 生成复现项目
3. **横向评测**：对比 v1/v2/dynamic-tennis-v2 三版本性能
4. **最优组合**：选择各技术栈最优方法组合，形成超越方案

## 核心改进（v2 vs v1）

| 改进项 | v1 问题 | v2 改进 | 来源 |
|--------|---------|---------|------|
| 奖励函数 | 只有基础距离奖励 | 添加预测性导航奖励 + velocity_alignment | dynamic-tennis |
| 拦截点计算 | 无 | 添加 intercept_bonus 奖励 | dynamic-tennis |
| control_cost | 0.001 (过高) | 0.0005 | dynamic-tennis |
| step_penalty | 无 | -0.3 | dynamic-tennis |
| XML 加载 | 临时目录拷贝 | from_xml_string 优先 | sports-robot |

## 项目结构

```
tennis-robot-v2/
├── configs/              # 环境、训练、感知配置
├── docs/                 # 开发日志和性能报告
├── saved_models/         # 训练模型
├── tennis_robot_v2/      # 核心代码
│   ├── envs/             # Gymnasium 环境
│   ├── perception/       # 感知模块（sim/real 双模式）
│   └── ...
├── tests/                # 测试
└── README.md
```

## 安装

```bash
pip install -e .
```

## 快速开始

### 1. 环境测试

```bash
python -c "
import gymnasium as gym
from tennis_robot_v2.envs.registration import register
import gymnasium as gym
env = gym.make('TennisNavigationV2-v1')
obs, info = env.reset()
print(f'Observation shape: {obs.shape}')
env.close()
"
```

### 2. 训练（Sim 模式）

```bash
python scripts/train.py --total_timesteps 50000
```

### 3. 评估

```bash
python scripts/evaluate.py --episodes 10 --model saved_models/tennis_robot_v2_sac.zip
```

## 性能验证结果

### Sim 模式（真值推理）评测

| 指标 | dynamic-tennis-v2 Baseline | tennis-robot-v2 | 超越判定 |
|------|---------------------------|-----------------|----------|
| 成功率 | 86.7% | **93.3%** | ✅ +7.6% |
| 平均奖励 | 14145.5 | **14992.2** | ✅ +6.0% |
| 奖励标准差 | 4525.0 | **3751.0** | ✅ 更稳定 |

### Real 模式（图像推理）评测

| 指标 | Baseline (sim) | Real 模式 | Gap |
|------|----------------|-----------|-----|
| 成功率 | 86.7% | 20% | -66.7% |

**Real 模式瓶颈**：
- 球检测率 75.8%
- 深度估计精度不足
- sim→real domain gap

**Real 模式优化路径**：
- P0: YOLOv8 替代 HSV 检测（目标 90%+ 检测率）
- P0: Domain randomization 训练
- P1: WLS 滤波提升深度精度

## 吸收的 Skills 和 Plugins

### 核心 Skills

| Skill | 来源 | 功能 |
|-------|------|------|
| `mujoco-tennis-world-builder` | sports-robot | MuJoCo 网球世界构建 |
| `gymnasium-mujoco-env-builder` | sports-robot | Gymnasium 环境封装 |
| `sb3-rl-training-runner` | sports-robot | SB3 训练入口 |
| `truth-state-policy-input` | sports-robot | 真值状态观测 |
| `sim-camera-perception-input` | sports-robot | 仿真相机感知 |

### Plugins

| Plugin | 功能 |
|--------|------|
| `ball-project-assimilator` | 球类机器人项目吸收与超越主插件 |
| `ball-project-distiller` | 项目技术栈沉淀 |

## 关键技术洞察

### 1. 观测向量的双速度源设计

`env._get_obs()` 的 16 维观测向量内部使用了两种不同的速度来源：
- **dims 10-12**：位置差分速度 `(pos_t - pos_{t-1}) / dt`
- **dim 13 (TTC)**：MuJoCo qvel 物理速度

### 2. Coriolis 修正

从 base 坐标系速度恢复世界坐标系速度需要 Coriolis 项：
```
v_world = v_robot_world + R_b2w @ v_base + ω × r_world
```

### 3. 课程学习的风险

Baseline 明确禁用课程学习，使用固定高难度训练效果更好。

## 文档

- [开发日志](docs/development-log.md) - 详细开发过程记录
- [代码级验证报告](docs/code-level-verification-report.md) - 功能验证详情
- [Baseline 指标](docs/dynamic-tennis-v2-baseline-metrics.json) - 原始项目性能
- [tennis-robot-v2 指标](docs/tennis-robot-v2-baseline-metrics.json) - 复现项目性能

## License

继承 sports-robot 框架 License
