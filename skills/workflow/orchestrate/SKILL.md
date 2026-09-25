---
name: orchestrate
description: W0 总体编排——主 agent 把 Owner 的多 repo 目标拆成可交付切片，选执行来源（Dev Team issue 或 subagent），派发、监督并按 PR 证据验收；自己不写产品代码。用于“完成这个跨仓目标 / 继续某个 goal / 看看怎么继续 / 协调多个 repo 的升级 / 派活并盯到合并”。
---

# W0 总体编排

主 agent 只做：**计划 → 委派 → 观察 → 验收 → 向 Owner 报告**。实现、审查、合并分别属于 W3、W4 的角色。
全局索引与合并规则见 [workflow 索引](../README.md)。

## 1. 读状态（每次继续前）

1. 读 goal 的**单页台账**（每 repo 一行：当前 PR/SHA、下一动作 owner、hold）。台账超过一页就先压缩再继续。
2. 刷新真实状态，不信历史描述：各 repo `gh pr list`、最近 CI run、Multica 相关 issue、正在跑的 agent 会话。
3. 区分：已完成 / 在途（有唯一 owner）/ 等 Owner / 被外部故障阻塞。外部故障只阻塞依赖它的动作。

完成条件：每个未完成项都有 owner 与下一动作，或明确 hold 原因。

## 2. 切片

- W0 明确各 repo 的目标、验收和真实依赖；跨 repo 按 provider → 发布 → 消费者（W5）。
- 交给 Dev Team 的目标由其 [Planner 在规划阶段拆需求/spec/layer task](../README.md#dev-teamplanner-给出任务范围w2)，W0 不代替 Planner 定义 FS 的任务范围。
  直接交其他 agent 的任务按目标仓 AGENTS 目录下的开发文档执行，不额外要求 Planner 拆分或统一 PR 范围检查。
- 依赖只按真实的数据/接口关系排；无依赖的切片并行，但**同一 repo 同一路径只有一个写者**。
- 共享接口、迁移、全局重构串行；机械推广（多仓同一模板）可并行。
- 需求不清先问 Owner（W7）或用 grilling；架构迁移不夹带功能/UX 改动。

完成条件：目标、验收、依赖和承接者明确；Dev Team 的实现就绪条件由 Planner 与既有 spec/plan gate 保证。

## 3. 选来源并派发

| 适合 Dev Team（W1→W2） | 适合 subagent（直接 W3） |
|---|---|
| 产品功能/bug、需要 Planner 拆解、要留 issue 历史 | 模板推广、脚手架、调研、一次性工具、Dev Team 不可用时 |

派发内容包含[交接最小字段](../README.md#交接最小字段)。给 Dev Team 的目标交其 Planner 产出任务图；
直接派发其他 agent 时写明目标 repo/base、任务与验收、“从 AGENTS.md 目录读取开发指南”、禁止事项及完成时回报 PR URL。
携带当前任务需要的指针，不假设执行者或部署角色会自动读到个人 skills 的更新。

## 4. 观察

- 以 PR 为观察单位：CI 结果、review comment、是否卡住。实现/检查失败交回**原作者**；Dev Team 的规划调整由 TL 返回 Planner；确需新审批、权限或运行边界决策才交 Owner。不开第二个写者。
- 不给 PRM 增加 PR 大小/范围反馈或验收职责；它按现有 CI/review 与合并条件推进。
- 主 agent 可以安全停止失控的执行，但不手工替代 Supervisor/PRM 去推进，否则如实记为手工介入。
- 故障（Multica/NAS/daemon/runner 不可用）走 [W6](../runtime-recovery/SKILL.md)，不重复重试。

## 5. 验收与报告

- 交付完成 = PR merged + 验收项在 PR 上有证据（CI、review、必要时截图/消费者 build），不追加通用范围门禁。
- 目标完成 = 所有切片完成 + goal 的整体验收项逐条有证据；不从“CI 绿”推断“已消费/已发布”。
- 向 Owner 报告：完成了什么（链接）、还剩什么、哪些等 Owner、下一步。不写过程流水账。

## 红线

- 不改产品代码、不 merge、不改 ruleset/凭据/可见性，除非 Owner 对该具体操作授权。
- 不修改 Multica 源码；平台能力缺口写成提案给 Owner。
- 不为“完成目标”批量关闭 issue/PR；无关历史项逐个交 Owner。
- 账号、profile、本机路径不写进任何 repo。
