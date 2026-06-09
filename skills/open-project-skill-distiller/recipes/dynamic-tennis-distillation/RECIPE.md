# Dynamic Tennis Distillation Recipe

## 概述

从 dynamic-tennis 项目中蒸馏可复用技能模式。

## 源项目

- 路径：`dynamic-tennis`
- 类型：tennis
- 许可证：需确认

## 蒸馏步骤

### 步骤 1：识别 MuJoCo 场景

源文件：
- `mujoco_mecanum/robots/summit_xl_description/summit_xls.xml`
- `mujoco_mecanum/robots/summit_xl_description/assets/*.xml`

映射 skill：`mujoco-tennis-world-builder`

提取模式：
- XML include 层级结构（主文件 → 子资产）
- free joint 用于网球动态位置
- 执行器映射（4 轮电机）

### 步骤 2：识别 Gymnasium 环境

源文件：
- `scripts/envs/mecanum_navigator/mecanum_navigator_v1.py`
- `scripts/envs/navigaterobot/navigaterobot_v2.py`

映射 skill：`gymnasium-mujoco-env-builder`

提取模式：
- MujocoEnv → WTRBlockReacherEnv → MecanumNavigatorEnv 继承链
- 12 维观测空间（距离、角度、速度、网球速度）
- 3 维动作空间（Mecanum IK）
- 预测性导航奖励函数
- 网球动态更新（恒速直线运动）

### 步骤 3：识别训练入口

源文件：
- `scripts/train_mecanum_navigator.py`

映射 skill：`sb3-rl-training-runner`

提取模式：
- SAC/PPO/DDPG/TD3 算法选择
- SubprocVecEnv 并行训练
- MecanumPlotsCallback 自定义回调
- 模型保存与继续训练

### 步骤 4：识别评估脚本

源文件：
- `scripts/test_mecanum_navigation.py`

映射 skill：`mujoco-policy-evaluator`

提取模式：
- 模型加载与评估
- 指标记录（reward、steps、success、distance）

### 步骤 5：识别配置管理

源文件：
- `scripts/cfg/mecanum_navigator.yaml`

映射 skill：无（新 skill 候选）

提取模式：
- YAML 配置分层（dynamics/reward_scales/navigation/mecanum/mujoco）
- 配置热加载

## 输出

- 技术栈图谱：`docs/assimilation/dynamic-tennis-stack-map.md`
- Skill 缺口报告：`docs/assimilation/dynamic-tennis-skill-gap.md`
