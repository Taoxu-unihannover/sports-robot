# Ball Project Assimilator Development Guide

## 工作流

1. **技术栈拆解**：使用 `scan_project.py` 扫描项目，输出 stack_map 和 skill_gap
2. **项目复现**：根据 reproduction_plan 通过 skills 生成复现项目
3. **横向评测**：使用 `run_stack_benchmark.py` 对比方法性能
4. **最优组合**：使用 `compose_best_stack.py` 组合最优方法

## 文件命名规范

- 技术栈图谱：`{project_name}-stack-map.md` / `.json`
- 缺口报告：`{project_name}-skill-gap.md` / `.json`
- 评测报告：`{project_name}-stack-benchmark-report.md`
- 超越报告：`{project_name}-plus-performance-report.md`

## 退出条件

- 成功：复现版 ≥ baseline 95%，增强版 > baseline 5%
- 带差距：复现版达标但增强版未超越
- 失败：连续 3 轮同因失败或 5 轮迭代仍低于 95%
