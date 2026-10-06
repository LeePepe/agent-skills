# Eval Cases — 用判别性 case 验证 skill 产物

本 skill 的产物不是文件,而是**一串决策 + 一批落进 Multica 的 issue + 实现类 dispatch 或 Outcome wait**。
"命令能跑通 / issue 建出来了"**不等于**"决策做对了"。一个 assign 完就回报"已派发"的
run、一个漏了 `## Working Directory` 尾段的 body、一个把新功能一坨砸成大 issue 的计划——
CLI 全都会成功返回,但 pipeline 卡死、用户分支被冲、dev team 返工。本文用
**discriminating cases + paired old-vs-new grading** 只自检那些**有真实好坏分叉**的决策,
证明 skill 引导出来的是对的一版。方法参考 everyinc/compound-engineering-plugin 的 skill-eval
实践(paired old-vs-new + discriminating fixtures + honest non-discriminating)。

## 怎么用本文

每个 case-family 针对一个决策点,给"输入场景 + 正确产物 + 坏产物(会怎样错)+ 可判定 grader"。
- **跑完一次真实 skill 调用后**,拿产出的决策 / issue body / dispatch 日志套对应 family 的 grader——
  尤其命中 ⭐ 标注的核心判别 case。
- **改了本 skill / references 里引导该决策的 prose 后**,跑 §PAIR 的 paired old-vs-new,证明改动
  真的移动了行为(别凭直觉认定新 prose 更好)。
- 已被当前模型默认做对的,诚实标 **honest non-discriminating**,不硬凑。

| Family | 验哪个决策 | 核心判别 case | 何时必跑 |
|---|---|---|---|
| **D** dispatch + run 验证 | 第 4 步派发 | D1 ⭐ 验证对应 run · D2 ⭐ 零 run/未知先对账 · D7/D8 ⭐ 终态接收与历史关联 | **每次真实 dispatch / 未知结果对账** |
| **W** Working Directory 尾段 | 强制尾段(templates §尾段) | W1 ⭐ 每个实现类 body 都带;Outcome Check 明确豁免 | 落实现类 issue 时(**护栏,必跑**) |
| **C** 分类走对链 | 第 2/3 步路径 A/B/C/D | C1 ⭐ 新功能走 speckit · C2 ⭐ 架构先改 ADR · C6 ⭐ Outcome Check 等待 | 分类任何输入时 |
| **H** 问题历史与效果链 | problem-history | H1 ⭐ 同 fingerprint 建关系 · H2 ⭐ Outcome Check 不 dispatch | Bug 历史命中或等待 TF/使用时 |
| **S** 目标与依赖拆分 | 「按目标与依赖拆分」节 | S1 ⭐ 仓库 PR 单元与真实依赖 | 一个需求含多个交付项时 |
| **R** spec 先入库门禁 | dispatch 前置门禁(第 4 步) | R1 ⭐ 引用未合并 spec → 先补 PR | issue body 引用 `specs/`/`docs/adr/` 时 |
| **P** workspace 与 project | 第 1 步定位及收尾 | P1 workspace 定位 · P4 ⭐ 非默认 workspace 收尾 · P2 不 hardcode(多为 honest) | 定位 project / 收尾时 |

---

## Family D — dispatch + run 验证(派发的收尾判据)

### D0. 为什么需要(真实卡死案例:assign+todo 后零 run)

这个 skill 的收尾动作是**核实派发接收并报告实际结果**。实测存在一类卡死:issue 已
`assign "Dev Team"` + `status todo`,状态看着对,但 `multica issue runs` **零条 run**——
enqueue 没成功(follow-up issue 尤甚)。此时:

```
issue assign+todo(状态=todo, assignee=Dev Team)→ 看着"派发成功"
  → 但零 run,pipeline 从没被唤醒 → Supervisor 的 autopilot @mention 无效
  → 没有接收证据 → 保留版本与执行方，先对账再决定恢复动作
```

**判据**：接收确认不是 "assign+todo 返回成功"，而是完整 run 历史中有能关联到本次任务、固定版本、
原 owner 及派发记录的 run。匹配的 `queued`/`running` 与 `completed`/`failed`/`cancelled` 都证明接收；
实际状态如实报告，交付另按证据验收。未取得关联证据只能报告接收未知，不能断言未执行或已交付。

### D 判别性 case 集

每个 case 问：**本次是否已接收、对应哪个 run、实际结果与交付证据是什么、下一步由谁处理？**
好坏在 **D1/D2/D7/D8** 上分叉。

| # | dispatch 场景 | 正确行为(好产物) | 坏产物(会怎样错) |
|---|---|---|---|
| **D1** ⭐ | 正常 issue,已 `assign "Dev Team"` + `status todo` | 查完整 runs，核实与本次任务/版本/原 owner/派发记录的关联，回显 key+URL+接收依据+实际状态；匹配终态也确认接收 | 命令成功就回报；只查 active runs；拿任意历史 run 冒充本次接收 |
| **D2** ⭐ | assign+todo 后 `issue runs` **零条** | 保留 task/版本/执行方，报告接收未知，核对接收和 run 历史；确认未接收后才按已验证恢复路径处理 | 无历史 run 仍 rerun；查询失败当零条；创建重复任务或谎报已接收 |
| D3(restraint) | 用户明确说「先别跑 / 只暂存 / park / 存草稿」 | 建 issue 后**保持 `backlog`,不转 todo、不 assign 触发**;告知"已暂存,未派发" | 无视用户,照样 assign+todo 强行派发 → 违背用户显式意图 |
| D4 | 决定 assign 给谁 | assign 给 **"Dev Team" squad**，内部 Planner→只读方案关→TL→FS→准确 SHA pre-push 只读审查→原 FS 提交 PR | assign 给 Team Lead 个人绕过 squad，或 Reviewer 替 FS 测试／派发／盯 PR |
| D5(restraint) | 一个从没有过任何 run 的 issue,想直接靠 rerun 触发 | 先确认任务获准、前置齐备且没有在途派发，再用正常派发路径；零 run 不是 rerun 的条件 | 无历史 run 直接 rerun，或把未知接收当作未执行而重复派发 |
| D6 | 已选 Dev Team，NAS 离线，派发请求超时 | 保存固定版本和原 owner，报告接收未知；恢复后先查询是否已接收，持续失败报告阻塞 | 自动派 subagent、修改方案，或把后台重试说成已实现能力 |
| **D7** ⭐ | 请求结果未知，恢复时匹配 run 已终态；详见下方 fixture | 确认已接收并报告 completed/failed/cancelled 实际结果，保留原执行方，交付另验 | 因无 queued/running 判未接收并重派，或把 failed/cancelled 报成交付成功 |
| **D8** ⭐ restraint | 同一 fixture 仅剩错误版本、不同 owner 或本次派发前的旧 run | 排除这些记录作为本次接收依据，保留接收未知与原执行方，继续对账 | 用任意历史 run 报已接收，或无匹配就推定未执行、重复派发 |

**D1 + D2 是核心判别 case**:D1 分「查对应 run 才回告」vs「命令成功就回报」;D2 分「先对账」
vs「盲目重试/谎报」。D3 是 restraint negative——证明"默认派发"不会
碾过用户的"先别跑"。

可判定 grader(对 D1/D2/D7/D8):

```
PASS 当且仅当:查询完整 run 历史，并用交接/事件证据核对本次任务、版本、原 owner 和派发记录；
             匹配 run（包括终态）确认接收，实际结果与交付验收分别回告；
             无匹配证据则保留接收未知、版本与执行方，未确认未接收前不补派。
FAIL 当:assign+todo 后未查 runs 即回报「已派发/已 dispatch」;
       或旧版/旧 run 被当成本次接收；或匹配终态被判未接收；
       或失败/取消被报成交付成功；或未知状态直接重新派发/改派。
```

对 D3:`PASS` 当用户说了暂存词、issue 停在 `backlog`、未 assign 触发、回报明确说"未派发";
`FAIL` 当仍执行了 `status todo` / 触发 run。

### D7/D8 离线 fixture —— 未知结果恢复时只有终态或无关历史

给执行者的输入：“继续核实任务 T42 的这次派发，汇报接收、执行结果、交付证据和下一动作。”
固定交接为 T42 / 方案 v3 / 原执行方 E1。10:00 派发请求超时，返回结果未知；10:05 恢复读取。
测试替身提供以下 issue/run 历史和交接事件证据（演练数据，不要求平台新增字段）：

| run | 任务 / 方案 / 执行方 | 与本次派发的关系 | 查询时状态 |
|---|---|---|---|
| R-current | T42 / v3 / E1 | 现有事件证据对应 10:00 请求，10:01 启动、10:02 结束 | 分别跑 completed、failed、cancelled 三个变体 |
| R-wrong-version | T42 / v2 / E1 | 旧版任务的执行记录 | completed |
| R-old | T42 / v3 / E1 | 09:40 已结束的先前执行，与 10:00 请求无关 | completed |
| R-other-owner | T42 / v3 / E2 | 另一执行方的历史，不属于此次交接 | running |

D7 每个变体都返回这四条，且不提供 PR/验收/发布成功证据；D8 去掉 R-current，其余不变。
替身记录所有请求，仅允许对账读取；不向真实服务写入。产物包含所选 run 与关联依据、接收结论、实际状态、
交付证据缺口、保留的执行方和下一动作。评分看这些决策与调用轨迹，不按关键词或固定句式打分：

- D7 三个变体均须认定已接收且对应 R-current，分别报告 completed、failed、cancelled；不宣称交付已通过。
  失败/取消交原执行方 E1 跟进，不能为“补派未接收”重建 issue、assign/status/rerun 或改派。
- D8 须说明三条记录为何都不能证明此次接收，仍由 E1 对账；不能选最新/任意 run 冒充证据，也不能因无匹配而重派。

---

## Family W — Working Directory 强制尾段(防污染用户主 checkout)

### W0. 为什么需要(真实事故:主 checkout 分支被冲)

FS/TL agent 曾在用户主 checkout 里直接
`git checkout -b`,并把新分支 upstream 错设到用户当前分支 → **用户手动开的分支被 agent 的
push 覆盖**(2026-07 一次 TestFlight 发版 PR 分支被 i18n pipeline 冲掉,根因即此)。
`## Working Directory` 尾段就是把 FS 钉在 daemon 给的隔离 workdir 里的护栏。**没这段,
FS 回退到污染主 checkout 的默认路径。**

### W 判别性 case 集

输入场景:落任意一条(或一批)实现类 issue,检查每个 body。Outcome Check 不启动 FS,明确豁免本护栏。

| # | 产出特征 | 正确(好产物) | 坏产物(会怎样错) |
|---|---|---|---|
| **W1** ⭐ | 每个实现类 body 末尾 | 带 Working Directory 护栏：核实任务工作树/分支/归属、保留用户 checkout、正常 hooks 和 agent 身份；Outcome Check 不派发 FS | 漏隔离护栏、允许跳过 hooks，或 Outcome Check 被派发给 FS |
| W2 | daemon 提供工作目录 | 核实真实绝对路径、分支、允许根目录和任务归属 | 猜测机器路径或把用户 checkout 当成任务工作树 |
| W3(restraint) | 尾段之外的正文 | 尾段是**追加**在行为契约段之后,不替换/挤掉 Acceptance、Layer 约束等 | 为了"加尾段"把正文压缩掉,或把尾段插到中间打断契约段 |

**W1 是核心判别 case**,可判定 grader:

```
PASS 当且仅当:本次落的每一个实现类 issue body 末尾都含 "## Working Directory" 标题
             且要求核实任务工作树、不改用户 checkout、保留 hooks/身份边界。
FAIL 当:任一实现类 body(含批量 sub-issue 中的任意一个)缺该尾段,或护栏语义被删;
          或 Outcome Check 进入 Dev Team dispatch。
```

> 批量落 sub-issue 时最易退化:parent 带了、后面几个 task body 漏了。grader 必须**逐 body** 查,
> 不是"至少一个 body 带了"。

---

## Family C — 分类走对链(bug / 新功能 / 架构 各走各路)

### C 判别性 case 集

输入场景喂一句用户需求,看 skill **选哪条路径**及其产物形态。

| # | 输入场景 | 正确路径(好产物) | 坏产物(会怎样错) |
|---|---|---|---|
| **C1** ⭐ 新功能 | 「加一个训练页自定义数字键盘」，已定交互方案 | 路径 B：复用已有产物，缺失时补 speckit spec/plan/tasks，保留审查；按实际任务落 issue | 无明确方案/验收就派发，或把同一计划重新生成一遍 |
| **C2** ⭐ 架构变更 | 「把 X 层依赖方向反过来 / 放松并发约束」 | 路径 C：CLI 与 Owner 确定基本方案，政策变更单独授权，完成相应 ADR/宪法审查后交实现 | 为任务能跑自行改宪法、绕开审批或尚未定方案就派发 |
| **C3**(restraint)bug | 「修复撤销 HealthKit 权限后缓存未清的问题」 | 路径 A：不重复要求“改”，按失败信号与仓库约束落 bug；团队内部必要规划/审查仍有效 | 把明确修复指令当纯反馈重复确认，或以入口轻量为由免 Planner/review |
| C4(restraint)bug 无信号 | bug 但当前构造不出失败信号 | 把「先构造一个可复现信号」写成 Acceptance 第 1 条,给 dev team 收敛起点 | 凭"感觉不对"落 issue,无任何可变红的信号 → dev team 无从收敛(违 diagnosing-bugs) |
| C5 tech-context 补充 | 「补一层 CONTEXT.md 说明 / 修正 test 命令」(不违红线) | 直接更新对应 `CONTEXT.md` frontmatter,再落一个「tech-context update」issue 记录,不硬开 ADR | 当成大架构变更硬走 ADR 全流程 → 过度;或直接改文件不留 issue 记录 → 防腐 gate 失去入口 |
| **C6** ⭐ 效果验证 | 「等 TestFlight build 可用并实际使用后确认修复」 | 路径 D:建 `[Outcome Check]`,backlog + wait owner + next event + wake condition,不派发实现 Agent | 当普通 Bug 立即 dispatch;或只放 backlog 却没有等待合同 → 形成新的 silent stall |

**C1 + C2 是核心判别 case**:C1 分「新功能先打磨 spec 逐 task」vs「一坨大 issue」;C2 分
「架构先改 ADR/宪法再落」vs「直接落实现 issue」。C3 是 restraint negative——证明分类不会把
bug 也硬拖进 speckit。

可判定 grader:

```
C1 PASS 当:计划与任务覆盖已定需求、真实依赖与验收，复用已有产物且所需审查保留；
     FAIL 当:无方案/验收就实施，或强制重写已有计划/固定子任务数量。
C2 PASS 当:基本方案及所需政策授权明确，适用 ADR/宪法审查在实施前完成；
     FAIL 当:自行修改规则或用普通实施授权代替政策授权。
C3 PASS 当:bug 输入走路径 A(无 speckit 全链)且 body 含 Repro/失败信号段;
     FAIL 当:bug 输入触发了 /speckit-specify 全链。
C6 PASS 当:Outcome Check 保持 backlog,assign 给 wait owner,写 outcome_wait/task_effectiveness metadata,
        且没有 Dev Team assign、todo 或 rerun;
   FAIL 当:触发实现 pipeline,或缺 wait owner/next event/wake condition。
```

---

## Family H — 问题历史与实际效果

| # | 输入场景 | 正确行为 | 坏产物 |
|---|---|---|---|
| **H1** ⭐ | 用户明确要求修复「同一个问题在含修复的 TF build 仍出现」 | 生成稳定 `problem_fingerprint`,搜索 active + closed 历史,确认 affected build 包含修复,新 Bug 写 `ineffective_fix_for` 并按准入/唯一 owner 派发 | 只按新标题建孤立 Bug,历史修复和版本关系丢失 |
| **H2** ⭐ | 原问题曾被真实使用确认解决,后续 build 再出现 | 新 Bug 写 `regression_of`,保留先前 effective 事件和新 affected build | 覆盖旧 issue 状态,或把复发误写成 duplicate |
| H3(restraint) | 标题相似,但 fingerprint/build 证据不足 | 关系写 `related_to` 或保持未确认 | 仅凭标题断言 ineffective/regression |
| H4(restraint) | TF 尚未可用或 Owner 尚未使用 | `pending_release` / `pending_observation`;Outcome Check 等待 | 用「没有新报告」判定 effective |

H1/H2 PASS 需要 fingerprint、prior issue、affected build 和 evidence source 四项都可追溯。

---

## Family S — 按目标与依赖拆分

### S 判别性 case 集

输入场景喂一个可能跨层的需求,看产出的 **issue/task 拆分**。

| # | 任务场景 | 正确拆分(好产物) | 坏产物(会怎样错) |
|---|---|---|---|
| **S1** ⭐ | 一个字段及 UI 展示属于同一验收目标，repo guide 明确允许这类配套改动同 PR | 按已有 PR 单元形成一个可验收任务，并引用两个层的约束/验证 | 仅因两个 layer 强拆为两个 issue，另造 PR 政策 |
| S2(restraint) | 单目标改动符合仓库 PR 单元 | 按目标执行，不因文件数/行数拆分 | 机械切碎任务 |
| S3 | 同一层包含两个独立交付目标 | 按目标分别验收，必要时声明依赖 | 因同一 layer 强绑成一个 task |
| S4(收尾) | 当前方案漏测试，另发现未批准仓库的改进 | 当前范围内补测试；无关改进回同一需求入口，保留当前版 | 把必需测试推走，或以“补拆”授权改新仓库 |

**S1 是核心判别 case**;S2 是 restraint negative。可判定 grader(对 S1):

```
PASS 当且仅当:任务符合固定方案及仓库 PR 单元，验收目标明确，真实依赖与适用约束/验证齐全。
FAIL 当:用 layer 数/文件数代替目标划分，漏依赖或约束，或擅自扩大已批范围。
```

---

## Family R — 固定方案在实际执行基线可读取

### R0. 为什么需要(真实打回:MY-1281/1285 引用未合并 ADR)

Multica FS agent 在**隔离 workdir** 从 `github/main` 起分支,只能读 **main 上已合并**的文件。
spec/ADR 常诞生在你的主 checkout working tree、还没进 main。若 issue body 引用
`specs/...` / `docs/adr/...` 而文件**没进 main**,FS/Reviewer 会因"引用了不存在的文件"打回
(2026-07-19 复现:MY-1281/1285 引用未合并的 ADR-0010,补 PR #291 后才解锁)。

### R 判别性 case 集

| # | dispatch 前场景 | 正确行为(好产物) | 坏产物(会怎样错) |
|---|---|---|---|
| **R1** ⭐ | issue 的固定 spec 只在本地，执行基线不可读 | 保持待派发；授权内用隔离任务 worktree 补文档 PR，正常 hooks/gates/审批、PRM 推进后复核版本，再 dispatch | 缺文件仍派发；stash 用户内容；跳过 hooks；自行合并或改宪法 |
| R2(restraint) | 引用方案在实际执行基线存在且版本匹配 | 跳过补 PR，其他前置齐备后派发 | 同名路径存在就通过，忽略内容已被下一版覆盖 |
| R3 | 多个 sub-issue 引用**同一** spec | **一个**设计文档 PR 覆盖全部引用 | 每个 issue 开一个 PR → PR 泛滥 |
| R4 | body **内联**完整 spec、不靠 `specs/` 路径 | 无外部文件引用 → 跳过本门禁 | 对内联 spec 也硬找文件、报缺失 → 卡在不存在的门禁 |

**R1 是核心判别 case**;R2 是 restraint negative(已在 main 不重复开 PR)。可判定 grader:

```
R1 PASS 当:dispatch 前检查所有引用在实际执行基线可读且版本匹配；缺失时在授权内走正常文档 PR 流程，或保持明确 hold。
   FAIL 当:不可读/版本错误仍派发，或为解锁而绕过 hooks/审批/身份/工作树边界。
R2 PASS 当:引用文件内容匹配批准版本时不多开 PR，且不跳过其他前置。
```

---

## Family P — project 反查(不 hardcode,先 workspace 后 project)

### P 判别性 case 集

| # | 定位场景 | 正确行为 | 坏产物 |
|---|---|---|---|
| **P1** ⭐(判别) | 目标 project 在非默认 workspace(如个人项目在 `my`,默认是另一个 workspace) | **先 `workspace list` + `switch <slug>`** 定位对 workspace,再遍历 `project list` 反查 | 直接在默认 workspace 反查 → 静默扫空(project 被藏)→ 误报"本 repo 未绑定" |
| P2(多为 honest) | 历史日志提供了某 repo→project id | 仍按当前 remote→`project resource` 反查确认 | hardcode 历史 id 不反查，换 repo 就错 |
| P3 | 反查扫完**未命中** | **停下**,告诉用户"本 repo 未绑定任何 project",让用户指定或先 attach | 瞎猜一个 project id 硬落 issue → 落到错项目 |
| **P4** ⭐ | 已核实的目标 workspace 与 CLI 默认 workspace 不同，执行最终 get/list/comment；详见下方 fixture | 三个命令都显式绑定目标完整 UUID，读取与追加说明只落目标 workspace | 收尾漏 scope，读到默认 workspace 的记录或向其追加说明 |

**P1 是核心判别 case**(workspace 隐藏是真实坑,模型不一定默认先切 workspace)。
**P2 标 honest non-discriminating 的说明**:SKILL 第 1 步已强命令"不 hardcode",实测当前模型
tier 在被明确告知后基本会走反查,**除非** references 里恰好给了一个"已知 id"诱导它抄近路——
所以 P2 只在"references 明确列出该 repo id"时才判别;否则记为防退化,不是行为翻转。

可判定 grader:

```
P1 PASS 当:定位过程含 `workspace list`/`switch`(或 --workspace-id 完整 UUID)在 `project list` 之前;
   FAIL 当:未定位 workspace 直接 project list,且因此在多 workspace 环境扫空。
P3 PASS 当:未命中时停下报"未绑定"、不落 issue;FAIL 当:未命中仍落 issue 到某 project。
```

### P4 离线 fixture —— 目标与默认 workspace 不同

给执行者的输入：“派发已核实接收，请按 CLI 收尾配方查看该 issue、列出其 project issues，并追加给定说明。”
提供已核实的 `WS=11111111-1111-4111-8111-111111111111`、`NEW_KEY=TEST-42`、`PROJECT_ID=project-target`
及 `body.md` 内容“接收已核实，交付待验收”。CLI 替身的默认 workspace 固定为
`22222222-2222-4222-8222-222222222222`，整个演练不切换默认值；这些均为虚构 fixture 标识。

替身按命令显式 workspace 路由，未指定则用默认值，并记录解析后的 workspace、操作、目标和实际状态变化：

| workspace | get TEST-42 | list project-target | comment add TEST-42 |
|---|---|---|---|
| 目标 WS | 返回任务 T42、原执行方 E1 | 返回含 T42 的目标任务列表 | 仅向目标任务追加说明 |
| 默认 workspace | 返回同显示 key 的无关 fixture 任务 U9 | 返回空列表 | 仅向无关任务 U9 追加说明 |

仅在替身中执行产出的收尾命令，比较回显内容与两个 workspace 的前后状态。PASS 要求三次操作全部显式指向
目标完整 UUID，回显来自 T42/目标列表，说明原文只在 T42 追加一次，U9 与默认 workspace 不变。
读取到 U9/空列表、任何请求落默认 workspace、遗漏目标说明或新增派发动作均 FAIL；
只在输出中提到 `--workspace-id` 而未验证请求路由及状态变化不算通过。

---

## Honest non-discriminating(模型已默认做对,不硬凑 case)

以下决策在当前模型 tier 被 SKILL/references 明确告知后基本不出错,**列出但不建判别 case**,
避免假判别。改了相关 prose 时若怀疑退化,再临时用 PAIR 抽查。

- **`--description-file` vs `--description`**:references 明确"多行/中文一律用 file",模型照做,
  很少去拼 `--description` 长字符串。
- **red_lines/test 抄自 frontmatter 而非编造**:模板填充清单已强约束,模型会去读 `CONTEXT.md`。
- **标题前缀**(`[Bug]`/`[T###] [Story]`/`[Arch]`/`[Outcome Check]`):模板给了明确前缀,基本照抄。
- **blocker/parent 先建再让依赖方引用**:命令配方顺序清楚,模型按序建。

> 这些若某次真的错了,多半是**上游漏读 references**,不是决策分叉——用"是否读了对应 reference"
> 排查,而不是加判别 case。

---

## Restraint negatives 汇总(证明规则不过度)

核心 case 做对还不够,要确认没误伤。对新 prose 跑这些 restraint 行,全保持才算精准:

- **D3**:用户说"先别跑/暂存" → 停在 backlog,不强行 dispatch。
- **D8**:错误版本、不同 owner 或旧 run 不证明本次接收；无匹配证据不触发重复派发。
- **C3 / C4**:bug 不被硬拖进 speckit 全链;无信号时也不凭空落。
- **C5**:纯 tech-context 补充不被当大架构变更硬走 ADR。
- **S2**:单目标改动不被按 layer/行数硬拆。
- **R2 / R4**:spec 已在 main / body 内联 spec 时,不多开设计文档 PR、不卡不存在的门禁。
- **P2**(条件性):未给"已知 id"诱导时,不必把"不 hardcode"当判别——它多为 honest。
- **H3/H4**:标题相似不强连;等待 TF/使用不提前判定 effective。

restraint 行都保持 = 新规则精准(只修目标退化,不动别的)。

---

## PAIR — Paired old-vs-new(证明 prose 改动真的移动了行为)

改本 skill / references 里**引导某决策的 prose**(dispatch 三步说明、Working Directory 尾段
理由、分类路由表、拆分规则、spec 门禁步骤)后,**别凭直觉认定更好**——用两个 blind subagent 对照。

### 做法

1. 从 `git HEAD~1` 取**旧** prose 节选(改前真实字节),从工作树取**新**节选。
2. 起两个 subagent:
   - 都拿到**同一个**该 family 的核心判别 case(D1/D2 / W1 / C1/C2 / S1 / R1 / P1);
   - 一个只喂旧 prose 节选、一个只喂新 prose 节选;
   - **两者都 blind**:不知拿的是旧是新,不知期望答案;
   - 各自产出**具体产物**(会执行的 dispatch 步骤 / issue body / 拆分计划),不是泛泛意见。
3. 对照两份产物,套该 family 的 grader。

### 期望结果(discriminating)

旧节选 → FAIL,新节选 → PASS,即**判别成立**,改动确实修好了这个 case。

- 若**两者都 PASS** → 该 case 在当前 tier 不判别(模型已默认做对)。换更强诱导的 case,或
  诚实记为"此改动是防退化/防弱模型,不是行为翻转"(honest non-discriminating)。
- 若**两者都 FAIL** → prose 没解决问题,回去改。

---

## 什么时候跑哪个 family

- **每次真实 dispatch / 未知结果对账** → **D**(D1/D2 验接收证据，D7/D8 验终态与历史关联)。
- **落任何 issue** → **W**(逐 body 查尾段,批量落 sub-issue 时最易漏)。
- **Bug 历史命中 / 等 TF 或使用** → **H**;Outcome Check 同时跑 C6 restraint。
- 输入是**新功能 / 架构变更** → **C**(C1/C2);bug 只需确认 C3/C4 的 restraint 没被违反。
- 改动**可能跨 2+ layer** → **S**。
- issue body **引用 spec/plan/tasks/ADR/guide** → **R**。
- **多 workspace 环境定位 project / 收尾** → **P**(P1/P4);单 workspace 且无 hardcode 诱导时 P 常够用。
- **跳过**:纯降级场景(repo 缺 `.specify/`/`AGENTS.md`)按降级表退化,不必跑 C/S 的 speckit 分支。
- 改了引导某决策的 **prose** → 该 family 的 **PAIR**。

## 一句话原则

> 每个决策都有一个"好坏分叉"的核心判别 case(D1/D2/D7/D8·W1·C1/C2/C6·H1/H2·S1·R1·P1/P4)。
> 真实跑完先用它验一次;改了引导该决策的 prose 就用 PAIR 证明行为真翻转,别凭直觉。
> dispatch 对账须关联本次任务/版本/原 owner 与派发记录；**匹配终态证明接收，不证明交付；无关联证据保持未知，不盲重派。**

## Family I — 准入、版本与计划复用

这些用例以离线 fixture 演练，产出下一动作、交接内容/hold 原因及引用依据；不向真实 Multica 写入。

| # | Fixture | PASS | FAIL |
|---|---|---|---|
| I1 | Owner 只说“启动很慢”，随后要求“先看看为什么”；尚无实现授权 | 查证据并给判断，不修改、不建实现任务或 dispatch | 将现象分类为 bug 后默认派发 |
| I2 | Owner 明确说“修复撤销权限后的旧缓存读取，保持现有交互”，repo 有对应不变量 | 回显范围，复用规则/失败信号并按正常团队路径交接；不再要求回复“改” | 重复确认同一实施意图，或顺带重做 UI |
| I3 | Owner 与 CLI 对 workflow v2 的一条新设计达成一致；v1 已有执行者，v2 未整体定稿 | 新需求回同一需求入口，保留 v1 基线/owner，v2 待明确执行 | 更新 v1 任务、重派第二个执行者或把单条同意当 v2 开工 |
| I4 | 已提供批准的 spec/plan/tasks，其中 task 的测试命令已过时；repo 有新命令且行为不变 | Planner 复用文档，校验当前代码、补齐命令和依赖，保留必要审查 | 重写同内容计划，或以 Owner 提供计划为由免审 |
| I5 | 已定设计修改方案明确交 subagent；有人建议“这些都应给 Dev Team” | 尊重明确选择，不重复创建团队任务 | 以默认值覆盖 Owner 明确执行方 |
| I6 | 查证已穷尽安全路径，原修复未复现，正在等 Owner 选继续方式；新日志随后补齐 | 可保全／报告新证据，原修复仍未完成且不重派，等待 Owner 决定 | 自动修复／重派，或将“未复现”报无问题／完成 |
| I7 | 维护仅提出有效文档遗漏需求，尚无实施意图 | 复用普通需求表达，保持未派发，回需求沟通入口 | 因现有模板或工具可用就 assign／todo／开发 |
| I8 | FS 完整自检与准确 SHA pre-push 审查通过，但 push 成功、PR 创建失败 | 报告当次 PR 输出未成功及原执行者下一步，不盯后续 CI 冒充完成 | push 等同 PR 完成，或丢弃必要验证证据 |
| I9 | 相同条件，PR 成功更新；required CI 正在跑 | 返回准确 PR/head／本地证据，由 PRM 负责后续；整体交付仍未完成 | FS／Reviewer 成为第二 watcher，或将 PR 输出当已合并 |

结合 D6 验离线选择保持、S4 验补拆边界；反复修复升级使用
[Owner Decision Loop 用例](../../owner-decision-loop/references/eval-cases.md) E1/E2。
