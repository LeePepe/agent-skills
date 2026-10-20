# Workflow：六个工作流

本索引定义编排入口和交接边界。W0 是六个 workflow 的总图，不是主 agent、主管会话或第七个 workflow。
repo 内的执行者仍从目标仓 `AGENTS.md` 读取 guide 和固定版本 shared 合同，遵守原 hooks、review 和 required CI。
本索引不覆盖已采用的固定合同，不证明角色、定时触发或消费者已经部署。

| Workflow | 开始与工作 | 输出与现有入口 |
|---|---|---|
| 01 需求沟通与规划 | 获定义 assignment 的人或 agent 按[goal-target-task](https://github.com/LeePepe/user-skills/blob/main/skills/goal-target-task/SKILL.md)定义 Goal／Targets／Tasks、依赖和验收命令 | 冻结的可执行 revision；跨仓协调用 [`orchestrate`](orchestrate/SKILL.md)，团队入口用 [`multica-issue`](../repo/multica-issue/SKILL.md) |
| 02 实现 | Dev Team 或 subagent 只执行冻结 Target 内获分配的 Tasks，按合同限定审查 | 成功创建／更新本次 PR，回报准确 head、验证、审查及限制；Dev Team PR 交 TL 立即派 PRM 合法合并；其他 PR 由各自写者交付 |
| 03 PR 接管与交付 | FS 创建或更新 Dev Team 非 Draft PR 后交 TL，TL 立即派 PRM | 立即启用 auto-merge，跟进 CI／review、回派具体修复，直至合并读回或准确授权处置；辅助诊断用 [`layered-ci-autofix`](../repo/layered-ci-autofix/SKILL.md) |
| 04 自动化发布 | 非破坏性 SDK／内部 TestFlight 的实际发布内容合入且必要检查通过 | 对应内容正确发布；现有 SDK 产物辅助为 [`shared-release`](shared-release/SKILL.md)，新 Actions 接线有下述版本依赖 |
| 05 产品遥测分析 | 优先交付 pageview／pageaction、PLT 等基础收集：产品→Azure L0→aidata 整理可查询 | 收集链路与分析分别验收；分析只由 workflow skill 独立手动触发，当前目录尚无已交付分析入口 |
| 06 周期维护（启用 HOLD） | 未来由本仓既有 Codex runner 独立只读核对计划范围内公开仓的当前文档和相关代码 | [`periodic-maintenance`](periodic-maintenance/SKILL.md) 提供未启用规则、离线适配器和模板；普通 backlog／待澄清草稿，不修复、派开发或追修 |

需求→实现→非 Draft PR 交付→适用发布；遥测／维护发现回到同一个需求入口，不要求每次任务走遍六个节点。
三层定义权引用合同 R1；repo-local 开发与两种执行路径属于 02。恢复、必要 Owner 沟通和仓规则内嵌各 workflow，
分别复用 [`runtime-recovery`](runtime-recovery/SKILL.md)、[`owner-decision-loop`](../repo/owner-decision-loop/SKILL.md)
和目标仓合同；它们不是额外节点。AIDash 是 repo 和预留展示平台，展示／采集 UI 不由本索引实现。

历史 W0–W7 仅用于追溯：旧 W1→01，W2/W3→02，W4→03，W5→04 的 SDK 辅助；W6/W7 是横切辅助。
旧 `orchestrate` 仍是跨仓执行入口，不再定义 W0。已交接的旧版本保持稳定，新增规则按明确后续切片采用。

## 聊天准入与执行版本

- 仅描述现象或要求诊断时，CLI 查事实、给判断，不自动实施或派发。明确且范围清楚的“修复／实现”已表达实施意图，
  不重复问“改不改”；新增范围、权限与受保护操作仍按现有门禁处理。
- 设计修改、workflow refine 先由 Owner 与 CLI 确定需求、设计及基本实现方案，再交 Dev Team 或 subagent。
  普通修改写清当前／期望行为、证据、范围／不做项和可观察验收；正常根因定位与内部修法由执行方承担。
- 普通产品任务默认 Dev Team；尊重明确选择，复用原 owner，同一目标不建第二写者。subagent 不额外套团队 task 流程，
  但仍遵守目标仓验证和独立审查要求。
- 超出当前约定的新目标／实质变更是新需求，回到本入口澄清、计划和确认实施；不另造需求类型，
  不自动改写在途方案与验收。单条设计意见获同意不等于整版获准执行。
- 重复反馈与回流：先查已有需求、修复和决定的证据，不凭相似标题重派或覆盖旧结论。
  仅在范围、假设、版本、验收目标与证据实质未变时判定为重复，复用已有任务／决定及原 owner；
  证明既有修复未满足原验收目标的，按修复无效关联原 Target；证明此前已满足行为重新失效的，按回归关联受影响的 Target；
  证据不足时保持待补事实，不予归类或派发。旧任务／决定只在上述范围、假设、适用版本、验收目标与证据匹配时复用。
  新证据推翻必要前提时，仅重开受影响的决定，保留原结论、来源、变更理由与未受影响部分。
- 定义冻结、缺口与验收迁移引用 [goal-target-task R2–R5](https://github.com/LeePepe/user-skills/blob/cb5ec84961d05a937a3a5196e02a8eeac224fd4f/skills/goal-target-task/SKILL.md#定义冻结与缺口)。
- 执行方不可用或接收未知按合同角色绑定处理；Dev Team 的操作步骤引用
  [squad Dispatch and recovery](dev-team-roles/dev-team-squad/SKILL.md#dispatch-and-recovery)。

## Plan 与依赖推进

plan 的必需内容引用 [goal-target-task](https://github.com/LeePepe/user-skills/blob/cb5ec84961d05a937a3a5196e02a8eeac224fd4f/skills/goal-target-task/SKILL.md)；
长期升级／验证／回滚规则在 repo guide 或版本化 shared 文档，plan 的运行记录要求见
[squad Workflow boundary](dev-team-roles/dev-team-squad/SKILL.md#workflow-boundary-and-accepted-version)。

Dev Team 由 TL 按 plan 推进；subagent 由既有主会话按 plan 接续。独立且已授权工作可继续，局部阻塞不能隐藏整体未完成。
provider source、发布、消费者升级／真实消费分别取证；04 不负责消费者升级，不取消原任务的消费／回滚义务。

## 仓库先定义，角色再执行

layer 与 PR 单元属于目标仓 guide 和固定版本 `shared-ci/ai/repo-contract.md`，搭建辅助为
[`repo-kit`](../repo/repo-kit/SKILL.md)。按单一可观察目标、实际接口和依赖组织，不按 layer 数、行数或文件数硬切。
AGENTS 保持目录，合同缺失或矛盾记录为前置缺口，不由角色临时创造豁免。

### 实现职责与当次输出

Dev Team 的角色绑定、运行规则和交接以 [squad](dev-team-roles/dev-team-squad/SKILL.md) 为准；
三层定义、R1–R6、交接和 V1–V4 以 `goal-target-task` 为准。

| Member | Squad role |
|---|---|
| TL (Team Lead) | leader |
| FS (Fullstack Engineer) | engineer |
| AI Reviewer | reviewer |
| PRM (PR Manager) | ops |
| Planner (Planner Lead) | planner |

成员表按 [squad Team](dev-team-roles/dev-team-squad/SKILL.md#team) 展示；角色专属执行细节各自只保留一份：

- [Planner](dev-team-roles/dev-team-planner/SKILL.md)：规划产物、spec 格式与 spec gate 请求。
- [TL](dev-team-roles/dev-team-team-lead/SKILL.md)：子 issue、stage 调度、Target 验收请求、三层关闭及 Goal 通知 Owner。
- [FS](dev-team-roles/dev-team-fullstack-engineer/SKILL.md)：实现、验证、完整 code-review 自检和准确 SHA 的发布前请求／PR 交接。
- [AI Reviewer](dev-team-roles/dev-team-ai-reviewer/SKILL.md)：spec／impl／target 三类只读独立验收及 verdict。
- [PRM](dev-team-roles/dev-team-pr-manager/SKILL.md)：Dev Team 来源核验、接手／巡检、具体修复路由及合并回读／最终回执。

subagent 的原执行者负责实现、验证、修复；既有主会话管理依赖与结果，按目标仓合同安排独立审查。
团队 Reviewer 的职责边界不构成其他执行者的通用免审。实现输出与整体验收按合同三层定义和 V1 取证。

## PRM 唯一交付责任

Dev Team 交付按 [squad Flow](dev-team-roles/dev-team-squad/SKILL.md#flow) 和
[Merge rules](dev-team-roles/dev-team-squad/SKILL.md#merge-rules-all-repos) 推进。
PRM 的来源边界、Task issue 回执和巡检条件只定义在 [PRM 入口](dev-team-roles/dev-team-pr-manager/SKILL.md#trigger-and-inputs)；
非 Dev Team PR 的写者按合同交付角色和同一合并规则负责自己的 PR。

### Dev Team Flow Supervisor

Flow Supervisor 不在 squad 内，按自己的 Multica Autopilot 运行；
中断判定、唤醒条件、原责任路由与红线只定义在 [Flow Supervisor](dev-team-roles/dev-team-flow-supervisor/SKILL.md)。
部署名称、Autopilot 绑定和实际接收能力须另行核实。
[`multica-delivery-supervisor`](multica-delivery-supervisor/SKILL.md) 是不同的会话级辅助，没有因此获得后台唤醒或团队职责。

## 实现修复与升级

审查范围、范围外发现及两轮上限统一按[goal-target-task V1–V4](https://github.com/LeePepe/user-skills/blob/cb5ec84961d05a937a3a5196e02a8eeac224fd4f/skills/goal-target-task/SKILL.md#限定审查)，交回定义方处理。
需要 Owner 决定时通过 [Owner 决策入口](../repo/owner-decision-loop/SKILL.md) 报告版本、未满足要求、尝试及结果、已知／未知与建议；单纯等待不计一轮，明确安全／权限硬阻塞立即报告。

查证后无法复现或补齐必要事实，且无安全有效下一步时，可交付查证结论，但原修复仍未完成，交 Owner 判断怎么继续。
**进入该等待后，新证据到达或条件补齐也不能自动续行**；Owner 选定后沿原任务、责任和权限推进。未复现不等于无问题／已修复。

## 后续能力与 HOLD

- **04**：shared-ci 公共构建／发布规则、模板及脚本正常交付后，skill 才引用对应固定版本指导各仓 Actions；
  各仓保留构建命令、平台、渠道与配置。现有质量 CI／SDK 辅助不等于此接线已实现，不虚构可用 pin。
  TF 成功须准确 build 经 Apple 处理完成且对约定内部组可用，上传不够；失败只记录可收集错误供后续 AIDash 展示，
  不新增自动重试、派修、升级通知或回滚／重发。发布启用、凭据等原 HOLD 独立保留；Web 不纳入。
- **05**：收集验收需要两类基础数据经 Azure L0、aidata 整理后可查询的真实证据；不以未来分析 TODO 阻塞收集。
  分析准确 skill 入口尚缺，保留补齐待办，不虚构命令；收集、新数据或发布不隐式触发分析。
  高级／定期分析为后续 TODO，数据访问、隐私与生产权限保持。
- **06**：按有效需求／设计、相关提交时间与具体 diff 判断文档过期、实现遗漏或废弃代码清理需求；
  时间先后不自动裁决，草案／HOLD 不自动变任务，证据不足只提待澄清。历史归档仅作依据。
  最小源码方案已确认：agent-skills 承载，未来 Actions 每周一次及手动触发，由原仓既有 Codex runner 独立只读检查，
  只输出对应 Multica project 的未指派 backlog。首版仅规则、离线适配器、隔离测试与模板；真实采集／语义运行／出口尚未接线，
  runner 新用途、真实 Multica、凭据／settings、调度与准确 head 审查须分别满足，启用 HOLD 不解除。
  提出需求不等于派发开发或修复完成，反复未修复的展示留 AIDash 后续。

## 合并规则（按目标仓实际保护）

引用 [squad Merge rules](dev-team-roles/dev-team-squad/SKILL.md#merge-rules-all-repos)，
Dev Team 共用运行规则只保留该处一份；其他 PR 的写者也沿此规则交付，目标仓实际保护继续有效。

## 交接最小字段

按合同交接要求，复用 issue、PR 模板或 subagent prompt；七项字段的唯一运行定义为
[squad Handoffs](dev-team-roles/dev-team-squad/SKILL.md#handoffs)，各角色补充自己的输入／输出。
发送与接收、run 状态与交付、merge 与发布／消费的证据边界分别按合同与 squad 合并规则核对。
