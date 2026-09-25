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
   按依赖顺序建好,派发前核验设计已进入默认分支执行基线、批准和唯一 writer。
   就绪的实现 issue 才走受控 dispatch;等待记录与未解除 hold 保持不派发。

**方法论借鉴**:distill 自 [`mattpocock/skills`](https://github.com/mattpocock/skills) 的四个
适配技巧 —— AGENT-BRIEF 结构、diagnosing-bugs「先有失败信号」、to-issues「acceptance + blocker 先建」、
grilling「一次一问 + 附推荐答案 + 能查码就查」。**不照搬** triage 的 label 状态机(Multica 无 label)
或按 skill 固定跨层/单层切法;交付边界来自目标仓库定义,见下。

**先读**:`references/multica-cli.md`(命令配方)、`references/issue-templates.md`(body 模板)、
`references/speckit-bridge.md`(speckit / 架构流程)。这三个是执行细节,本文件是主流程。
验证本 skill 的行为时读 [eval-cases.md](references/eval-cases.md)。

**执行边界**:仓内修改遵守目标 repo `AGENTS.md` 和其固定版本协议;发布/合并由
[W4 PR Manager](../../workflow/README.md) 接管。显式 human pause、Owner hold、未合并依赖
都先于默认派发。规则冲突需要 Owner 决策,不是自动修改规则的授权。

---

## 前提检查

```bash
command -v multica >/dev/null || { echo "multica CLI 未安装 → 先 multica setup"; exit 1; }
git rev-parse --show-toplevel >/dev/null 2>&1 || { echo "不在 git repo 内"; exit 1; }
```

---

## 第 1 步:定位 project(repo → Multica project)

按 [CLI 配方的 workspace/project 反查](references/multica-cli.md) 读取当前 remote、明确的
workspace 和 project resources。唯一匹配且查询成功才取得目标 ID;未知/多命中先报告,
不猜缓存 ID,也不修改全局默认 workspace。完成条件是可复核的 repo → workspace/project 唯一对应。

同时探测**上下文能力**(决定后续走哪条路、能填多少):

```bash
ls .specify/memory/constitution.md 2>/dev/null   # 有宪法 → 任何路径先读它
ls AGENTS.md 2>/dev/null                          # 沿入口链接读取实际 layer map/resolver
ls -d specs 2>/dev/null                           # 有 specs → 新功能走 speckit;看现有编号定新目录号
ls -d docs/adr 2>/dev/null                        # 有 ADR → 架构变更走 ADR 流
```

**任何路径,动手前先读 `constitution.md`(若存在)**。需求与红线冲突时,先提出 ADR/宪法变更,
经仓库计划审查与 Owner 批准、合并后再派发实现;起草需求不等于获准放松红线。

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
3. **映射 layer**:沿 `AGENTS.md` 链接到实际 layer map/resolver 定位,读取指定的叶子上下文:
   repo-kit 使用 `tech-context.md` 的 `red_lines`/`gate`,旧仓使用 `CONTEXT.md` 的对应字段。
   验证命令来自仓库事实源,不假定所有仓都用 Swift。
4. **填 body**:用 bug 模板(Category / Current / Desired / Repro-信号 / Problem history / Key interfaces /
   Acceptance / Out-of-scope / 该层 red_lines + test)。
5. **标题** `[Bug] <layer>: <一句话>`;设 `--priority`。按目标仓已有工作单元定 issue;
   跨层依赖见下方「跨层拆分」,不因层数机械扩张或拆分。

### 路径 B —— 新功能(speckit 全链)

对齐 `specs/README.md` 的约定:specify → clarify → plan → tasks → **逐 task 落 Multica issue,
不跑 `/speckit-implement`**(实现走 Multica pipeline)。完整命令序列见 `references/speckit-bridge.md`。

1. `/speckit-specify <用户输入>` → `specs/NNN-name/spec.md`。
2. `/speckit-clarify` 打磨模糊点(grilling 风格:一次一问 + 附推荐 + 能查码就查)。
3. `/speckit-plan` → `plan.md`;`/speckit-tasks` → `tasks.md`。
   - plan / tasks **必须 reference constitution 章节**(不重述规则)。
   - 按仓库定义的 layer/PR 工作单元映射需求、路径和验收,不由本 skill 重定义层边界。
     跨层需求按接口依赖拆成可独立验证的交付,保留必要测试/文档和每步可构建性;
     一个 spec 可对应多个依赖 task,不机械地一 package 一 layer 或按行数拆分。
4. **逐 task 落 issue**(命令见 `references/multica-cli.md`):
   - 先建一个 **parent issue**(feature 总述,body 指向 `specs/NNN/spec.md`)。
   - 每个 task → 一个 sub-issue:`--parent <parent-key> --project $PROJECT_ID`,标题
     `[T###] [Story] Brief`(spec-kit handoff 约定),body 用 feature-task 模板(What /
     Acceptance / 该层 red_lines + test / Blocked-by)。
   - **有依赖顺序的 task 用 `--stage N`**:同一 stage 的 sub-issue 全部完成才唤醒 parent
     (Multica staged barrier),对应 tasks.md 的依赖组。**blocker 先建**,拿到真实 issue key
     后再让依赖方引用它。
5. **dispatch**:前置批准和依赖就绪后,按第 4 步及 CLI 配方给 **"Dev Team" squad** 派发。
   先查 live run,再决定是否需要启动;不要同时启动 parent 和同一范围的子 issue。

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

### dispatch 前置门禁 —— 引用的 spec/ADR 必须先在执行基线

执行者的隔离 worktree 读不到 Owner working tree 中未发布的设计。按
`references/multica-cli.md`「spec 先入库门禁」核验 remote、默认分支和所有引用路径。

- 缺失时,在专用 task worktree 准备一个设计文档 PR,经过正常 hooks、同入口 verify、计划审查及
  W4;保留 Owner checkout 的分支、staged/unstaged/untracked 内容,不 stash 或切换它。
- hook/CI 失败先修复原因或报告 blocker;不绕过 hooks,也不预判纯文档一定绿。
- Draft/Owner hold、CODEOWNERS 批准、保护未安装等状态由 W4/Owner 解除;本 skill 不自行 merge。
- 合并后刷新执行基线并逐路径复核,再检查 hold 与 live run,才可派发。
- 多个 issue 共用设计时只补一个 PR。无外部引用的完整内联设计不需要文件存在性检查,
  但仍遵守目标仓对 spec/ADR 和批准的要求。

### dispatch —— 就绪后默认派发

**就绪的实现类 issue 默认派发;未就绪时回报具体 hold 与下一 owner。**
前置批准、依赖、运行状态均已核验就绪才执行默认派发。用户**明确说**「先别跑 / 只暂存 / 存草稿 / park」
时保持 backlog;未解除的 Owner hold 同样阻止启动。

Outcome Check 是非实现型等待记录:按路径 D 保持 backlog + 明确 wait owner/next event,不进入本 dispatch 流程。

执行 [CLI 配方](references/multica-cli.md) 的「dispatch / 收尾」,它是启动与重试的唯一流程源。
成功查询到 active run 后才报告已接收;`waiting_local_directory` 是在途阻塞,不等于实现已运行。
失败/超时/无效 JSON/截断响应表示状态未知,不是零 run。任何 retry 前重新确认 live run 和显式 hold。

- **回显**:每条 issue 的 key、URL、run ID/真实状态、下一 owner 或 hold。W2 的
  TL → Planner → FS → AI Reviewer 完成仓内交付后交 **PR Manager (W4)**;本 skill 不负责合并。

---

## 跨层拆分(贯穿 A-C 实现路径)

读取 [仓库权威与角色分工](../../workflow/README.md),按仓库定义的 PR 单元、接口依赖和
实际验证命令划任务;必要配套随实现,独立目的另片。发现相邻问题交回原 owner 重新定范围,
不扩张当前 issue。PRM 不新增范围/大小审查,只消费已有 CI/review/审批并路由具体修复。

---

## 降级(repo 缺上下文时)

这个 skill 是 repo-general 的。缺少可选工具可调整起草方式;缺少确定责任/验证/批准所需的事实时,
先保留待澄清记录,补齐后再派发,不把文件不存在解释为没有规则:

| 缺什么 | 降级 |
|---|---|
| 无 `.specify/` | 新功能路径跳过 speckit,退化为「直接起草一个 feature issue + acceptance」,提示用户可先 init speckit |
| 沿入口仍无实际 layer map/resolver | 标明责任/验证事实缺口,先保留待澄清记录;补齐前不派发未知范围 |
| 无 `constitution.md` | 读取其他仓库架构/政策权威;不能据此推断没有红线 |
| 无 `docs/adr/` | 架构变更退化为在 issue body 内联记录 Decision,提示用户补建 ADR 目录 |
