# agent-skills

可复用的 Claude Code / Codex agent skills,按 **workflow / design / repo / research / meta** 组织。
每个 skill 是 `skills/<category>/<name>/` 下的一个目录,含 `SKILL.md`(frontmatter + 指令)
与可选 `references/`、`scripts/`、`assets/`、`templates/`。

## Skills

> 下表由 `scripts/gen_registry.py` 从各 `SKILL.md` 的 frontmatter **自动生成**,勿手改。
> 机器可读索引见 [`skills.json`](./skills.json)。

<!-- SKILLS:BEGIN -->
### Workflow 编排（`skills/workflow/`）

| Skill | 作用 |
|---|---|
| [`multica-delivery-supervisor`](./skills/workflow/multica-delivery-supervisor/) | Supervise named Multica projects and delivery PRs, or resume tasks affected by a shared blocker after the Owner reports recovery, preserving existing Dev Team roles and authority. |
| [`orchestrate`](./skills/workflow/orchestrate/) | W0 总体编排——主 agent 把 Owner 的多 repo 目标拆成可交付切片，选执行来源（Dev Team issue 或 subagent），派发、监督并按 PR 证据验收；自己不写产品代码。用于“完成这个跨仓目标 / 继续某个 goal / 看看怎么继续 / 协调多个 repo 的升级 / 派活并盯到合并”。 |
| [`runtime-recovery`](./skills/workflow/runtime-recovery/) | W6 运行恢复——Multica 控制面/NAS/Azure 链路、本机 Multica daemon、self-hosted GitHub runner 不可用或执行者中断时，定位故障层、暂停依赖动作、自动拉起 daemon/runner、恢复后触发 Supervisor 巡检并由原 owner 接回。用于“Multica 连不上 / daemon 挂了 / runner offline / PR 卡在 codex-review… |
| [`shared-release`](./skills/workflow/shared-release/) | W5 共享库发布与消费者升级——shared-* 仓合并后打不可变版本，随版本发布 ai/ 合同，在外部消费者验证，再为每个消费 repo 开独立 pin 升级 PR。用于“发布 shared-ci/telemetry/design-system/tokens/VoxKit 新版本 / 让产品升级到新版共享库 / 回滚共享库版本”。 |

### 设计（`skills/design/`）

| Skill | 作用 |
|---|---|
| [`my-designer`](./skills/design/my-designer/) | Design lead only for rendered UI and visual-interface work in the personal projects VitalStride (including the VitalStrike alias), AIDash, Financial, and VoxPocket: layout, hierarchy, styling, interaction, chart prese… |
| [`visual-design-modernization`](./skills/design/visual-design-modernization/) | Use when a user says an app's UI "looks bad / dated / not modern" and wants to improve visual quality (spacing, typography, color, hierarchy, data-viz) — especially for SwiftUI/macOS/iOS but the method is framework-ag… |

### Repo 工程（`skills/repo/`）

| Skill | 作用 |
|---|---|
| [`auto-review-merge`](./skills/repo/auto-review-merge/) | Use when a user wants automated PR code review plus hands-off auto-merge on a GitHub repo — "review my PRs automatically", "auto-merge when CI passes", "gate merges on a Claude review", "set up PR automation". Install… |
| [`code-review`](./skills/repo/code-review/) | Review a branch, PR, worktree, or implementation handoff against both repository standards and feature intent. Use for implementer self-review or independent review when the target repo may contain Spec Kit artifacts … |
| [`layered-ci-autofix`](./skills/repo/layered-ci-autofix/) | 运行时(run-time)闭环:把改动 commit/push、开 PR、监督 PR 的 required CI、失败时读结构化失败信号 {layer, path, kind, detail, red_lines} 做**按 layer 收窄的自动修复**,修完再 push、重新等 CI,直到绿灯或触发升级。它是 repo-kit(setup-time 脚手架)的**运行时消费者**——消费后者铺好的 CI 信号与每层 red_l… |
| [`layered-data-warehouse`](./skills/repo/layered-data-warehouse/) | 给一个项目把数据仓库"分层重构/梳理成型"——先扫描项目真实的数据模型(ORM/DDL/DB/已有派生服务/导入管线),再套标准数仓分层(ODS/DWD/DIM/DWS/ADS,附 medallion 与 dbt 交叉映射),产出一份可演进的 warehouse 蓝图:分层清单、一致性维度、指标口径登记、SCD 与增量幂等策略、血缘、项目专属 red-lines、gap 分析与分阶段 refine 计划。产物是设计蓝图不是实现代码… |
| [`multica-issue`](./skills/repo/multica-issue/) | 向 Multica dev team 提交新 issue,让 dev team(Team Lead → Fullstack Engineer → AI Reviewer → PR Manager)完成任务。给一句用户输入,skill 会:按当前 repo 的 github remote 反查正确的 Multica project;判定输入属于 bugfix / 新功能 / 技术架构(tech-context)变更;bug 会检索同… |
| [`owner-decision-loop`](./skills/repo/owner-decision-loop/) | Resolve delivery decisions through reusable owner calibration. Use when Team Lead cannot determine Planner or Fullstack content from repository authority because product intent, acceptance, scope, architecture, policy… |
| [`repo-kit`](./skills/repo/repo-kit/) | 用 shared-ci 的模板与检查器让一个 repo 满足统一的 repo 合同（薄 AGENTS、layer 表、同入口 verify、shared-ci caller、required 汇总 gate、PR 模板、CODEOWNERS），或接入共享库新版本，或从现有 repo 拆出共享库。三种模式：init（新建或补齐）、adopt（接入/升级共享库）、split（拆出 SDK/共享库，保留历史）。取代 layered-ag… |
| [`teamwork`](./skills/repo/teamwork/) | Multi-agent pipeline for complex tasks — spec-first, plan-led execution with gated review, verification, and shipping. team-lead orchestrates; specialist agents do the work. |
| [`xcode-cli`](./skills/repo/xcode-cli/) | Route Apple-platform builds, tests, simulator runs, and result inspection through Swift and Xcode command-line tools. Use when Codex needs to build or test a Swift package, Xcode project, or workspace; diagnose Apple … |

### 调研（`skills/research/`）

| Skill | 作用 |
|---|---|
| [`deep-research`](./skills/research/deep-research/) | 对任意主题做深度、多来源、经交叉核查的调研,产出带引用、按置信度分级的报告。五阶段流水线:把问题分解成 4-8 个子问题 → 跨渠道(web/github/news/academic)并行 fan-out 调研 → 对每个发现做对抗式核查(证伪而非确认,发现者≠核查者)→ 交叉验证+圆桌综合、标注分歧 → 输出 HIGH/MEDIUM/LOW/CONTESTED 分级的引用报告。Provider-agnostic:同一份 skil… |

### 元/工具（`skills/meta/`）

| Skill | 作用 |
|---|---|
| [`save-tool`](./skills/meta/save-tool/) | Use when the user shares a message containing skills, tools, GitHub repos, or resource links they want to stockpile for later — "存起来", "save this tool", "collect these links", "先放着以后再看怎么用". Extracts every repo/link/to… |
<!-- SKILLS:END -->

## 安装

本地开发(软链到 `~/.claude/skills/`):

```bash
scripts/install-symlinks.sh
```

Claude Code plugin marketplace:

```text
/plugin marketplace add LeePepe/agent-skills
/plugin install <skill>@agent-skills
```

## 校验

```bash
python3 scripts/validate_skills.py
python3 scripts/gen_registry.py --check
```

CI(`.github/workflows/validate-skills.yml`)在每个 PR 上运行同样的检查。

<!-- app-identity-probe -->
