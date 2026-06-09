# Generic Ball Project Assimilation Recipe

## 概述

通用球类机器人开源项目吸收与超越流程。

## 前置条件

- 开源项目 A 已克隆到本地
- sports-robot 环境已安装
- Python >= 3.10

## 步骤

### 阶段 1：技术栈拆解

1. 扫描项目结构
   ```bash
   python plugins/ball-project-assimilator/scripts/scan_project.py \
     --project_path <project_path> \
     --domain <domain> \
     --output_dir docs/assimilation
   ```

2. 审查技术栈图谱和 skill 缺口报告

3. 对未覆盖模块，创建新 skill 候选

### 阶段 2：项目复现

1. 根据复现计划，通过 sports-robot skills 生成复现项目
2. 运行可运行性验证
3. 运行性能复现
4. 输出复现报告

### 阶段 3：横向评测

1. 为每个技术栈建立统一 benchmark
2. 将项目 A 方法和 sports-robot 方法接入同一 schema
3. 使用相同数据/种子/配置运行评测
4. 输出方法排名

### 阶段 4：最优组合

1. 组合各技术栈最优方法
2. 检查组合兼容性
3. 生成增强项目
4. 运行整体评测
5. 输出超越报告

## 验证

- 技术栈覆盖率 100%
- 复现版可运行性 100%
- 复现版核心性能 ≥ baseline 95%
- 增强版核心指标 > baseline 5%
