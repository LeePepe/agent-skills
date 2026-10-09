# Speckit bridge —— 功能 / 架构路径的完整流程

本 skill 不重新实现 speckit,它**编排**已装好的 speckit skill(`/speckit-specify` 等)+
把产出**桥接**到 Multica issue。前提:目标 repo 有 `.specify/`(否则走 SKILL.md §降级)。

参照 `specs/README.md` 的既有约定。先复用、校验、补齐已有 spec/plan/tasks；以下生成步骤只用于缺失产物，
已有计划继续走必要 spec/plan 审查。设计修改/workflow refine 的基本方案由 Owner 与 CLI 先确定，团队负责实现。

---

## 功能路径:specify → clarify → plan → tasks → 逐 task 落 issue

### 1. specify

```
/speckit-specify <用户的功能描述>
```
产出 `specs/NNN-name/spec.md`(NNN 自增,看 `ls specs/` 现有最大编号 +1)。

### 2. clarify(grilling 风格)

```
/speckit-clarify
```
打磨 spec 里的模糊点。风格纪律(distill 自 mattpocock grilling):
- **一次只问一个问题**,等回答再问下一个(一次抛一堆会让人懵)。
- **每个问题附上你的推荐答案**。
- **能靠读代码回答的,先读代码,别问用户**。

### 3. plan + tasks

```
/speckit-plan     # → specs/NNN-name/plan.md
/speckit-tasks    # → specs/NNN-name/tasks.md,task ID 形如 [T###] [Story]
```

**两条硬约束**(写进 plan/tasks,也是 review 时会被 gate 的点):
- **reference constitution 章节**,不重述规则(如「见 Constitution §II Swift 6 Strict Concurrency」)。
- **按目标、真实依赖和目标仓 PR 单元拆**，不以 layer 数机械切任务。plan 记录本次方案版本、任务、依赖、
  完成条件与下一动作，引用适用版本的 repo guide/shared 文档；通用政策留在这些来源。

### 4. 逐 task 落 Multica issue(不跑 speckit-implement)

**关键:不执行 `/speckit-implement`。** 实现交给 Multica pipeline。用 `references/multica-cli.md`
的命令把 tasks.md 桥接成 issue:

1. 建 **parent issue**(feature 总述,body 见 `issue-templates.md` 模板 2 的 parent 版,
   指向 `specs/NNN/spec.md`)。
2. tasks.md 每个 task → 一个 sub-issue:
   - `--parent <parent-key>` `--project $PROJECT_ID`
   - 标题原样用 tasks.md 的 `[T###] [Story] Brief`
   - body 用 feature-task 模板，Layer 约束段引用该 task 涉及层的 CONTEXT.md frontmatter
     (red_lines + depends_on + test)
   - tasks.md 的依赖组 → `--stage N`(同 stage 全完成才唤醒 parent)
3. **blocker 先建**,拿到真实 key 后依赖方在 Blocked-by 段引用它。
4. **spec 先入库门禁**：核实引用的 spec/plan/tasks/ADR 在实际执行基线可读且匹配批准版本。
   缺失时保持待派发，只在授权内补文档 PR，通过既有 gates 和审批后复核；详见 `SKILL.md` 第 4 步与
   `multica-cli.md` §「spec 先入库门禁」。
5. dispatch:parent(或第一个 stage 的 issues)assign 给 "Dev Team" squad + 转 todo + 验证 run(两步+验证)。

> 若 repo 装了 speckit 的 `/speckit-taskstoissues`,它是用 **GitHub MCP** 建 GitHub issue 的
> —— 与本 workflow(Multica issue)**不同**,**不要**用它。本 skill 走 Multica CLI。

---

## 架构路径:先改 tech-context / 宪法,再落 issue

判断改动性质,二选一。

### C1. 纯 tech-context 补充/修正(不违反红线)

例:补一层 CONTEXT.md 的说明、修正一条 test 命令、澄清数据流。

1. 直接编辑对应层 `Packages/<X>/CONTEXT.md`(含 frontmatter `layer`/`depends_on`/`red_lines`/`test`)
   或顶层 `CONTEXT.md` 的 `canonical_roles`。
2. 落一个 `[Arch]` issue 记录这次 tech-context 变更(模板 3),让 pipeline 的 frontmatter 防腐
   hook / CI 校验一致性。

### C2. 改架构方向 / 违反现宪法

例:加 layer、换依赖方向、放松并发或隐私约束。

先确认 Owner 与 CLI 已定基本方案；政策/权限变化另需明确授权，不能为了实现自行放松红线。
超出当前约定的新方案回到同一需求沟通入口，Owner 确认该版可以执行后才交接；当前执行版不被讨论自动改写。

1. **先**更新宪法或写 ADR:
   - 跑 `/speckit-constitution` 更新 `.specify/memory/constitution.md` + 版本 bump;或
   - 写 `docs/adr/NNNN-<slug>.md`(记录 Decision / Context / Consequences / 例外原因)。
   - 依据:`specs/README.md`「与 Constitution 冲突 → 先改 Constitution(走 ADR + 版本 bump),
     再写 spec」+ constitution「例外仅限……且必须在 ADR 中显式记录原因」。
2. **再**落实现 issue(模板 3),body 的 `## ADR / Constitution` 段指向第 1 步的产物。
3. 若架构变更有多个交付目标 → 复用功能路径，按目标仓合同和依赖安排 sub-issue，不按 layer 数切分。

---

## 降级(无 speckit)

目标 repo 无 `.specify/` 时:
- 功能路径退化为「直接起草一个 feature issue + 清晰 acceptance」(模板 2 的 parent 版,单 issue),
  在回复里提示用户「本 repo 未初始化 speckit,如需 spec-driven 流程可先 init」。
- 架构路径退化为「在 issue body 内联记录 Decision/Consequences」,提示补建 `docs/adr/`。
