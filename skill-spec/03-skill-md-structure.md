# 第 3 章 SKILL.md 的标准结构

## 本章解决什么问题

`SKILL.md` 是 Skill 的核心契约。本章拆解 frontmatter 和正文如何写，避免写成散文、百科或临时 prompt。

## 核心概念

一个生产级 `SKILL.md` 应包含：

- `name`：全局唯一，建议 kebab-case。
- `description`：给路由器看的触发说明。
- `when_to_use`：更明确的使用场景。
- `allowed-tools`：工具白名单。
- `input_schema` / `output_schema`：可测试契约。
- 正文五段式：何时使用、输入约束、步骤、输出格式、失败处理。

## 工程方法

`description` 先写触发条件，不写背景故事。正文只放核心流程，长规范、示例、脚本放到支持文件。

## 模板：生产级 SKILL.md

```markdown
---
name: action-domain-output
description: 在用户需要完成某类明确任务并产出某种结果时使用。不要用于泛泛咨询。
when_to_use: 用户提到相关任务、对象、交付物或风险评估时触发。
version: 1.0.0
allowed-tools:
  - readonly.search
input_schema:
  type: object
  required: [target]
  properties:
    target: { type: string }
output_schema:
  type: object
  required: [summary, actions, risks]
---

# Skill Name

## 何时使用

## 输入约束

## 执行步骤

## 输出格式

## 失败处理
```

## 反例

`description: 这是一个很强大的代码助手 Skill。`  
问题：没有触发条件、对象、交付物和边界，路由器无法稳定判断何时加载。

## 练习

把一个普通 prompt 改写成标准 `SKILL.md`。要求包含 `allowed-tools`、`input_schema` 和 `output_schema`。

## 检查清单

- [ ] name 使用 kebab-case
- [ ] description 明确触发条件
- [ ] 正文有失败处理
- [ ] 输入输出可验证
- [ ] 工具权限最小化
