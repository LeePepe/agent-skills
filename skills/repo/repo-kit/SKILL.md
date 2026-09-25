---
name: repo-kit
description: 用 shared-ci 的模板与检查器让一个 repo 满足统一的 repo 合同（薄 AGENTS、layer 表、同入口 verify、shared-ci caller、required 汇总 gate、PR 模板、CODEOWNERS），或接入共享库新版本，或从现有 repo 拆出共享库。三种模式：init（新建或补齐）、adopt（接入/升级共享库）、split（拆出 SDK/共享库，保留历史）。取代 layered-agent-context。
---

# repo-kit

**规则不在本 skill 里。** 合同、模板、检查器都在 `LeePepe/shared-ci`，按固定 SHA 使用：

| 需要 | 读取（`shared-ci@<SHA>`） |
|---|---|
| repo 最少要有什么 | `ai/repo-contract.md`（机器可读：`schemas/repo-contract-v1.json`） |
| 执行 agent 在 repo 内怎么工作 | `ai/agent-protocol.md` |
| 模板 | `templates/`（`AGENTS.md`、`tech-context.md`、`pull_request_template.md`、`CODEOWNERS`、`ci.yml`、`verify`） |
| 检查 | `scripts/context audit`（合同）、`resolve <path>`（路径→唯一 layer） |

先取当前 shared-ci 发布 SHA（其 release notes / README 顶部），整个任务只用这一个 SHA。

## 共同前置

- init/adopt/split 是流程，不是 PR 范围。先按[共享 PR 范围](../../workflow/README.md#pr-范围)的路径、layer、CI 验证及审查责任拆任务。
  CI 接线、文档整理、reviewer/审批规则、工具实现各自成片并携带必要测试/文档；不可分离的最小配套须在派发前列清，有依赖就顺序接入。
- 在目标 repo 建专用分支/worktree；原 checkout 的未提交内容不动。
- worktree 只建在本机的 agent worktree 根下（见下节）；Owner 的主 checkout 不作为 agent 的写入位置。
- 读目标 repo 现有 `AGENTS.md`、`CLAUDE.md`、constitution、`docs/`，**保留业务事实和红线**，只改结构。
- 账号、profile、本机路径、repo 数字 ID 不写进 repo（audit 会拒绝）。

### Worktree 根

| 根 | 用途 |
|---|---|
| `~/Development/worktrees/<task>/` | 协调者 / subagent 的任务 worktree |
| `~/multica_workspaces/` | Multica daemon 的任务工作区 |
| `~/orca/workspaces/<repo>/<task>/` | Orca worktree（主 checkout 的 linked worktree） |

agent 提交身份由本机 git config 按 agent worktree 根绑定，不在 repo 内设置。首次提交前用 `git config user.email` 确认；若 repo 自带 `user.email`（`.git/config`）会覆盖绑定，此时报告给 Owner，不要自行改 repo config。

## init：新建或补齐 repo 合同

1. **探测**：栈（SPM / npm / Python / Xcode）、package/target 列表、测试根、现有 hooks 与 CI、ruleset 当前 required checks（`gh api repos/<o>/<r>/rules/branches/main`）。
2. **layer 表**：每个 package/target 一个 layer。每个 layer 目录放 `tech-context.md`，frontmatter：
   ```yaml
   layer: VoxDomain
   owns: [Packages/VoxDomain/**]
   depends_on: []
   gate: {build: "swift build --package-path Packages/VoxDomain", test: "swift test --package-path Packages/VoxDomain"}
   red_lines: ["不依赖 UI/平台框架"]
   ```
   根目录 `docs/architecture/tech-context.md` 放一张总表（layer → 路径 → 依赖），并声明 `support`（docs 等）排除项。
   每个可执行路径恰好属于一个 layer；`resolve` 对全部 `git ls-files` 无 unmapped/overlap。
3. **AGENTS.md**：按模板，≤150 行。只写：必读顺序、协议指针（SHA）、`scripts/verify` 用法、required checks 名单（与 ruleset 一致）、本仓红线与已批准例外、交付要求。
   `CLAUDE.md` 等其他 agent 文件只写“先读 AGENTS.md”加该工具特有注意，不重复事实。
4. **verify**：`scripts/verify [--changed|--all]` 调 resolver 选 layer 并跑其 gate；`.githooks/pre-push` 与 CI 都调它。
5. **CI**：`.github/workflows/ci.yml` 调 `LeePepe/shared-ci/.github/workflows/quality.yml@<SHA>` 与 review workflows；保留原 required check 名，或在同一 PR 里给出 ruleset 名单映射。
6. **PR 模板 + CODEOWNERS**：模板原样使用；CODEOWNERS 覆盖重要路径。
7. **验收**：`audit` 零发现；PR 上汇总 gate 与 review 通过；合并后回读 ruleset（required 含汇总 gate，原有 required 不减少）。
   ruleset 变更是重要操作：列出 old→new 给 Owner，获批后再改。

## adopt：接入或升级共享库

1. 读该库**目标版本**的 `ai/INTEGRATION.md`（新接入）或 `ai/MIGRATION.md`（升级），兼容性看 `ai/COMPATIBILITY.md`。
2. 只改：依赖 pin（exact 版本 / 完整 SHA）、AGENTS 依赖段的版本指针、必要适配代码（放在消费方自己的 adapter layer）。
3. `scripts/verify --all` 通过；PR 标为重要 PR（依赖 pin）。

## split：从现有 repo 拆出共享库

先在原 repo 内完成、每步一个 PR、行为不变：

1. **切接缝**：在原 repo 新建暂存包（如 `Packages/<Kit>`）；把对宿主的依赖（日志/遥测/凭据/配置读取）改为协议注入；统一对外 API 风格。
2. **搬迁**：代码移入暂存包，宿主改依赖它；现有测试全部保留并通过（golden/回归测试兜底）。
3. **补齐能力**：新增的库内能力在暂存包里完成并测试。
4. **拆 repo**（前 3 步合并后）：
   - 隐私预检：对将导出的历史做凭据/私有配置扫描，发现即停交 Owner。
   - `git filter-repo --path Packages/<Kit>/ --path-rename Packages/<Kit>/:` 保留历史，推到新 repo。
   - 新 repo 执行 **init**；随首个 tag 发布 `ai/`；按 W5 外部消费者验证。
   - 原 repo 执行 **adopt**，把 path 依赖换成远程 exact 版本；本地开发可临时切回 path 依赖，但不得提交。
5. 新 repo 的可见性、许可证、平台范围在拆分前由 Owner 确认。
