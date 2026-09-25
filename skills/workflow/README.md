# Workflow（W0–W7）

编排者（主 agent、Dev Team 角色）用的 workflow 索引。**repo 内的执行 agent 不依赖本目录**：它们只读目标
repo 的 `AGENTS.md` 与其中固定 SHA 引用的 `shared-ci/ai/agent-protocol.md`，并由 hooks / required CI /
ruleset 强制。

```
Owner ──目标/决策──► W0 总体编排（主 agent；只计划/委派/核验）
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
| W0 | 总体编排 | Owner 给目标 | 主 agent | [`orchestrate`](orchestrate/SKILL.md) |
| W1 | Issue 入口 | “让 dev team 做 X” | 主 agent | [`multica-issue`](../repo/multica-issue/SKILL.md) |
| W2 | Dev Team 流水线 | issue 被指派 | TL / Planner / FS / AI Reviewer / Pipeline Supervisor | Multica 角色 instructions（源文本在私有仓，不随本仓发布） |
| W3 | Repo agent | 任何改 repo 的任务 | 唯一执行者 | **目标 repo** `AGENTS.md` + `shared-ci@<SHA>/ai/agent-protocol.md`；搭建用 [`repo-kit`](../repo/repo-kit/SKILL.md) |
| W4 | PR 生命周期 | PR 创建/更新 | PRM | repo 内 PR 模板 + required checks；自动修复 [`layered-ci-autofix`](../repo/layered-ci-autofix/SKILL.md) |
| W5 | 共享库发布 | shared repo merge | 该库 FS / PRM | [`shared-release`](shared-release/SKILL.md) + 各库 `ai/MIGRATION.md` |
| W6 | 运行恢复 | 故障/中断 | 运行维护者 / Supervisor | [`runtime-recovery`](runtime-recovery/SKILL.md) |
| W7 | Owner 决策 | 需要新授权 | 主 agent → Owner | [`owner-decision-loop`](../repo/owner-decision-loop/SKILL.md) |

## PR 范围

PR 大小由范围约束，不设统一行数或文件数上限。一个 PR = 一个可独立验收的目的 + 一个主要责任域 + 完成它必需的配套改动。
责任域按目标仓已有的路径归属、layer、CI 验证职责和 reviewer 分工确定，可以是某个代码层、CI 接线、文档或 reviewer 规则；不是只按文件扩展名分组。

**派发前**，Planner/W0 在现有 intent/scope 中确定以下内容，执行者按此改动：

| 范围字段 | 要求 |
|---|---|
| 目的 / 主责任域 | 一个验收结果；同一 repo、layer、reviewer 或总计划都不足以合并多个独立目的 |
| 允许路径 / 不做项 | 具体文件或有界目录，包括必要测试、文档；不能以整个仓库作兜底范围 |
| layer / 依赖 | 从仓库既有 layer 表解析；support 路径也要说明所属目的，不能成为无限附加项 |
| CI 验证 | 按实际 diff、依赖影响和既有强制全量规则确定检查；多跑依赖层不扩大可修改范围 |
| 审查责任 | 指定对应 Reviewer 职责与需要 Owner 决策的受保护事项；从可信规则判定，不靠作者选 label |

- **切片**：某层实现携带其必要测试和配套文档；独立 CI 改造、文档整理、reviewer 规则或审批政策变更各自成片。
  即使在同一路径内也按目的拆分。确实不能独立合并的跨域改动，派发前列明最小配套路径、不可分离原因及全部 CI/审查责任。
- **执行**：检查整 PR 的实际 diff，不只看最后一次 push。新独立问题另开任务；范围不足先回 TL/W0，不能由执行者追加目录或改范围声明来追认越界。
  当前补丁引入的缺陷仍须修好；必要修复越界时先修订任务或重切，保留每片可构建、可验证的状态。
- **审查**：Reviewer 对照原任务范围与整 PR diff 检查每处改动是否必要，路径在范围内也不能夹带第二目的。
  PRM 核对当前 head 的范围审查、required CI 和审批证据，不重复代码审查。越界退原实现者/TL，不自动转交 Owner review 整个大包。
- **自动化边界**：路径解析、CI layer selection、范围准入是不同检查。现有 selection 决定测试影响面，不证明改动在授权范围内；
  尚未实现或采纳的范围门禁要明确报告，不能把 CI 绿或行数少当作范围合格。所有既有 required checks 与服务器保护继续适用。

行数/文件数可作估算和发现范围膨胀的信号，不是验收标准；按职责和目的重新切片，保留必要测试/文档，不为凑数字删覆盖或拆出不可构建的片段。
上述规则属于共享 workflow/CI；AGENTS 只提供读取入口，不复制这些规则。

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
| scope | [PR 范围](#pr-范围)中的主责任域、允许路径/不做项、layer、CI 验证和审查责任；不在其中的不改 |
| owner | 唯一执行者；来源（dev-team / subagent / owner） |
| evidence | PR URL、head SHA、整 PR 范围审查结论、required checks 与所需审批结果 |
| next | 下一动作的唯一 owner 与唤醒条件，或明确 hold |

发送 ≠ 被接受；run completed ≠ 交付；merge ≠ 发布/消费。
