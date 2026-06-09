# Ball Project Assimilator — 球类项目吸收与超越 Team

> 项目吸收与超越开发环境。含 3 个核心 Skill、3 个 Agent、从技术栈拆解到最优组合的完整 pipeline。

## 架构概览

```
ball-project-assimilator/
├── plugin.json
├── AGENTS.md
├── quickstart.md
├── assets/
│   ├── assimilator_config.yaml
│   ├── stack_map.schema.yaml
│   ├── skill_gap.schema.yaml
│   ├── benchmark.schema.yaml
│   ├── best_stack.schema.yaml
│   └── performance_report.schema.yaml
├── agents/
│   ├── assimilation-architect.md
│   ├── assimilation-developer.md
│   └── assimilation-reviewer.md
├── scripts/
│   ├── scan_project.py
│   ├── build_stack_map.py
│   ├── match_existing_skills.py
│   ├── run_stack_benchmark.py
│   ├── compose_best_stack.py
│   └── render_reports.py
├── workflows/
│   ├── development-guide.md
│   ├── task-prompts.md
│   └── templates/
├── recipes/
│   ├── generic-ball-project-assimilation/
│   └── dynamic-tennis-assimilation/
└── tests/
```

## 三核心 Skills

| Skill | 职责 | 输入 | 输出 |
|-------|------|------|------|
| `open-project-skill-distiller` | 拆解项目技术栈、匹配 skills、输出缺口报告 | 项目路径 | stack_map + skill_gap + reproduction_plan |
| `stack-method-benchmark` | 横向比较同类技术栈方法性能 | stack_map + candidates | benchmark_report + ranking + best_method |
| `best-stack-composer` | 组合最优方法、检查兼容性、验证超越 | best_method + baseline | best_stack.yaml + plus_report |

## 四阶段工作流

```text
阶段 1: 技术栈拆解
  open-project-skill-distiller → stack_map + skill_gap + reproduction_plan

阶段 2: 项目复现
  sports-robot skills → reproduction project → reproduction_report

阶段 3: 横向评测
  stack-method-benchmark → benchmark_report + ranking + best_method

阶段 4: 最优组合
  best-stack-composer → best_stack.yaml + enhanced_project → plus_report
```

## 退出条件

- 成功退出：复现版 ≥ baseline 95%，增强版核心指标 > baseline 5%
- 带差距退出：复现版达标但增强版未超越，输出瓶颈报告
- 失败退出：连续 3 轮同因失败，或 5 轮迭代仍低于 baseline 95%
