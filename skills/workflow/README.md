# Workflow（W0–W7）

编排者（主 agent、Dev Team 角色）用的 workflow 索引。**repo 内的执行 agent 不依赖本目录**：它们只读目标
repo 的 `AGENTS.md` 条件目录,沿链接读取层上下文、验证/交付权威及版本协议。依赖 pin 位于实际
manifest/lockfile/caller,不从 AGENTS prose 取值;hooks / required CI / ruleset 提供强制。

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

## 合并目标与实际门禁

- 目标合同:普通 PR 的 fail-closed 汇总 gate ✓ + `codex-review-target` ✓ → auto-merge；无需 Owner 批准。
  codex 发现问题 → PR comment + check 失败 → 原作者修复 push → 新 SHA 重审。`kimi-review` 只评论，不阻塞。
- 普通授权范围内的测试编辑/删除不因测试变更本身要求 Owner approve、Decision ID 或执行 hold;
  仍说明测试损失的理由并接受正常质量检查与适用的 AI Plan-Review。AI 审查通过后不把普通测试
  再转成 Owner 执行批准;这不是跳过 AI loop 的测试类豁免。产品/范围/policy/permission 决策另行判断。
- 重要 PR：另需 Owner approve（CODEOWNERS：`.github/**`、policy/schema/gate、AGENTS/constitution、依赖 pin
  升级、凭据/隐私/数据迁移）。先回读目标 repo 的有效 ruleset 和 CODEOWNERS,不能假定各仓已经落实。
- 尚未强制 Owner review,或存在显式 Owner hold 的候选保持 Draft + `owner-review`（若已有标签）。
  标签不等于服务器门禁;批准/保护未就绪前不启用可立即执行的 auto-merge,也不关闭已有请求。
- W4 PR Manager 负责 PR 生命周期;TL/issue 入口不自行 merge。settings/ruleset 需精确 old→new
  和 Owner 授权,不是完成 repo-kit 文件就自动生效。
- 新 push 使旧 review/check 过期；证据以 PR head SHA 为准，不另写本地回执。

## 交接最小字段

任何跨 W 的交接（issue comment、PR body、subagent prompt）都要带：

| 字段 | 内容 |
|---|---|
| target | repo full_name、base 分支/SHA |
| intent | 目标、验收、禁止事项（行为/UX 默认不变） |
| scope | owned 路径（layer），不在其中的不改 |
| owner | 唯一执行者；来源（dev-team / subagent / owner） |
| evidence | PR URL、head SHA、required checks 结果 |
| next | 下一动作的唯一 owner 与唤醒条件，或明确 hold |

发送 ≠ 被接受；run completed ≠ 交付；merge ≠ 发布/消费。
