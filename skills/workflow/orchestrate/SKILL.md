---
name: orchestrate
description: 跨仓拆分与编排——把已确认的多 repo 目标拆成可交付切片，按计划依赖交给 Dev Team 或 subagent，跟踪并按交付证据验收；自己不写产品代码。用于继续跨仓 goal、协调多个 repo 的升级或派活并跟踪交付；是 W0 整体交付循环的子流程。
---

# 跨仓拆分与编排

主 agent 只做：**计划 → 委派 → 观察 → 验收 → 向 Owner 报告**。实现、审查、合并分别属于 W3、W4 的角色。
W0 是整体交付循环，本 skill 是其中的跨仓子流程。开始前读 [workflow 索引](../README.md) 中的聊天准入、执行版本、
plan/guide 分工和修复升级合同；本 skill 不授予新的实施或受保护操作权限。

## 1. 读状态（每次继续前）

1. 读 goal 的**单页台账**（每 repo 一行：当前 PR/SHA、下一动作 owner、hold）。台账超过一页就先压缩再继续。
2. 刷新真实状态，不信历史描述：各 repo `gh pr list`、最近 CI run、Multica 相关 issue、正在跑的 agent 会话。
3. 区分：已完成 / 在途（有唯一 owner）/ 等 Owner / 被外部故障阻塞。外部故障只阻塞依赖它的动作。

完成条件：每个未完成项都有 owner 与下一动作，或明确 hold 原因。

## 2. 切片

- 将已确认方案中的各 repo 目标、验收和真实依赖写入本次 plan；跨 repo 按 provider → 发布 → 消费者（W5），
  指向适用版本的 repo guide/shared 规则，并写明每步完成后的下一动作。
- 先读[仓库已有的 layer/PR 规范](../README.md#仓库先定义角色再执行)。Dev Team 的 Planner 据此拆需求/spec task，编排者不另定义架构边界。
  其他 agent 也遵循同一仓库规范，但不要求 Dev Team 的 Planner/task 流程；合同缺失先按 repo-kit 在授权范围补齐，
  需要新权限则报告阻塞，而非让角色各定一套。
- 依赖只按真实的数据/接口关系排；无依赖的切片并行，但**同一 repo 同一路径只有一个写者**。
- 共享接口、迁移、全局重构串行；机械推广（多仓同一模板）可并行。
- 需求不清先问 Owner（W7）或用 grilling；架构迁移不夹带功能/UX 改动。

完成条件：仓库合同可读取，目标、验收、依赖和承接者明确；Dev Team 的任务拆分由 Planner 与既有 spec/plan gate 保证。

## 3. 选来源并派发

| 适合 Dev Team（W1→W2） | 适合 subagent（直接 W3） |
|---|---|
| 普通产品任务的默认出口；已定方案的设计修改/workflow refine 也可承接 | 明确选择的直接执行；已定方案的设计修改/workflow refine 也可承接 |

派发先核对固定方案、Owner 执行确认和已有唯一 owner。所选团队离线或结果未知时保留版本与执行方，先对账再补派，不自动改派。
内容包含[交接最小字段](../README.md#交接最小字段)，并指向仓库规范。给 Dev Team 的目标交其 Planner 复用、校验、补齐已有任务图，
保留 spec/plan 审查；TL 按依赖推进。
直接派发其他 agent 时写明目标 repo/base、任务与验收、“从 AGENTS.md 目录读取开发指南”、禁止事项及完成时回报 PR URL。
主会话按 plan 接续 subagent 的后续动作。携带当前任务需要的指针，不假设执行者或部署角色会自动读到个人 skills 的更新。

## 4. 观察

- 以 PR 为观察单位：CI 结果、review comment、是否卡住。实现/检查失败交回**原作者**；本版必要实现补拆由 TL 返回 Planner，
  方案变更归下一版。按[实现修复与升级](../README.md#实现修复与升级)处理两轮无进展及 TL 诊断后仍无解的情况，不开第二个写者。
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
