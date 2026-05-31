# 第 13 章 四个完整实战 Skill

## 本章解决什么问题

本章给出 4 个可复制的 `SKILL.md` 示例，覆盖文档、代码、企业审批和安全审计场景。

## 案例 1：Markdown 格式规范 Skill

### 需求分析

把结构混乱的 Markdown 文档整理成层级清晰、标题规范、列表统一、代码块带语言标识的版本。

### 目录结构

```text
format-markdown-document/
  SKILL.md
  examples/
    messy.md
    formatted.md
  tests/
    trigger.yaml
```

### 完整 SKILL.md

```markdown
---
name: format-markdown-document
description: 规范化 Markdown 文档结构和格式。适用于用户要求整理 Markdown、修复标题层级、统一列表和代码块格式；不用于改写文章观点。
when_to_use: 用户提到 Markdown、文档格式、标题层级、列表混乱、代码块语言标识时使用。
version: 1.0.0
allowed-tools:
  - filesystem.read
  - filesystem.write
input_schema:
  type: object
  required: [file_path]
  properties:
    file_path: { type: string }
output_schema:
  type: object
  required: [summary, changed_sections]
---

# Markdown 格式规范 Skill

## 何时使用
当用户需要整理 Markdown 文档格式，而不是改写内容含义时使用。

## 输入约束
- 必须能读取目标 Markdown 文件。
- 不改变事实、观点和代码逻辑。

## 执行步骤
1. 读取文档并识别标题层级、列表、表格、代码块。
2. 修复标题跳级和重复空行。
3. 统一列表缩进和代码块语言标识。
4. 输出修改摘要和被调整的章节。

## 输出格式
返回 summary、changed_sections、remaining_issues。

## 失败处理
如果文件不存在，返回 missing_file；如果不是 Markdown，返回 unsupported_format。
```

## 案例 2：PR 代码审查 Skill

```markdown
---
name: review-pr-risk
description: 审查 Pull Request 的风险点并输出结构化风险报告。适用于 PR、合并请求、上线前检查、代码审查；不用于普通代码解释。
when_to_use: 用户提到 review PR、合并前风险、测试缺口、安全风险时使用。
version: 1.0.0
allowed-tools:
  - github.get_pull_request
  - github.list_files
  - github.get_diff
  - tests.run_changed
input_schema:
  type: object
  required: [repo, pr_number]
  properties:
    repo: { type: string }
    pr_number: { type: integer }
output_schema:
  type: object
  required: [summary, risks, rollback_notes, test_gaps]
---

# PR 风险审查 Skill

## 何时使用
用户要求审查 PR 风险、合并风险、安全问题、回归风险或测试缺口时使用。

## 输入约束
- 需要 repo 和 pr_number。
- 只读 PR、diff 和相关文件。

## 执行步骤
1. 获取 PR 元信息、文件列表和 diff。
2. 按正确性、安全、兼容性、回滚难度、测试缺口分类审查。
3. 优先报告会影响行为的风险，不输出低价值风格评论。
4. 如可运行变更相关测试，运行并记录结果。

## 输出格式
输出 summary、risks、rollback_notes、test_gaps。risks 必须包含 severity、file、reason、suggestion。

## 失败处理
PR 不存在返回 missing_pr；权限不足返回 permission_denied；diff 过大时先输出高风险文件摘要并请求范围收敛。
```

## 案例 3：财务报销审核 Skill

```markdown
---
name: audit-expense-claim
description: 审核财务报销申请并输出规则命中、风险等级和审批建议。适用于报销单、发票、差旅费用和审批流；不用于财务制度咨询闲聊。
when_to_use: 用户要求审核报销、检查发票、判断费用合规时使用。
version: 1.0.0
allowed-tools:
  - finance.read_claim
  - finance.read_policy
  - ocr.read_invoice
input_schema:
  type: object
  required: [claim_id]
  properties:
    claim_id: { type: string }
output_schema:
  type: object
  required: [summary, risk_level, rule_hits, recommendation]
---

# 财务报销审核 Skill

## 何时使用
用于审核单个报销申请是否符合制度、票据是否完整、金额是否异常。

## 输入约束
- 必须提供 claim_id。
- 只能读取报销记录和制度，不直接批准付款。

## 执行步骤
1. 读取报销单、附件和适用制度。
2. 校验金额、日期、发票抬头、重复票据和预算科目。
3. 按低、中、高风险分级。
4. 给出批准、补材料、人工复核或拒绝建议。

## 输出格式
输出 summary、risk_level、rule_hits、missing_evidence、recommendation。

## 失败处理
附件缺失返回 missing_evidence；制度冲突返回 policy_conflict；高风险必须建议人工复核。
```

## 案例 4：安全审计 Skill

```markdown
---
name: audit-security-sensitive-change
description: 审计涉及权限、密钥、危险命令或敏感文件的变更，并输出安全风险和拦截建议。适用于安全审计、上线前安全检查、敏感操作复核；不用于一般代码风格审查。
when_to_use: 用户提到密钥、权限、删除、生产环境、凭证、敏感文件、安全审计时使用。
version: 1.0.0
allowed-tools:
  - filesystem.read
  - git.diff
  - secrets.scan
input_schema:
  type: object
  required: [target]
  properties:
    target: { type: string }
output_schema:
  type: object
  required: [summary, findings, required_approvals]
---

# 安全审计 Skill

## 何时使用
当变更涉及敏感文件、凭证、权限、生产写入、删除操作或危险命令时使用。

## 输入约束
- 只读目标文件或 diff。
- 不执行任何写入型工具。

## 执行步骤
1. 扫描密钥、token、私钥、生产配置和危险命令。
2. 识别权限扩大、审计缺失、回滚困难和数据破坏风险。
3. 按 critical/high/medium/low 分级。
4. 给出阻断、人工审批或允许继续的建议。

## 输出格式
findings 包含 severity、location、evidence、impact、recommendation。

## 失败处理
无法读取目标时返回 inaccessible_target；扫描工具失败时降级为人工规则检查并标记 scan_incomplete。
```

## 测试点与指标

| Skill | 必测项 | 指标 |
| --- | --- | --- |
| Markdown | 不改内容含义 | 格式修复率 |
| PR 审查 | 风险召回、噪声控制 | 缺陷召回率、评论噪声率 |
| 财务审核 | 规则命中、人工复核 | 误批率、补材料准确率 |
| 安全审计 | 敏感信息、危险命令 | 高危召回率、误报率 |

## 反例

实战 Skill 只给目录不给完整 `SKILL.md`。读者无法复制，也无法判断元数据、正文、权限和失败处理是否一致。

## 练习

任选一个案例，为它补充 `tests/regression.yaml`，至少包含 5 条应触发样本和 3 条异常样本。

## 检查清单

- [ ] 有完整 SKILL.md
- [ ] 有目录结构
- [ ] 有测试点
- [ ] 有指标
- [ ] 有失败处理
