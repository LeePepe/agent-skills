# Workflow：六个工作流

本索引定义编排入口和交接边界。W0 是六个 workflow 的总图，不是主 agent、主管会话或第七个 workflow。
repo 内的执行者仍从目标仓 `AGENTS.md` 读取 guide 和固定版本 shared 合同，遵守原 hooks、review 和 required CI。
本索引不覆盖已采用的固定合同，不证明角色、定时触发或消费者已经部署。

| Workflow | 开始与工作 | 输出与现有入口 |
|---|---|---|
| 01 需求沟通与规划 | 获定义 assignment 的人或 agent 按[执行合同](execution-contract.md)定义 Goal／Targets／Tasks、依赖和验收命令 | 冻结的可执行 revision；跨仓协调用 [`orchestrate`](orchestrate/SKILL.md)，团队入口用 [`multica-issue`](../repo/multica-issue/SKILL.md) |
| 02 实现 | Dev Team 或 subagent 只执行冻结 Target 内获分配的 Tasks，按合同限定审查 | 成功创建／更新本次 PR，回报准确 head、验证、审查及限制；后续交 PRM 合法合并 |
| 03 PR 接管与交付 | PRM 发现或收到负责 repo 内任意来源的非 Draft PR | 跟进 CI／review／审批、回派具体修复，直至合法合并或准确授权处置；辅助诊断用 [`layered-ci-autofix`](../repo/layered-ci-autofix/SKILL.md) |
| 04 自动化发布 | 非破坏性 SDK／内部 TestFlight 的实际发布内容合入且必要检查通过 | 对应内容正确发布；现有 SDK 产物辅助为 [`shared-release`](shared-release/SKILL.md)，新 Actions 接线有下述版本依赖 |
| 05 产品遥测分析 | 优先交付 pageview／pageaction、PLT 等基础收集：产品→Azure L0→aidata 整理可查询 | 收集链路与分析分别验收；分析只由 workflow skill 独立手动触发，当前目录尚无已交付分析入口 |
| 06 周期维护（启用 HOLD） | 未来由本仓既有 Codex runner 独立只读核对计划范围内公开仓的当前文档和相关代码 | [`periodic-maintenance`](periodic-maintenance/SKILL.md) 提供未启用规则、离线适配器和模板；普通 backlog／待澄清草稿，不修复、派开发或追修 |

需求→实现→非 Draft PR 交付→适用发布；遥测／维护发现回到同一个需求入口，不要求每次任务走遍六个节点。
三层定义权取决于 assignment，不按 01／02 划分；repo-local 开发与两种执行路径属于 02。恢复、必要 Owner 沟通和仓规则内嵌各 workflow，
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
- 定义交出即冻结；发现缺口、验收迁移和新增 Target 按[执行合同 R2–R5](execution-contract.md#定义冻结与缺口)，不由执行者补进当前 Target。
- 已选执行方不可用或接收未知时，保留固定版本、任务标识、原执行方与真实状态；先对账、去重，
  再沿已验证入口补派确认未接收的任务。不自动改派，不把后台重试／唤醒描述当已实现能力。

## Plan 与依赖推进

本次 plan 按[执行合同](execution-contract.md)记录三层范围、父级／代码层、依赖、验收命令和冻结 revision。
长期升级／验证／回滚规则在 repo guide 或版本化 shared 文档；plan 引用实际采用版本，不复制政策。

Dev Team 由 TL 按 plan 推进；subagent 由既有主会话按 plan 接续。独立且已授权工作可继续，局部阻塞不能隐藏整体未完成。
provider source、发布、消费者升级／真实消费分别取证；04 不负责消费者升级，不取消原任务的消费／回滚义务。

## 仓库先定义，角色再执行

layer 与 PR 单元属于目标仓 guide 和固定版本 `shared-ci/ai/repo-contract.md`，搭建辅助为
[`repo-kit`](../repo/repo-kit/SKILL.md)。按单一可观察目标、实际接口和依赖组织，不按 layer 数、行数或文件数硬切。
AGENTS 保持目录，合同缺失或矛盾记录为前置缺口，不由角色临时创造豁免。

### 实现职责与当次输出

- **Dev Team**：Planner 按定义 assignment 复用、校验、补齐 spec/plan/tasks；AI Reviewer 只读方案审查通过后交 TL，
  TL 按冻结 Tasks 及依赖派 FS；每 Target 一个写者，Tasks 留在其内部清单。
- **FS**：开发、必要验证、修复和现有完整 code-review 自检。完成后交准确 SHA 的 pre-push 独立 spec 与 architecture 审查；
  通过由原 FS 推送／创建更新 PR；缺口按合同回定义方，不默认换作者。
- **Dev Team AI Reviewer**：承担只读 spec/plan（spec gate），以及发布前准确 SHA 的独立 spec 与 architecture 审查；
  不承担代码缺陷／规范审查（由 PR head 的 `codex-review-target` 负责），不执行或裁定 build/test/lint/hooks/CI，不盯 PR。FS 完整 code-review 自检保留，不能替代独立审查。
- **subagent**：原执行者负责开发、验证、修复；既有主会话管理依赖与结果，适用审查按仓合同安排。
  团队 Reviewer 的职责边界不构成其他执行者的通用免审。
- **当次实现输出**：本次必要实现、验证与审查满足，且所需 PR 成功创建／更新后回报 PR URL、准确 head、
  对应证据、剩余限制与下一责任。执行者可选择留下等待 required checks 并自行修复失败，也可直接交接离场；PR Manager 均为兜底。不隐去已知失败或缺失验证。
  push／PR 失败不是本次实现成功；此交接不是 PR 最终交付或仓合同的远端 done，required gates 全部保留。

## PRM 唯一交付责任

PRM 对负责 repo 内任意来源的**非 Draft PR**负责发现、去重接管、持续跟进 CI／review／审批、具体修复回派及正常交付。
直接交接是快捷入口，不是接管前提。Dev Team 绝不开 Draft PR（需要等待 Owner 时使用 `owner-review` 标签，绝不用 Draft）；
其他来源的 Draft 保留原作者和既有审批路径，不由 PRM 处理、派修或自动 Ready。
PRM 消费既有仓库 PR 单元及门禁，不新增 PR 大小／范围审查或额外审批层。

- **Dev Team PR**：PRM 全程负责直至合并，包括 CI、review、审批，以及沿原路径回派具体修复（TL 协调，原 FS 修复）；发生根本冲突时保留现场并交 TL 通知 Owner。回派时不重复启动活跃写者。
- **其他来源 PR**（CLI subagent、Owner、外部等）：PRM 跟进至合法合并，但不接管普通修复；不联系作者，也不通知 Owner。仅在无新 push 满 **5 分钟** 且属于明确小问题（clear small issue）时，交 Dev Team 在同分支修复；具体范围、不做项及第三方 fork 例外见 [`dev-team-pr-manager`](dev-team-roles/dev-team-pr-manager/SKILL.md)，不在此重复规定。其他问题记录于回执后等待作者推送。
- **根本冲突**：非 Dev Team PR 的根本冲突就地记录并保留，不联系作者、不通知 Owner、不打标签或执行特殊处置流；git merge conflict / base lag 与根本冲突区分处理，按角色规定推进。
- 正常等 CI／review／审批不是故障；回派接收未知先对账，不重复启动写者。新 head 使用新证据，已有准确批准不重索。
  合并须真实回读；CI 绿、已派修或 run completed 不等于合并。

### Dev Team Flow Supervisor

既有 Multica Autopilot 定时触发时，只检查 Dev Team 当前 workflow 是否真中断：已具备下一步条件而原责任 agent
未继续，才沿合法入口唤醒该责任方。正常运行、等待 CI／review／批准及人工暂停不因时间经过变为中断。
状态未知先只读对账；核实实际接收后结束本次唤醒，未恢复则报告证据与阻塞。

此角色不做 PR 发现／修复判断／交付，不代替 TL／FS／PRM、不重规划／改派／关闭／合并，也不接管 subagent 主会话。
唤醒不清零失败历史，不授权修 daemon、runner 或凭据；部署名称、Autopilot 绑定和实际接收能力须另行核实。
[`multica-delivery-supervisor`](multica-delivery-supervisor/SKILL.md) 是不同的会话级辅助，没有因此获得后台唤醒或团队职责。

## 实现修复与升级

审查范围、范围外发现及两轮上限统一按[执行合同 V1–V4](execution-contract.md#限定审查)，交回定义方处理。
需要 Owner 决定时通过 [Owner 决策入口](../repo/owner-decision-loop/SKILL.md) 报告版本、未满足要求、尝试及结果、已知／未知与建议；明确安全／权限硬阻塞立即报告。

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

普通 PR 沿现有 fail-closed required CI／review gates 和正常 auto-merge；重要政策、gate、隐私、凭据、迁移、pin 等
仍需适用 Owner 准确 head 审批。普通测试修改保留理由及正常审查，不因测试改动单独索批，也不豁免实际 policy 变更。
新 head 重新核证据，绝不弱化 gates／保护来交付；缺失有效保护记录为缺口，不据此跳过必要审批。

## 交接最小字段

复用 issue、PR 模板或 subagent prompt：target（repo/base）、intent（目标／验收／不做项）、baseline（固定方案及执行授权）、
scope（仓 PR 单元／任务）、owner（唯一执行者与来源）、evidence（PR/head、验证／审查／批准）、next（下一责任／唤醒条件或 HOLD）。
这不是新 schema。发送≠接受，run completed≠交付，merge≠发布／消费；整体验收按原目标逐项取证。
