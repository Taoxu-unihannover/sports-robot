# 第 11 章 Skill + Plugin

## 本章解决什么问题

单个 Skill 可以本地使用，但团队复用需要打包、版本、权限说明、安装和回滚。本章讲如何把 Skill 变成能力包。

## 核心概念

Plugin 应同时携带：

- Skills
- Hooks
- MCP 配置
- 命令或入口
- 权限声明
- 测试与版本说明

## 工程方法

第三方或跨团队 Plugin 默认禁用。启用前展示工具面、权限面、版本和 owner。

## 模板：Plugin Manifest

```json
{
  "name": "team-review-skills",
  "version": "1.0.0",
  "skills": [
    {
      "name": "review-pr-risk",
      "path": "./skills/review-pr-risk/SKILL.md"
    }
  ],
  "hooks": [
    {
      "event": "pre_tool",
      "mode": "blocking",
      "command": "python hooks/policy.py"
    }
  ],
  "mcpServers": {
    "github-readonly": {
      "allowedTools": ["get_pull_request", "get_diff"]
    }
  },
  "permissions": {
    "defaultEnabled": false,
    "requiresApproval": ["write_tools"]
  }
}
```

## 反例

只把一堆 `SKILL.md` 压缩成包，没有权限说明和版本兼容。  
问题：安装者不知道它会调用哪些工具，也无法安全升级。

## 练习

设计一个“团队代码审查 Plugin”，列出包含的 Skill、MCP server、hook、权限和回归测试。

## 检查清单

- [ ] manifest 有版本
- [ ] 默认禁用高风险能力
- [ ] 权限面可见
- [ ] 带 smoke test
- [ ] 有回滚说明
