---
name: repo-kit
description: 用 shared-ci 的模板与检查器让一个 repo 满足统一的 repo 合同（薄 AGENTS、layer 表、同入口 verify、shared-ci caller、required 汇总 gate、PR 模板、CODEOWNERS），或接入共享库新版本，或从现有 repo 拆出共享库。三种模式：init（新建或补齐）、adopt（接入/升级共享库）、split（拆出 SDK/共享库，保留历史）。取代 layered-agent-context。
---

# repo-kit

**规则不在本 skill 里。** 合同、模板、检查器都在 `<owner>/shared-ci`，按固定 SHA 使用：

| 需要 | 读取（`shared-ci@<SHA>`） |
|---|---|
| repo 最少要有什么 | `ai/repo-contract.md`（机器可读：`schemas/repo-contract-v1.json`） |
| 如何定义本仓 layer 与 PR | 同版本 `ai/repo-contract.md` 的 Repository development contract；格式见 `docs/context-cli-contract.md` |
| 执行 agent 在 repo 内怎么工作 | `ai/agent-protocol.md` |
| 模板 | `templates/`（目录入口、root/leaf tech-context、`development.md`、PR 模板、CODEOWNERS、CI、verify） |
| 检查 | `scripts/context audit`（合同）、`resolve <path>`（路径→唯一 layer） |

先取当前 shared-ci 发布 SHA（其 release notes / README 顶部），整个任务只用这一个 SHA。

## 共同前置

- 仓库先定义 layer/PR/验证规范，各种 agent 都从 AGENTS 目录读取它；Dev Team 的 Planner/task 流程只是消费者，不是规则来源。
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
2. **layer 合同**：从稳定职责、接口与依赖确定边界，不机械地把每个 package/target 当一层，也不为一次任务新增假 layer。
   按目标版本的 root/leaf 模板生成总表与各层 `tech-context.md`：实现和对应测试的归属、依赖、验证命令、职责/不做项与红线。
   每个 tracked 路径唯一归属 layer 或有理由的 support；不把整个脚本/源码目录默认排除。实际 import 边界检查接入本仓验证命令。
3. **PR 与开发规范**：适配已有开发指南，或从 `templates/development.md` 生成 `docs/development.md`。
   根据本仓 layer 与 CI/docs/review 等支持职责列 PR 工作单元、允许的必要配套、验证和审查来源；引用 layer 的路径权威，不复制第二套 globs。
   检查需求/spec 跨层时能按接口依赖独立交付，测试/必要文档随实现；记录检查的 enforced/manual/planned/N/A 与证据，不让模板示例冒充已接入。
4. **AGENTS.md**：只作目录，每个入口说明何时读取哪份权威文档，必须能找到上面的开发/PR 指南、架构与验证/审查来源。
   使用目标版本的目录模板，保留其机器必需的标题/固定版本指针；读取不到新合同/模板时报告版本迁移依赖，不复制旧 handbook 细则。
   `CLAUDE.md` 等其他 agent 文件只写“先读 AGENTS.md”加该工具特有注意，不重复事实。
5. **verify**：`scripts/verify [--changed|--all]` 调 resolver 选 layer 并跑其 gate；`.githooks/pre-push` 与 CI 都调它。
6. **CI**：`.github/workflows/ci.yml` 调 `<owner>/shared-ci/.github/workflows/quality.yml@<SHA>` 与 review workflows，传本仓命令；保留原 required check 名，或在同一 PR 里给出 ruleset 名单映射。
   用 self-hosted runner 跑 review/CI 时先按下文 self-hosted runner 一节注册。
7. **PR 模板 + CODEOWNERS**：模板让作者引用仓库 PR 单元，不要求另造范围；CODEOWNERS 覆盖实际重要路径。
8. **验收**：从 AGENTS 可找到全部规则；示例已替换为本仓事实；归属/依赖 audit 零发现且本仓验证有真实结果；PR 上汇总 gate 与 review 通过；合并后回读 ruleset（required 含汇总 gate，原有 required 不减少）。
   ruleset 变更是重要操作：列出 old→new 给 Owner，获批后再改。

## self-hosted runner：每个 repo 独立注册

个人账号的 GitHub runner 只能按 repository 注册，没有账号级 runner；跨 repo 共享需要 organization runner group。
每个用自托管硬件跑 AI review/CI 的 repo 各有自己的 repository-scoped runner。
已有 runner 不复用、不搬迁、不重新注册到其他 repo，也不跨 repo 共享；禁止用 `config.sh --replace` 抢占其他 repo 的 runner。

| 项目 | 每 repo 命名 |
|---|---|
| 安装目录 | `$HOME/actions-runner-<repo>` |
| runner name | `<repo>-mac`（下文 `<name>`） |
| LaunchAgent | `actions.runner.<owner>-<repo>.<name>`（由 `svc.sh` 创建） |
| labels | `self-hosted,macOS,ARM64`，加本 repo 专用 label（如需；下文 `<labels>`） |

已有 runner 的 repo：VoxPocket、AIDash、VitalStride、Localis；shared-ci（正在添加）。

1. **下载与校验**：确认安装目录未被占用，新建并进入该目录；固定官方 [actions/runner v2.335.1](https://github.com/actions/runner/releases/tag/v2.335.1)。
   从该 release 下载 `actions-runner-osx-arm64-2.335.1.tar.gz`，用 `shasum -a 256 actions-runner-osx-arm64-2.335.1.tar.gz` 与该 release notes 公布的 SHA-256 核对。
   再用 `tar tzf actions-runner-osx-arm64-2.335.1.tar.gz` 检查成员：不得有绝对路径或 `..` 路径段。
   两项检查都通过后才 `tar xzf actions-runner-osx-arm64-2.335.1.tar.gz`；校验失败即停，通过前不运行归档内任何内容。
2. **注册 token**：经 Owner 批准的身份调用 `POST repos/<owner>/<repo>/actions/runners/registration-token`。
   token 短时有效，只在当前进程内临时传递；不打印、不记日志、不落盘，关闭命令跟踪，使用后立即清除。
3. **注册**：在安装目录执行 `./config.sh --url https://github.com/<owner>/<repo> --token <token> --name <name> --labels <labels> --unattended`。
4. **托管**：`./svc.sh install && ./svc.sh start`。
5. **核验**：`gh api repos/<owner>/<repo>/actions/runners` 显示本 repo 的 runner 为 `online`，name 与 labels 均符合上表。

launchd 不读取交互 shell profile；模型 provider 的 base URL / keys 必须由服务启动包装脚本提供，细节见 [runtime-recovery「托管时的坑」](../../workflow/runtime-recovery/SKILL.md)。

AI review 启用顺序：runner online → 设置本 repo 的启用变量（shared-ci caller 如 `SHARED_CI_REVIEW_RUNNER=true`）→ 跑真实正向、负向 review，分别验证放行与拦截 → 将 review gate 加入 required checks。
ruleset 变更按 init 第 8 步视为重要操作：先列 required checks 的 old→new 名单给 Owner，获批后再改，原有 required 不减少。

[setup-runner.sh](../auto-review-merge/assets/ci/setup-runner.sh) 是 auto-review-merge 模板的辅助脚本，未校验 SHA-256 且使用 `--replace`；本配方按上述步骤手动执行，或先给脚本补齐校验并去掉 `--replace` 后再用。

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
