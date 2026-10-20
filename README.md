# agent-skills

可复用的 Claude Code / Codex agent skills,按 **workflow / repo** 组织。
每个 skill 是 `skills/<category>/<name>/` 下的一个目录,含 `SKILL.md`(frontmatter + 指令)
与可选 `references/`、`scripts/`、`assets/`、`templates/`。

开发执行遵守独立的 [`goal-target-task` skill](https://github.com/LeePepe/user-skills/blob/main/skills/goal-target-task/SKILL.md)。

## Skills

> 下表由 `scripts/gen_registry.py` 从各 `SKILL.md` 的 frontmatter **自动生成**,勿手改。
> 机器可读索引见 [`skills.json`](./skills.json)。

<!-- SKILLS:BEGIN -->
### Workflow 编排（`skills/workflow/`）

| Skill | 作用 |
|---|---|
| [`multica-delivery-supervisor`](./skills/workflow/multica-delivery-supervisor/) | Supervise named Multica projects and delivery PRs, or resume tasks affected by a shared blocker after the Owner reports recovery, preserving existing Dev Team roles and authority. |
| [`orchestrate`](./skills/workflow/orchestrate/) | 跨仓拆分与编排——把已确认的多 repo 目标拆成可交付切片，按依赖交给 Dev Team 或 subagent，协调原责任并按完整目标验收；自己不写产品代码。用于继续跨仓 goal、协调多个 repo 升级或跟踪整体交付，不替代 PRM。 |
| [`periodic-maintenance`](./skills/workflow/periodic-maintenance/) | 06 周期维护的未启用源码入口：按有效决定核对公开仓当前文档与相关实现，准备有证据的普通 backlog 或待澄清草稿。用于维护规则审查和离线演练；真实运行仍受启用 HOLD 约束。 |
| [`runtime-recovery`](./skills/workflow/runtime-recovery/) | 运行恢复辅助——控制面、daemon、runner 不可用或执行者中断时，定位故障层并按已有授权恢复，由原责任方接回。用于 Multica 连不上、runner offline、review pending 或任务中断；不接管 PR 交付，不授权主机配置或凭据变更。 |
| [`team-workflow-audit`](./skills/workflow/team-workflow-audit/) | Audit an explicitly named team, repository, or project delivery workflow against evidence, current instructions, workflow fitness, and delivered outcomes. Use only when the user explicitly invokes $team-workflow-audit… |
| [`to-tickets`](./skills/workflow/to-tickets/) | Turn an accepted spec and plan into vertical product slices plus a dependency graph of layer-scoped implementation tasks. Use when Planner Lead creates or refines Spec Kit `tasks.md` or Multica child issues for work t… |

### Repo 工程（`skills/repo/`）

| Skill | 作用 |
|---|---|
| [`layered-ci-autofix`](./skills/repo/layered-ci-autofix/) | PRM 的 CI 诊断与原路径修复辅助。用于读取准确 PR head 的失败信号、定位仓库约束并交回原执行者，或执行已交回的具体修复；不启动第二条 PR watcher，不接管 Draft，不安装 CI 或自行合并。 |
| [`multica-issue`](./skills/repo/multica-issue/) | 从当前 repo 定位 Multica project，把已确认的 bug/feature/架构实施需求或现有 plan/tasks 交给 Dev Team；记录问题历史与 ineffective/regression 关系，或创建不派发 Agent 的 Outcome Check。适用于明确提 issue、交团队实现、批量入库或等待发布后验证；现象反馈与诊断请求先澄清，不自动派发。 |
| [`owner-decision-loop`](./skills/repo/owner-decision-loop/) | Resolve owner choices or unresolved repair investigations when existing repository authority cannot decide. Use for product, scope, architecture, policy or evidence conflicts, or failed diagnosis by Team Lead or the o… |
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
