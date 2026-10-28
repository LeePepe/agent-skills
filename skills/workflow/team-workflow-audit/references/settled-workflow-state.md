# 三项目最终 workflow 决定与证据

观察截止：2026-09-21 PR交付续接（主机已加载，三项required Codex PASS，PR51/209/438已合并；精确终态及核验来源见[17]，其余条目保留各自观察日期）。仅适用于本次 AIDash、VoxPocket、VitalStride 讨论；不是其他团队的通用模型或角色配置。本表是审计参考，不授权修改配置、派发、重试、合并或发布。“已部署”指下列回执当时的写入/回读，不代表本次重新全量核验线上，也不代表在途进程已热更新。

## 最终流程与角色边界

- **A：实现并发起PR。** Dev Team、直接执行agent或其他开发者均可作为来源；不强制先经Codex整理或预建issue-tracker item。以下内部先审后发布协议适用于Dev Team FS，不把直接作者伪装成FS/TL来源。
- **Dev Team A段：** 保留必要的Planner规划路径 → FS准备/复用工作区、实现与自审 → 固定未提交Git tree → 内部AI Reviewer明确允许发布 → FS commit/push/创建或更新PR。Planner并非每任务必跑；原有规划门槛和no-code验收不增加、不豁免。
- **B：PR后统一交付。** Dev Team FS 创建或更新非 Draft PR 后交 TL，TL 立即派 PRM接管跟踪 → GitHub Actions独立审查与required CI → 交唯一实现者修复 → 新候选与复验 → 合并 → 按项目获授权发布 → 实际使用/效果验收与反馈。Adopt不等于Ship；红门禁不构成拒绝接管的理由；必须有 Dev Team Target issue 的 FS 交接或 delivery 信息，不按作者身份区分，其他 PR 由各自写者交付。
- PRM持有 TL 派发的 Dev Team PR 交付推进责任，不改代码/配置；TL持有实现侧监督、恢复与范围判断责任；FS/唯一实现者修复。the control plane原生Autopilot对 PR 只跟进已有 Dev Team 交接，不发现新 PR，不成为第二套开发团队。
- AIDash既是普通受管App，也是状态、证据及Owner反馈界面，不是自动修复者。Dev Team保持同一物理daemon，保留provider/runtime分工；仅FS模型按下表明确授权变更。各项目保留自己的门禁和发布方式。

## 最终改动与落地状态

| 项 | 最终改动 / 责任落点 | 已有证据与不能推出的结论 |
|---|---|---|
| 1：首次准备 | 首次工作区准备由FS执行；TL不再为准备额外运行一个TL。准备条件集中于workspace协议，角色使用条件指针；保留Planner先行、既有工作区复用和半成品恢复。 | 9/18配置部署与独立回读、17项静态断言。[1] 未启动业务验收；没有因此修复跨issue授权来源。 |
| 2：FS模型 | 共享FS角色设为`gemini-3.7-flash`，`custom_args=["--context","long_context"]`；不硬写窗口上限，不改provider/runtime/daemon或其他角色模型。 | 9/18会话目录声明总窗口1M/输入936K，配置独立回读。[2] 无新业务进程argv验收，不声称旧在途任务已切换；Owner仅同意本轮先视第2项完成，未证明收尾问题已解决；结束hook未安装。 |
| 3：PRM入口 | 三项目保留提前Adopt、由 TL 按 Dev Team Target issue 的 FS 交接或 delivery 信息立即派发，不以内部PASS作为接管前提；B段消费required `codex-review-target`与optional `kimi-review`，不再向Dev Team内部Reviewer补派PR后审查。 | 9/18纠正部署与独立回读、静态/保护测试。[3] Claude/legacy Codex暂停未恢复；缺乏自动唤醒接线不能由入口合同代替。 |
| 3补充：发布许可 | 内部Reviewer输出绑定候选的`publication_status=approved|blocked`及`allowed_operations`；正常新候选获准后FS才能commit/push/PR。TL与PRM承认合法待审、获批待发布状态。 | 9/19六字段部署回读、49项静态检查与21个原生Git隔离用例。[4] 不是已安装的Git/runtime硬阻断，也不等于真实Dev Team业务闭环已通过。 |
| 4：Actions误判 | AIDash/VoxPocket把Codex主prompt抽为Markdown并用单次非执行性渲染；AIDash安全段独立Markdown、原Swift证据helper保留。VitalStride沿用原模板/renderer，纠正未来规范与当前审查操纵的判据。没有AGENTS白名单；实质泄密/提权/绕门禁仍阻塞。 | 15次无工具隔离模型评测；AIDash#208（<owner>/AIDash#208）、VoxPocket#47（<owner>/VoxPocket#47）、VitalStride#436（<owner>/VitalStride#436）均经实际Actions审查、required CI正常合并，merge tree匹配批准候选。[5] 新的可信base会读新规则；未重放历史身份PR。 |
| 4附带授权：文档结构 | VoxPocket AGENTS由159→130行，完整身份段逐字移到`docs/agents/github-identity.md`，根文件保留所有Git/gh操作前的必读指针；140行门槛未改。 | 单独Owner授权、原块字节一致、原docs-map/freshness通过并随#47合并。[5] 不是删除身份要求、放宽门禁或修复共享local-review。 |
| 5：Supervisor交接接续 | 仅修改现有Supervisor.instructions中三项目分支，按下节收窄为交接连续性监督；其他项目原规则保留。 | 9/19 12:54Z委派单字段更新，1次写入/1次确认；12:55Z Root独立回读一致，其他角色/模型/权限/Autopilot/schedule配置不变。85项结构、35项部署保护检查；17个隔离模型案例精确9/17，其余8项独立语义复核允许，原始结果保留。[7] 未启动业务验收，不声称热加载、runtime硬门或Owner介入已减少。 |

## 第6项：VitalStride测试同步（9/20 PR437正常合入）

Owner授权单独修复后，仅修改AppUI的Controller和对应测试：默认生产事件仍走.shared，测试注入独立TelemetryService，actor记录器按目标事件实际收到结束等待，保留超时诊断与取消；新增延迟投递和另一控制器同名事件不能补足本夹具缺失事件的回归。没有扩大到TelemetryKit API、CI门禁或共享instructions。[9]

真实Controller/TelemetryKit的受控延迟复现中，旧100ms断言失败而同一事件随后收到；本地隔离5例、原生iOS定向11例及完整App测试1296项均通过，保留CI原有隔离项；退回固定sleep或共享fixture的两个负向变异均失败。独立内容复核无阻断。Owner后续明确授权交付，提交`14b2649`经PR437（<owner>/VitalStride#437）的9项required checks、Codex required与Kimi advisory实际PASS，03:19:36Z原生自动合并`db930310bec7897cfe4375f5780c5d472a6caa2f`；merge tree与批准候选完全一致。CI第1次运行通过，无追加修复/手动rerun。仅证明本次直接执行修复的PR交付，不证明PRM自动接管、Dev Team真实业务闭环或Owner介入指标改善；未发布。完整结果、advisory、范围外runtime警告与环境限制以[9]为准。

9/21历史观察：telemetry-event-sync工作区此前已不存在/未注册，当时本地分支及github跟踪ref均指向`14b264962c60242a18249d25a2c1597951255946`，不归因于后续清理。Owner随后明确“删除即可”，委派于2026-09-21T02:34:43Z按该精确OID删除本地/GitHub `fix/telemetry-call-site-sync`及本地github跟踪ref。Root独立确认远端matching-refs为空、本地仅移除这两个ref且无新增、bundle verify通过。PR437修复仍在main，原commit对象及已验证的增量`telemetry-branch-backup.bundle`保留，可按清理回执与恢复说明（本地审计记录，未公开：`workflow-audit-output/20260920/item6-telemetry-sync/telemetry-branch-cleanup.md`）恢复；未删除或重建原工作区。

## 补充决定：废弃VoxPocket旧local reviewer（9/20环境阻断；9/21 PR51正常合入，限定范围安装清理已验收）

Owner确认旧`local-review-skill`应废弃，不继续修补假PASS；后续明确“架构检查先不改，只清退local review的AI reviewer”。委派候选删除旧AI配置、meta-agent定义/注册、merge AI hook/wrapper和当前安装说明；pre-commit/pre-push直接接回既有确定性门禁，保留内部AI Reviewer及Actions审查。固定提交`60b10f7cfb2b25b65b22c6313e44c600f91e2b90`经Root独立17/17复验及原生pre-push，已由执行agent推送并于08:29:51Z创建PR51（<owner>/VoxPocket#51）。原工作流08:30:00Z启用squash auto-merge。**9/20当时已push/建PR、未合并；主checkout及共享安装未切换。**

9/20旧head的7项确定性required CI全部通过；Kimi advisory PASS，但其diff截断、覆盖不完整，不能替代required审查。Codex required run `35499714106` attempt 1在内容审查前失败：`Runner is missing Raven environment variable OPENAI_API_KEY; no direct fallback`。Root独立回读日志、bot comment和runner元数据，目标为`macmini-local`（ID21）。这是runner环境缺口，不是清退代码finding；未修改候选、未rerun、未合并。当时需Owner使现有Raven凭据进入runner服务环境并操作必要重启；此历史边界已由9/21“你来运行”的一次性精确授权及完成记录接续，见下节。保留累计预算与失败记录，不重复询问已确定的清退目标。[13][15]

9/20后续接入实施时回读：主VoxPocket checkout已在`main/3edf880`，三个旧hook仍消费共享skill及公共`local-review.skill-path`/`local-review.version`；保留既有未跟踪`docs/research/`及`core.hooksPath=.githooks`。此前`b85f163`是较早观察。当时共享目录与废弃metadata保留；旧工作区删除不能证明保留checkout已无依赖。9/21新head `d299c8cd87bca88558531429d947c1b8fdd498bb`的8项required全部PASS，PR51于02:11:15Z正常合并`5d2ab2fafc453017f909dc289b81aead73c83918`，Root核验merge tree等于批准候选。retirement worker报告main/config/archive执行与自检完成（main快进5d2ab2f、两废弃config移除、完整旧安装INACTIVE归档、确定性hooks保留），Root已独立验收限定三个repo/已知discovery范围的安装清理[18]，不宣称全机卸载；安装清理、真实交付及业务闭环分别验收。[10][14][17]

## 后续授权：三项目Raven Actions接入与构建skill（9/20；9/21主机执行完成）

Owner明确要求修改AIDash/VoxPocket/VitalStride接入、同步layered-agent-context并监督PR到merge；架构checker、角色/模型参数、required/advisory、NAS/schedule/发布暂停边界不改。执行agent分别实现，Root独立复核。[14]

- **skill已交付**：Skills PR2（<owner>/Skills#2） 于14:06:02Z正常合并`3765dd0`，批准tree与merge tree完全一致，PR及合并后CI通过。新增provider服务环境/凭据分层/可信base bootstrap及证据验收约定；当前canonical文件已增量同步，保留本地身份规则及未发布提交，不将原dirty main混推。
- **真实PR交付**：三个批准head均已发布，required Codex均attempt1 PASS且有意消费OLD可信base。Root独立核验VoxPocket PR51的8项required全PASS、02:11:15Z合并`5d2ab2f`；AIDash PR209的3项required全PASS、02:13:38Z合并`30092ed`，两merge tree均等于批准候选。VitalStride PR438于02:26:17Z原生auto-squash合并`6ad3e994cf963b5777663c9a7a87d1fa25219fdb`、9项required全PASS、CI attempt1成功；文档worker API确认merge tree等于批准候选`845370e7ca4aa740bbbdac1b323c773b0569922c`，Root另已独立核验全部三个PR的merge tree、合并actor及required checks[18]。完整SHA/base/run/job/时间/tree以[17]为准，不借旧head检查放行。
- **主机已安装并加载**：9/20工具经Root独立35例及只读dry-run批准、当时限Owner执行的记录保留[16]。9/21 Owner明确“你来运行”，一次性授权已审定的现有key接线和三个idle runner精确重载；执行完成，不再等待Owner向导。plan `d9314f1573a4758c2abcae8469c870c8f137fc578d66c6c93100bef1ea924e33`；manifest `<本机路径，未公开>`为installed。Root独立核验五个目标hash/mode、三plist全部非ProgramArguments属性及原review-source hash未变、loaded wrapper和service PID13034/13801/14371（VoxPocket/AIDash/VitalStride），GitHub均online/idle。专用review home与key仅供三个runner及其子job，非step级隔离；旧共享profile只读、不复制auth/cache。[14][15]
- **加载恢复与权限**：VoxPocket立即bootstrap的error5源于旧服务异步teardown尚未完成；确认移除/idle后一次定向bootstrap重试成功，另两服务等待teardown后首次成功。这不是Actions rerun；无扩大服务范围或应用rollback。Root未读取凭据正文或dump进程环境。未来凭据轮换/服务操作仍归Owner，除非另有明确授权。[15]
- **证据分层与advisory**：主机smoke、installed文件、loaded wrapper/PID与online/idle不替代实际Actions审查；本轮三项required Codex已有真实PASS。VoxPocket Kimi PASS仍为截断覆盖；AIDash malformed-TOML/诊断建议及VitalStride PATH/UTF8建议非阻断，不另开修复PR。保留PR51旧head环境失败35499714106，本轮0实现修复、0 Actions rerun、无手动/admin merge。新合并helper源码的实际review消费等待后续自然PR，不造验证PR/事件；不宣称业务效果。[17]

精确提交、工作区、测试、主机执行及Root独立核验摘要、接续顺序统一见[14]；[16]为9/20历史批准，不是当前待执行指令。无需重新确认已确定的目标/角色/provider/交付权限。本次未做App发布或统一业务验收。

### NAS清理独立验收（9/20续接）

执行agent于07:40:56Z完成两处已授权NAS linked worktree的原生无force移除；Root独立确认目录和注册消失、两仓库全部refs不变，主仓库、nas-sync、两个任务工作区及交接资料保留。VitalStride四份本地文件已备份并逐字节比对，原件另行移存，删除后校验再次通过；旧TestFlight补丁保留且未应用。这仅完成当时的工作区清理；9/20该快照中主VoxPocket仍依赖共享reviewer。9/21 PR51交付及安装清理续接另见[17]。未恢复PR事件、NAS部署、schedule或发布。回执及恢复说明见[11]，Root独立证据见[12]。

## 补充决定：VoxPocket本地审查走Raven（9/20 PR50正常合入）

9/19 Owner放弃云端runner方案，要求本地审查使用当前Codex CLI相同的Raven路由。日常配置与审查配置是两个入口；审计不能因终端Codex已走Raven就推断Actions也已接入。VoxPocket旧脚本自7/20就明确绕过Raven，#49两次25分钟取消的日志确认实际provider为OpenAI；不是第4项prompt整改改变了provider。[8]

候选仅为VoxPocket调用导入已有Raven连接参数，保留独立审查CODEX_HOME、安全隔离和原模型选择；不复制凭据、不改三项目共享profile，不顺带迁移AIDash/VitalStride或Dev Team。缺配置/环境明确失败，不回退直连。初始9项离线回归与一次实际CLI无工具Raven合成调用通过，提交`a9c3116`并创建PR #50（<owner>/VoxPocket#50）。9/19旧base审查25分钟超时的失败仍保留，不把隔离测试当成线上成功。[8]

9/20 Owner报告启VPN并明确授权单次重试，旧入口约55秒完成实际审查，发现env_key可误选GH_TOKEN。第1轮范围内修复将凭据名限制为既有OPENAI_API_KEY/RAVEN_API_KEY，并在读取前拒绝其他名称；新增负例先红后绿，最终11项路由测试及6项prompt测试通过，两路独立复审通过，提交`b85f163`。新候选的8项required checks及Codex/Kimi实际审查通过，**00:50:47Z原生自动合并，merge `3edf8805e9ee8bde3e2e8c1e5d8fb01667a89ae0`，tree与批准候选一致。** 前次超时、真实changes与后续PASS分别保留；跨run/SHA预算不重置，Owner授权的额外一次复验单独记账。[8]

迁移PR被旧入口阻断是当时观察，不是永久逻辑死锁；恢复原入口连接也是正常接续路径，本次无需修改共享profile。该Owner介入提供了网络环境变化，不只是催促；不能据此推断VPN是唯一根因或授权agent自行启VPN。PR50审查仍跑旧可信base，其合并当时新Raven入口真实Actions运行尚未验证。9/20后续PR51旧head消费新入口时因runner缺少OPENAI_API_KEY在setup失败，当时无成功内容审查证据[13]；9/21主机执行后的新head已有独立required Codex PASS并合并[17]，不得借用PR50旧入口PASS。 未重跑#49、未发布或制造业务验收任务；不把本次合并等同于Owner介入已减少，也未宣称修复25分钟失败回传与重试预算执行。[8]

## Supervisor的最终职责（第5项已配置上线）

Supervisor监督现有issue-tracker item / Dev Team交接连续性：交接证据是否存在、谁持有下一动作、是否缺少接续。实现内容是否正确、FS是否真正完成和逐条finding是否修好由执行者/Reviewer判断；Supervisor不看源码或diff、不重审、不裁定merge就绪或App效果。它可消费现有issue关联PR证据，不扩为独立全PR扫描器，也不要求直接作者补建issue。[7]

- **缺交接找发送者，已接收找责任角色。** 先补读触发/父线程与真实交接证据，再通过合法入口唤醒发送者补交接；已接受后由接收角色继续。责任或调用目标不明时找发送者/当前责任人/TL澄清，不自动向Owner索要权限，也不无条件rerun当前assignee。
- **合法等待不是停滞。** 固定候选已有对应运行中的内部Reviewer则等审；已获发布许可但未push由原FS发布；当前候选被Reviewer阻塞则回原实现/修订负责人。保留Planner先行与规划修订、FS准备、no-code/legacy及现有先审后发布协议；Supervisor不新增验收门。PRM接受交接后独立负责B段，Supervisor仅跟踪责任和活动，不给B段补派内部Reviewer。
- **先读完整证据，再形成动作。** 按触发、线程、候选代次/base/tree/SHA及真实author/run/交接元数据关联；增量时间窗只是发现游标，旧FAIL不能代替新候选结果，执行者自述不能代替跨角色接收。GET返回反证后废弃旧草稿，重建阶段、责任人、摘要与latch；不把依赖未读GET的写入预先批处理。
- **唤醒不创造权限。** 操作前确认预期接收者与真实invoke目标、在途活动和既有冷却；原5分钟同agent冷却不作为 TL 派 PRM 的静默门槛。保留人工暂停、相关Action、唯一实现者与跨run/SHA累计预算。实际denied才记录拒绝，保留caller/run/目标/操作/时间；不换actor、mention或assignment绕过。未知结果先只读核对。
- **Owner只接真实的人类决策或外部权限缺口。** 流程证据缺失先由发送者/当前责任人/TL补齐；真实拒绝与错误完成摘要分开处理。原人工升级去重latch保留，沉默或新一轮巡检不清零。终结结论消费责任角色按原合同给出的正式交接，不能用run completed、PR merged或执行者自述独立宣布完成；既有done/cancelled issue不重开。

这些是现有instructions的决策规则，不是新运行时状态机或硬门；本节也不授权审计skill执行上述动作。早先把“验证修复真正完成”交给Supervisor的提案已被此职责边界取代，历史错误摘要仍是审计观察，不能据此扩张Supervisor职权。[7]

## 发布许可的审计要点

固定候选包含base/tree/范围。内容、基线或范围变化使批准失效；hook若改内容，不得继续发布旧许可。FS从真实平台元数据核验Reviewer comment/run/author ID，不让Reviewer自证尚未生成的评论ID。推送绑定批准的固定commit OID和明确ref，不依赖可被hook移动的HEAD。内部批准不等于GitHub权限、CI通过或App发布许可。[4]

已有真实未push commit可按实际OID/tree/parent审查后复用；已有published-SHA的历史审查可按真实证据接续。新内容或新违规不能自称legacy以绕过新协议。PRM经 TL 派发可提前跟踪 Dev Team PR，但原实现者仍在实现/待审/修复/待发布/恢复时不得合并、清理或关闭；没有push不单独构成执行失败。[4]

## 保留的恢复、权限与发布边界

- Dev Team PR 由 TL 立即派 PRM，不设30分钟静默门槛；修复或 rerun 仍核对人工暂停、相关Actions和在途实现，保持唯一实现者。
- 同一问题最多2轮自动修复，同错最多2次rerun；平台尝试计入预算，换agent/run/SHA不清零。明确不可修立即升级；职责不等于当前调用者有invoke权限，不能换入口试探绕过真实拒绝。
- 需求限定修改范围，实际diff决定适用gate。不为过关顺带改架构、workflow或共享instructions；第四项文档调整有单独授权，不构成通用扩权。
- 保留独立审查、服务端required CI；Kimi不阻塞合并，但实际结果与失败尝试留存。Draft只跑基础CI，不做AI review、不自动Ready。
- 写入身份（2026-10-12 起取代旧做法）：agent 对仓库的写入一律使用运行环境提供的 agent GitHub App 身份，不使用 Owner 的个人账号；写入前核验身份、目标及权限，不因变量存在或来源未知反复问Owner。不启VPN；未来凭据变更/服务操作交Owner，除非另有明确授权；9/21精确host bootstrap与三runner重载的一次性授权已执行完毕。[15]
- 原生PR事件接续实施、NAS与新schedule继续暂停，不把它们作为其他改善前置；三个App的TestFlight仅经明确授权手动触发。合并不是发布，本次未发布。
- 不读取音频、参考文本、转写或凭据正文。Docker/Loki/Azure日志存储及已解决的TestFlight客户端显示问题不纳入本批。

## 未完成、撤回与效果边界

- 第5项规则已配置上线并独立回读，真实业务接续效果未验；第6项已由PR437正常合并，见上节及[9]，未发布或启动统一业务验收。MY-1555是依赖准备授权事故；run_only跨issue private-agent限制不据此改写成已证明的PR接管事故。[6][7]
- 已撤回“B段PRM派内部Reviewer补审”的方案；按第3项最终纠正及后续A段发布许可分别审计，不能复活旧接管规则。
- VoxPocket旧local-review漏派发嵌套commands、`codex -q`不兼容仍可能聚合PASS、按净工作树跳过push差异等历史缺陷不再走“修好继续用”路径；9/20 Owner选择废弃，清退提交`60b10f7`已进入PR51，历史runner环境阻断已由9/21主机执行接续，PR51新head已正常合并，安装清理已由worker报告完成，Root独立执行后验收已完成[18]，见上节及[10][13][14][17]。此前有效审查来自真实独立候选批准与Actions，不是该假PASS；配置存在、hook安装及exit0不能互相替代。[5]
- VitalStride #436首轮UI准备超时，同SHA只重跑1次后通过；失败保留，未改App/测试，也未因此修复第6项。中间日志缺匹配完成行不证明最后测试独占卡死，实际复验最终成功。[5]
- 真实业务任务仍由Owner在各项处理后提供统一验收。本次治理PR交付成功，不等于Dev Team配置已被真实任务消费、实际使用有效或Owner介入次数已下降；无基线不编造指标/总分。[6]

## 更新与证据索引

后续每项最终决定或整改落地，更新本表对应项的适用范围、最终规则、观察日期、部署/合并证据与未验边界。提案不写成已生效，撤回方案标明替代关系；案例细节保留在[Owner介入案例](owner-intervention-cases.md)与原始回执。更新记录不授权审计skill执行整改。

- [1] 本地审计记录（未公开）：`workflow-audit-output/20260918/fs-preparation-supervision-result.md`
- [2] 本地审计记录（未公开）：`workflow-audit-output/20260918/fs-gemini-model-change.md`
- [3] 本地审计记录（未公开）：`workflow-audit-output/20260918/item3-actions-review-correction-result.md`
- [4] 本地审计记录（未公开）：`workflow-audit-output/20260919/prepublish-review/supervision-result.md`
- [5] 本地审计记录（未公开）：`workflow-audit-output/20260919/item4-review-false-positive/delivery/status.md`
- [6] 本地审计记录（未公开）：`workflow-audit-output/20260918/workflow-remediation-progress.md`
- [7] 本地审计记录（未公开）：`workflow-audit-output/20260919/item5-supervisor/supervision-result.md`
- [8] 本地审计记录（未公开）：`workflow-audit-output/20260919/voxpocket-raven/status.md`
- [9] 本地审计记录（未公开）：`workflow-audit-output/20260920/item6-telemetry-sync/status.md`
- [10] 本地审计记录（未公开）：`workflow-audit-output/20260920/retire-local-reviewer/status.md`
- [11] 本地审计记录（未公开）：`workflow-audit-output/20260920/nas-worktree-cleanup/status.md`
- [12] 本地审计记录（未公开）：`workflow-audit-output/20260920/nas-worktree-cleanup/root-verification.md`
- [13] 本地审计记录（未公开）：`workflow-audit-output/20260920/retire-local-reviewer/delivery-root-verification.md`
- [14] 本地审计记录（未公开）：`workflow-audit-output/20260920/raven-actions-integration/supervision-status.md`
- [15] 本地审计记录（未公开）：`workflow-audit-output/20260920/raven-actions-integration/host-execution-result.md`
- [16] 本地审计记录（未公开）：`workflow-audit-output/20260920/raven-actions-integration/host-root-approval.md`
- [17] 本地审计记录（未公开）：`workflow-audit-output/20260920/raven-actions-integration/pr-supervision-result.md`
- [18] 本地审计记录（未公开）：`workflow-audit-output/20260920/raven-actions-integration/root-rollout-verification.md`