# Owner 反复介入：先定位断点，再提方案

观察截止：2026-09-20（补充VoxPocket Raven及MY-842历史放行案例，其余保留原观察日期）。用于审计诊断与证据判读，不授权执行整改、派发、重试、配置更新或发布。下方案例是历史观察，不代表今天复测；项目决定只适用于所列三个项目。

## 可复用的诊断方法

先还原整体链路，再定位具体中断：需求与已有授权 → 实现/内部审查/发布候选 → PR 接管 → Actions 审查与 CI → 唯一实现者修复 → 新候选复验 → 合并/项目发布/实际效果。按当时项目合同确定每段顺序与负责人，不能从角色名称推断同一份审查。

每案只记录足以判断下一动作的事实：

- Owner 已给的需求/权限；中断前最后真实产物；当时谁持有下一动作。
- 系统已读到的失败、暂停、待审或复验信号；具体拒收条件、状态失真或缺失的唤醒。
- Owner 哪次介入让流程继续，增加了新需求、新权限、新证据，还是只催促；无介入的后续路径若无证据，写未知。
- 归类为接续缺失、合同拒收/责任丢失、修复负责人缺失、恢复规则不当、误判/多余确认、证据未回传，或确需 Owner。可以多因，但各自要有证据。

提出改动前，把已证实的错误与待证因果分开。明确某次工具根本未调用，不能归因于它被权限拒绝；已有发布要求却未履行，不能用再加一次同样文字代替诊断。源码存在某个拒绝分支不证明线上就是该分支；保留部署版本/日志缺口。

Owner 只需提供超出现有授权的选择或外部操作。已有需求、权限与证据足够时，应由现有责任人继续判断；审计指出这一点，但不替执行者恢复。委派文件清单是子任务分工，不是 Owner 新设权限边界；协调者可在已授权范围内补读必要依赖。

## 案例与反例

| 历史案例 / 观察日期 | 已证实的具体问题 | 避免错误修法 / 保留边界 |
|---|---|---|
| MY-1555，9/17 调查；9/18 职责调整 | 所谓“子 TL”是同一 TL 在另一 issue 的第二次 run；当时 workspace 规则明确要求该准备 run。父子 issue 授权来源丢失是另一个断点。 | 可把准备交给现有 FS，保留 Planner 先行与工作区复用；不能宣称消除额外准备 run 已修复平台授权链。不是已证实的 Autopilot `run_only` PR 接管事故。[1][2] |
| MY-1539，9/17 调查 | 当时输入明确要求处理八条 findings、发布新 SHA 再审；只改一文件、跑检查即正常结束。压缩摘要沿用旧候选完成状态。 | 未证明压缩或模型是唯一原因；配置更换不是收尾缺陷修复实证。9/19 新发布顺序不倒推约束9/17事件。[3][7] |
| 模型目录核查，9/18 | 同 CLI 的全局 `models.list` 未列出模型，而 `/model` 与 session-aware `session.model.list` 列为 enabled 并提供 long-context 档位。 | 核对同一认证/集成/会话入口与原生参数；不能直接断言版本旧或账号无权限。目录能力、存储配置和实际进程生效分开，不固化某个模型为通用推荐。[4] |
| VoxPocket #43 接管，9/17 调查；9/18 扩展并纠正 | 旧 PRM 要求成熟的 FS/TL shipping handoff，与直接实现者的早期 PR 输入不符；该次只读核验本来要求回复后停止。 | Adopt≠Ship。不能把主动停止当漏唤醒；也不能为 B 段补审误派 Dev Team 内部 Reviewer。[5][6] |
| Dev Team 先审后发布，9/19 | Owner 新决定要求内部 Reviewer 对固定未提交候选明确允许发布；监督必须识别合法待审状态。 | 获批候选绑定 tree/base 与真实审查来源，内容变化重新审；“没 push”本身不等于失败。存储规则与离线 Git fixture不是运行时硬门或业务完成。[7] |
| AIDash #206/#207 与两项目对照，9/16–17 事件，9/19 核查 | required Actions Codex 将未来 agent 规范误作操纵当前 reviewer；VoxPocket #45、VitalStride #435 的同类身份文档当时 PASS。 | 不是所有 AGENTS 改动都会失败。将 prompt 移到 Markdown 只解决构造风险，仍需受众/行为判据与语义正反评测。[8] |
| MY-1539 Supervisor，9/17事件，9/19复核与职责收窄 | 取数窗口排除触发修复的FAIL；最后读到FAIL仍发布“修复完成”旧草稿并写入latch。parent rerun同时有真实permission denied。 | 错误完成摘要与真实拒绝分开；沿候选/触发线程读取交接证据，GET返回后重建阶段/责任人/摘要。历史精确拒绝分支仍缺证。早先“由Supervisor验证修复真正完成”的提案已被Owner收窄为交接连续性；不看代码判FS真假完成，缺交接找发送者、已接收找责任角色。9/19第5项单字段配置上线及独立回读完成，业务效果未验，最终规则见[状态表](settled-workflow-state.md)。[10][11] |

第5项交接接续规则已配置上线，真实业务验收未启动；第6项9/20已修复并经PR437独立审查、required CI正常合并，见[状态表](settled-workflow-state.md)。本参考不把配置写入当实际恢复成功，也不续接历史任务；本次直接执行交付不等于Dev Team统一业务验收。[9][11][13]

补充案例（MY-842，6/24引入，9/20核查）：测试同步缺陷由`22be6c4`引入，当时源码AGENTS及issue明确采用no-PR；现有GitHub PR门禁不能倒推为当时的放行者。两轮内部审查均未发现固定100ms等待/全局事件源风险，只指出其他业务finding及覆盖不足。第二轮仍为CHANGES REQUESTED，TL却按“two-review-round warning-only、无critical”交付`758356c`，并记录等价本地测试通过及因hook误判使用no-verify。后两项是回执，不是原始运行日志。区分三件事：潜伏测试竞速未被审查发现、普通调度下测试可能绿、另有已知finding被历史预算规则降级放行；不能声称该同步缺陷已被指出却忽略。当前两轮上限意味着停止并升级，不意味着两轮后自动批准。修复此测试不自动授权治理整改或重开旧issue。[13]

补充案例（VoxPocket #50，9/19–20）：旧审查入口超时阻断Raven迁移PR；9/20 Owner报告启VPN并明确授权一次复验，旧入口恢复并提出真实凭据选择finding。经第1轮范围内修复、新提交`b85f163`及真实复验后正常合并`3edf880`。这次Owner介入带来网络环境变化，不是纯催促；恢复旧入口也是正常交付路径，不应把“迁移依赖”包装为只能改共享profile或绕门禁。额外复验单独记授权与原失败，不清零累计预算；连接恢复、内容审查changes、修复后PASS、合并、新Raven入口实际运行分别判定。新入口真实Actions运行尚未验证，不能只凭合并宣布运行闭环成功。[12]

审计第4类审查误判时，进一步阅读[prompt构造安全与语义判据](prompt-safety-and-semantics.md)，核对正反例和本地评测、线上生效的证据边界。

## 三项目特定决定（不是通用角色重定义）

截至2026-09-19的最终决定、部署/合并证据与保留边界统一见[三项目最终workflow状态](settled-workflow-state.md)。其中已包含第1～4项、A段发布许可、FS模型最终配置、第四项三个PR合并结果及第5项已批准的职责收窄；本页保留历史案例，不再复制一套可能漂移的当前合同。只对指定三项目覆盖旧例，历史事件按当时有效规则判断。

## 验收证据层级

分别记载：历史报告 → 当前源码能力 → 隔离结构/行为测试 → 线上配置回读 → 新运行实际消费配置 → 新候选与复验 → 发布与实际效果。每项带观察日期、候选/事件身份、证据来源；前一层不替代后一层，`run completed`、`issue done` 或 `PR merged` 都不能单独证明目标完成。

关注 Owner 追问次数、无必要确认次数、无人负责停滞、恢复是否到新候选与复验、结果是否主动回传。没有基线或完整事件覆盖就标缺证，不编总分或宣称提升。第2项虽按 Owner 决定“本轮先视为完成”，实际质量改善仍待验。[9]

## 定向证据索引

以下为个人工作区的历史原件；文件不可用时保留缺证，不把本参考当线上现状证明：

- [1] 本地审计记录（未公开）：`workflow-audit-output/20260917/cause-investigation/conclusions.md`
- [2] 本地审计记录（未公开）：`workflow-audit-output/20260918/fs-preparation-supervision-result.md`
- [3] 本地审计记录（未公开）：`workflow-audit-output/20260917/case-causes/02-execution-finish.md`
- [4] 本地审计记录（未公开）：`workflow-audit-output/20260918/fs-gemini-model-change.md`
- [5] 本地审计记录（未公开）：`workflow-audit-output/20260917/cause-investigation/03-pr-intake.md`
- [6] 本地审计记录（未公开）：`workflow-audit-output/20260918/item3-actions-review-correction-result.md`
- [7] 本地审计记录（未公开）：`workflow-audit-output/20260919/prepublish-review/supervision-result.md`
- [8] 本地审计记录（未公开）：`workflow-audit-output/20260919/item4-review-false-positive/cross-project-conclusion.md`
- [9] 本地审计记录（未公开）：`workflow-audit-output/20260918/workflow-remediation-progress.md`
- [10] 本地审计记录（未公开）：`workflow-audit-output/20260919/item5-supervisor/current-evidence-and-proposal.md`
- [11] 本地审计记录（未公开）：`workflow-audit-output/20260919/item5-supervisor/supervision-result.md`
- [12] 本地审计记录（未公开）：`workflow-audit-output/20260919/voxpocket-raven/status.md`
- [13] 本地审计记录（未公开）：`workflow-audit-output/20260920/item6-telemetry-sync/status.md`