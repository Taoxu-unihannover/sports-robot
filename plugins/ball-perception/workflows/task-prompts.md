# Subagent 调用参数详情

本文档是 SportsRobot 调用各阶段 Subagent 的**唯一执行手册**。每个 Step 包含：调用参数、关联 Skill、完成验证、约束提醒。

---

## Step 1：需求分析与方案设计

### Subagent 调用参数

```
{
  "description": "感知方案设计",
  "subagent_type": "ball-perception:perception-architect",
  "prompt": "
请为以下感知场景设计方案：
- 运动类型：{sport_type}
- 相机配置：{camera_setup}
- 精度要求：{accuracy_requirements}
- 实时性要求：{latency_requirements}

【输出】
- 技术设计：perception/{project_name}/docs/DESIGN.md，参考 workflows/templates/design-template.md
- 开发计划：perception/{project_name}/docs/PLAN.md，参考 workflows/templates/plan-template.md

【验收标准】
- DESIGN.md 和 PLAN.md 都已创建
- 设计包含：检测器选型、滤波器模型、三角化方法、相机布局
- 计划包含：模块清单、测试计划、精度目标
  "
}
```

---

## Step 2：设计串讲

### Developer 串讲审查

```
{
  "description": "设计串讲",
  "subagent_type": "ball-perception:perception-developer",
  "prompt": "
请以「设计串讲模式」审查以下感知方案：
- 项目名称：{project_name}
- 技术设计：perception/{project_name}/docs/DESIGN.md
- 开发计划：perception/{project_name}/docs/PLAN.md

【重点审查章节】
- 检测器选型是否匹配运动类型
- 滤波器模型是否匹配运动特性
- 相机布局是否满足精度要求
- 模块间接口是否清晰可行

【输出】
- 请将质疑清单输出到 perception/{project_name}/docs/WALKTHROUGH.md

【验收标准】
- 质疑清单按严重性分级（🔴 阻塞 / 🟡 需讨论 / 🟢 建议）
- 每个质疑包含：问题描述、影响分析、建议方案

【审查重点（5 项）】
| 序号 | 审查维度 | 审查方法 |
|------|---------|---------|
| 1 | 检测器可行性 | 模型是否存在？输入分辨率是否合理？置信度阈值是否合适？ |
| 2 | 跟踪器参数合理性 | 窗口大小是否匹配帧率？max_gap 是否足够？ |
| 3 | 滤波器模型正确性 | CV/CA/EKF 选择是否匹配运动特性？噪声参数是否合理？ |
| 4 | 几何重建可行性 | 相机标定是否完整？基线距离是否足够？ |
| 5 | 实时性可行性 | 各模块延迟是否满足端到端要求？ |
  "
}
```

---

## Step 3：代码实现

### Developer 实现

```
{
  "description": "代码实现",
  "subagent_type": "ball-perception:perception-developer",
  "prompt": "
请根据设计方案实现感知系统代码：
- 项目名称：{project_name}
- 技术设计：perception/{project_name}/docs/DESIGN.md
- 开发计划：perception/{project_name}/docs/PLAN.md

【实现阶段】
1. 检测器实现 → 单元测试
2. 跟踪器实现 → 单元测试
3. 滤波器实现 → 单元测试
4. 几何重建实现 → 单元测试
5. 流水线集成 → 端到端测试

【验收标准】
- 所有模块通过单元测试
- 端到端流水线可运行
- 更新 PLAN.md 进度
  "
}
```

---

## Step 4：代码审查

### Reviewer 审查

```
{
  "description": "代码审查",
  "subagent_type": "ball-perception:perception-reviewer",
  "prompt": "
请审查以下感知系统代码：
- 项目名称：{project_name}
- 代码文件：perception/{project_name}/

【审查维度】
1. 代码规范（命名、类型注解、文档）
2. 算法正确性（与 DESIGN.md 一致性）
3. 精度指标（运行精度测试）
4. 性能指标（测量各模块延迟）
5. 边界条件（遮挡、快速运动、低光照）

【输出】
- perception/{project_name}/docs/REVIEW.md
- perception/{project_name}/docs/accuracy-report.md

【验收标准】
- REVIEW.md 包含分级问题清单
- accuracy-report.md 包含所有精度指标实测值
  "
}
```
