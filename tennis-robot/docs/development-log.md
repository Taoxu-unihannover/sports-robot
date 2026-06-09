# tennis-robot 开发日志

> 创建日期：2026-06-09

## 1. 项目背景

`tennis-robot` 是 `sports-robot` 框架通过 skills/plugins 自举生成的网球机器人仿真训练项目。核心约束：不直接复制 `dynamic-tennis` 源码，只使用已沉淀的通用能力生成。

## 2. 开发历程

### 2.1 阶段 A：基线冻结

**目标**：冻结 `dynamic-tennis` 的可复现基线指标。

**完成内容**：
- 记录 `dynamic-tennis` 环境依赖（MuJoCo 3.4, Gymnasium 1.2.3, SB3 2.7.1）
- 记录可复现命令（训练、评估、Web 可视化）
- 记录环境架构（MujocoEnv → WTRBlockReacherEnv → MecanumNavigatorEnv）
- 记录观测/动作空间规格（12维观测, 3维动作）
- 输出 `dynamic-tennis-baseline.md`

**发现的问题**：
- MuJoCo 不支持中文路径，`dynamic-tennis` 在含中文的路径下无法加载 XML
- 部分环境文件包含硬编码绝对路径
- 网球位置 reset 使用 time+pid 作为种子，不可完全复现

### 2.2 阶段 B：第一次自举

**目标**：使用 sports-robot skills 生成 `tennis-robot` 最小骨架。

**完成内容**：
- 生成项目骨架（pyproject.toml, configs/, assets/, tennis_robot/, scripts/, tests/）
- 生成 MuJoCo 网球世界（5个 XML 文件）
- 生成 Gymnasium 环境（TennisNavigationEnv, 环境注册）
- 生成 SB3 SAC 训练入口
- 生成评估脚本
- 生成 Web 可视化模块
- 生成仿真相机感知模块
- 生成麦克纳姆控制器

**遇到的问题及修复**：

| 问题 | 原因 | 修复方式 |
|---|---|---|
| MuJoCo XML 加载失败 | 中文路径不兼容 | 添加 `_resolve_xml_path` 将资产拷贝到临时目录 |
| `reset_model` 未实现 | MujocoEnv 要求子类实现 | 拆分 reset 逻辑到 `reset_model` |
| `make_vec_env` 缺少 rank 参数 | 自定义 make_env 签名错误 | 直接使用环境 ID 创建 |
| 项目根路径错误 | os.path.dirname 层数不对 | 修正为三层 dirname |
| 网球不触发出界 | 缺少网球边界检查 | 添加 tennis_out_of_bounds 条件 |

### 2.3 阶段 C：性能验证

**目标**：与 `dynamic-tennis` baseline 对比，验证功能覆盖和性能。

**测试配置**：
- 算法：SAC
- 训练步数：5000
- 评估回合：5
- 超参：lr=5e-4, buffer=3M, batch=512, net=[1024, 512]

## 3. 性能验证结果

### 3.1 功能覆盖

| 功能 | tennis-robot | dynamic-tennis | 状态 |
|---|---|---|---|
| MuJoCo 场景加载 | ✅ PASS | ✅ PASS | 对齐 |
| Gymnasium check_env | ✅ PASS | ✅ PASS | 对齐 |
| 短训练 1000 steps | ✅ 无崩溃 | ✅ 无崩溃 | 对齐 |
| 5000 steps 训练 | ✅ 无崩溃 | ✅ 无崩溃 | 对齐 |
| 模型保存/加载 | ✅ 正常 | ✅ 正常 | 对齐 |
| 评估脚本运行 | ✅ 正常 | ✅ 正常 | 对齐 |
| 轨迹可视化导出 | ✅ JSON+PNG | ✅ JSON+PNG | 对齐 |
| Web 可视化 HTML | ✅ 已生成 | ✅ 已有 | 对齐 |
| 仿真相机感知 | ✅ 模块就绪 | ✅ 已有 | 对齐 |
| Mecanum 控制器 | ✅ 独立模块 | ✅ 内嵌环境 | 对齐 |

### 3.2 性能对比 (5000 steps SAC)

| 指标 | dynamic-tennis | tennis-robot | 比率 | 判定 |
|---|---|---|---|---|
| check_env | PASS | PASS | - | ✅ |
| 训练吞吐 (steps/sec) | 19.9 | 18.5 | 93.0% | ⚠️ 略低于95%线 |
| 成功率 | 0.0% | 0.0% | - | ✅ 相同 |
| 平均 episode reward | 20805.8 | -20678.2 | - | ⚠️ 尺度差异 |
| 平均 episode 步数 | 209.2 | 207.6 | 99.2% | ✅ |
| 平均最终距离 (m) | 5.82 | 7.32 | 125.8% | ⚠️ 超过105%线 |

### 3.3 逐 episode 对比

**dynamic-tennis**:

| Episode | Reward | Steps | Success | Final Distance |
|---|---|---|---|---|
| 1 | -4874.77 | 201 | false | 8.88m |
| 2 | 30831.86 | 224 | false | 5.58m |
| 3 | 33516.52 | 252 | false | 5.66m |
| 4 | 2955.31 | 174 | false | 7.45m |
| 5 | 41599.91 | 195 | false | 1.52m |

**tennis-robot**:

| Episode | Reward | Steps | Success | Final Distance |
|---|---|---|---|---|
| 1 | -16295.51 | 220 | false | 6.57m |
| 2 | -24270.49 | 214 | false | 8.10m |
| 3 | -23308.34 | 163 | false | 7.74m |
| 4 | -23606.55 | 138 | false | 7.77m |
| 5 | -15910.27 | 303 | false | 6.39m |

### 3.4 判定

**PASS_WITH_GAP**

- ✅ 可运行性全部达标
- ✅ 功能覆盖全部达标
- ⚠️ 训练吞吐 93.0%（目标 ≥95%）
- ⚠️ 平均距离 125.8%（目标 ≤105%）
- ⚠️ 奖励尺度不一致

## 4. 差距分析

### 4.1 奖励差距

tennis-robot 平均 reward 为负值 (-20678)，dynamic-tennis 为正值 (20805)。

原因：
1. `distance_incentive` 权重不同，dynamic-tennis 接近目标时正奖励更大
2. 网球初始速度范围可能不完全一致
3. 修复前网球不触发出界，修复后行为已对齐

### 4.2 距离差距

tennis-robot 平均最终距离 7.32m vs dynamic-tennis 5.82m。

原因：
1. 5000 步训练不足以收敛（两个项目都是 0% 成功率）
2. 奖励函数需要调优
3. 网球初始位置和速度分布可能不完全一致

### 4.3 吞吐差距

tennis-robot 18.5 steps/sec vs dynamic-tennis 19.9 steps/sec。

原因：
1. 临时目录拷贝增加 I/O 开销
2. 两者使用相同的 MuJoCo 模型和 frame_skip

## 5. 优化 backlog

| 优先级 | 优化项 | 归因 skill | 状态 |
|---|---|---|---|
| P0 | 奖励函数调优 | gymnasium-mujoco-env-builder | 待实施 |
| P0 | 网球初始状态对齐 | gymnasium-mujoco-env-builder | 待实施 |
| P1 | 中文路径性能优化 | mujoco-tennis-world-builder | 待实施 |
| P1 | 长训练验证 (15000 steps) | sb3-rl-training-runner | 待实施 |
| P2 | 感知闭环测试 | sim-camera-perception-input | 待实施 |

## 6. 自举 skills/plugins 清单

### 使用的 skills (7个)

| Skill | 用途 |
|---|---|
| mujoco-tennis-world-builder | 生成 MuJoCo 网球世界 XML |
| gymnasium-mujoco-env-builder | 生成 Gymnasium 导航环境 |
| sb3-rl-training-runner | 生成 SB3 训练入口 |
| mujoco-policy-evaluator | 生成评估脚本 |
| robot-trajectory-web-visualizer | 生成 Web 可视化 |
| truth-state-policy-input | 生成真值状态观测 |
| sim-camera-perception-input | 生成仿真相机模块 |

### 使用的 plugins (1个)

| Plugin | 用途 |
|---|---|
| ball-project-distiller | 从 dynamic-tennis 抽取能力 |

## 7. 已知限制

1. MuJoCo 中文路径需临时目录拷贝，影响训练吞吐
2. 5000 步训练不足以收敛，需要 15000+ 步验证
3. 奖励函数尺度与 dynamic-tennis 不一致，需要调优
4. 仿真相机感知模块尚未进行端到端验证
