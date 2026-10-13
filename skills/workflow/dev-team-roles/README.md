# Dev Team 角色

Multica 上 Dev Team 角色与 squad 规则的**唯一来源**。每个角色是一个 skill 目录（`<role>/SKILL.md`）。它们位于
`skills/workflow/` 下的第三层，不会被 `scripts/gen_registry.py` 当作本机 Claude/Codex skill 注册或安装。

Multica 用链接部署：

- 首次：`multica skill import --url https://github.com/LeePepe/agent-skills/tree/main/skills/workflow/dev-team-roles/<role>`
- 更新：`multica skill refresh <skill-id>`（保留 skill ID 和 agent 绑定），然后回读核对
- agent 和 squad 的 instructions 只写一个指针指向对应 skill，**不在 Multica 里复制正文**

| 目录 | Multica skill | 绑定到 |
|---|---|---|
| `squad/` | `dev-team-squad` | 六个 Dev Team agent；squad instructions 也指向它 |
| `team-lead/` | `dev-team-team-lead` | Team Lead |
| `planner/` | `dev-team-planner` | Planner Lead |
| `fullstack-engineer/` | `dev-team-fullstack-engineer` | Fullstack Engineer |
| `ai-reviewer/` | `dev-team-ai-reviewer` | AI Reviewer |
| `pr-manager/` | `dev-team-pr-manager` | PR Manager；PR 发现由每 30 分钟的 Autopilot 触发 |
| `flow-supervisor/` | `dev-team-flow-supervisor` | Dev Team Flow Supervisor（原 Pipeline Supervisor，2026-10-13 改名并收窄） |

改动流程：改本目录 → PR 合并 → `multica skill refresh` → 回读核对。

写法：每个角色只写职责、输入、输出、交接字段（见 [workflow 索引](../README.md#交接最小字段)）与红线；
仓内规则一律引用目标 repo 的 `AGENTS.md` 与 `shared-ci@<SHA>/ai/agent-protocol.md`，不在角色文本里复制。
本仓公开：GitHub 账号和 App 的数字 ID 可以写；Multica 的 agent、成员、项目等 ID 不写进来，运行时用 `multica` 查询；
令牌、私钥、本机路径一律不写。

历史：2026-09-24 至 2026-10-13 这些角色以复制方式部署，源文本和当时的部署存档保存在私有仓 LeePepe/Skills。
