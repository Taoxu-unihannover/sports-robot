# Dynamic Tennis Assimilation Recipe

## 概述

以 `dynamic-tennis` 为首个验证样本，执行完整的吸收与超越流程。

## 项目信息

| 属性 | 值 |
|---|---|
| 项目名称 | dynamic-tennis |
| 仓库地址 | https://github.com/Taoxu-unihannover/dynamic-tennis |
| 项目类型 | tennis |
| 语言 | Python |
| 仿真平台 | MuJoCo |
| RL 框架 | Stable-Baselines3 |
| 环境 | Gymnasium |

## 阶段 1：技术栈拆解

### 1.1 扫描项目

```bash
python plugins/ball-project-assimilator/scripts/scan_project.py \
  --project_path dynamic-tennis \
  --project_name dynamic-tennis \
  --project_url https://github.com/Taoxu-unihannover/dynamic-tennis \
  --domain tennis \
  --output_dir docs/assimilation
```

### 1.2 已知技术栈

| 技术栈 | 模块 | 映射 Skill | 覆盖状态 |
|---|---|---|---|
| 仿真 | MuJoCo 网球世界 | mujoco-tennis-world-builder | ✅ 已覆盖 |
| 感知 | 真值状态观测 | truth-state-policy-input | ✅ 已覆盖 |
| 感知 | 仿真相机 | sim-camera-perception-input | ✅ 已覆盖 |
| 训练 | SB3 SAC/PPO | sb3-rl-training-runner | ✅ 已覆盖 |
| 评估 | 策略评估 | mujoco-policy-evaluator | ✅ 已覆盖 |
| 可视化 | Web 轨迹可视化 | robot-trajectory-web-visualizer | ✅ 已覆盖 |
| 执行 | Mecanum 底盘 | mobile-base-executor | ⚠️ 部分覆盖 |
| 控制 | Mecanum IK | 内嵌于环境 | ⚠️ 部分覆盖 |
| 奖励 | 预测性导航奖励 | gymnasium-mujoco-env-builder | ⚠️ 部分覆盖 |
| 工程 | 配置管理 | 无 | ❌ 未覆盖 |

### 1.3 Skill 缺口

| 优先级 | 缺口 | 补充方案 |
|---|---|---|
| P0 | 预测性导航奖励函数 | 扩展 gymnasium-mujoco-env-builder recipe |
| P0 | 网球轨迹预测拦截 | 新建 tennis-interception-recipe |
| P1 | Mecanum IK 独立模块 | 扩展 mobile-base-executor |
| P2 | 配置管理 | 新建 config-manager skill |

## 阶段 2：项目复现

### 2.1 创建复现项目

```bash
# 使用 tennis-robot-v2 作为复现项目
mkdir tennis-robot-v2
```

### 2.2 通过 skills 生成

调用以下 skills 生成复现项目：
1. `mujoco-tennis-world-builder` → MuJoCo 场景
2. `gymnasium-mujoco-env-builder` → Gymnasium 环境
3. `sb3-rl-training-runner` → 训练入口
4. `mujoco-policy-evaluator` → 评估脚本
5. `robot-trajectory-web-visualizer` → 可视化
6. `truth-state-policy-input` → 观测构造
7. `sim-camera-perception-input` → 感知输入

### 2.3 验证命令

```bash
cd tennis-robot-v2
python scripts/smoke_test.py
python scripts/train.py --algorithm SAC --total_timesteps 5000 --version baseline
python scripts/evaluate.py --model_path saved_models/baseline/tennis_robot_SAC_final --algorithm SAC --episodes 5
```

### 2.4 性能目标

| 指标 | dynamic-tennis baseline | 复现目标 (≥95%) |
|---|---|---|
| 训练吞吐 | 19.9 steps/sec | ≥ 18.9 |
| 成功率 | 0.0% | 0.0% |
| 平均 reward | 20805.8 | ≥ 19765 |
| 平均最终距离 | 5.82m | ≤ 6.11m |

## 阶段 3：横向评测

### 3.1 评测技术栈

| 技术栈 | 项目 A 方法 | sports-robot 方法 | 评测指标 |
|---|---|---|---|
| 仿真 | 直接加载 XML | 临时目录拷贝 | 训练吞吐 |
| 观测 | 内嵌 _get_obs | truth-state recipe | 观测一致性 |
| 奖励 | 预测性导航奖励 | 基础距离奖励 | reward 收敛 |
| 训练 | SB3 SAC | SB3 SAC (同配置) | 收敛速度 |
| 评估 | 自定义脚本 | mujoco-policy-evaluator | 指标一致性 |

### 3.2 评测条件

- 算法：SAC
- 训练步数：5000
- 评估回合：5
- 随机种子：[0, 42, 123]

## 阶段 4：最优组合

### 4.1 最优方法选择

| 技术栈 | 最优方法 | 来源 | 原因 |
|---|---|---|---|
| 仿真 | from_xml_string | sports-robot | 避免临时目录 I/O |
| 观测 | 12维预测性观测 | project_a | 含网球速度和拦截预测 |
| 奖励 | 预测性导航奖励 | project_a | 收敛更快 |
| 训练 | SB3 SAC | 两者相同 | 标准实现 |
| 评估 | mujoco-policy-evaluator | sports-robot | 标准化输出 |

### 4.2 超越目标

| 指标 | baseline | 增强目标 (>5%) |
|---|---|---|
| 训练吞吐 | 19.9 steps/sec | > 20.9 |
| 成功率 | 0.0% | > 0% (需长训练) |
| 平均 reward | 20805.8 | > 21846 |
| 平均最终距离 | 5.82m | < 5.53m |
