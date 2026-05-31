# 第 14 章 十个行业案例卡片

## 本章解决什么问题

本章把 Skill 方法迁移到更多行业场景，帮助读者从案例中抽取组件组合和部署策略。

## 案例卡片

| 案例 | 组件组合 | 最小接口 | 测试指标 | 部署建议 |
| --- | --- | --- | --- | --- |
| 自动化运维巡检 | Skill + Hook + MCP + Retry | `run_cluster_audit(clusters)` | 成功率、误报率、重试次数 | 只读凭证、审计日志、沙箱 |
| PR 代码审查 | Skill + Handoff + Trace | `review_pr(repo, pr)` | 缺陷召回率、噪声率、成本 | GitHub 只读 MCP |
| 仓库级 bug 修复 | Skill + Session + Guardrails | `solve_issue(repo, issue_id)` | 测试通过率、回滚次数 | 隔离容器执行 |
| 浏览器竞品监控 | Browser Skill + Hooks | `watch_site(url, schema)` | 页面成功率、抽取完整率 | profile 隔离、代理池 |
| 数据分析助手 | Flow + Skill + Memory | `analyze(csv, question)` | 图表成功率、延迟 | 文件权限和计算容器分离 |
| 企业知识问答 | Skill + RAG + MCP | `ask_enterprise(question)` | 引用覆盖率、幻觉率 | 返回证据和引用 |
| 合规审批流 | Graph + HITL + Checkpoint | `submit_change(req)` | 审批耗时、恢复成功率 | 持久化 checkpoint |
| 插件生态平台 | Plugin + Marketplace + Policy | `install_plugin(name)` | 安装成功率、回滚时间 | 私有 marketplace |
| 联邦式多代理 | A2A + MCP + Session Broker | `invoke_remote(agent, task)` | 跨域延迟、失败重试率 | agent card 和认证 |
| 自演化技能系统 | Registry + Eval + Patch | `learn_from_trace(trace_id)` | 复用率、回归通过率 | 人审、灰度、回滚 |

## 模板：案例扩写卡

```markdown
## 案例名

- 目标场景：
- 组件组合：
- 最小接口：
- Skill 边界：
- 工具权限：
- 测试样本：
- 指标：
- 部署建议：
- 常见失败：
```

## 反例

案例只讲业务价值，不讲工具权限、测试指标和部署建议。这样的案例无法指导生产落地。

## 练习

任选一个行业案例，按模板扩写成 2 页小节。

## 检查清单

- [ ] 有最小接口
- [ ] 有组件组合
- [ ] 有测试指标
- [ ] 有部署建议
- [ ] 有常见失败
