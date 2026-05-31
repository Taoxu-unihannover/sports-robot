# 第 12 章 Skill 测试、评测与回归

## 本章解决什么问题

Skill 没有测试，就无法放心演化。本章给出触发、schema、输出、权限、成本和 trace 的测试方法。

## 核心概念

测试层次：

| 类型 | 验证内容 |
| --- | --- |
| Router test | 是否正确触发 |
| Schema test | 输入输出字段是否齐全 |
| Behavior test | 核心步骤是否完成 |
| Policy test | 危险工具是否被拦截 |
| Cost test | 单任务成本是否超预算 |
| Trace replay | 旧任务是否可复现 |

## 工程方法

每个 Skill 至少维护 20 条回归样本：10 条应触发、5 条不应触发、3 条异常路径、2 条高风险权限路径。

## 模板：pytest 回归测试

```python
from typing import Any

def validate_output_schema(result: dict[str, Any]) -> None:
    required = {"summary", "risks", "test_gaps"}
    missing = required - set(result)
    if missing:
        raise AssertionError(f"missing keys: {missing}")

def test_skill_router_selects_review_pr(router):
    skill = router.select("请帮我 review 这个 PR 的风险", {"repo": "org/repo"})
    assert skill is not None
    assert skill.name == "review-pr-risk"

def test_review_pr_output_schema(review_pr_skill):
    result = review_pr_skill.run(
        {"session_id": "s1"},
        {"repo": "org/repo", "pr_number": 42}
    )
    validate_output_schema(result)

def test_dangerous_tool_requires_approval(policy_engine):
    decision = policy_engine.check("deploy-prod", actor="alice")
    assert decision.allowed is False
    assert decision.reason == "approval_required"

def test_cost_budget(eval_runner):
    result = eval_runner.run_suite("review-pr-risk-regression")
    assert result.cost_per_task_usd <= 0.12
```

## 反例

只用一个 happy path 测试：“能生成报告”。  
问题：无法发现误触发、权限绕过、输出字段缺失、成本失控。

## 练习

为你的 Skill 设计 20 条回归样本，并按触发、异常、权限、成本分类。

## 检查清单

- [ ] 有触发测试
- [ ] 有 schema 测试
- [ ] 有危险工具测试
- [ ] 有异常路径测试
- [ ] 有成本预算
