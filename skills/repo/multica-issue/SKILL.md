---
name: multica-issue
description: 从当前 repo 定位 Multica project，把已确认的 bug/feature/架构实施需求或现有 plan/tasks 交给 Dev Team；记录问题历史与 ineffective/regression 关系，或创建不派发 Agent 的 Outcome Check。适用于明确提 issue、交团队实现、批量入库或等待发布后验证；现象反馈与诊断请求先澄清，不自动派发。
user-invocable: true
---

# Multica Issue — 向 dev team 提交 issue

把「起草一个 issue 并交给 Multica dev team」变成一条可靠流程。核心:**issue 是 dev team 的
工作输入**,起草质量直接决定 FS 是否返工、Reviewer 是否打回。所以这个 skill 做三件事:

1. **定位** —— 从当前 repo 反查它绑定的 Multica project(不 hardcode)。
2. **分类 + 打磨** —— 判定 bug / 新功能 / 架构变更,按类型决定是否先用 speckit 把需求写清。
3. **落 issue + dispatch/wait** —— 用 repo 的合同与验证事实填充 issue，按依赖顺序建好，核实固定方案可由执行者读取，
   再将已授权且选定 Dev Team 的实现任务派发给 squad，并验证 run；等待与阻塞如实保留。

**方法论借鉴**:distill 自 [`mattpocock/skills`](https://github.com/mattpocock/skills) 的四个
适配技巧 —— AGENT-BRIEF 结构、diagnosing-bugs「先有失败信号」、to-issues「acceptance + blocker 先建」、
grilling「一次一问 + 附推荐答案 + 能查码就查」。**不照搬** triage 的 label 状态机(Multica 无 label)
和固定的 layer/vertical-slice 切法；任务边界采用目标仓已有合同。

**先读**:`references/multica-cli.md`(命令配方)、`references/issue-templates.md`(body 模板)、
`references/speckit-bridge.md`(speckit / 架构流程)。这三个是执行细节,本文件是主流程。

---

## 前提检查

先读 [聊天准入与执行版本](../../workflow/README.md#聊天准入与执行版本)。明确、范围清楚的修复指令无需重复确认；
设计修改/workflow refine 则先有 Owner 与 CLI 定稿并获准执行的基本方案。复用已有 owner，不因调用本 skill 自动重派。
仅反馈、诊断、未批准的新需求草稿或明确暂存时，不进入实现 dispatch。维护提出的普通需求也须经过同一准入，
不能因来源是维护就启动开发。该准入不豁免团队内部 Planner/spec/plan 审查。

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
ls AGENTS.md 2>/dev/null                          # 读取仓库指南、PR 单元和 layer 约束
ls -d specs 2>/dev/null                           # 有 specs → 新功能走 speckit;看现有编号定新目录号
ls -d docs/adr 2>/dev/null                        # 有 ADR → 架构变更走 ADR 流
```

**任何路径,动手前先读 `constitution.md`(若存在)**。若需求与红线冲突，先向 Owner 报告具体冲突；只有明确获准的
政策变更才进入 ADR/宪法审查，不能为派发任务自行放松规则。安全、隐私、身份及 required gates 继续有效。

---

## 第 2 步:分类意图

完成准入后按需求判定四类之一；类型不代表授权。**模糊时用 grilling 风格确认:一次只问一个问题,每问附上你的推荐答案,
能靠读代码回答的就先读代码、别问用户。**

| 类别 | 触发信号 | 走哪条路 |
|---|---|---|
| **bug** | 已确认要修复的报错/崩溃/行为或数据问题 | 路径 A —— 起草 issue,**不走 speckit** |
| **新功能** | 「加 / 支持 / 新页面 / 新能力 / 新交互」 | 路径 B —— speckit 全链,一 task 一 issue |
| **技术架构 / tech-context** | 「改架构 / 加 layer / 换依赖方向 / 改缓存或并发策略 / 与现宪法冲突」 | 路径 C —— 先定方案及所需授权、完成适用文档审查，再落 issue |
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
   - 查证后仍无法复现／补齐必要事实，且无安全有效下一步 → 按 [问题历史](references/problem-history.md#investigation-without-a-safe-next-step)
     保留原修复未完成，交 Owner 判断；不是反复创建“先复现”任务或等待新证据后自动恢复。
2. **检索问题历史**:按 `problem-history.md` 生成稳定 `problem_fingerprint`,搜索 active + closed issue。
   确认 `duplicate_of`、`ineffective_fix_for`、`regression_of` 或 `related_to`,并记录 affected
   version/build 与证据来源。标题相似只用于发现候选,不直接建立关系。
3. **映射 layer**:从报错文件/路径对照 `AGENTS.md` 的 layer map,定位落在哪个 layer →
   读该层 `CONTEXT.md` 的 frontmatter,取 `red_lines`(修的时候不能踩)+ `test`(修完跑哪条验证)。
4. **填 body**:用 bug 模板(Category / Current / Desired / Repro-信号 / Problem history / Key interfaces /
   Acceptance / Out-of-scope / 该层 red_lines + test)。
5. **标题** `[Bug] <area>: <一句话>`;设 `--priority`。按单目标、真实依赖和仓库 PR 单元决定是否拆子 issue，
   不以涉及多个 layer 自动判定过大。

### 路径 B —— 新功能(speckit 全链)

入口已有 spec/plan/tasks 时直接引用，要求接手的 Planner 复用、校验、补齐；只对缺少的产物按 `specs/README.md` 的约定执行
specify → clarify → plan → tasks → **逐 task 落 Multica issue,
不跑 `/speckit-implement`**(实现走 Multica pipeline)。完整命令序列见 `references/speckit-bridge.md`。

1. `/speckit-specify <用户输入>` → `specs/NNN-name/spec.md`。
2. `/speckit-clarify` 打磨模糊点(grilling 风格:一次一问 + 附推荐 + 能查码就查)。
3. `/speckit-plan` → `plan.md`;`/speckit-tasks` → `tasks.md`。
   - plan / tasks **必须 reference constitution 章节**(不重述规则)。
   - 按目标仓已有 PR 单元、单目标和真实依赖拆分；plan 写本次版本、仓库、任务、完成条件与下一动作，
     引用版本化 guide/shared 规则。已有计划保留必要 spec/plan 审查，不重写同内容计划。
4. **逐 task 落 issue**(命令见 `references/multica-cli.md`):
   - 先建一个 **parent issue**(feature 总述,body 指向 `specs/NNN/spec.md`)。
   - 每个 task → 一个 sub-issue:`--parent <parent-key> --project $PROJECT_ID`,标题
     `[T###] [Story] Brief`(spec-kit handoff 约定),body 用 feature-task 模板(What /
     Acceptance / 该层 red_lines + test / Blocked-by)。
   - **有依赖顺序的 task 用 `--stage N`**:同一 stage 的 sub-issue 全部完成才唤醒 parent
     (Multica staged barrier),对应 tasks.md 的依赖组。**blocker 先建**,拿到真实 issue key
     后再让依赖方引用它。
5. **dispatch**:把 parent(或第一个 stage 的 issues)assign 给 **"Dev Team" squad** + 状态转 `todo`
   + 验证 run。TL 根据 plan 推进依赖；未确认接收时先对账，见第 4 步。

### 路径 C —— 技术架构 / tech-context 变更

详见 `references/speckit-bridge.md` §架构。先判断改动性质:

- **只是技术上下文补充/修正,不违反红线**(如补一层 CONTEXT.md 的说明、修正 test 命令) →
  直接更新对应层 `Packages/<X>/CONTEXT.md`(含 frontmatter `depends_on`/`red_lines`/`test`)
  或顶层 `CONTEXT.md` 的 `canonical_roles`,然后落一个「tech-context update」issue 记录变更
  (frontmatter 防腐 hook / CI 会 gate 一致性)。
- **改架构方向 / 与现宪法冲突** → 先由 Owner 与 CLI 确定基本方案，涉及政策或权限变更另取明确授权；
  由内容负责人写 `docs/adr/NNNN-*.md` 或所需宪法变更并通过既有审查，**再** 落本版实现 issue。
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
  这段是护栏:防止 FS agent 回退到用户主 checkout 执行 `git checkout -b`,
  把用户手动开的分支冲掉(2026-07 已复现事故)。**落任何 issue 前确认这段在 body 里。**
- **顺序**:blocker / parent 先建 → 拿到真实 `MY-XXXX` key → 依赖方引用它再建。

### dispatch 前置门禁 —— 固定方案可读取

核实执行者实际使用的 repo/base，检查 issue 引用的 spec/plan/tasks/ADR/guide 在该基线可读，且内容对应已批准版本；
只有同名路径存在不够。记录 commit/ref，防止最新讨论替换当前实施方案。

缺少文件时保留待派发状态。若已授权补文档，使用允许根目录下的独立任务 worktree、配置的 agent 身份与正常
commit/push/PR 流程，只提交所需文件；保留他人的 checkout 与未提交内容。所需 CI、独立审查和 Owner 审批继续有效，
PR 交 PRM 推进，不因“纯文档”跳过 hooks 或自动改宪法。合并后复核实际执行基线与固定版本，再派发。
多个任务引用同一份方案可共用设计文档 PR；内联完整、固定的方案则不需要不存在的外部路径检查。

命令核验见 `references/multica-cli.md` §「spec 先入库门禁」。

### dispatch —— 已授权实现任务的派发

已确认执行、选定 Dev Team、依赖与门禁齐备且没有现有执行者的实现任务，默认继续派发，不重复询问。
明确暂存、未获准执行、依赖未满足或接收未知时保留相应状态；缺少“先别跑”不代表实施授权。

Outcome Check 是非实现型等待记录:按路径 D 保持 backlog + 明确 wait owner/next event,不进入本 dispatch 流程。

派发按三步执行；**接收确认、run 结果与交付验收分开记录**，第 3 步取得对应证据才报告已接收：

1. **assign** 给 **"Dev Team" squad**(不是 Team Lead 个人;`--to "Dev Team"` 或 `--to-id <squad-uuid>`)。
2. **转 todo**:`issue status <key> todo`。光 assign 不触发,必须转 todo 才 enqueue。
3. **核实本次派发是否已接收**：查询 `multica issue runs <uuid>`，默认返回完整历史，不只 active runs。
   依据现有 issue/run 历史与固定交接记录，核对本次任务、方案版本、原 owner 及派发记录；同一 issue 下任意历史 run
   不足以证明本次接收，旧版、不同 owner 或本次派发前的旧 run 都不能冒充对应证据。
   - 找到真正匹配的 run → 无论 `queued`/`running` 还是 `completed`/`failed`/`cancelled`，都确认已接收；
     报告关联依据、run 标识、实际状态与 issue URL，保留原执行方，不按“未接收”重新派发。
   - `queued` 不等于已开始实现；`failed`/`cancelled` 是已接收后的失败/取消，交原执行方跟进，不是交付成功。
     `completed` 也只说明 run 已结束，交付仍按任务验收、PR、发布/消费等适用证据判断。
   - 零 run、只有不匹配的历史 run、关联不足、超时或查询失败 → 保留任务、固定版本和所选执行方，报告接收未知；
     先核对接收记录与唯一写者，只有确认未接收后才按已验证的恢复路径补派。`rerun` 不作为零历史 run 的兜底；
     未知状态不触发重建 issue、重复写者或改派。持续不可用报告阻塞，运行恢复另按现有恢复入口处理。

- **回显**:每条新建 issue 打印 `identifier`(MY-XXXX)+ URL + 接收结论及依据 + 实际 run 状态；交付证据不足则明确待验收。
  提醒用户后续 pipeline 是
  Planner → AI Reviewer 只读方案关 → TL 按依赖派 FS → FS 实现、必要验证及完整自检 →
  AI Reviewer 对准确 SHA 作 pre-push spec/architecture 只读审查 → 原 FS 推送／创建更新 PR。
  Reviewer 不运行／裁定测试或盯 PR；成功 PR 输出交 PRM 按[非 Draft 边界](../../workflow/README.md#prm-唯一交付责任)接管。
  任一步失败如实保留，角色实际部署另行核验。

---

## 按目标与依赖拆分(贯穿 A-C 实现路径)

采用 [plan 与仓库合同](../../workflow/README.md#plan-与依赖推进)，不另建 layer/PR 政策。单 PR 单目标，
按真实依赖和可验收交付拆任务。既定仓库/范围/方案/验收/权限内的必要适配或测试可补进当前计划；无关遗留、
新仓库和方案变更分开记录，不扩大当前任务。TL 按依赖推进，已有 spec/plan gates 保留。

---

## 降级(repo 缺上下文时)

这个 skill 是 repo-general 的。目标 repo 若缺某些文件,按存在与否降级,不报错硬停:

| 缺什么 | 降级 |
|---|---|
| 无 `.specify/` | 新功能路径跳过 speckit,退化为「直接起草一个 feature issue + acceptance」,提示用户可先 init speckit |
| 无 `AGENTS.md` layer map | 跳过 layer 映射与 red_lines 填充,body 里 layer/red_lines 段留 TODO 让 dev team 补 |
| 无 `constitution.md` | 跳过红线检查,正常落 issue |
| 无 `docs/adr/` | 架构变更退化为在 issue body 内联记录 Decision,提示用户补建 ADR 目录 |
