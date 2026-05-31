# 第 6 章 输入输出契约化

## 本章解决什么问题

没有输入输出契约，Skill 就无法稳定测试，也难以和其他流程组合。本章把 Skill 从自由文本流程升级为可验证接口。

## 核心概念

输入契约回答：需要什么数据、类型、权限和前置状态。  
输出契约回答：交付物结构、字段、格式、机器可检查标记。

## 工程方法

优先使用 JSON Schema、Pydantic 或 zod 描述参数和产物。即使最终输出给人看，也应保留结构化核心。

## 模板：输入输出 Schema

```yaml
input_schema:
  type: object
  required: [repo, pr_number]
  properties:
    repo:
      type: string
      description: owner/repo
    pr_number:
      type: integer
output_schema:
  type: object
  required: [summary, risks, test_gaps]
  properties:
    summary:
      type: string
    risks:
      type: array
      items:
        type: object
        required: [severity, file, reason]
    test_gaps:
      type: array
```

## 反例

输出要求：“给我一个详细分析”。  
问题：无法判断字段是否齐全，也无法做自动回归。

## 练习

为“财务报销审核 Skill”设计 input_schema 和 output_schema，至少包含金额、发票、规则命中、风险等级和审批建议。

## 检查清单

- [ ] 必填字段明确
- [ ] 类型明确
- [ ] 输出字段可检查
- [ ] 错误输出也有格式
- [ ] 可被测试脚本验证
