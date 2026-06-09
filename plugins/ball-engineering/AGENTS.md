# Ball Engineering — 球类工程开发 Team

> 工程层开发环境。含 8 个专业 Skill、3 个 Agent、实时/电源/HIL/发布验证 pipeline，以及 MuJoCo/Gymnasium/SB3 项目工程化能力。

## 架构概览

```
ball-engineering/
├── plugin.json
├── AGENTS.md
├── quickstart.md
├── init.sh
├── assets/config.yaml
├── agents/
│   ├── engineering-architect.md
│   ├── engineering-developer.md
│   └── engineering-reviewer.md
├── scripts/pipeline.py
├── tests/regression.py
├── references/papers.md
├── examples/engineering_validation.md
└── workflows/
```

## 八模块 Skills

| Skill | 职责 | 输入 | 输出 |
|-------|------|------|------|
| `realtime-system-integration` | 实时预算和 watchdog | 延迟配置 | 总延迟、超时状态 |
| `ros2-rtos-middleware` | 生命周期与 QoS | 节点配置 | lifecycle/QoS |
| `power-electronics-bms` | 电源与 BMS | 电压、电流、容量 | 功率、SOC、欠压 |
| `hil-verification` | HIL/日志回放验证 | 日志指标 | RMSE、延迟统计 |
| `maintenance-release` | 维护发布 | 版本、标定配置 | checksum、兼容性 |
| `mujoco-tennis-world-builder` | MuJoCo 网球世界生成 | 球场/机器人配置 | MJCF XML + 资产 |
| `gymnasium-mujoco-env-builder` | Gymnasium 环境封装 | MuJoCo 模型 + 任务配置 | 标准 Env 类 |
| `robot-trajectory-web-visualizer` | Web 轨迹可视化 | episode 数据 | HTML + JSON |

## MuJoCo/Gymnasium/SB3 工程化能力

### 项目结构标准

球类机器人仿真项目应遵循以下结构：

```
project/
  pyproject.toml
  configs/
    env.yaml
    train_sac.yaml
  assets/
    mujoco/
      tennis_world/
        scene.xml
        robots/
        meshes/
  project_name/
    envs/
      registration.py
      navigation_env.py
    training/
      train.py
    evaluation/
      evaluate.py
    visualization/
      export_episode.py
      web/
    perception/
      vision.py
    control/
      mecanum_controller.py
  scripts/
    train
    evaluate
    smoke_test
  tests/
```

### MuJoCo XML 路径兼容

MuJoCo 不支持中文路径，需使用以下策略：

1. 检测 XML 文件路径是否包含非 ASCII 字符
2. 若包含，将整个资产目录拷贝到 `tempfile.mkdtemp()` 生成的临时目录
3. 使用临时目录中的 XML 路径加载模型
4. 环境关闭时清理临时目录

### Gymnasium 环境注册

```python
from gymnasium.envs.registration import register

register(
    id="ProjectNavigation-v1",
    entry_point="project_name.envs.navigation_env:NavigationEnv",
    max_episode_steps=2000,
)
```

### SB3 训练入口标准

- 支持 SAC/PPO/DDPG/TD3 算法选择
- 使用 `make_vec_env` 创建并行环境
- 支持 TensorBoard callback
- 模型保存到 `saved_models/` 目录
- 日志保存到 `logs/` 目录

## 三 Agent 分工

### Engineering Architect

- 职责：系统拓扑、实时预算、中间件、电源、验证与发布策略、MuJoCo/Gymnasium 项目架构。
- 输出：`DESIGN.md` + `PLAN.md`。

### Engineering Developer

- 职责：实现配置校验、HIL、日志回放、发布辅助工具和测试、MuJoCo 环境和训练脚本。
- 输出：工程 pipeline、配置、测试报告。

### Engineering Reviewer

- 职责：审查上线条件、日志覆盖、回滚路径和现场运维风险、环境 check_env 验证。
- 输出：`REVIEW.md`、发布检查清单。

## 工作流

```
Step 1: Architect 冻结系统拓扑和上线标准
Step 2: Developer 实现实时/电源/HIL/发布校验
Step 3: Developer 运行工程回归测试
Step 4: Reviewer 审查发布与回滚风险
```
