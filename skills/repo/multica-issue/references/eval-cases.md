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
| **D** dispatch + run 验证 | 第 4 步「默认直接派发」三步 | D1 ⭐ 验证 run vs assign 完就回报 · D2 ⭐ 零 run 用 rerun 兜底 | **每次真实 dispatch(有真实卡死案例)** |
| **W** Working Directory 尾段 | 强制尾段(templates §尾段) | W1 ⭐ 每个实现类 body 都带;Outcome Check 明确豁免 | 落实现类 issue 时(**护栏,必跑**) |
| **C** 分类走对链 | 第 2/3 步路径 A/B/C/D | C1 ⭐ 新功能走 speckit · C2 ⭐ 架构先改 ADR · C6 ⭐ Outcome Check 等待 | 分类任何输入时 |
| **H** 问题历史与效果链 | problem-history | H1 ⭐ 同 fingerprint 建关系 · H2 ⭐ Outcome Check 不 dispatch | Bug 历史命中或等待 TF/使用时 |
| **S** 跨层拆分 | 「跨层拆分」节 | S1 ⭐ 跨层拆多 issue vs 一坨 | 改动可能跨 2+ layer 时 |
| **R** spec 先入库门禁 | dispatch 前置门禁(第 4 步) | R1 ⭐ 引用未合并 spec → 先补 PR | issue body 引用 `specs/`/`docs/adr/` 时 |
| **P** project 反查不 hardcode | 第 1 步定位 | P1 workspace 定位(判别)· P2 不 hardcode(多为 honest) | 定位 project 时 |

---

## Family D — dispatch + run 验证(派发的收尾判据)

### D0. 为什么需要(真实卡死案例:assign+todo 后零 run)

这个 skill 的收尾动作是"**让 pipeline 真的跑起来**"。实测存在一类卡死:issue 已
`assign "Dev Team"` + `status todo`,状态看着对,但 `multica issue runs` **零条 run**——
enqueue 没成功(follow-up issue 尤甚)。此时:

```
issue assign+todo(状态=todo, assignee=Dev Team)→ 看着"派发成功"
  → 但零 run,pipeline 从没被唤醒 → Supervisor 的 autopilot @mention 无效
  → 只会反复 escalate,不会自己重入队 → issue 永远不动,靠人 rerun 才解锁
```

**判据**:dispatch 完成的定义**不是** "assign+todo 返回成功",而是 **`issue runs` 里
确认到 `queued`/`running`**。没看到 run,就没派发完,回报"已派发"即为坏产物。

### D 判别性 case 集

每个 case 给一个 dispatch 场景,问:**这次 dispatch 算不算完成?回报了什么?** 好坏在
**D1/D2** 上分叉。

| # | dispatch 场景 | 正确行为(好产物) | 坏产物(会怎样错) |
|---|---|---|---|
| **D1** ⭐ | 正常 issue,已 `assign "Dev Team"` + `status todo` | **查 `multica issue runs <uuid>`** 确认有 `queued`/`running`,再回显 key+URL+run 状态 | assign+todo 命令都成功 → 直接回报「已派发」,**从不查 runs** → 若零 run 则实际卡死却谎报成功(D0) |
| **D2** ⭐ | assign+todo 后 `issue runs` **零条** | 识别零 run → **`multica issue rerun <uuid>` 兜底** → **再查一次 runs** 确认变 `queued` 才算完成 | 看到零 run 但仍回报「已派发」;或 rerun 后不复查就收尾;或干脆没查所以没发现零 run |
| D3(restraint) | 用户明确说「先别跑 / 只暂存 / park / 存草稿」 | 建 issue 后**保持 `backlog`,不转 todo、不 assign 触发**;告知"已暂存,未派发" | 无视用户,照样 assign+todo 强行派发 → 违背用户显式意图 |
| D4 | 决定 assign 给谁 | assign 给 **"Dev Team" squad**(`--to "Dev Team"` / `--to-id <squad-uuid>`),squad 内部路由 TL→FS→Reviewer | assign 给 **Team Lead 个人** → 绕过 squad 路由 / 或 enqueue 语义不对 |
| D5(restraint) | 一个从没有过任何 run 的 issue,想直接靠 rerun 触发 | 先走 assign+todo 产生首个 run 记录,rerun 只作兜底 | 跳过 assign+todo 直接 `rerun` 一个零 run 历史的 issue → rerun 对「从无 run」的 issue 无效,白调 |

**D1 + D2 是核心判别 case**:D1 分「查 run 才算完」vs「命令成功就回报」;D2 分「零 run 用
rerun 兜底并复查」vs「谎报 / 兜底不复查」。D3 是 restraint negative——证明"默认派发"不会
碾过用户的"先别跑"。

可判定 grader(对 D1/D2):

```
PASS 当且仅当:dispatch 收尾里出现一次 `multica issue runs <uuid>` 查询,
             且回报的完成结论以「runs 含 queued/running」为前提;
             若首查零 run,则有 `rerun` + 二次 `runs` 复查,复查见 queued/running 才回报完成。
FAIL 当:assign+todo 后未查 runs 即回报「已派发/已 dispatch」;
       或查到零 run 仍回报成功;或 rerun 后不复查就收尾。
```

对 D3:`PASS` 当用户说了暂存词、issue 停在 `backlog`、未 assign 触发、回报明确说"未派发";
`FAIL` 当仍执行了 `status todo` / 触发 run。

---

## Family W — Working Directory 强制尾段(防污染用户主 checkout)

### W0. 为什么需要(真实事故:主 checkout 分支被冲)

FS/TL agent 的默认行为是在用户 `~/Development/<Project>` 主 checkout 里直接
`git checkout -b`,并把新分支 upstream 错设到用户当前分支 → **用户手动开的分支被 agent 的
push 覆盖**(2026-07 一次 TestFlight 发版 PR 分支被 i18n pipeline 冲掉,根因即此)。
`## Working Directory` 尾段就是把 FS 钉在 daemon 给的隔离 workdir 里的护栏。**没这段,
FS 回退到污染主 checkout 的默认路径。**

### W 判别性 case 集

输入场景:落任意一条(或一批)实现类 issue,检查每个 body。Outcome Check 不启动 FS,明确豁免本护栏。

| # | 产出特征 | 正确(好产物) | 坏产物(会怎样错) |
|---|---|---|---|
| **W1** ⭐ | 每个实现类 body 末尾 | **都**带 `## Working Directory(CRITICAL …)` 尾段,含"不要 `cd ~/Development/<Project>`""只在 daemon workdir 工作""push 用 `--no-verify`";Outcome Check 无此尾段且不派发 FS | 实现类 body 漏尾段;或 Outcome Check 被误派发给 FS |
| W2 | `<project-slug>` 占位 | 换成真实小写项目名(如 `vitalstride`) | 原样留 `<project-slug>` / `<Project>` 未替换 → 指令含糊 |
| W3(restraint) | 尾段之外的正文 | 尾段是**追加**在行为契约段之后,不替换/挤掉 Acceptance、Layer 约束等 | 为了"加尾段"把正文压缩掉,或把尾段插到中间打断契约段 |

**W1 是核心判别 case**,可判定 grader:

```
PASS 当且仅当:本次落的每一个实现类 issue body 末尾都含 "## Working Directory" 标题
             且含 "不要 cd ~/Development" 与 "workdir" 关键护栏语义。
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
| **C1** ⭐ 新功能 | 「加一个训练页自定义数字键盘」 | 路径 B:speckit 全链 `specify→clarify→plan→tasks`,把 spec 打磨清,再**逐 task 落 sub-issue**(parent + 按 stage 的 sub-issue,每个带 layer 约束) | 跳过 speckit,**直接砸一个大 feature issue**"实现自定义键盘",无 spec、无 task 拆分 → FS 拿到模糊需求返工 |
| **C2** ⭐ 架构变更 | 「把 X 层依赖方向反过来 / 加一个新 layer / 放松并发约束」 | 路径 C:**先**写 `docs/adr/NNNN-*.md`(或 `/speckit-constitution` bump),**再**落实现 issue,body 引用该 ADR | **直接落一个实现 issue** 就改依赖方向,没 ADR、没宪法 bump → 违宪例外无记录,Reviewer 打回 |
| **C3**(restraint)bug | 「撤销 HealthKit 权限后缓存没清、还在读旧数据」 | 路径 A:**不走 speckit**,直接落 bug issue,先要一个 tight 失败信号(失败测试/repro/崩溃栈),映射 layer 带 red_lines+test | 把一个明确 bug **硬塞进 speckit 全链**(specify→clarify…)→ 过度流程、拖慢一个本该直接落的修复 |
| C4(restraint)bug 无信号 | bug 但当前构造不出失败信号 | 把「先构造一个可复现信号」写成 Acceptance 第 1 条,给 dev team 收敛起点 | 凭"感觉不对"落 issue,无任何可变红的信号 → dev team 无从收敛(违 diagnosing-bugs) |
| C5 tech-context 补充 | 「补一层 CONTEXT.md 说明 / 修正 test 命令」(不违红线) | 直接更新对应 `CONTEXT.md` frontmatter,再落一个「tech-context update」issue 记录,不硬开 ADR | 当成大架构变更硬走 ADR 全流程 → 过度;或直接改文件不留 issue 记录 → 防腐 gate 失去入口 |
| **C6** ⭐ 效果验证 | 「等 TestFlight build 可用并实际使用后确认修复」 | 路径 D:建 `[Outcome Check]`,backlog + wait owner + next event + wake condition,不派发实现 Agent | 当普通 Bug 立即 dispatch;或只放 backlog 却没有等待合同 → 形成新的 silent stall |

**C1 + C2 是核心判别 case**:C1 分「新功能先打磨 spec 逐 task」vs「一坨大 issue」;C2 分
「架构先改 ADR/宪法再落」vs「直接落实现 issue」。C3 是 restraint negative——证明分类不会把
bug 也硬拖进 speckit。

可判定 grader:

```
C1 PASS 当:产物是 parent issue + ≥2 个 [T###] sub-issue,存在 speckit 产出(specs/NNN/{spec,plan,tasks}.md)被引用;
     FAIL 当:只产出一个大 feature issue、无 task 拆分、无 spec 引用。
C2 PASS 当:实现 issue 之前先落地/引用了 docs/adr/NNNN-*.md 或宪法版本 bump;
     FAIL 当:直接落改架构方向的实现 issue,无 ADR/宪法变更在先。
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
| **H1** ⭐ | 用户报告「同一个问题在含修复的 TF build 仍出现」 | 生成稳定 `problem_fingerprint`,搜索 active + closed 历史,确认 affected build 包含修复,新 Bug 写 `ineffective_fix_for` 并正常 dispatch | 只按新标题建孤立 Bug,历史修复和版本关系丢失 |
| **H2** ⭐ | 原问题曾被真实使用确认解决,后续 build 再出现 | 新 Bug 写 `regression_of`,保留先前 effective 事件和新 affected build | 覆盖旧 issue 状态,或把复发误写成 duplicate |
| H3(restraint) | 标题相似,但 fingerprint/build 证据不足 | 关系写 `related_to` 或保持未确认 | 仅凭标题断言 ineffective/regression |
| H4(restraint) | TF 尚未可用或 Owner 尚未使用 | `pending_release` / `pending_observation`;Outcome Check 等待 | 用「没有新报告」判定 effective |

H1/H2 PASS 需要 fingerprint、prior issue、affected build 和 evidence source 四项都可追溯。

---

## Family S — 跨层拆分(按 layer 边界,不按行数,不一坨)

### S 判别性 case 集

输入场景喂一个可能跨层的需求,看产出的 **issue/task 拆分**。

| # | 任务场景 | 正确拆分(好产物) | 坏产物(会怎样错) |
|---|---|---|---|
| **S1** ⭐ | 一个改动同时碰 `data` 层(加字段)和 `ui` 层(展示该字段) | 拆成 2 个 issue:先 `data`(独立可 `swift build/test`,一 commit)→ 再 `ui`(`--stage`/`Blocked-by` 引用 data),各带**本层** red_lines+test | 一个大 issue 里一次改两层 → 跨层耦合、无法独立验证、review 面爆炸,layer 约束段填哪层都不对 |
| S2(restraint) | 改动只落在**单个** layer 内 | **不拆**,一个 issue 直接做 | 机械按文件数/行数硬拆单层 → 过度拆分,违反"用 layer 边界不用行数阈值" |
| S3 | 单层内的**大**改动 | 按技术切面拆(纯逻辑→校验→编排→输出转换→fixture→文档),每片本层内可测 | 因"只在一层"就不拆 → 一个巨型 issue;或跨到别层去拆 |
| S4(收尾) | 做一层时发现别层有遗留 | 遗留**记为新 issue**,不回头扩大当前 issue | 顺手把别层也塞进当前 issue → 当前 issue 膨胀成跨层,回到 S1 坏态 |

**S1 是核心判别 case**;S2 是 restraint negative。可判定 grader(对 S1):

```
PASS 当且仅当:产出 ≥2 个 issue,每个 issue 的改动集只落在 1 个 layer 内,
             顺序遵守依赖方向(被依赖层先行,用 --stage / Blocked-by 表达),
             每个 issue 的 Layer 约束段是**该层自己**的 red_lines+test。
FAIL 当:把跨层改动放进单个 issue;或按行数/文件数而非 layer 边界拆;
       或多个 issue 的 Layer 约束段抄了同一层(说明没真按层切)。
```

---

## Family R — spec 先入库门禁(引用文件必须先在 main)

### R0. 为什么需要(真实打回:MY-1281/1285 引用未合并 ADR)

Multica FS agent 在**隔离 workdir** 从 `github/main` 起分支,只能读 **main 上已合并**的文件。
spec/ADR 常诞生在你的主 checkout working tree、还没进 main。若 issue body 引用
`specs/...` / `docs/adr/...` 而文件**没进 main**,FS/Reviewer 会因"引用了不存在的文件"打回
(2026-07-19 复现:MY-1281/1285 引用未合并的 ADR-0010,补 PR #291 后才解锁)。

### R 判别性 case 集

| # | dispatch 前场景 | 正确行为(好产物) | 坏产物(会怎样错) |
|---|---|---|---|
| **R1** ⭐ | issue body 引用 `specs/NNN/spec.md`,但该文件**只在本地 working tree、未合并 main** | 门禁扫引用 → `git cat-file -e github/main:<path>` 查缺失 → **自动开设计文档 PR、监督 CI 合并、复核文件已落 main**,再 dispatch | 检测不到缺失 / 或不检测,直接 dispatch → FS 隔离 workdir 读不到 spec → 困惑或打回(MY-1281) |
| R2(restraint) | 引用的 spec/ADR **已在 main** | 查到全部存在 → 跳过补 PR,直接 dispatch | 无脑每次都开一个设计文档 PR → 空 PR 噪音 |
| R3 | 多个 sub-issue 引用**同一** spec | **一个**设计文档 PR 覆盖全部引用 | 每个 issue 开一个 PR → PR 泛滥 |
| R4 | body **内联**完整 spec、不靠 `specs/` 路径 | 无外部文件引用 → 跳过本门禁 | 对内联 spec 也硬找文件、报缺失 → 卡在不存在的门禁 |

**R1 是核心判别 case**;R2 是 restraint negative(已在 main 不重复开 PR)。可判定 grader:

```
R1 PASS 当:dispatch 前对每个被引用 specs//docs/adr/ 路径做过 `git cat-file -e github/main:<path>`,
        缺失的走了「开 PR→合并→复核在 main」再 dispatch;
   FAIL 当:引用了未合并文件却直接 dispatch(无存在性检查)。
R2 PASS 当:引用文件全在 main 时直接 dispatch,未多开 PR。
```

---

## Family P — project 反查(不 hardcode,先 workspace 后 project)

### P 判别性 case 集

| # | 定位场景 | 正确行为 | 坏产物 |
|---|---|---|---|
| **P1** ⭐(判别) | 目标 project 在非默认 workspace(如个人项目在 `my`,默认是另一个 workspace) | **先 `workspace list` + `switch <slug>`** 定位对 workspace,再遍历 `project list` 反查 | 直接在默认 workspace 反查 → 静默扫空(project 被藏)→ 误报"本 repo 未绑定" |
| P2(多为 honest) | 已知某 repo→project id(如 VitalStride 的 UUID 写在 references) | 仍按 remote→`project resource` 反查确认,references 里的 id 只作已知参照 | **hardcode** 一个 id 不反查 → 换 repo 就错 |
| P3 | 反查扫完**未命中** | **停下**,告诉用户"本 repo 未绑定任何 project",让用户指定或先 attach | 瞎猜一个 project id 硬落 issue → 落到错项目 |

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
- **C3 / C4**:bug 不被硬拖进 speckit 全链;无信号时也不凭空落。
- **C5**:纯 tech-context 补充不被当大架构变更硬走 ADR。
- **S2**:单层改动不被按行数硬拆。
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

- **每次真实 dispatch** → **D**(D1+D2 命中卡死风险最高,是本 skill 唯一"会静默假成功"的收尾)。
- **落任何 issue** → **W**(逐 body 查尾段,批量落 sub-issue 时最易漏)。
- **Bug 历史命中 / 等 TF 或使用** → **H**;Outcome Check 同时跑 C6 restraint。
- 输入是**新功能 / 架构变更** → **C**(C1/C2);bug 只需确认 C3/C4 的 restraint 没被违反。
- 改动**可能跨 2+ layer** → **S**。
- issue body **引用 `specs/`/`docs/adr/`** → **R**(R1 有真实打回案例)。
- **多 workspace 环境定位 project** → **P**(P1);单 workspace 且无 hardcode 诱导时 P 常够用。
- **跳过**:纯降级场景(repo 缺 `.specify/`/`AGENTS.md`)按降级表退化,不必跑 C/S 的 speckit 分支。
- 改了引导某决策的 **prose** → 该 family 的 **PAIR**。

## 一句话原则

> 每个决策都有一个"好坏分叉"的核心判别 case(D1/D2·W1·C1/C2/C6·H1/H2·S1·R1·P1)。
> 真实跑完先用它验一次;改了引导该决策的 prose 就用 PAIR 证明行为真翻转,别凭直觉。
> dispatch 的判据尤其硬:**没在 `issue runs` 里看到 `queued`/`running`,就没派发完——回报"已派发"即是坏产物。**
