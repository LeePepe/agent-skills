# Speckit bridge —— 功能 / 架构路径的完整流程

本 skill 不重新实现 speckit,它**编排**已装好的 speckit skill(`/speckit-specify` 等)+
把产出**桥接**到 Multica issue。前提:目标 repo 有 `.specify/`(否则走 SKILL.md §降级)。

参照 `specs/README.md` 的既有约定 —— 本文件是它的可执行展开。

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
- **按 layer 拆,不用 vertical slice**:
  - 改动只落 1 个 layer → 一个 task。
  - 跨 2+ layer → 拆成 N 个各自可独立 `swift build/test` 的子任务,一层一 commit。
  - 单层内仍很大 → 按技术切面再拆(纯逻辑 → 输入/校验 → 处理/编排 → 输出转换 → fixture → 文档 → 迁移)。

  > 这条**覆盖** mattpocock to-issues 的「每个 slice 切穿所有层」。VitalStride 的 `AGENTS.md`
  > §「按 layer 收窄」明确要求按 layer 拆(层是 agent 的工作单元,一层一 commit 便于 `swift test`
  > 秒级验证 + 减少跨层 PR 冲突)。服从 repo 规则。

### 4. 逐 task 落 Multica issue(不跑 speckit-implement)

**关键:不执行 `/speckit-implement`。** 实现交给 Multica pipeline。用 `references/multica-cli.md`
的命令把 tasks.md 桥接成 issue:

1. 建 **parent issue**(feature 总述,body 见 `issue-templates.md` 模板 2 的 parent 版,
   指向 `specs/NNN/spec.md`)。
2. tasks.md 每个 task → 一个 sub-issue:
   - `--parent <parent-key>` `--project $PROJECT_ID`
   - 标题原样用 tasks.md 的 `[T###] [Story] Brief`
   - body 用 feature-task 模板,**Layer 约束段从该 task 所属 layer 的 CONTEXT.md frontmatter 抄**
     (red_lines + depends_on + test)
   - tasks.md 的依赖组 → `--stage N`(同 stage 全完成才唤醒 parent)
3. **blocker 先建**,拿到真实 key 后依赖方在 Blocked-by 段引用它。
4. **spec 先入库门禁**:feature 路径的 issue 必然引用 `specs/NNN/spec.md`。dispatch 前**先确保这些
   spec(+ 相关 plan/tasks、若有新 ADR/宪法 bump)已合进已核验的默认分支**——隔离 workdir 的 FS 读执行基线,
   spec 没合并会踩空。缺失时在 task worktree 准备设计 PR,正常过 hooks/verify/计划审查与 Owner hold,
   交 W4 PR Manager,合并后复核再 dispatch。命令见
   `references/multica-cli.md` §「spec 先入库门禁」;主流程见 `SKILL.md` 第 4 步同名小节。
5. dispatch:按 `multica-cli.md` 的唯一 dispatch 流程检查 hold、active/family runs,再启动就绪的
   parent 或子任务,不同时重复启动重叠范围。

> 若 repo 装了 speckit 的 `/speckit-taskstoissues`,它是用 **GitHub MCP** 建 GitHub issue 的
> —— 与本 workflow(Multica issue)**不同**,**不要**用它。本 skill 走 Multica CLI。

---

## 架构路径:先改 tech-context / 宪法,再落 issue

判断改动性质,二选一。

### C1. 纯 tech-context 补充/修正(不违反红线)

例:补一层 CONTEXT.md 的说明、修正一条 test 命令、澄清数据流。

1. 在专用 task worktree 编辑 AGENTS 指定的叶子上下文:repo-kit 的 `tech-context.md` 或旧仓
   `CONTEXT.md`;保留现有 frontmatter 的 layer、依赖与 gate。
2. 落一个 `[Arch]` issue 记录这次 tech-context 变更(模板 3),让 pipeline 的 frontmatter 防腐
   hook / CI 校验一致性。

### C2. 改架构方向 / 违反现宪法

例:加 layer、换依赖方向、放松并发或隐私约束。

**顺序不能反:先立规矩,再落实现。**

1. **先**在 task worktree 提出宪法/ADR 变更,经计划审查与 Owner 批准后发布:
   - 跑 `/speckit-constitution` 更新 `.specify/memory/constitution.md` + 版本 bump;或
   - 写 `docs/adr/NNNN-<slug>.md`(记录 Decision / Context / Consequences / 例外原因)。
   - 依据:`specs/README.md`「与 Constitution 冲突 → 先改 Constitution(走 ADR + 版本 bump),
     再写 spec」+ constitution「例外仅限……且必须在 ADR 中显式记录原因」。
2. **再**落实现 issue(模板 3),body 的 `## ADR / Constitution` 段指向第 1 步的产物。
3. 若架构变更牵出多层实现工作 → 可退回功能路径,用 speckit plan/tasks 把实现拆成按 layer 的 sub-issue。

---

## 降级(无 speckit)

目标 repo 无 `.specify/` 时:
- 功能路径退化为「直接起草一个 feature issue + 清晰 acceptance」(模板 2 的 parent 版,单 issue),
  在回复里提示用户「本 repo 未初始化 speckit,如需 spec-driven 流程可先 init」。
- 架构路径退化为「在 issue body 内联记录 Decision/Consequences」,提示补建 `docs/adr/`。
