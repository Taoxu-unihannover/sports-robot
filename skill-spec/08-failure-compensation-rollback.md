# 第 8 章 失败、补偿与回滚

## 本章解决什么问题

生产 Skill 必须假设工具会失败、网络会超时、用户会拒绝审批、外部系统会部分写入。本章让失败成为显式设计。

## 核心概念

| 机制 | 用途 |
| --- | --- |
| retry | 处理临时失败 |
| checkpoint | 保存可恢复状态 |
| idempotency | 防止重复副作用 |
| human approval | 处理高风险动作 |
| compensation | 对已发生副作用做补偿 |
| side-effect log | 审计外部写入 |

## 工程方法

副作用工具必须满足至少一项：

- 支持幂等键。
- 执行前 checkpoint。
- 执行后写 side-effect log。
- 有补偿动作或人工回滚说明。

## 模板：副作用记录

```json
{
  "skill": "submit-expense-review",
  "task_id": "task_001",
  "tool": "finance.submit_decision",
  "idempotency_key": "expense-8848-review-v1",
  "status": "committed",
  "rollback": "finance.reopen_expense"
}
```

## 反例

接口超时后直接重试提交报销审批。  
问题：第一次请求可能已经成功，重试会造成重复审批或重复通知。

## 练习

为“发送客服回复 Skill”设计失败策略，覆盖草稿生成失败、审批拒绝、发送超时和重复发送。

## 检查清单

- [ ] 写操作有幂等键
- [ ] 有 checkpoint
- [ ] 有副作用日志
- [ ] 有补偿策略
- [ ] 高风险动作需要审批
