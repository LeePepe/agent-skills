# Workflow：六个工作流

快速导航：[公共执行契约](execution-contract.md) · [Multica Dev Team 角色源码](dev-team-roles/README.md) ·
[显式团队入口 teamwork](../repo/teamwork/SKILL.md) · [本仓可注册技能与安装](../../README.md)。

本索引定义编排入口和交接边界。W0 是六个 workflow 的总图，不是主 agent、主管会话或第七个 workflow。
repo 内的执行者仍从目标仓 `AGENTS.md` 读取 guide 和固定版本 shared 合同，遵守原 hooks、review 和 required CI。
本索引不覆盖已采用的固定合同，不证明角色、定时触发或消费者已经部署。

与 CLI 沟通开发需求、直接执行或委派 subagent 时，必须遵守同一份
[`CLI 与 subagent 执行规范`](execution-contract.md)：Goal → Target → Task、计划基线、target 集中独立验收与复审。
显式 Dev Team 同样引用它；个人全局入口的安装见[仓库说明](../../README.md#cli-默认规范)。

| Workflow | 开始与工作 | 输出与现有入口 |
|---|---|---|
| 01 需求沟通与规划 | 输入原始请求、已有决定和当前事实／artifact；负责该项的规划者或获相应宽范围的原实现者补齐未定框架，协调者负责分配、路由决定 | 输出调查判断，或固定版本的 Goal／Targets／Tasks、验收、权限、依赖、唯一实现者与验证方案；保留已有讨论决定；跨仓协调入口为 [`orchestrate`](orchestrate/SKILL.md) |
| 02 实现 | 输入已受审且获准执行的固定基线、已满足依赖及 assignment；Task-only FS 只连续执行所分配 Task 集，父 Goal／Target 是约束及上下文 | 普通 CLI／subagent、显式 [`teamwork`](../repo/teamwork/SKILL.md) 或已选 Multica 的 [`multica-issue`](../repo/multica-issue/SKILL.md)；输出适用 PR、准确 head、验证／审查证据、限制与下一责任；后续交 03 |
| 03 PR 接管与交付 | PRM 发现或收到负责 repo 内任意来源的非 Draft PR | 跟进 CI／review／审批、回派具体修复，直至合法合并或准确授权处置；辅助诊断用 [`layered-ci-autofix`](../repo/layered-ci-autofix/SKILL.md) |
| 04 自动化发布 | 非破坏性 SDK／内部 TestFlight 的实际发布内容合入且必要检查通过 | 对应内容正确发布；现有 SDK 产物辅助为 [`shared-release`](shared-release/SKILL.md)，新 Actions 接线有下述版本依赖 |
| 05 产品遥测分析 | 优先交付 pageview／pageaction、PLT 等基础收集：产品→Azure L0→aidata 整理可查询 | 收集链路与分析分别验收；分析只由 workflow skill 独立手动触发，当前目录尚无已交付分析入口 |
| 06 周期维护（启用 HOLD） | 未来由本仓既有 Codex runner 独立只读核对计划范围内公开仓的当前文档和相关代码 | [`periodic-maintenance`](periodic-maintenance/SKILL.md) 提供未启用规则、离线适配器和模板；普通 backlog／待澄清草稿，不修复、派开发或追修 |

需求→实现→非 Draft PR 交付→适用发布；遥测／维护发现回到同一个需求入口，不要求每次任务走遍六个节点。
框架拆分属于 01，可由 assignment 允许的原实现者补缺；repo-local 开发与所选执行方式属于 02。恢复、必要 Owner 沟通和仓规则内嵌各 workflow，
分别复用 [`runtime-recovery`](runtime-recovery/SKILL.md)、[`owner-decision-loop`](../repo/owner-decision-loop/SKILL.md)
和目标仓合同；它们不是额外节点。AIDash 是 repo 和预留展示平台，展示／采集 UI 不由本索引实现。

历史 W0–W7 仅用于追溯：旧 W1→01，W2/W3→02，W4→03，W5→04 的 SDK 辅助；W6/W7 是横切辅助。
旧 `orchestrate` 仍是跨仓执行入口，不再定义 W0。已交接的旧版本保持稳定，新增规则按明确后续切片采用。

## 聊天准入与执行版本

01 接收原始请求、已有决定、事实与现有方案，由负责该项的规划者或获相应宽范围的原实现者判断并补缺；协调者不代写方案。
Task-only 调用只细化所分配 Tasks 的实现／验证步骤，不重新定义父 Goal／Target。
研究、数仓蓝图或视觉设计按下方地图解决具体内容缺口，不因调用专业 skill 改变流程角色。

| 输入情况 | 当次下一动作与输出 |
|---|---|
| 反馈、诊断或方案讨论 | 相应 worker 查证并返回判断、证据与剩余未知；不自动实施或派发 |
| 明确且范围清楚的修复／实现 | 复用已有实施意图与仓库规则，形成必要的范围、验收与验证依据；不重复询问同一授权 |
| 定义真正尚缺，或只有部分讨论结论 | 宽范围实现者可在 assignment 内补缺；固定已定部分，不因 artifact／审查未完成重选。Task-only 遇到父级缺口回原调用者；讨论本身不新增执行授权 |
| 已有受审方案／在途实现 | 校验准确版本和适用范围，复用原 owner；只补缺口，不重做同内容规划或启动第二写者 |
| 新目标、实质方案或权限变化 | 交原决定入口处理受影响部分；单项设计意见、skill 可用或 agent 已绑定不等于整版获准实施 |

普通产品任务沿既有 Dev Team 默认值，明确选择 CLI／subagent 或同步团队时尊重该选择。
重复反馈先按 [Multica 问题历史](../repo/multica-issue/references/problem-history.md) 核对范围、版本与效果证据，
不凭标题重派；接收未知先对账，保留固定基线与原执行方。授权、发现分流及原责任规则统一见
[公共合同](execution-contract.md#plan-与执行基线)。

**01 → 02 交接**：明确的执行意图、适用的独立计划审查、执行者可读取的固定基线和已满足的依赖同时具备，
才由原实现者继续。有效决定直接复用；视觉方向批准和实施授权分别识别，不重复索取已覆盖的批准。

## Plan 与依赖推进

负责定义的规划者或获相应宽范围的原实现者输出固定 Goal／Targets／Tasks、验收映射、责任、真实依赖、权限与验证方案；仓库原生 plan／issue 或
Spec Kit 产物均可承载，遵守该仓实际要求。跨仓框架保留已有决定，团队 Planner 复用、校验并补齐实际缺口，不要求重做已定内容。
按[公共合同](execution-contract.md#plan-与执行基线)区分受审基线与执行台账；长期政策引用 repo guide／固定 shared 版本。
一个跨层 target 可含多个内部 task；issue 按受审 target／仓库交付单元映射，task 不自动建票、拆 PR 或增加审查轮次。

Dev Team 由 TL 按 plan 推进；subagent 由既有主会话按 plan 接续。独立且已授权工作可继续，局部阻塞不能隐藏整体未完成。
provider source、发布、消费者升级／真实消费分别取证；04 不负责消费者升级，不取消原任务的消费／回滚义务。

## Skill 参与地图与来源边界

下表覆盖已盘点的各组入口，按用途选择能力；没有要求每次调用全部 skill 或经过同一角色链。
专业能力只在当次 assignment 内工作，不授予协调、实现、部署或独立验收权限。

| 分组 | 名称、参与条件与输出 |
|---|---|
| 01／02 入口 | [`orchestrate`](orchestrate/SKILL.md) 跨仓协调；[`multica-issue`](../repo/multica-issue/SKILL.md) 已授权的 Multica 交接；[`teamwork`](../repo/teamwork/SKILL.md) 显式同步团队实现。三者不互相替代 |
| 01 专业产物 | [`deep-research`](../research/deep-research/SKILL.md) 提供研究证据；[`layered-data-warehouse`](../repo/layered-data-warehouse/SKILL.md) 提供数仓蓝图；[`my-designer`](../design/my-designer/SKILL.md)、[`visual-design-modernization`](../design/visual-design-modernization/SKILL.md) 按项目／视觉需求形成设计产物并支持后续实现。产物本身不启动生产修改 |
| 02 工程能力 | [`repo-kit`](../repo/repo-kit/SKILL.md) 用于明确的仓库接入／升级／拆库任务；[`xcode-cli`](../repo/xcode-cli/SKILL.md) 用于 Apple 构建验证；[`code-review`](../repo/code-review/SKILL.md) 用于适用的内容审查。不接管 Goal |
| 横切辅助 | [`owner-decision-loop`](../repo/owner-decision-loop/SKILL.md)、[`runtime-recovery`](runtime-recovery/SKILL.md)、[`multica-delivery-supervisor`](multica-delivery-supervisor/SKILL.md) 处理原流程内的决定、恢复或监督，不增加实施权限 |
| 其他 workflow／专项任务 | [`layered-ci-autofix`](../repo/layered-ci-autofix/SKILL.md) 为 03 修复辅助；[`auto-review-merge`](../repo/auto-review-merge/SKILL.md) 用于明确的自动审查／合并接线任务；[`shared-release`](shared-release/SKILL.md) 属于 04；[`periodic-maintenance`](periodic-maintenance/SKILL.md) 属于 06，启用 HOLD 保留；[`team-workflow-audit`](team-workflow-audit/SKILL.md) 仅用于明确请求的审计 |
| 独立用途 | [`save-tool`](../meta/save-tool/SKILL.md) 收藏记录，不安装或实施 |
| 七项角色源码 | [角色索引](dev-team-roles/README.md)：`dev-team-squad` 团队规则；`dev-team-team-lead` 协调；`dev-team-planner` 规划；`dev-team-fullstack-engineer` 实现；`dev-team-ai-reviewer` 方案及 pre-push spec／architecture；`dev-team-pr-manager` 03 交付；`dev-team-flow-supervisor` 中断检查。不是七个本机注册入口 |
| Multica 规划 helpers | `codebase-design`、`domain-modeling`、`speckit`、`to-tickets` 按缺口使用；不重建已有产物，不由 helper 强制拆票 |
| Multica 实现 helpers | `fs-codebase-design`、`fs-diagnosing-bugs`、`fs-tdd`、`helix`，以及同名 `xcode-cli`、`code-review`，按实现范围、仓库规则与实际可用性使用 |
| Multica 审查／完成辅助 | `review-agent`、`Verification Before Completion`、同名 `owner-decision-loop`；绑定不等于每次必须调用，不扩大所属角色职责 |
| Multica 其余库存 | `daily-digest` 用于独立日总结；`review-code-quality`、`review-doc-sync`、`review-privacy`、`review-security` 保留库存记录，不据名称或空内容宣布弃用或强制接入 |
| 私有／旧个人入口 | `postmortem` 为专项复盘；`layered-agent-context` 是已由 `repo-kit` 替代的旧入口。保留历史，不删除或迁移 |
| System 能力 | `imagegen`、`openai-docs`、`review-agent`、`skill-creator`、`skill-installer` 由 provider 管理，按需使用，不复制其规则 |
| 插件能力 | `visualize`、`documents`、`pdf`、`presentations`、`spreadsheets`、`excel-live-control`、`template-creator` 按产物／工具场景参与，也可独立使用 |
| 已见 Claude 同步项 | `morning`、`deep-research`、`xlsx`、`pdf`、`import-memory`、`docs`、`skill-creator`、`pptx`、`google-workspace`、`chrome-browser`、`built-in-browser`、`computer-use`、`docx`：按描述用于研究、文档、浏览／操作或独立工具；同名项保留来源变体，不未经证据合并 |

权威源码为 `skills/<category>/<name>/SKILL.md`；公共政策在 [execution-contract.md](execution-contract.md)，
团队特有职责在角色源码。本表只是阶段路由。客户端软链是安装指针，按实际目标区分版本；provider／插件／同步内容由各自来源维护。
Multica 安装来源、内容版本和实际绑定须分别回读，参见[只读查询指引](dev-team-roles/README.md#只读核对运行端)；
本地源码、同名描述或绑定存在都不能证明当前会话已加载候选内容。私有回执、旧部署副本与 dated reviews 只在原时间／版本范围内作历史证据。

## 仓库先定义，角色再执行

layer 与 PR 单元属于目标仓 guide 和固定版本 `shared-ci/ai/repo-contract.md`，搭建辅助为
[`repo-kit`](../repo/repo-kit/SKILL.md)。按单一可观察目标、实际接口和依赖组织，不按 layer 数、行数或文件数硬切。
AGENTS 保持目录，合同缺失或矛盾记录为前置缺口，不由角色临时创造豁免。

### 实现职责与当次输出

02 的原实现 worker 接收固定基线和验收映射；宽范围 assignment 可补齐未定定义，Task-only FS 仅细化并连续完成已派 Tasks 的实现、验证与修复。
父 Goal／Target 保留为约束及上下文，不授予重选目标、调度同级或承接未派工作的权限。部分 Tasks 完成须记录剩余覆盖，不宣称完整 Target 就绪。
同一 FS 保持唯一写者，不逐 Task 换人、回协调者或启动完整审查；既定审查请求、修复返回及 PRM 交接继续有效。
调用专业能力只解决当前缺口，独立验收仍由既有 reviewer 负责，依[角色／来源绑定](execution-contract.md#角色与调用来源)执行。

| 所选方式 | 参与与交接 |
|---|---|
| 普通 CLI／subagent | 按公共合同完成 assignment 内的工作；Task-only 仅返回已派 Tasks 及剩余覆盖，完整 target 按既定就绪条件交独立验收；不额外套团队角色关口 |
| 显式同步团队 | 使用 [`teamwork`](../repo/teamwork/SKILL.md) 的团队适配器及其角色来源，不替代仓库合同 |
| 明确选定 Multica | [`multica-issue`](../repo/multica-issue/SKILL.md) 桥接固定 target 与授权；团队按[角色索引](dev-team-roles/README.md)推进，接收、run 结果和交付分别取证 |

实现者自检不默认另起全量独立 reviewer，也不替代仓库必需审查。团队 AI Reviewer 的方案／pre-push spec 与 architecture 职责见
[`dev-team-ai-reviewer`](dev-team-roles/dev-team-ai-reviewer/SKILL.md)；PR-head defects／standards 由既有 `codex-review-target` 负责。
角色绑定某个专业 skill 不扩大职责；团队限制不构成其他路径的通用免审。独立验收与修复收敛沿[公共合同](execution-contract.md#独立验收与复审)。

**当次输出**：适用的 PR 成功创建／更新后，回报 PR URL、准确 head、验证／审查证据、限制和下一责任；没有所需 PR 时不得以 push 或 run completed 冒充成功。
执行者可留下修复后续失败，也可交接离场，03 PRM 兜底；本次输出与最终合并、发布、真实消费分别取证，required gates 保留。

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

同一根问题两轮完整修复／验证／复查无实质进展：TL／既有主会话把诊断交原 Planner 或实现 worker，监督下一动作；原执行者仍负责修复。
仍无解通过 [Owner 决策入口](../repo/owner-decision-loop/SKILL.md) 报告任务／版本、未满足要求、尝试及结果、已知／未知与建议。
task/run/SHA 变化不清零，单纯等待不计一轮；明确安全／权限硬阻塞立即报告，不凑次数。

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
- **Skill 管理后续**：按名称选择安装、弃用 skill 处理与同步内容治理保留为后续能力；本轮仅补导航与对齐既有安装指针，不实施这些能力。

## 合并规则（按目标仓实际保护）

普通 PR 沿现有 fail-closed required CI／review gates 和正常 auto-merge；重要政策、gate、隐私、凭据、迁移、pin 等
仍需适用 Owner 准确 head 审批。普通测试修改保留理由及正常审查，不因测试改动单独索批，也不豁免实际 policy 变更。
新 head 重新核证据，绝不弱化 gates／保护来交付；缺失有效保护记录为缺口，不据此跳过必要审批。

## 交接最小字段

复用 issue、PR 模板或 subagent prompt：target（repo/base）、intent（目标／验收／不做项）、baseline（固定方案及执行授权）、
scope（仓 PR 单元／获分配 Task 集）、owner（唯一执行者与来源）、evidence（PR/head、验证／审查／批准）、next（下一责任／唤醒条件或 HOLD）。
父 Goal／Target 约束放在现有 intent／baseline，执行边界放在 scope；显式带角色／调用来源及父级绑定、允许操作、返回对象和 helper 权限。
宽范围输入保留原始需求与已有决定，只补未定定义；Task-only 父级信息不授予管理权限，helper 权限不含同级派发。
绑定或执行边界缺失／冲突时回原调用者指出具体缺口，暂停依赖动作，不自行升级角色。
这不是新 schema。发送≠接受，run completed≠交付，merge≠发布／消费；整体验收按原目标逐项取证。
