---
name: multica-issue
description: 向 Multica dev team 提交新 issue,让 dev team(Team Lead → Fullstack Engineer → AI Reviewer → PR Manager)完成任务。给一句用户输入,skill 会:按当前 repo 的 github remote 反查正确的 Multica project;判定输入属于 bugfix / 新功能 / 技术架构(tech-context)变更;bug 会检索同一问题历史并记录 duplicate / ineffective fix / regression 关系;需要等待 TestFlight 或实际使用时可建立不派发 Agent 的 Outcome Check。实现类 issue 默认直接派发。当用户想「提个 issue 给 dev team / 让 dev team 做 X / 提 bug / 记录复发问题 / 等 TF 使用后验证 / 提新功能需求 / 改技术架构 / 把 tasks 批量入 Multica」时使用。
user-invocable: true
---

# Multica Issue — 向 dev team 提交 issue

把「起草一个 issue 并交给 Multica dev team」变成一条可靠流程。核心:**issue 是 dev team 的
工作输入**,起草质量直接决定 FS 是否返工、Reviewer 是否打回。所以这个 skill 做三件事:

1. **定位** —— 从当前 repo 反查它绑定的 Multica project(不 hardcode)。
2. **分类 + 打磨** —— 判定 bug / 新功能 / 架构变更,按类型决定是否先用 speckit 把需求写清。
3. **落 issue + dispatch/wait** —— 用 repo 自带的事实源(layer map + red_lines + test)填充 issue,
   按依赖顺序建好,派发前**自动确保引用的 spec/ADR 已合进 `main`**(隔离 workdir 的 FS 只读 main),
   再**默认直接派发**给 Dev Team squad(assign + 转 todo + 验证 run 起来),不停在 backlog。

**方法论借鉴**:distill 自 [`mattpocock/skills`](https://github.com/mattpocock/skills) 的四个
适配技巧 —— AGENT-BRIEF 结构、diagnosing-bugs「先有失败信号」、to-issues「acceptance + blocker 先建」、
grilling「一次一问 + 附推荐答案 + 能查码就查」。**不照搬** triage 的 label 状态机(Multica 无 label)
和 to-issues 的 vertical-slice 强切所有层(与「按 layer 拆」冲突,见下)。

**先读**:`references/multica-cli.md`(命令配方)、`references/issue-templates.md`(body 模板)、
`references/speckit-bridge.md`(speckit / 架构流程)。这三个是执行细节,本文件是主流程。

---

## 前提检查

```bash
command -v multica >/dev/null || { echo "multica CLI 未安装 → 先 multica setup"; exit 1; }
git rev-parse --show-toplevel >/dev/null 2>&1 || { echo "不在 git repo 内"; exit 1; }
```

---

## 第 1 步:定位 project(repo → Multica project)

不要 hardcode project id。按 `references/multica-cli.md` §「project 反查」执行:

1. 取当前 repo 的 github remote URL(规范化:去 `.git` 后缀、转小写)。
2. 反查:遍历 `multica project list` → 对每个 project 跑 `multica project resource list <id>` →
   匹配 `resource_type == github_repo` 且 `resource_ref.url` == 本 repo remote → 命中即为目标 project。
3. 命中 → 记住 `PROJECT_ID`;**未命中 → 停下**,告诉用户「本 repo 没绑定任何 Multica project」,
   让用户手动指定 project id 或先 `multica project resource` 绑定。不要瞎猜。

同时探测**上下文能力**(决定后续走哪条路、能填多少):

```bash
ls .specify/memory/constitution.md 2>/dev/null   # 有宪法 → 任何路径先读它
ls AGENTS.md 2>/dev/null                          # 有 layer map → 能按 layer 拆 + 带 red_lines
ls -d specs 2>/dev/null                           # 有 specs → 新功能走 speckit;看现有编号定新目录号
ls -d docs/adr 2>/dev/null                        # 有 ADR → 架构变更走 ADR 流
```

**任何路径,动手前先读 `constitution.md`(若存在)**。若用户需求与红线冲突 → **先改宪法(ADR +
版本 bump),再落 issue**,不要落一个注定被 Reviewer 打回的 issue。

---

## 第 2 步:分类意图

按用户输入判定四类之一。**模糊时用 grilling 风格确认:一次只问一个问题,每问附上你的推荐答案,
能靠读代码回答的就先读代码、别问用户。**

| 类别 | 触发信号 | 走哪条路 |
|---|---|---|
| **bug** | 「X 坏了 / 报错 / 崩溃 / 行为不对 / 数据错」 | 路径 A —— 直接落 issue,**不走 speckit** |
| **新功能** | 「加 / 支持 / 新页面 / 新能力 / 新交互」 | 路径 B —— speckit 全链,一 task 一 issue |
| **技术架构 / tech-context** | 「改架构 / 加 layer / 换依赖方向 / 改缓存或并发策略 / 与现宪法冲突」 | 路径 C —— 先改 tech-context/宪法,再落 issue |
| **效果验证 / Outcome Check** | 「等 TestFlight / 发版 / 实际使用后再确认是否解决」 | 路径 D —— 建显式等待记录,不派发实现 Agent |

判不准时,优先问一个能区分的问题,例如:「这是修一个既有行为(bug),还是要一个当前没有的能力
(feature)?」

---

## 第 3 步:执行路径

### 路径 A —— Bug

distill:diagnosing-bugs +  AGENT-BRIEF。详见 `references/issue-templates.md` §bug。
涉及既有问题、修复后仍出现或复发时,同时读 [problem-history.md](references/problem-history.md)。

1. **先要一个 tight 失败信号**(diagnosing-bugs 的核心)。问/找:有没有一个会**因这个 bug 变红**的
   信号 —— 失败测试、一段 repro 步骤、崩溃栈、错误日志?
   - 有 → 写进 issue 的「Repro / 失败信号」段。
   - 没有、且暂时构造不出 → **把「先构造一个可复现信号」本身写成 issue 的第一条 Acceptance**,
     不要凭空描述「感觉不对」。给 dev team 一个能收敛的起点。
2. **检索问题历史**:按 `problem-history.md` 生成稳定 `problem_fingerprint`,搜索 active + closed issue。
   确认 `duplicate_of`、`ineffective_fix_for`、`regression_of` 或 `related_to`,并记录 affected
   version/build 与证据来源。标题相似只用于发现候选,不直接建立关系。
3. **映射 layer**:从报错文件/路径对照 `AGENTS.md` 的 layer map,定位落在哪个 layer →
   读该层 `CONTEXT.md` 的 frontmatter,取 `red_lines`(修的时候不能踩)+ `test`(修完跑哪条验证)。
4. **填 body**:用 bug 模板(Category / Current / Desired / Repro-信号 / Problem history / Key interfaces /
   Acceptance / Out-of-scope / 该层 red_lines + test)。
5. **标题** `[Bug] <layer>: <一句话>`;设 `--priority`。单个 issue 即可,除非 bug 跨 2+ layer
   → 按 layer 拆成子 issue(见下方「跨层拆分」)。

### 路径 B —— 新功能(speckit 全链)

对齐 `specs/README.md` 的约定:specify → clarify → plan → tasks → **逐 task 落 Multica issue,
不跑 `/speckit-implement`**(实现走 Multica pipeline)。完整命令序列见 `references/speckit-bridge.md`。

1. `/speckit-specify <用户输入>` → `specs/NNN-name/spec.md`。
2. `/speckit-clarify` 打磨模糊点(grilling 风格:一次一问 + 附推荐 + 能查码就查)。
3. `/speckit-plan` → `plan.md`;`/speckit-tasks` → `tasks.md`。
   - plan / tasks **必须 reference constitution 章节**(不重述规则)。
   - **按 layer 拆分,不用 vertical slice**:改动只落 1 层 = 一个 task;跨 2+ layer = 太大 =
     拆成 N 个各自可 `swift build/test` 的子任务(一层一 commit)。这是 `AGENTS.md` §「按 layer
     收窄」的硬规则,**压过** mattpocock to-issues 的「一片切所有层」。
4. **逐 task 落 issue**(命令见 `references/multica-cli.md`):
   - 先建一个 **parent issue**(feature 总述,body 指向 `specs/NNN/spec.md`)。
   - 每个 task → 一个 sub-issue:`--parent <parent-key> --project $PROJECT_ID`,标题
     `[T###] [Story] Brief`(spec-kit handoff 约定),body 用 feature-task 模板(What /
     Acceptance / 该层 red_lines + test / Blocked-by)。
   - **有依赖顺序的 task 用 `--stage N`**:同一 stage 的 sub-issue 全部完成才唤醒 parent
     (Multica staged barrier),对应 tasks.md 的依赖组。**blocker 先建**,拿到真实 issue key
     后再让依赖方引用它。
5. **dispatch**:把 parent(或第一个 stage 的 issues)assign 给 **"Dev Team" squad** + 状态转 `todo`
   + 验证 run 起来(零 run 就 `rerun` 兜底)。默认直接派发,见第 4 步「默认直接派发」。

### 路径 C —— 技术架构 / tech-context 变更

详见 `references/speckit-bridge.md` §架构。先判断改动性质:

- **只是技术上下文补充/修正,不违反红线**(如补一层 CONTEXT.md 的说明、修正 test 命令) →
  直接更新对应层 `Packages/<X>/CONTEXT.md`(含 frontmatter `depends_on`/`red_lines`/`test`)
  或顶层 `CONTEXT.md` 的 `canonical_roles`,然后落一个「tech-context update」issue 记录变更
  (frontmatter 防腐 hook / CI 会 gate 一致性)。
- **改架构方向 / 违反现宪法**(加 layer、换依赖方向、放松并发或隐私约束) → **先** 写
  `docs/adr/NNNN-*.md`(或跑 `/speckit-constitution` 更新宪法 + 版本 bump),**再** 落实现 issue。
  对齐 `specs/README.md`「冲突先改宪法再写 spec」+ constitution「例外须 ADR 记录」。

body 用 tech-context/ADR 模板(Decision / Context / Consequences / 受影响 layer 的 `depends_on`
变更 / 迁移步骤 / Acceptance)。标题 `[Arch] <一句话>`。

### 路径 D —— Outcome Check

仅当任务是否成功必须等待 TestFlight、发版、硬件、实际使用或观察窗口时使用。先读
[problem-history.md](references/problem-history.md),用 Outcome Check 模板创建
`[Outcome Check] <origin issue>: <behavior>`。

- 保持 `backlog`,assign 给明确的等待负责人。
- 写入 `outcome_wait` 和当前 `task_effectiveness` metadata。
- `next_event`、`wake_condition`、release channel/build、`not_before` 必须明确。
- 不 assign Dev Team,不转 `todo`,不调用 `rerun`,不要求 Working Directory。
- 正向使用证据记录 `effective` 并关闭 check;仍有问题或复发则走路径 A 创建正常 Bug,
  关联 `ineffective_fix_for` 或 `regression_of`。

---

## 第 4 步:落 issue + dispatch(统一收口)

命令细节见 `references/multica-cli.md`。要点:

- **用 `--description-file` 传 body**(临时 md 文件),不要用 `--description` 拼长字符串
  —— 避免 `\n`/中文转义踩坑。
- **每个实现类 body 末尾必带 `## Working Directory` 强制尾段**(见 `references/issue-templates.md` §强制尾段)。
  这段是护栏:没它,FS agent 会回退到在用户主 checkout `~/Development/<Project>` 里 `git checkout -b`,
  把用户手动开的分支冲掉(2026-07 已复现事故)。**落任何 issue 前确认这段在 body 里。**
- **顺序**:blocker / parent 先建 → 拿到真实 `MY-XXXX` key → 依赖方引用它再建。

### dispatch 前置门禁 —— 引用的 spec/ADR 必须先在 `main`(CRITICAL,全自动)

**根因**:Multica FS agent 在**隔离 workdir** 从 `github/main` 起分支实现,只能读到 **main 上已合并**
的文件。而 spec/ADR 常诞生在你的主 checkout working tree(还没提交/合并)。若 issue body 引用了
`specs/...` 或 `docs/adr/...`,而这些文件**还没进 main**,则 FS/Reviewer 会因「引用了不存在的文件」
困惑或打回(2026-07-19 已复现:MY-1281/1285 引用未合并的 ADR-0010,必须先补 PR #291)。

**规则**:dispatch 前,对每个待派发 issue 做一次「引用文件在 main 存在性」检查。**全自动,不打断用户**——
检测到缺失 → 自动开设计文档 PR、等合并、再 dispatch。步骤(命令见 `references/multica-cli.md` §「spec 先入库门禁」):

1. **扫引用**:从每个 issue body 里 grep `specs/\S+` 和 `docs/adr/\S+` 的路径。无引用 → 跳过本门禁,直接 dispatch。
2. **查 main**:对每个被引用路径 `git cat-file -e github/main:<path>`(先 `git fetch github`)。全部存在 → 直接 dispatch。
3. **有缺失 → 自动补 PR**:
   - 从最新 `github/main` 切干净分支(`git fetch github` 后 `git checkout -b feat/<slug>-design-docs github/main`);
     working tree 有挡路的无关 tracked 改动就先 `git stash push -- <那些文件>`,切完不动它们。
   - **只 add 缺失的 spec/ADR + 它们依赖的规矩文件**(如宪法 bump、新 ADR);排除噪音(`firebase-debug.log`、
     `.specify/feature.json`)和无关 specs。
   - `git commit --no-verify` + `git push --no-verify -u github <branch>` + `gh pr create --base main`。
   - **确认 lint 范围**:VitalStride 的 `.swiftlint.yml` `included:` 只含 app targets + Packages,**不含
     `specs/`/`docs/`** → 纯文档 PR 不触发 `no_hardcoded_chinese`,CI 应全绿。别的 repo 先核对其 lint scope。
   - **监督 CI 到终态**(Monitor 或轮询 `gh pr checks`):auto-merge 开着就等自动合;没开则 CI 绿后 `gh pr merge`。
   - 合并后 `git fetch github` + `git cat-file -e github/main:<path>` 复核文件确已落 main。
4. **再 dispatch**:文件在 main 后,才走下面的「默认直接派发」。

> 例外:issue body **内联**了完整 spec(不靠 `specs/` 文件路径)时无需本门禁——但按 VitalStride 约定,
> spec 应落 `specs/` 版本管理,内联仅用于极小改动。跨多个 sub-issue 引用同一 spec 时,**一个设计文档 PR
> 覆盖全部引用**,不要每个 issue 开一个 PR。

### dispatch —— 默认直接派发(不问、不暂存)

**实现类 issue 的收尾动作就是「让 pipeline 真的跑起来」。实现类默认派发,不要停在 backlog 等人。**
只有当用户**明确说**「先别跑 / 只暂存 / 存草稿 / park」时才保持 backlog;没这句话 = 派发。

Outcome Check 是非实现型等待记录:按路径 D 保持 backlog + 明确 wait owner/next event,不进入本 dispatch 流程。

派发 = **三步,做完必须确认第 3 步为真**:

1. **assign** 给 **"Dev Team" squad**(不是 Team Lead 个人;`--to "Dev Team"` 或 `--to-id <squad-uuid>`)。
2. **转 todo**:`issue status <key> todo`。光 assign 不触发,必须转 todo 才 enqueue。
3. **验证 run 起来了**(关键,别省):`multica issue runs <uuid>` 看有没有 `queued`/`running`。
   - 有 → 派发成功,回显 key + URL。
   - **零 run**(assign+todo 没能 enqueue,已知会发生)→ **`multica issue rerun <uuid>` 兜底**,
     再查一次 `runs` 确认变 `queued`。**没确认到 run 就不算派发完成**,不要回报「已派发」。

> 为什么加第 3 步:实测存在「issue 已 assign+todo 但零 run」卡死(follow-up issue 尤甚),
> Supervisor 的 autopilot @mention 无效、只会反复 escalate,唯一解锁靠人 assign+触发。
> `rerun` 只对「有过 run」的 issue 有效——但 assign+todo 已经产生首个 run 记录后,rerun 就能兜底重入队。

- **回显**:每条新建 issue 打印 `identifier`(MY-XXXX)+ URL + 当前 run 状态。提醒用户后续 pipeline 是
  TL → FS(开 PR)→ AI Reviewer → TL merge(见 `AGENTS.md` §FS/TL workflow)。

---

## 跨层拆分(贯穿 A-C 实现路径)

实现改动落在 2+ layer = 太大。按 `AGENTS.md` 规则拆成每层一个 issue(或 speckit task),
一层一 commit,各自可独立 `swift build/test`。单层内仍很大 → 按技术切面再拆(纯逻辑 → 输入/校验
→ 处理/编排 → 输出转换 → fixture → 文档 → 迁移)。**收尾遗留记为新 issue,不回头扩大当前 issue。**

---

## 降级(repo 缺上下文时)

这个 skill 是 repo-general 的。目标 repo 若缺某些文件,按存在与否降级,不报错硬停:

| 缺什么 | 降级 |
|---|---|
| 无 `.specify/` | 新功能路径跳过 speckit,退化为「直接起草一个 feature issue + acceptance」,提示用户可先 init speckit |
| 无 `AGENTS.md` layer map | 跳过 layer 映射与 red_lines 填充,body 里 layer/red_lines 段留 TODO 让 dev team 补 |
| 无 `constitution.md` | 跳过红线检查,正常落 issue |
| 无 `docs/adr/` | 架构变更退化为在 issue body 内联记录 Decision,提示用户补建 ADR 目录 |
