# tennis-robot 能力沉淀与自举计划

> 创建日期：2026-06-09  
> 范围：以 `dynamic-tennis` 为样本项目，沉淀 sports-robot 的标准 skills / plugins，并验证 sports-robot 能否在不直接复制 `dynamic-tennis` 源码的前提下自举生成新的 `tennis-robot` 项目。  
> 核心约束：`tennis-robot` 的搭建过程只能调用 sports-robot 已沉淀的 plugins / skills / recipes / scripts / templates；当 sports-robot 能力不足时，只能把缺失能力从 `dynamic-tennis` 的技术栈抽象成通用 skill 或 plugin，再重新自举。

## 一、目标与验收标准

### 1.1 总目标

把 `dynamic-tennis` 中已经验证过的网球机器人仿真、感知、控制、训练、评估与可视化能力，沉淀为 sports-robot 可复用的标准 skills / plugins，使 sports-robot 能够逐步自动搭建类似功能的新球类机器人项目。

最终产物包括：

- `skills/` 下新增或升级的一组标准 skills，覆盖 MuJoCo 仿真环境、Gymnasium 环境封装、强化学习训练、仿真图像感知、导航/击球控制、评估与 Web 可视化。
- `plugins/` 下新增或升级的 plugin，负责“从已有球类机器人项目抽取技术栈、转化为 skills、再用 skills 自举新项目”的闭环流程。
- 新目录 `tennis-robot/`，由 sports-robot 自身能力搭建，包含可运行的网球机器人仿真训练/测试/可视化项目骨架。
- 对比报告，证明 `tennis-robot` 的功能覆盖与关键性能不弱于 `dynamic-tennis` 的基线，或明确差距、补齐路径与下一轮沉淀项。

### 1.2 硬性验收标准

| 类别 | 验收标准 |
|---|---|
| 技术栈沉淀 | `dynamic-tennis` 的核心技术栈被拆成标准 `SKILL.md` + `scripts/` + `references/` + `recipes/`，每个 skill 有清晰触发描述、输入输出、执行步骤、验证方式 |
| 自举约束 | `tennis-robot` 生成过程不得直接复制 `dynamic-tennis` 的业务源码；只能使用 sports-robot 的 skills/plugins 生成代码、配置、模板和测试 |
| 功能覆盖 | 支持 MuJoCo 场景、网球/目标动态、机器人真值状态控制、仿真相机图像输入、强化学习训练、模型测试、轨迹输出、Web/图像可视化 |
| 算法覆盖 | 至少支持 SAC，预留 PPO/DDPG/TD3；使用 Gymnasium 接口和 Stable-Baselines3 训练入口 |
| 性能不退化 | 在同等训练步数、随机种子和任务难度下，成功率、平均回合奖励、到达误差、推理延迟、训练吞吐不低于 `dynamic-tennis` 基线的 95%；若原基线不可复现，则先固化可复现基线 |
| 可验证性 | 每个新 skill/plugin 至少有 smoke test；核心训练环境有 `check_env`、短步数训练、模型加载测试、轨迹可视化测试 |
| 可复用性 | 新 plugin 能处理“其他球类机器人项目”作为输入，并输出能力差距清单、skill 候选、recipe 候选和项目自举计划 |

### 1.3 `tennis-robot` 性能门槛

`tennis-robot` 必须先通过可运行性门槛，再进入性能对齐门槛。若 `dynamic-tennis` 的长训练结果无法完全复现，则先冻结短步数 baseline；baseline 一旦冻结，后续循环不得随意降低标准。

| 指标 | 最低通过线 | 目标通过线 | 说明 |
|---|---:|---:|---|
| MuJoCo 场景加载 | 100% | 100% | 所有 XML/mesh 路径可加载，无缺失资产 |
| Gymnasium 环境检查 | 100% | 100% | 通过 `stable_baselines3.common.env_checker.check_env` |
| 短训练可运行性 | 1000 steps 无崩溃 | 5000 steps 无崩溃 | SAC 至少完成一次保存与加载 |
| 评估成功率 | 不低于 baseline 95% | 不低于 baseline 100% | baseline 来自 `dynamic-tennis` 同任务同配置 |
| 平均 episode reward | 不低于 baseline 95% | 不低于 baseline 100% | 使用相同随机种子集合 |
| 最终目标距离/轨迹误差 | 不高于 baseline 105% | 不高于 baseline 100% | 误差类指标越低越好 |
| 推理延迟 | 不高于 baseline 105% | 不高于 baseline 100% | 包含观测构造与策略推理 |
| 训练吞吐 | 不低于 baseline 95% | 不低于 baseline 100% | steps/sec，同硬件同并行数 |
| 图像感知状态误差 | 不高于真值输入误差的 120% | 不高于 110% | 用 MuJoCo 渲染图像模拟真实感知链路 |
| Web/轨迹可视化导出 | 100% | 100% | 每次评估能输出 episode JSON 与 HTML/图像结果 |

性能判定采用分级结果：

- `PASS`：所有最低通过线达标，且无阻塞缺陷。
- `PASS_WITH_GAP`：可运行性达标，但存在未达到目标通过线的指标；允许进入下一阶段，但必须生成优化任务。
- `FAIL_NEEDS_SKILL_REDESIGN`：任一最低通过线未达标，必须回到 skills/plugins 设计阶段，不能继续堆项目代码。
- `FAIL_BASELINE_INVALID`：baseline 无法复现或指标不可比较，必须先修复 baseline 冻结流程。

## 二、`dynamic-tennis` 技术栈标准 skills 拆解

### 2.1 已识别技术栈

从 `dynamic-tennis` 当前结构可归纳出以下技术栈：

- 语言与环境：Python 3.10、conda、pip、YAML 配置。
- 仿真：MuJoCo 3.4、Gymnasium `MujocoEnv` / 自定义 `Env`、MJCF XML、URDF/Xacro/mesh 资产。
- 强化学习：Stable-Baselines3、SAC/PPO/DDPG/TD3、PyTorch、SubprocVecEnv、TensorBoard callback、模型 checkpoint。
- 机器人平台：麦克纳姆移动底盘、WAM/Barrett 机械臂、网球拍/球网/目标/障碍物、轮式导航与击球/到达任务。
- 控制输入：真值状态输入，包括球位置/速度、机器人位置/速度、目标点、距离、碰撞/成功信号。
- 感知输入：MuJoCo 渲染图像、相机截图、图像处理/视觉估计，用仿真相机模拟真实感知链路。
- 任务环境：`MecanumNavigatorEnv`、`WTRBlockReacherEnv`、`WTRArmReacherEnv`、`WTR3DReacherEnv`、`WTRStrokeEnv`。
- 训练与评估：训练脚本、测试脚本、继续训练、GPU/CPU 环境、超参数脚本、episode 轨迹记录。
- 可视化：Matplotlib 轨迹图、MuJoCo GUI、HTML/JavaScript Web 可视化、JSON episode 数据、本地 HTTP server。
- 工程能力：GPU 训练优化、显存参数、并行环境、配置文件、模型目录、运行日志。

### 2.2 标准 skill 设计清单

| Skill 名称 | 来源能力 | 归属层 | 主要职责 | 关键资源 |
|---|---|---|---|---|
| `mujoco-tennis-world-builder` | MJCF/mesh/球场/球网/球拍/机器人资产 | engineering/modeling | 生成可加载的 MuJoCo 网球机器人世界，管理资产路径、碰撞体、相机、传感器、目标体 | `SKILL.md`、MJCF 模板、资产规范、加载测试 |
| `gymnasium-mujoco-env-builder` | 自定义 Gymnasium/MuJoCo 环境 | engineering/control | 生成标准 `reset/step/render/observation_space/action_space` 环境，支持 `check_env` | 环境模板、观测/动作 schema、smoke test |
| `mecanum-mobile-base-sim` | 麦克纳姆底盘导航 | execution/control | 建模麦克纳姆底盘动作接口、速度限制、目标导航、奖励项 | 运动学脚本、奖励参考、配置模板 |
| `tennis-ball-dynamics-sim` | 动态网球与轨迹 | modeling | 生成球的初始状态、速度、反弹、目标区域、噪声与域随机化 | 球动力学脚本、轨迹评估 |
| `truth-state-policy-input` | 真值状态训练 | control | 将仿真真值转换为策略观测向量，定义归一化、延迟、噪声、缺失值处理 | observation schema、normalizer、测试 |
| `sim-camera-perception-input` | MuJoCo 图像模拟真实感知 | perception/engineering | 从 MuJoCo camera/render buffer 采集图像，接入 ball-detector/tracker/state-estimator | 渲染脚本、图像管线 adapter |
| `sb3-rl-training-runner` | SB3 训练入口 | control/engineering | 统一 SAC/PPO/DDPG/TD3 训练、并行环境、checkpoint、TensorBoard、继续训练 | 训练脚本模板、超参 recipe |
| `tennis-navigation-task` | 网球导航任务 | control | 定义移动机器人追球/到达击球点任务、奖励函数、终止条件、成功判据 | task config、reward tests |
| `tennis-strike-task` | 击球/到达任务 | control/execution | 定义机械臂/拍面目标、击球时刻、末端约束、成功判据 | target pose schema、IK/RL 接口 |
| `mujoco-policy-evaluator` | 测试脚本与指标 | engineering | 加载模型并输出成功率、误差、奖励、轨迹、延迟、视频/截图 | evaluator、metrics schema |
| `robot-trajectory-web-visualizer` | HTML/JSON 可视化 | engineering | 输出 episode JSON、HTML 播放器、本地 server、轨迹图 | Web 模板、JSON schema |
| `sim-to-real-robustness-benchmark` | GPU/域随机/延迟/噪声 | engineering/control | 对比真值输入与图像感知输入，在扰动下评估性能 | benchmark recipe、报告模板 |

### 2.3 标准 skill 格式要求

每个 skill 必须采用 sports-robot 统一格式，并逐步修正当前部分 skill frontmatter 过宽的问题：

- `SKILL.md` frontmatter 只保留 `name` 和 `description`，触发条件写入 `description`。
- 正文包含：用途、输入、输出、执行步骤、失败处理、验证方式、可选 recipes。
- 可执行代码放入 `scripts/`，详细资料放入 `references/`，可复用模板放入 `assets/` 或 `recipes/`。
- 每个 skill 至少有一个 `tests/` smoke test。
- 若 skill 来自 `dynamic-tennis`，必须抽象成“球类机器人通用能力”，避免保留仅对原项目路径生效的硬编码。

## 三、用 sports-robot 自举 `tennis-robot` 的循环

### 3.1 自举原则

`tennis-robot` 的目标不是复制 `dynamic-tennis`，而是验证 sports-robot 的能力是否足够成熟。执行时采用以下循环：

1. 只使用 sports-robot 当前已有 skills/plugins 规划并生成 `tennis-robot`。
2. 运行最小验证：导入、环境加载、`check_env`、短步数训练、模型测试、可视化输出。
3. 若失败，记录失败点：缺少哪类 skill、schema、脚本、模板或 recipe。
4. 回到 `dynamic-tennis`，只抽取“技术栈模式”和“工程经验”，沉淀成新的通用 skill/plugin。
5. 重新从 sports-robot skills/plugins 生成或修正 `tennis-robot`。
6. 重复直到功能覆盖和性能达到验收标准。

### 3.1.1 闭环控制机制

每一轮自举必须执行同一套闭环，不允许跳过“性能判定 -> 能力归因 -> skill 重设计”步骤：

```text
冻结/读取 baseline
  -> 选择 sports-robot skills/plugins
  -> 生成或更新 tennis-robot
  -> 运行 smoke tests
  -> 运行短训练与评估
  -> 与 baseline 对比
  -> 输出 PASS / PASS_WITH_GAP / FAIL_NEEDS_SKILL_REDESIGN / FAIL_BASELINE_INVALID
  -> 若失败，更新 skills/plugins/recipes
  -> 下一轮自举
```

失败归因必须落到 skill 或 plugin 层，而不是只修改 `tennis-robot` 项目代码：

| 失败类型 | 归因目标 | 下一步 |
|---|---|---|
| 环境无法加载 | `mujoco-tennis-world-builder` / `gymnasium-mujoco-env-builder` | 重设计资产路径、XML 模板、环境初始化 skill |
| 训练脚本崩溃 | `sb3-rl-training-runner` | 重设计训练配置、callback、模型保存加载接口 |
| reward 无法收敛 | `tennis-navigation-task` / `tennis-strike-task` / `truth-state-policy-input` | 重设计任务、观测、奖励、终止条件 |
| 感知闭环误差过大 | `sim-camera-perception-input` / `ball-perception` | 重设计相机、渲染、检测、状态估计 adapter |
| 评估不可比较 | `mujoco-policy-evaluator` / `sim-to-real-robustness-benchmark` | 重设计指标、随机种子、baseline 固化流程 |
| 可视化缺失 | `robot-trajectory-web-visualizer` | 重设计 episode schema 与导出器 |

### 3.1.2 循环退出机制

循环必须有明确退出条件，避免无限迭代。

成功退出：

- `PASS`：所有最低通过线达标，且核心性能达到 baseline 95% 以上；生成最终验收报告后退出。
- `PASS_WITH_GAP`：所有最低通过线达标，但部分目标通过线未达成；允许退出当前建设阶段，但必须把差距登记为优化 backlog。

失败退出：

- 连续 3 轮都卡在同一能力缺口，退出循环，输出 blocker 报告，说明需要人工决策或外部资源。
- 总循环次数达到 5 轮仍未达到最低通过线，退出循环，冻结当前成果并重审整体架构。
- baseline 无法复现且无法在 2 轮内建立替代 baseline，退出循环，先处理基线问题。
- 需要下载大模型、外部数据集、专有 mesh、GPU 长训练或真实硬件验证时，退出自动循环，转为人工批准任务。

每轮退出时必须写入：

- 本轮使用的 skills/plugins 版本。
- 本轮生成或修改的文件清单。
- 测试命令与指标结果。
- 与 baseline 的差距。
- 下一轮需要重设计的 skill/plugin。
- 是否满足成功退出、失败退出或继续循环条件。

### 3.2 `tennis-robot/` 目标目录结构

建议由 sports-robot plugin 生成以下结构：

```text
tennis-robot/
  README.md
  pyproject.toml
  configs/
    env.yaml
    train_sac.yaml
    task_navigation.yaml
    task_perception.yaml
  assets/
    mujoco/
      tennis_world.xml
      robots/
      meshes/
  tennis_robot/
    envs/
      tennis_navigation_env.py
      tennis_perception_env.py
    perception/
      mujoco_camera_adapter.py
      vision_state_adapter.py
    control/
      observation_builder.py
      reward.py
      safety.py
    training/
      train_sb3.py
      callbacks.py
    evaluation/
      evaluate_policy.py
      metrics.py
    visualization/
      export_episode.py
      web/
  tests/
    test_mujoco_load.py
    test_gym_env.py
    test_short_training.py
    test_visualization_export.py
  runs/
  saved_models/
  web_viz_data/
```

### 3.3 自举阶段计划

#### 阶段 A：基线冻结

- 运行 `dynamic-tennis` 的现有测试/评估入口，记录可复现命令。
- 固化至少 3 个基线指标：成功率、平均 episode reward、目标距离/轨迹误差。
- 记录环境依赖：CPU/GPU 两套 conda 配置、MuJoCo 版本、SB3 版本、PyTorch 版本。
- 输出 `docs/todo/dynamic-tennis-baseline.md`。

完成标准：

- 有明确的 baseline 命令、配置、模型路径、指标输出。
- 如果无法复现原训练性能，至少完成短步数 smoke baseline，并标记不可复现项。

#### 阶段 B：第一次自举

- 使用现有 `ball-perception`、`ball-modeling`、`ball-control`、`ball-execution`、`ball-engineering` 和已有 skills 生成 `tennis-robot` 的最小骨架。
- 不读取或复制 `dynamic-tennis/scripts/*.py` 的实现细节，只根据已沉淀 skill 的说明生成。
- 生成最小 MuJoCo 场景、Gymnasium 环境、SB3 SAC 训练入口、评估入口。
- 运行 smoke tests。

预期缺口：

- MuJoCo 项目生成 skill 不完整。
- Gymnasium/SB3 训练 runner 不足。
- 仿真相机到感知输入的 adapter 不足。
- 任务 reward、观测归一化、终止条件缺少标准 schema。

#### 阶段 C：缺口沉淀

针对 B 阶段失败点，从 `dynamic-tennis` 抽象以下能力：

- MuJoCo XML/mesh 资产组织规范。
- Gymnasium 环境注册、`check_env`、并行环境创建。
- SAC/PPO/DDPG/TD3 训练参数模板。
- 训练 callback、checkpoint、TensorBoard、继续训练。
- MuJoCo 截图、无头渲染、GUI 渲染、Web 可视化。
- 真值状态观测与图像感知观测的双输入接口。

每沉淀一个 skill，需要同步补：

- `SKILL.md`
- `scripts/`
- `references/`
- `recipes/`
- `tests/`
- 在相关 plugin 的 `plugin.json` / `AGENTS.md` / `quickstart.md` 中注册或说明

#### 阶段 D：第二次自举

- 清理或隔离第一次失败产物。
- 重新只使用 sports-robot 新增 skills/plugins 生成 `tennis-robot`。
- 跑通以下命令级验收：
  - `python -m pytest tests -q`
  - `python tennis_robot/training/train_sb3.py --config configs/train_sac.yaml --total-timesteps 1000`
  - `python tennis_robot/evaluation/evaluate_policy.py --episodes 3 --export-web`
  - 打开或生成 `web_viz_data/*.json` 和 Web 可视化 HTML。

#### 阶段 E：性能对齐

- 使用相同训练步数、相同随机种子、相同任务难度运行 `dynamic-tennis` 和 `tennis-robot`。
- 输出对比表：
  - 训练吞吐：steps/sec
  - 平均 reward
  - 成功率
  - 最终目标距离
  - 轨迹长度/平滑度
  - 推理延迟
  - 图像感知输入下的状态估计误差
- 若任一核心指标低于 baseline 95%，进入下一轮能力沉淀。

## 四、项目沉淀/借鉴/融合 plugin 设计

### 4.1 新 plugin：`ball-project-distiller`

目标：把任意球类机器人项目转化为 sports-robot 的可复用 skills/plugins，并能驱动自举项目。

职责：

- 扫描输入项目，生成技术栈清单。
- 识别项目模块：仿真、感知、建模、控制、执行、训练、评估、可视化、部署。
- 匹配 sports-robot 已有 skills，输出覆盖率矩阵。
- 对缺失能力生成 skill 候选。
- 把已验证流程转为 recipes。
- 生成自举任务计划和验证基准。

建议结构：

```text
plugins/ball-project-distiller/
  plugin.json
  AGENTS.md
  quickstart.md
  assets/
    distill_config.yaml
  agents/
    distiller-architect.md
    distiller-developer.md
    distiller-reviewer.md
  scripts/
    scan_project.py
    map_to_skills.py
    generate_skill_plan.py
    compare_project_baseline.py
  workflows/
    development-guide.md
    task-prompts.md
    templates/
      distillation-report-template.md
      skill-gap-template.md
      bootstrap-plan-template.md
  recipes/
    tennis-project-distillation/
      RECIPE.md
  tests/
    test_project_scan.py
    test_skill_mapping.py
```

### 4.2 配套新 skill：`project-to-skill-distillation`

目标：给 agent 一套稳定流程，把项目能力沉淀成标准 skill。

输入：

- 源项目路径
- 目标球类机器人类型
- 禁止直接复制的文件范围
- 允许抽象参考的文件范围
- 目标 sports-robot skill/plugin 路径

输出：

- 技术栈清单
- 能力图谱
- skill gap 列表
- 新 skill 草案
- recipe 草案
- smoke test 草案

核心规则：

- 先抽象接口和行为，再生成通用实现。
- 不把源项目路径、实验机用户名、模型文件绝对路径写入新 skill。
- 对算法实现保留可解释伪代码、schema、测试，不直接复制业务代码。
- 对资产文件区分：通用模板可生成，专有 mesh/model 只登记依赖或生成占位资产。

### 4.3 自举控制 skill：`sports-robot-bootstrap-loop`

目标：让 sports-robot 自己执行“生成项目 -> 运行测试 -> 发现缺口 -> 沉淀 skill -> 再生成”的闭环。

流程：

1. 读取目标项目需求。
2. 匹配现有 sports-robot skills/plugins。
3. 生成项目结构和最小实现。
4. 执行验证命令。
5. 将失败按能力类型归因。
6. 生成 skill/plugin 更新任务。
7. 完成更新后重新执行。
8. 输出最终验收报告。

需要注意：

- 每轮必须保存 `bootstrap-run-{n}.md`，记录输入、使用 skills、失败点、补齐项、下一轮命令。
- 每轮生成物必须可 diff，避免难以追溯。
- 任何性能对齐都必须使用相同指标和配置，不能只凭主观功能相似判断。

## 五、详细任务拆分

### 5.1 第一批新增/升级 skills

- [x] 新增 `mujoco-tennis-world-builder` — SKILL.md + world_builder.py + tests + recipe
- [x] 新增 `gymnasium-mujoco-env-builder` — SKILL.md + tennis_navigation_env.py + recipe
- [x] 新增 `sb3-rl-training-runner` — SKILL.md + recipe
- [x] 新增 `mujoco-policy-evaluator` — SKILL.md + recipe
- [x] 新增 `robot-trajectory-web-visualizer` — SKILL.md + recipe
- [x] 新增 `truth-state-policy-input` — SKILL.md + recipe
- [x] 新增 `sim-camera-perception-input` — SKILL.md + recipe
- [x] 升级 `skill-policy-controller`，补足 SB3/MuJoCo/Gymnasium 场景，并修正 frontmatter 为标准格式
- [x] 升级 `mobile-base-executor`，补足麦克纳姆底盘动作/速度接口
- [x] 升级 `whole-body-executor`，补足网球拍/机械臂击球任务接口

### 5.2 第一批新增/升级 plugins

- [x] 新增 `ball-project-distiller` — PLUGIN.md + distill.py
- [x] 升级 `ball-engineering`，纳入 MuJoCo/Gymnasium/SB3 项目工程化能力
- [x] 升级 `ball-control`，纳入 RL 训练 runner、真值状态策略输入、图像感知策略输入
- [x] 升级 `ball-perception`，纳入 MuJoCo render/camera adapter 与仿真图像测试 recipe
- [x] 升级 `ball-modeling`，纳入网球动力学、反弹、目标区域、域随机化 recipe
- [x] 升级 marketplace 或 plugin 注册信息，使新 plugin 能被发现

### 5.3 `tennis-robot` 自举任务

- [x] 生成项目骨架
- [x] 生成 MuJoCo 网球世界
- [x] 生成 Gymnasium 环境
- [x] 生成真值状态训练环境
- [x] 生成仿真图像感知环境
- [x] 生成 SB3 SAC 训练入口
- [x] 生成模型评估入口
- [x] 生成 Web 可视化导出
- [x] 生成 smoke tests
- [x] 运行短步数训练并保存 checkpoint
- [x] 运行 3 episodes 评估并输出 metrics
- [x] 与 `dynamic-tennis` baseline 对比

### 5.4 文档与报告

- [x] `docs/todo/dynamic-tennis-baseline.md`
- [x] `docs/todo/dynamic-tennis-skill-map.md`
- [x] `docs/todo/tennis-robot-bootstrap-run-1.md`
- [x] `docs/todo/tennis-robot-bootstrap-run-2.md`
- [x] `docs/todo/tennis-robot-performance-comparison.md`
- [x] `docs/tech-report/004-仿真强化学习层.md`
- [x] `docs/tech-report/005-项目能力沉淀闭环.md`

## 六、执行顺序建议

1. 先冻结 `dynamic-tennis` baseline，否则“性能不能比原先差”无法量化。
2. 再把 MuJoCo/Gymnasium/SB3 三个基础能力沉淀为 skills，这是自举 `tennis-robot` 的最短路径。
3. 然后做 `tennis-robot` 第一次自举，不追求完美，只追求能暴露能力缺口。
4. 根据缺口补充感知输入、可视化、评估与域随机化。
5. 最后实现 `ball-project-distiller`，把这次经验固化成可用于其他球类机器人项目的通用 plugin。

## 七、风险与控制

| 风险 | 影响 | 控制措施 |
|---|---|---|
| `dynamic-tennis` 原始性能不可复现 | 无法证明不退化 | 先建立短步数可复现 baseline，再逐步恢复长训练 |
| 直接复制源码导致自举验证失真 | 无法考察 sports-robot 能力 | 明确禁止复制业务源码，仅抽象技术栈和接口 |
| MuJoCo 资产路径复杂 | 环境加载失败 | 建立资产清单与路径校验脚本 |
| GPU/PyTorch 版本不稳定 | 训练无法启动 | CPU smoke test 与 GPU recipe 分离 |
| 图像感知闭环太晚接入 | 只验证真值控制 | 从第一版就预留 `truth_state` / `rendered_image` 双观测模式 |
| skill 粒度过大 | 难以复用到其他球类项目 | 按仿真、观测、训练、评估、可视化拆分 |

## 八、下一步立即行动

建议下一次执行从以下三个文件开始：

1. `docs/todo/dynamic-tennis-baseline.md`：冻结 `dynamic-tennis` 可复现基线。
2. `skills/gymnasium-mujoco-env-builder/SKILL.md`：沉淀 Gymnasium + MuJoCo 环境构建标准。
3. `skills/sb3-rl-training-runner/SKILL.md`：沉淀 Stable-Baselines3 训练/评估 runner。

这三项完成后，即可开始 `tennis-robot` 的第一轮自举。
