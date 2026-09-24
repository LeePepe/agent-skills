# Issue body 模板

四套 body 模板,对应 SKILL.md 的四条路径。用 `--description-file` 传给 `multica issue create`。

**结构来源**(distill 自 [mattpocock/skills](https://github.com/mattpocock/skills)):
- 骨架 = triage 的 **AGENT-BRIEF**(Current / Desired / Key interfaces / Acceptance / Out-of-scope)
  —— 描述**行为契约**而非过程,让 issue 即使放几天、代码变了也仍然可用。
- Acceptance 勾选框 + 依赖排序 = **to-issues**。
- bug 的「先有失败信号」= **diagnosing-bugs**。

**三个实现类模板都有两个 VitalStride 专属槽位**,由 repo 的事实源填充:
- **该层 red_lines** —— 从 `Packages/<layer>/CONTEXT.md` frontmatter 的 `red_lines` 抄,修的时候不能踩。
- **该层 test** —— 从同 frontmatter 的 `test` 抄,修完跑这条验证。

> **路径规则的放松**:AGENT-BRIEF 原则是「不写文件路径,会过时」。VitalStride 现有 issue(如 MY-1070)
> 会带一段 `## 现状基线(basis: main)` 列具体文件/行号 —— 这是**刻意**的,给 dev team 一个精确起点。
> 所以本模板**允许**一段带 `basis:<ref>` 标注的现状基线;但**行为契约段(Desired/Acceptance)仍不绑路径**,
> 只描述行为。两者分工:基线段=当下事实(会过时,标了 ref 就行),契约段=目标行为(durable)。

---

## 模板 1 —— Bug

```markdown
## Category
bug

## 现状基线 (basis: main)
<可选。当前相关代码的事实:哪个文件/类/方法涉及,当前行为怎么实现的。标了 basis ref 即可,允许过时。>

## Current behavior(坏在哪)
<现在实际发生什么。这是被复现的错误行为。>

## Desired behavior(应该怎样)
<修好后应该发生什么。明确边界条件与错误处理。不绑文件路径,只描述行为。>

## Repro / 失败信号(diagnosing-bugs 前置)
<一个会因这个 bug 变红的 tight 信号:失败测试名 / repro 步骤 / 崩溃栈 / 错误日志。
若暂时构造不出,把「先构造一个可复现信号」写成 Acceptance 的第 1 条。>

## Problem history
- **problem_fingerprint**: `<product_area>|<behavior_or_invariant>|<user_visible_symptom>`
- **affected version/build**: <若可得>
- **evidence source**: <Owner use / user report / telemetry / test>
- **relation**: <duplicate_of / ineffective_fix_for / regression_of / related_to / none>
- **related issue**: <MY-XXXX 或 None>

## Key interfaces(行为契约,非过程)
- `TypeName` — 该改什么、为什么
- `funcName()` 返回 — 现在返回什么 vs 应该返回什么

## Acceptance criteria
- [ ] <可测的验收 1>
- [ ] <可测的验收 2>

## Out of scope
- <明确不在本 issue 处理的相邻问题>

## Layer 约束(来自 Packages/<layer>/CONTEXT.md)
- **layer**: <落在哪层>
- **red_lines**(修的时候不能踩): <抄该层 frontmatter red_lines>
- **test**(修完跑这条): `<抄该层 frontmatter test>`
```

---

## 模板 2 —— Feature task(speckit sub-issue)

一个 sub-issue = tasks.md 的一个 task。标题 `[T###] [Story] Brief`。

```markdown
## Parent
<parent feature issue 的 key,如 MY-1234;指向 specs/NNN-name/spec.md>

## What to build
<这个 task 交付的端到端行为(在**本 layer 范围内**)。描述行为,不逐文件写实现。
若 speckit 的 plan/prototype 产出了精确的决策片段(状态机 / schema / 类型形状),可内联那几行。>

## Acceptance criteria
- [ ] <可 demo / 可测的验收 1>
- [ ] <可 demo / 可测的验收 2>

## Blocked by
<依赖的具体 task key(如 MY-1235);无则写 "None — 可立即开始"。与 --stage 配合。>

## Constitution refs
<reference 宪法章节,如「Constitution §III SPM Package 优先」;不重述规则。>

## Layer 约束(来自 Packages/<layer>/CONTEXT.md)
- **layer**: <本 task 落在哪层>
- **depends_on**: <该层允许依赖的 layer,别引入反向依赖>
- **red_lines**: <抄该层 frontmatter red_lines>
- **test**(交付前跑): `<抄该层 frontmatter test>`
```

**Parent issue** body(feature 总述)简版:

```markdown
## Feature
<一句话概括这个功能对用户的价值>

## Spec
specs/NNN-name/spec.md(+ plan.md / tasks.md)

## Tasks(按 stage)
- Stage 1: [T001] ... (MY-xxxx)
- Stage 2: [T002] ... (MY-xxxx)
- Stage 3: [T003] ... (MY-xxxx)

## Constitution refs
<涉及的宪法章节>
```

---

## 模板 3 —— 技术架构 / tech-context

标题 `[Arch] <一句话>`。用于改架构方向 / tech-context 更新 / 违宪例外(须先有 ADR)。

```markdown
## Decision
<要做的架构决策,一句话。>

## Context
<为什么现在要做:什么约束/需求逼出这个决策。>

## Consequences
<决策带来的正/负后果。哪些 layer 受影响。>

## 受影响 layer 的 depends_on 变更
- <layer A>: depends_on <旧> → <新>
- <是否新增/删除 layer>

## Migration steps
1. <迁移步骤,按 layer,一层一 commit>
2. ...

## ADR / Constitution
<若违反现宪法:指向 docs/adr/NNNN-*.md 或宪法版本 bump。先有它,再有本 issue。>

## Acceptance criteria
- [ ] frontmatter 防腐校验通过(depends_on / test 与实际一致)
- [ ] <其他可测验收>
```

---

## 模板 4 —— Outcome Check(不派发实现 Agent)

标题 `[Outcome Check] <origin issue>: <behavior>`。

```markdown
## Outcome to confirm
<实际发布和使用后,什么行为才证明原任务真的解决。>

## Origin and delivery
- **origin issue**: <MY-XXXX>
- **delivery issue**: <MY-XXXX>
- **problem_fingerprint**: `<stable fingerprint>`
- **PR / merge SHA**: <若可得>

## Release exposure
- **channel**: <TestFlight / App Store / production / internal>
- **version/build**: <已知值或 pending_release>
- **available_at**: <已知值>

## Waiting contract
- **wait_owner**: <明确的人>
- **next_event**: <TF build available / Owner first use / telemetry window complete>
- **wake_condition**: <可判断的事件>
- **not_before**: <时间或 build>
- **deadline**: <可选;到期只升级缺证据,不自动判定成功>

## Confirmation evidence
- **effective**: <需要的正向使用/遥测证据>
- **ineffective**: <同 fingerprint 在包含修复的 build 上仍出现>
- **regressed**: <先 confirmed effective,后续 build 再出现>
```

Outcome Check 保持 `backlog`,assign 给 wait owner,并写 `outcome_wait` metadata。它不进入 Dev Team
dispatch,所以不追加 Working Directory 尾段。

---

## 强制尾段 —— Working Directory 隔离(每个实现类 issue 都要带,CRITICAL)

**每一个实现类** issue body(bug / feature-task / arch 三类)末尾**必须**追加下面这段,
原样照抄(`<project-slug>` 换成小写项目名,如 `vitalstride`)。放在 body 最后。

```markdown
## Working Directory(CRITICAL — 禁止污染用户主 checkout)

daemon 已在 `~/multica_workspaces/<workspace>/<task-id>/workdir/` 下为你建好隔离 worktree。
**只在那个 workdir 里工作。**

- **绝对不要** `cd ~/Development/<Project>`,**绝对不要**在用户主 checkout 里 `git checkout` / `git checkout -b` / `git fetch` / `git push`。
- 分支操作(建分支、commit、push、开 PR)全部在 daemon 给的 workdir 内完成。
- `git push` 用 `--no-verify`(pre-push hook 在 workdir 内无效,且会超时)。
```

> **为什么(不删这段)**:FS/TL agent 的默认行为是在用户的 `~/Development/<Project>` 里直接
> `git checkout -b`,并把新分支 upstream 错设成用户当前分支 → 用户手动开的分支被 agent 的 push 覆盖。
> 这是已复现的事故(2026-07 一次 TestFlight 发版 PR 分支被 i18n pipeline 冲掉,根因即此)。
> issue body 没这段 = FS 回退到污染主 checkout 的默认路径。**这段是护栏,不是可选说明。**

---

## 填充清单(落任何 issue 前自检)

- [ ] 标题前缀对(`[Bug]` / `[T###] [Story]` / `[Arch]` / `[Outcome Check]`)
- [ ] `## Layer 约束` 的 red_lines + test **来自该层 CONTEXT.md frontmatter**,不是编的
- [ ] Acceptance 至少一条、且**可测**(能对应一条命令 / 一个可观察结果)
- [ ] 行为契约段不绑文件路径(基线段可以,标 basis ref)
- [ ] 跨 2+ layer → 已拆成多 issue,不是一个大 issue
- [ ] 与宪法冲突 → 已先改宪法/写 ADR
- [ ] **每个实现类 body 末尾都带了 `## Working Directory` 强制尾段**(见上,防主 checkout 污染)
- [ ] Bug 已生成 `problem_fingerprint` 并搜索 active + closed 历史;关系与 affected build 有证据
- [ ] Outcome Check 有 wait owner / next event / wake condition,保持 backlog,且没有 Dev Team dispatch
