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

## 仓库先定义，角色再执行

layer 与 PR 的规范属于仓库，不由 Planner、FS 或 PRM 临时定义。统一合同在目标仓固定版本的
`shared-ci/ai/repo-contract.md`（Repository development contract）；[repo-kit](../repo/repo-kit/SKILL.md)
在接入时把它落实为本仓 layer 表、各层职责/依赖/验证、开发指南中的 PR 工作单元，以及相应 CI 接线。
AGENTS 只作这些文档的目录。这里不再维护第二份 layer/PR 定义。

- **Dev Team**：Planner 读取仓库规范，把需求/spec 验收项映射到已有 PR 单元，再给出 task、路径/不做项、依赖与验证。
  现有 spec/plan gate 通过后 TL 派发、FS 执行；一个跨层 spec 可以对应多个依赖 task，不能借任务划分重定义仓库边界。
- **其他 agent**：同样从 AGENTS 目录读取仓库开发规范并遵循；无需额外套用 Dev Team 的 Planner/task 流程。
- **CI / Review**：按同一仓库合同验证路径归属、声明依赖、实际构建/测试与已有审查要求。缺少检查时记录真实缺口；
  不把 layer 声明、相同行数或 CI 绿当作实现/PR 意图已被证明。
- **PRM**：消费已有 CI/review 和审批结果、路由具体修复、推进合并；不新增范围大小反馈或另一轮范围审查。

规范缺失先通过 repo-kit 补齐仓库合同；规范变更按实际架构/政策变更处理，不由任务或 label 自行豁免。
没有统一行数/文件数上限；规则源修改不等于消费者、现网角色和服务器保护已经更新。

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
| scope | 引用仓库已有 PR 单元与当前任务；Dev Team 另带 Planner task，不另造 layer/PR 规则 |
| owner | 唯一执行者；来源（dev-team / subagent / owner） |
| evidence | PR URL、head SHA、已有 required checks/review 与所需审批结果 |
| next | 下一动作的唯一 owner 与唤醒条件，或明确 hold |

发送 ≠ 被接受；run completed ≠ 交付；merge ≠ 发布/消费。
