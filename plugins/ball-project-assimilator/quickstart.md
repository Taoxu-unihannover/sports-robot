# Ball Project Assimilator Quickstart

## 快速开始

### 1. 扫描项目

```bash
python plugins/ball-project-assimilator/scripts/scan_project.py \
  --project_path dynamic-tennis \
  --domain tennis \
  --output_dir docs/assimilation
```

### 2. 查看技术栈图谱

```bash
cat docs/assimilation/dynamic-tennis-stack-map.md
```

### 3. 查看 Skill 缺口

```bash
cat docs/assimilation/dynamic-tennis-skill-gap.md
```

### 4. 运行复现

根据 reproduction_plan.md 中的步骤，通过 sports-robot skills 生成复现项目。

### 5. 运行横向评测

```bash
python plugins/ball-project-assimilator/scripts/run_stack_benchmark.py \
  --stack_map docs/assimilation/dynamic-tennis-stack-map.json \
  --output_dir docs/assimilation
```

### 6. 组合最优方法

```bash
python plugins/ball-project-assimilator/scripts/compose_best_stack.py \
  --best_method docs/assimilation/best_method_per_stack.json \
  --baseline docs/assimilation/dynamic-tennis-baseline-metrics.json \
  --output_dir docs/assimilation
```

## 四阶段工作流

| 阶段 | 命令 | 输出 |
|---|---|---|
| 技术栈拆解 | scan_project.py | stack_map + skill_gap |
| 项目复现 | sports-robot skills | reproduction project |
| 横向评测 | run_stack_benchmark.py | benchmark_report |
| 最优组合 | compose_best_stack.py | best_stack + plus_report |
