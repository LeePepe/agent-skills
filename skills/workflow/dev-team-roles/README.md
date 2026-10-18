# Dev Team 角色

Multica 上 Dev Team 角色与 squad 规则的**唯一来源**。每个角色是一个 skill 目录（`dev-team-<role>/SKILL.md`，目录名与 skill 名一致）。它们位于
`skills/workflow/` 下的第三层，不会被 `scripts/gen_registry.py` 当作本机 Claude/Codex skill 注册或安装。

下表七项是本仓维护的角色源码，不是 Multica 的完整实时库存。源码约定绑定、workspace 已安装 skill 的来源／版本和 agent 实际分配是三类信息，需要分别核对；本地文件本身不证明运行端已采用。

Multica 用链接部署：

- 首次：`multica skill import --url https://github.com/<owner>/agent-skills/tree/main/skills/workflow/dev-team-roles/dev-team-<role>`
- 更新：`multica skill refresh <skill-id>`（保留 skill ID 和 agent 绑定），然后回读核对
- agent 和 squad 的 instructions 只写一个指针指向对应 skill，**不在 Multica 里复制正文**

| 目录 | Multica skill | 源码约定绑定 |
|---|---|---|
| `dev-team-squad/` | `dev-team-squad` | 六个 Dev Team agent；squad instructions 也指向它 |
| `dev-team-team-lead/` | `dev-team-team-lead` | Team Lead |
| `dev-team-planner/` | `dev-team-planner` | Planner Lead |
| `dev-team-fullstack-engineer/` | `dev-team-fullstack-engineer` | Fullstack Engineer |
| `dev-team-ai-reviewer/` | `dev-team-ai-reviewer` | AI Reviewer |
| `dev-team-pr-manager/` | `dev-team-pr-manager` | PR Manager；PR 发现由每 30 分钟的 Autopilot 触发 |
| `dev-team-flow-supervisor/` | `dev-team-flow-supervisor` | Dev Team Flow Supervisor（原 Pipeline Supervisor，2026-10-13 改名并收窄） |

改动流程：改本目录 → PR 合并 → `multica skill refresh` → 回读核对。

写法：每个角色只写职责、输入、输出、交接字段（见 [workflow 索引](../README.md#交接最小字段)）与红线；
仓内规则一律引用目标 repo 的 `AGENTS.md` 与 `shared-ci@<SHA>/ai/agent-protocol.md`，不在角色文本里复制。
本仓公开，按 [review rules](../../../docs/review-rules.md)：不写账号名、数字 ID、仓库 ID、令牌、私钥和本机路径。
GitHub 身份运行时用 `gh api` 查（如仓库所有者 ID），Multica 的 agent、成员等 ID 运行时用 `multica` 查。

历史：2026-09-24 至 2026-10-13 这些角色以复制方式部署，源文本和当时的部署存档保存在私有的 Skills 仓。

## 只读核对运行端

在目标 workspace 中用 `skill list` 查看已安装库存，再用 `skill get` 回读具体 skill 的来源与版本元数据；用 `agent skills list` 查看 agent 的实际分配。查询入口如下，ID 均由当前环境取得，不写入本仓：

```text
multica --workspace-id <workspace-id> skill list --output json
multica --workspace-id <workspace-id> skill get <skill-id> --output json
multica --workspace-id <workspace-id> agent skills list <agent-id> --output json
```

按回执区分已安装项、导入来源／版本与实际绑定；字段缺失或查询失败时保留未知，不能从源码表推断当前状态。只读核对不执行导入、刷新或绑定变更。
