# 附录 A 模板库

## 1. 通用 SKILL.md

```markdown
---
name: action-domain-output
description: 用于...适用于...不用于...
when_to_use: 用户提到...时触发。
version: 1.0.0
allowed-tools: []
input_schema:
  type: object
  required: []
  properties: {}
output_schema:
  type: object
  required: []
  properties: {}
---

# Skill Name

## 何时使用

## 输入约束

## 执行步骤

## 输出格式

## 失败处理
```

## 2. Description 公式

```text
用于 + 任务对象 + 动作 + 交付物。适用于 + 用户触发表达。不用于 + 负面边界。
```

## 3. Input / Output Schema

```yaml
input_schema:
  type: object
  required: [target]
  properties:
    target: { type: string }
output_schema:
  type: object
  required: [summary, status]
  properties:
    summary: { type: string }
    status: { type: string, enum: [ok, blocked, failed] }
```

## 4. Skill 目录模板

```text
skill-name/
  SKILL.md
  scripts/
  references/
  assets/
  examples/
  tests/
```

## 5. Hook 配置

```json
{
  "event": "pre_tool",
  "mode": "blocking",
  "priority": 10,
  "command": "python hooks/policy_check.py"
}
```

## 6. MCP 配置

```json
{
  "mcpServers": {
    "readonly-service": {
      "command": "node",
      "args": ["server.js"],
      "allowedTools": ["read", "search"]
    }
  }
}
```

## 7. Plugin Manifest

```json
{
  "name": "team-skills",
  "version": "1.0.0",
  "skills": [],
  "hooks": [],
  "mcpServers": {},
  "permissions": {
    "defaultEnabled": false
  }
}
```

## 8. 发布检查表

```markdown
- [ ] description 有触发和负面边界
- [ ] allowed-tools 最小化
- [ ] input/output schema 可验证
- [ ] 有回归测试
- [ ] 有权限审查
- [ ] 有 trace 字段
- [ ] 有灰度计划
- [ ] 有回滚方式
```
