# Workflow（W0–W7）

编排者（主 agent、Dev Team 角色）用的 workflow 索引。**repo 内的执行 agent 不依赖本目录**：它们只读目标
repo 的 `AGENTS.md` 与其中固定 SHA 引用的 `shared-ci/ai/agent-protocol.md`，并由 hooks / required CI /
ruleset 强制。

```
多来源需求 ──► W0 整体交付循环（需求→实现→PR→发布→产品反馈→需求）
                      │
        ┌─────────────┼──────────────────┐
        ▼             ▼                  ▼
  W1 Issue 入口   W3 Repo agent       W7 Owner 决策
  → W2 Dev Team   （subagent 直派）
   TL→Planner→FS→Reviewer
        │  FS 在仓内同样执行 W3
        └──────┬──────┘
               ▼ push + PR（两种来源同一出口）
        W4 PR 生命周期（PRM：Adopt→CI/Review→修复→Ship）
               │ merge
     ┌─────────┴─────────┐
     ▼ shared repo        ▼ project repo
  W5 发布 + 消费者升级    交付回执 → W0 验收

  横切：W6 运行恢复（daemon/runner/控制面故障、executor 中断→Supervisor 接续）
```

| # | 名称 | 触发 | 执行者 | 定义在哪 |
|---|---|---|---|---|
| W0 | 整体交付循环 | 多来源需求与产品反馈 | 各子 workflow 的既有角色 | 本索引；跨仓拆分/编排子流程见 [`orchestrate`](orchestrate/SKILL.md) |
| W1 | Issue 入口 | “让 dev team 做 X” | 主 agent | [`multica-issue`](../repo/multica-issue/SKILL.md) |
| W2 | Dev Team 流水线 | issue 被指派 | TL / Planner / FS / AI Reviewer / Pipeline Supervisor | Multica 角色 instructions（源文本在私有仓，不随本仓发布） |
| W3 | Repo agent | 任何改 repo 的任务 | 唯一执行者 | **目标 repo** `AGENTS.md` + `shared-ci@<SHA>/ai/agent-protocol.md`；搭建用 [`repo-kit`](../repo/repo-kit/SKILL.md) |
| W4 | PR 生命周期 | PR 创建/更新 | PRM | repo 内 PR 模板 + required checks；自动修复 [`layered-ci-autofix`](../repo/layered-ci-autofix/SKILL.md) |
| W5 | 共享库发布 | shared repo merge | 该库 FS / PRM | [`shared-release`](shared-release/SKILL.md) + 各库 `ai/MIGRATION.md` |
| W6 | 运行恢复 | 故障/中断 | 运行维护者 / Supervisor | [`runtime-recovery`](runtime-recovery/SKILL.md) |
| W7 | Owner 决策与升级 | 需要取舍/新授权，或 TL 诊断后仍无法解决 | TL / 主 agent → Owner | [`owner-decision-loop`](../repo/owner-decision-loop/SKILL.md) |

## 聊天准入与执行版本

- 仅描述现象或要求诊断时，CLI 查事实、给判断，不自动实施或派发。明确且范围清楚的“修复/实现”已表达实施意图，
  无需再回复一次“改”；新增范围、权限与受保护操作仍按现有门禁处理。
- 设计修改、workflow refine 先由 Owner 与 CLI 确定需求、设计及基本实现方案，再交 Dev Team 或 subagent 实现。
  这不要求所有普通 bug 在入口查清完整根因，也不赋予团队重新选择产品/流程方案的职责。
- 普通产品任务默认 Dev Team；设计修改、workflow refine 可选 Dev Team 或 subagent。遵守明确选择，已有任务保留
  原 owner，同一目标不再建第二个写者。明确指定当前 CLI 执行时按该选择处理。
- 交接引用 Owner 对本版可以执行的明确确认和固定方案版本。后续设计讨论进入下一版草稿，单条意见获同意不等于
  整版获准执行；下一版经 Owner 明确定稿、可以执行后才交接，不回写在途任务的目标与验收。
- 已批准仓库、范围、方案、验收和权限内，补齐必需的适配/测试任务属于当前版实现。新增仓库、改变关键设计或权限
  不是“补拆”；真实阻塞和当前实现缺陷仍须报告、修复，不能移到下一版后声称本版完成。
- 已选执行方不可用或接收结果未知时，保留固定版本、任务标识、原执行方和实际状态；恢复后先核实接收与唯一写者，
  再补派未接收任务。持续失败报告阻塞，不自动改派 subagent。outbox、后台重试和唤醒能力须有实现证据，不能凭本规范宣称已存在。

## Plan 与依赖推进

本次 plan 记录方案版本、具体仓库/任务、依赖与可并行关系、完成条件及完成后的下一动作。
长期复用的升级/验证/回滚规则属于 repo guide 或版本化 shared 文档；plan 引用适用版本，不复制另一套政策。
拆分仍由下方仓库合同定义，按可验收目标与依赖组织，不按 layer 数、行数或文件数机械切分。

Dev Team 由 TL 按 plan 推进依赖；subagent 由原主会话按 plan 中的更新顺序接续派发。沿用这些角色，不增加监督层。
provider 合并、发布、消费者升级与真实消费分别取证，不能用前一项完成代替整体验收。

## 仓库先定义，角色再执行

layer 与 PR 的规范属于仓库，不由 Planner、FS 或 PRM 临时定义。统一合同在目标仓固定版本的
`shared-ci/ai/repo-contract.md`（Repository development contract）；[repo-kit](../repo/repo-kit/SKILL.md)
在接入时把它落实为本仓 layer 表、各层职责/依赖/验证、开发指南中的 PR 工作单元，以及相应 CI 接线。
AGENTS 只作这些文档的目录。这里不再维护第二份 layer/PR 定义。

- **Dev Team**：Planner 先复用、校验并补齐已有 spec/plan/tasks，核对当前代码、依赖、任务边界与验证是否可执行，
  只补缺少的实现步骤；再把需求/spec 验收项映射到已有 PR 单元、路径/不做项。已有计划不要求重写，也不自动免审。
  现有 spec/plan gate 通过后 TL 派发、FS 执行；一个跨层 spec 可以对应多个依赖 task，不能借任务划分重定义仓库边界。
- **其他 agent**：同样从 AGENTS 目录读取仓库开发规范并遵循；无需额外套用 Dev Team 的 Planner/task 流程。
- **CI / Review**：按同一仓库合同验证路径归属、声明依赖、实际构建/测试与已有审查要求。缺少检查时记录真实缺口；
  不把 layer 声明、相同行数或 CI 绿当作实现/PR 意图已被证明。
- **PRM**：消费已有 CI/review 和审批结果、路由具体修复、推进合并；不新增范围大小反馈或另一轮范围审查。

规范缺失先通过 repo-kit 补齐仓库合同；规范变更按实际架构/政策变更处理，不由任务或 label 自行豁免。
没有统一行数/文件数上限；规则源修改不等于消费者、现网角色和服务器保护已经更新。

## 实现修复与升级

Reviewer 的当前版实现缺口回原 FS 修复、验证与复查。同一问题连续两轮完整修复/复查无实质进展，TL 介入诊断
为什么修不好并协调；单纯等待不算一轮，改 finding 名称或任务编号不重置历史。已知权限等硬阻塞直接报告，不凑轮数。

TL 诊断协调后仍无法解决，即使技术原因尚未知，也通过 [W7](../repo/owner-decision-loop/SKILL.md) 升级 Owner，
带上本版任务、未满足要求与影响、每次尝试/验证、已知原因与未知项、建议下一步及所需帮助。
保留现场与失败证据，不无界重试、不降低验收、不自动改方案或改派；其他无依赖任务继续。

## 合并规则（所有 repo 一致）

- 普通 PR：fail-closed 汇总 gate ✓ + `codex-review-target` ✓ → auto-merge；无需 Owner 批准。
  codex 发现问题 → PR comment + check 失败 → 原作者修复 push → 新 SHA 重审。`kimi-review` 只评论，不阻塞。
- 普通测试代码删改仍走普通 PR 的 CI / AI review，不单独要求 Owner；修改实际 gate、policy 或权限仍按重要 PR 处理。
- 重要 PR：另需 Owner approve（CODEOWNERS：`.github/**`、policy/schema/gate、AGENTS/constitution、依赖 pin
  升级、凭据/隐私/数据迁移）。过渡期（GitHub App 上线前）只以 `owner-review` label 提醒。
- 新 push 使旧 review/check 过期；证据以 PR head SHA 为准，不另写本地回执。

## 交接最小字段

任何跨 W 的交接（issue comment、PR body、subagent prompt）都要带：

| 字段 | 内容 |
|---|---|
| target | repo full_name、base 分支/SHA |
| intent | 目标、验收、禁止事项（行为/UX 默认不变） |
| baseline | 本版方案/任务的固定引用与适用执行授权；聊天任务按上述准入确认，下一版讨论分开保存 |
| scope | 引用仓库已有 PR 单元与当前任务；Dev Team 另带 Planner task，不另造 layer/PR 规则 |
| owner | 唯一执行者；来源（dev-team / subagent / owner） |
| evidence | PR URL、head SHA、已有 required checks/review 与所需审批结果 |
| next | 下一动作的唯一 owner 与唤醒条件，或明确 hold |

发送 ≠ 被接受；run completed ≠ 交付；merge ≠ 发布/消费。
