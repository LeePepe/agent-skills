# agent-skills

可复用的 Claude Code / Codex agent skills,按 **workflow / design / repo / research / meta** 组织。
每个 skill 是 `skills/<category>/<name>/` 下的一个目录,含 `SKILL.md`(frontmatter + 指令)
与可选 `references/`、`scripts/`、`assets/`、`templates/`。

## 从哪里开始

| 要找什么 | 入口与用途 |
|---|---|
| 本仓可注册技能 | [Skills 目录](#skills)与机器索引 [`skills.json`](skills.json)；按现有五类组织 |
| 工作流 | [六个 workflow 总览](skills/workflow/README.md)，按任务找到入口与交接边界 |
| 沟通与实现 | [01 输入与方案输出](skills/workflow/README.md#聊天准入与执行版本) → [02 参与与交接](skills/workflow/README.md#实现职责与当次输出)；[全部已盘点 skill 的参与地图](skills/workflow/README.md#skill-参与地图与来源边界) |
| 公共执行规则 | [CLI／subagent 执行契约](skills/workflow/execution-contract.md)，政策正文集中在这里 |
| 显式团队入口 | [`teamwork`](skills/repo/teamwork/SKILL.md) |
| Multica 角色源码 | [Dev Team 角色索引](skills/workflow/dev-team-roles/README.md)维护七项角色源码，不属于下方本机 skill 注册目录；workspace 已安装技能与 agent 实际绑定需分别查询 |
| 安装与更新入口 | [安装](#安装)：skill 安装与 CLI 公共规范安装分别操作；本地安装目录保存指向源码 checkout 的链接，不是另一份源码 |
| 规划与历史 | [`specs/001-code-review/`](specs/001-code-review/)是该功能的交付材料；具体执行证据沿原任务／交接记录查找。审计 skill 内的 dated evidence 按项目和时间范围使用，不替代现行规则 |

## Skills

> 下表由 `scripts/gen_registry.py` 从各 `SKILL.md` 的 frontmatter **自动生成**,勿手改。
> 机器可读索引见 [`skills.json`](./skills.json)。

<!-- SKILLS:BEGIN -->
### Workflow 编排（`skills/workflow/`）

| Skill | 作用 |
|---|---|
| [`multica-delivery-supervisor`](./skills/workflow/multica-delivery-supervisor/) | Supervise named Multica projects and delivery PRs, or resume tasks affected by a shared blocker after the Owner reports recovery, preserving existing Dev Team roles and authority. |
| [`orchestrate`](./skills/workflow/orchestrate/) | 跨仓编排——把原始需求和已有决定交规划 worker 确定或校验 Goal/Targets，按受审依赖分配 Dev Team 或 subagent、监督原责任并报告独立验收证据；主 agent 不做规划、实现或技术验收。用于继续跨仓 goal、协调多个 repo 升级或跟踪整体交付，不替代 PRM。 |
| [`periodic-maintenance`](./skills/workflow/periodic-maintenance/) | 06 周期维护的未启用源码入口：按有效决定核对公开仓当前文档与相关实现，准备有证据的普通 backlog 或待澄清草稿。用于维护规则审查和离线演练；真实运行仍受启用 HOLD 约束。 |
| [`runtime-recovery`](./skills/workflow/runtime-recovery/) | 运行恢复辅助——控制面、daemon、runner 不可用或执行者中断时，定位故障层并按已有授权恢复，由原责任方接回。用于 Multica 连不上、runner offline、review pending 或任务中断；不接管 PR 交付，不授权主机配置或凭据变更。 |
| [`shared-release`](./skills/workflow/shared-release/) | 04 自动化发布——合并至默认分支且前置检查通过后触发的自动化发布工作流，引用 shared-ci v0.5.0 发布模板与规范。用于指导 shared-* 库及各 repo 的自动化发布接线、版本决策与发布边界。 |
| [`team-workflow-audit`](./skills/workflow/team-workflow-audit/) | Audit an explicitly named team, repository, or project delivery workflow against evidence, current instructions, workflow fitness, and delivered outcomes. Use only when the user explicitly invokes $team-workflow-audit… |

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
| [`layered-ci-autofix`](./skills/repo/layered-ci-autofix/) | PRM 的 CI 诊断与原路径修复辅助。用于读取准确 PR head 的失败信号、定位仓库约束并交回原执行者，或执行已交回的具体修复；不启动第二条 PR watcher，不接管 Draft，不安装 CI 或自行合并。 |
| [`layered-data-warehouse`](./skills/repo/layered-data-warehouse/) | 给一个项目把数据仓库"分层重构/梳理成型"——先扫描项目真实的数据模型(ORM/DDL/DB/已有派生服务/导入管线),再套标准数仓分层(ODS/DWD/DIM/DWS/ADS,附 medallion 与 dbt 交叉映射),产出一份可演进的 warehouse 蓝图:分层清单、一致性维度、指标口径登记、SCD 与增量幂等策略、血缘、项目专属 red-lines、gap 分析与分阶段 refine 计划。产物是设计蓝图不是实现代码… |
| [`multica-issue`](./skills/repo/multica-issue/) | 从当前 repo 定位 Multica project，把已确认的 bug/feature/架构实施需求或现有 plan/tasks 交给 Dev Team；记录问题历史与 ineffective/regression 关系，或创建不派发 Agent 的 Outcome Check。适用于明确提 issue、交团队实现、批量入库或等待发布后验证；现象反馈与诊断请求先澄清，不自动派发。 |
| [`owner-decision-loop`](./skills/repo/owner-decision-loop/) | Resolve owner choices or unresolved repair investigations when existing repository authority cannot decide. Use for product, scope, architecture, policy or evidence conflicts, or failed diagnosis by Team Lead or the o… |
| [`repo-kit`](./skills/repo/repo-kit/) | 用 shared-ci 的模板与检查器让一个 repo 满足统一的 repo 合同（薄 AGENTS、layer 表、同入口 verify、shared-ci caller、required 汇总 gate、PR 模板、CODEOWNERS），或接入共享库新版本，或从现有 repo 拆出共享库。三种模式：init（新建或补齐）、adopt（接入/升级共享库）、split（拆出 SDK/共享库，保留历史）。取代 layered-ag… |
| [`teamwork`](./skills/repo/teamwork/) | Synchronous Dev Team workflow 02 execution — spec-first, plan-led implementation from single-source roles to a non-Draft PR handoff. |
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

### 安装 skills

本地开发使用目录软链，默认将本仓全部 19 个 skill 安装到 `~/.claude/skills/`：

```bash
scripts/install-symlinks.sh
```

脚本不支持按名称选择；可用 `CLAUDE_SKILLS_DIR` 指定目标目录，例如 Codex：

```bash
CLAUDE_SKILLS_DIR="$HOME/.codex/skills" scripts/install-symlinks.sh
```

`~/.codex/skills/`、`~/.agents/skills/`、`~/.claude/skills/` 中的本地链接由实际目标决定内容版本；同名或相同描述不证明同源。
此脚本只安装 skill 链接，不安装下述 CLI 公共规范入口。

Claude Code plugin marketplace：

```text
/plugin marketplace add LeePepe/agent-skills
/plugin install <skill>@agent-skills
```

### CLI 默认规范

这是独立于 skill 安装的全局指令入口。
让普通 Codex／Claude CLI 会话也遵守[公共执行规范](skills/workflow/execution-contract.md)，无需显式调用 skill：

```bash
python3 scripts/install-cli-workflow.py --client codex --client claude
python3 scripts/install-cli-workflow.py --client codex --client claude --check
```

安装器在当前配置目录的全局 `AGENTS.md`／`CLAUDE.md` 中维护一个引用源码的薄入口，保留其他指令；
Codex 已有非空 `AGENTS.override.md` 时使用该生效文件。源码 checkout 需要保留，迁移后重跑安装器。
新会话加载入口；已启动会话需显式读取规范。全局入口不授予主 agent 身份：规划 worker 确定／校验 Goal 与 Targets，
主 agent 只分配监督、路由和报告；委派时须传角色／来源绑定、原始需求及受审基线，不能假设子会话继承。
这是共享工具权限下的行为规范，不是技术隔离；worker 不因读取全局指令或使用 helper 升为协调者。
其他 CLI 在其受支持的全局指令入口引用同一文件；本安装器只配置这两种客户端，不部署远端 Dev Team runtime。

## 校验

```bash
python3 scripts/validate_skills.py
python3 scripts/gen_registry.py --check
```

CI(`.github/workflows/validate-skills.yml`)在每个 PR 上运行同样的检查。
