# Ball Control — 球类控制开发 Team

> 控制层开发环境。含 7 个专业 Skill、3 个 Agent、击球规划到安全监督的完整 pipeline，以及 RL 训练 runner、真值状态策略输入和图像感知策略输入。

## 架构概览

```
ball-control/
├── plugin.json
├── AGENTS.md
├── quickstart.md
├── init.sh
├── assets/config.yaml
├── agents/
│   ├── control-architect.md
│   ├── control-developer.md
│   └── control-reviewer.md
├── scripts/pipeline.py
├── tests/regression.py
├── references/papers.md
├── examples/control_command.md
└── workflows/
```

## 七模块 Skills

| Skill | 职责 | 输入 | 输出 |
|-------|------|------|------|
| `hit-planner` | 击球点/时间/目标速度规划 | 预测轨迹、目标落点 | HitPlan |
| `mpc-controller` | 实时跟踪控制基线 | 状态、参考、约束 | 控制输入 |
| `skill-policy-controller` | 技能路由与动作混合 | 场景上下文 | 技能选择 |
| `control-safety-supervisor` | 控制安全门控 | 目标命令、边界 | ok/unsafe + reason |
| `sb3-rl-training-runner` | SB3 训练入口 | 环境配置、超参 | 训练模型 |
| `truth-state-policy-input` | 真值状态策略输入 | 仿真状态 | 归一化观测向量 |
| `sim-camera-perception-input` | 仿真相机感知输入 | MuJoCo 渲染图像 | 状态估计 |

## RL 训练与策略输入

### SB3 训练 Runner

支持 SAC/PPO/DDPG/TD3 算法的标准训练流程：

- 算法选择：通过配置文件指定算法和超参
- 并行环境：`make_vec_env` 创建多环境
- Checkpoint：定期保存模型和回放缓冲区
- TensorBoard：自动记录训练指标
- 继续训练：加载已有模型继续训练

### 真值状态策略输入

将仿真真值转换为策略观测向量：

- 目标距离：归一化到 [0, 1]（除以对角线长度）
- 目标角度：归一化到 [-1, 1]（除以 π）
- 相对角度：目标相对机器人朝向
- 机器人速度：归一化到 [-1, 1]（除以最大速度）
- 球速度：归一化到 [-1, 1]

### 图像感知策略输入

从 MuJoCo 渲染图像获取状态估计：

1. 配置 MuJoCo 相机（位置、朝向、分辨率）
2. 渲染 RGB/深度图像
3. 运行球体检测（颜色/轮廓/深度分割）
4. 状态估计（位置 + 速度）
5. 与真值对比计算误差

## 三 Agent 分工

### Control Architect

- 职责：控制频率分层、规划/MPC/策略选型、安全边界设计、RL 训练策略。
- 输出：`DESIGN.md` + `PLAN.md`。

### Control Developer

- 职责：实现规划器、控制器、技能策略、安全监督和回归测试、RL 训练脚本。
- 输出：控制 pipeline、配置、测试报告。

### Control Reviewer

- 职责：审查可达性、实时性、限幅、fallback 和安全状态机、训练收敛性。
- 输出：`REVIEW.md`、失败模式覆盖清单。

## 工作流

```
Step 1: Architect 冻结目标、约束、频率
Step 2: Developer 实现 planner/MPC/policy/safety
Step 3: Developer 运行回归与边界测试
Step 4: Reviewer 检查安全监督和执行层接口
```
