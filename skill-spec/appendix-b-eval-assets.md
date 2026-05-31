# 附录 B 测试与评测资产

## Router 触发测试

```yaml
skill: review-pr-risk
should_trigger:
  - 请审查这个 PR 的上线风险
  - 合并前看一下有没有回归风险
should_not_trigger:
  - 解释这段代码的含义
  - 帮我写一个 Python 函数
```

## Schema 校验

```python
def assert_required_keys(result, required):
    missing = set(required) - set(result)
    assert not missing, f"missing keys: {missing}"
```

## 危险工具审批测试

```python
def test_prod_write_requires_approval(policy_engine):
    decision = policy_engine.check(
        tool="database.write_prod",
        actor="alice",
        skill="audit-expense-claim"
    )
    assert decision.allowed is False
    assert decision.reason == "approval_required"
```

## 成本预算测试

```python
def test_skill_cost_budget(eval_runner):
    result = eval_runner.run_suite("skill-regression")
    assert result.cost_per_task_usd <= 0.12
    assert result.p95_latency_seconds <= 120
```

## Trace 样本格式

```json
{
  "task_id": "task_001",
  "skill": "review-pr-risk",
  "version": "1.0.0",
  "trigger": "auto",
  "tool_calls": [],
  "hook_events": [],
  "cost_usd": 0.08,
  "status": "ok",
  "failure_label": null
}
```

## 20 条回归样本分配

| 类别 | 数量 |
| --- | --- |
| 应触发 | 10 |
| 不应触发 | 5 |
| 异常路径 | 3 |
| 高风险权限路径 | 2 |
