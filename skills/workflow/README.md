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

## Dev Team：Planner 给出任务范围（W2）

以下拆分要求只适用于 Dev Team，不是所有 PR 的统一范围门禁，也不设行数/文件数上限。
范围在 **Planner 产出 spec/plan/tasks 时**给出，经现有 spec/plan gate 后由 TL 派发，FS 开始实现前已确定。

1. **Planner 拆需求/spec**：独立需求或不同 spec 的工作分别列出；一个 spec 可覆盖多个 layer，但每个 FS task 只实现其中一个 layer 的验收子集。
   跨层行为用接口契约和 task 依赖连接；必要时先规划可独立验证的接口/基础任务，再规划消费者任务，不合成一个跨层 FS task。
2. **Planner 产出 task 表**：每个 task 都有下列信息，同一 layer 内的独立需求也分 task；CI、独立文档整理、reviewer 规则按各自职责单列任务。

   | task 字段 | 内容 |
   |---|---|
   | 来源 | task ID、需求/spec 路径及版本、对应验收项 ID |
   | 范围 | 一个 layer 或非代码责任域、允许修改的路径、明确不做项 |
   | 交付 | 必要实现/测试/配套文档、task-local 验收、依赖 task 与合入顺序 |
   | 验证 | 所属 layer 的验证、受影响 CI、对应 reviewer 职责 |

3. **审查与派发**：现有 spec/plan gate 检查需求 → spec 验收项 → task 的完整对应和边界；TL 按已通过的任务图派发，不把多个 task 合成一个 FS 实现包。
   Planner 的规划文档交付与 FS 的实现交付分开；必要的实现配套文档、测试仍在对应 FS task 内。
4. **FS 执行**：一个已就绪 task 对应独立分支/PR，只改该 task 的内容。需要改另一 layer、spec 或新增需求时，在继续实现前交 TL 返回 Planner 调整任务并重过原规划关。
   当前 task 的必要测试和修复要完成；不可独立构建/验证的拆法在规划阶段重设计，不交给 FS 凑片段。
5. **PRM 接手**：只按已有规则跟进 CI/review、路由具体修复和合并；不判断或反馈“PR 范围过大”，不要求额外范围报告，也不新增范围阻塞项。

非 Dev Team 的 agent 直接从目标仓 `AGENTS.md` 目录进入开发指南/固定版本协议、相关 layer 文档和验证/审查规则，按用户任务开发。
不要求它们补 Planner task 图、范围声明或通过范围大小检查；既有用户授权、CI/review 和重要路径保护仍适用。
这些开发细则放在目录指向的权威文档，不放进 AGENTS 正文。修改本规则源不等于已经更新现网角色或消费者版本。

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
| scope | Dev Team 引用 Planner 的 task 及范围；其他来源简述任务即可，无须补统一范围声明 |
| owner | 唯一执行者；来源（dev-team / subagent / owner） |
| evidence | PR URL、head SHA、已有 required checks/review 与所需审批结果 |
| next | 下一动作的唯一 owner 与唤醒条件，或明确 hold |

发送 ≠ 被接受；run completed ≠ 交付；merge ≠ 发布/消费。
