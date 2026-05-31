# 附录 C 资料与研究路线

## 项目路线

| 项目 | 重点 |
| --- | --- |
| Claude Code | SKILL.md、hooks、plugins、MCP、权限 |
| OpenClaw | AgentSkills 兼容、多目录优先级、gating |
| Hermes Agent | skill_manage、自修补、plugin 默认禁用 |
| OpenHands | skills / extensions registry、产品化路径 |
| CrewAI | Flow、Memory、MCP、团队协作 |
| OpenAI Agents SDK | sessions、handoffs、guardrails、tracing |
| LangGraph | checkpoint、durable execution、HITL |
| browser-use | 浏览器技能、step hooks、观测 |

## 论文路线

| 工作 | Skill 设计启发 |
| --- | --- |
| ReAct | 推理和行动交错，但要控制轨迹长度 |
| Toolformer | 工具调用能力需要示例和筛选 |
| Reflexion | 失败反思必须绑定评测 |
| Voyager | Skill library 能积累长期能力 |
| SWE-agent | 环境接口会决定 Agent 表现 |
| AFlow | Workflow 和 Skill 组合可被优化 |

## 检索关键词

| 中文 | English |
| --- | --- |
| 技能系统、程序性记忆 | skill system, procedural memory |
| 渐进式披露 | progressive disclosure |
| 生命周期钩子 | lifecycle hooks |
| 模型上下文协议 | model context protocol |
| 回归评测 | regression evals |
| 技能市场 | skill marketplace |
| 自演化智能体 | self-improving agent |

## 更新原则

- 优先官方文档、源码仓库、论文原文。
- 闭源产品只分析公开接口和文档行为。
- 把产品名写轻，把 Skill 边界、契约、测试和治理写重。
