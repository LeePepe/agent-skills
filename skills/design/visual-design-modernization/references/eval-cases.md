# Eval Cases — 用判别性 case 验证 skill 产物

本 skill 的产物不是文档,而是一套**流程纪律**:DIAGNOSE→NORTH-STAR→隔离 PROTOTYPE→RENDER→
REVIEW→ITERATE→USER GATE→MIGRATE。**"UI 最后好看了 / 脚本能跑"不等于"流程走对了"**——一个从
代码臆断、直接改生产、问用户"好看吗"的 agent 也可能偶然产出还行的界面,但它把风险、返工、合规
墙全留下了。本文用 **discriminating cases + paired old-vs-new grading** 只自检那些**有真实好坏
分叉**的纪律点,证明 skill 逼出来的是对的那一版流程。方法参考 everyinc/compound-engineering-plugin
的 skill-eval 实践(paired old-vs-new injection + discriminating fixtures)。

## 怎么用本文

每个 case-family 针对一条核心纪律,给一组"输入场景 + 正确行为 + 坏行为(会怎样错)+ 可判定 grader"。
- **让本 skill 跑一个真实/模拟任务后,用命中 ⭐ 的核心判别 case 验一次**。
- **改了本 skill 里承载该纪律的 prose(the loop / Step 2 / Step 4 / When NOT to use)后**,跑 §PAIR
  的 paired old-vs-new,证明改动真的移动了行为(别凭直觉认定新 prose 更严)。

**先记住哪些不判别(honest non-discriminating,别浪费 case)**:所谓"现代化清单"本身——
max content width、独立 KPI 卡、sparkline/ring、≥3 级字号、状态色 pill、克制配色——一个够格的模型
在被要求"现代化"时**默认就会往这些方向做**。测"它知不知道要加 sparkline"不判别。真正会翻车的是
**流程纪律**:美学结论从哪来(渲染像素 vs 读代码)、在哪改(隔离 vs 生产)、谁来判(reviewer 打分
vs 问设计盲用户)、该不该用这个循环(丑 vs 坏)。下面四个 family 全部只打这四处。

| Family | 验哪条纪律 | 核心判别 case | 何时必跑 |
|---|---|---|---|
| **R** 渲染验证 | 美学结论必须来自渲染像素 | R1 ⭐ 出图再判 vs 读代码"觉得变好了" | 每次迭代要下"更好/更现代"结论时 |
| **I** 隔离原型 | 用户批准前不碰生产/宪法锁定代码 | I1 ⭐ 隔离目录 mock data vs 直接改生产 | repo 有 constitution / token-compliance 测试时 |
| **O** 客观评审 | reviewer 打分替代用户缺失的设计眼 | O1 ⭐ /35 打分 vs 问用户"好看吗" | 用户无设计经验(本 skill 主场景) |
| **N** 适用边界 | 丑才进循环,坏走普通工程 | N1 ⭐(restraint)功能 bug 不套视觉循环 | 分诊阶段,判断该不该起这个 skill |

---

## Family R — 渲染验证(美学结论只能来自渲染像素)

### R0. 为什么需要

`swift build` 不渲染;读 SwiftUI 代码看到 `.shadow(...)`、`.font(.largeTitle)`、`LazyVGrid` 会让
agent 产生"层级拉开了、有立体感了、更现代了"的幻觉——**但间距是否真的匀、卡片是否真的浮起来、
sparkline 有没有塌成空白,只有像素能回答**。本 skill 铁律(SKILL.md「Never skip 3–4」):任何美学
断言必须**对着一张渲染出来的 PNG、由 reviewer 或自读像素**得出,不得从代码断言。本 family 抓的就是
"跳过渲染直接下结论"这一最常见退化。

### R 判别性 case 集

输入场景:agent 已在 `Prototype/` 里改完一版界面,现在要判断"这一版是不是比上一版好 / 够不够现代"。

| # | 场景 | 正确行为 | 坏行为(会怎样错) |
|---|---|---|---|
| **R1** ⭐ | 判断这一迭代是否变好 | 用 `ImageRenderer` 出 PNG(light+dark、每个 seed 变体)→ Read 像素 / 交给 `design-reviewer` → 结论**引用那张图**;然后才推进 loop | 读代码/diff 就断言"现在有立体感、层级清晰、更现代了",**从不出图** → 幻觉验收,间距塌了/卡片糊在背景上都看不见 |
| **R2** | 出图但 PNG 空白/零高(ScrollView 塌陷或 LazyVGrid 没物化) | 识别 `img.size` 高度异常 → 换 eager 非滚动变体(`scrollable:false` + `.fixedSize` / `HStack` 代 `LazyVGrid`)重渲,拿到真内容再判 | 把空白/半截 PNG 当"渲染过了"验收 → 等于没渲染,回到 R1 坏态 |
| **R3** | 用户口头描述"感觉还是乱",没有截图 | 先出图(自渲或让用户贴)再定位具体 fault,不在"乱"这个 vibe 上直接改 | 凭口头 vibe 猜着改代码 → 无锚点,越改越偏 |

**R1 是核心判别 case**:区分"出图再判(好)"vs"读代码臆断(坏)"。R2 防的是"出了图但图是假的"这个
隐蔽变体——空白 PNG 被当成功比不出图更危险。

可判定 grader(对 R1):
```
PASS 当且仅当:
  - 在下任何"更好/更现代/层级清晰"类美学结论、或推进到下一 loop 步之前,
    本迭代确有一次 ImageRenderer 运行产出了非空 PNG 文件(img.size 高度含真实内容);
  - 且该结论的依据明确指向那张图(自读像素 or reviewer 打分),不是代码/diff 措辞。
FAIL 当:
  - 出现"看代码就知道更现代了 / 加了 shadow 所以有立体感了"这类从源码得出的美学断言;
  - 或本迭代没有产出 PNG;
  - 或产出的是零高/空白 PNG 却被当作"已渲染验收"。
```

---

## Family I — 隔离原型(用户批准前绝不碰生产 / 宪法锁定代码)

### I0. 为什么需要

生产设计系统常被一份 constitution 文档 + 一堵 token-compliance 测试墙守着(可能禁 shadow、禁彩色
填充、禁多级字号、禁新卡片类型)。**在用户还没批准一个方向之前就去改这些,是纯浪费**:要么撞测试墙
一路红、要么改错了方向还得回滚,且此时根本不知道用户要不要这个 look。SKILL.md Step 2 的解法:先在
全新 `Prototype/` 目录用 **mock data** 建新界面,**先确认 compliance 测试按显式文件名而非目录 glob
加载源码**(是 glob 就把原型移出扫描树),再证明"带着原型,生产 build + 全测试仍绿"= 零风险。本
family 抓"没到 USER GATE 就动生产/宪法"。

### I 判别性 case 集

输入场景:一个带 design constitution + token-compliance 测试的生产 app,用户说"界面太旧,现代化一下"。
问:**在用户批准方向之前,你的改动落在哪?**

| # | 场景 | 正确行为 | 坏行为(会怎样错) |
|---|---|---|---|
| **I1** ⭐ | 用户批准前的原型阶段 | 所有改动落在隔离 `Prototype/` + mock data;先 grep 确认 compliance 测试按显式文件名加载(否则把原型移出扫描树);跑 `swift build && swift test` 证明带原型仍全绿;**生产 token/视图/宪法一字不改** | 直接改生产共享 token 文件 / 生产视图 / 现在就 amend 宪法 → 撞 compliance 测试墙一路红,且是在用户根本没看过 look 之前做的返工 |
| **I2** | 原型放置位置 | 放在 compliance 扫描树**之外**的 sibling 目录,确认对测试不可见 | 把 `Prototype/` 塞进被 glob 扫描的源码树 → 原型自身触发 token 违规,测试红成一片,误以为"新设计不合规" |
| **I-restraint** | 用户**已在 USER GATE 批准**方向后 | 这时**才**改生产:port token/组件、同 PR 更新 compliance 测试到新值、走宪法自己的治理流程(PR+版本号+迁移说明)amend,保持原型可编译直到迁移落地 | 批准后仍只在 `Prototype/` 里打转、永不迁移;或迁移时绕过宪法治理直接硬改 token → 过度隔离 / 破坏单一事实源 |

**I1 是核心判别 case**:区分"隔离 mock 先做(好)"vs"直接改生产撞墙(坏)"。**I-restraint 是本 family
的 restraint negative**——证明"隔离"是**批准前**的纪律,不是"永远别碰生产":到点必须迁移,且迁移要
走宪法治理,不能因为"要隔离"就永不落地或绕过治理硬改。

可判定 grader(对 I1):
```
PASS 当且仅当:USER GATE 批准前,所有文件改动集只落在隔离原型目录(如 Prototype/)且用 mock data;
             生产 build + 全量测试在带原型状态下保持绿;生产视图/token/constitution 零改动;
             且原型放置前已核对 compliance 测试的加载方式(显式文件名 vs glob)。
FAIL 当:批准前编辑了任一生产视图/共享 token/constitution 文件;
        或把原型放进 compliance 扫描树而未先核对加载器,导致原型自身触发违规。
```

---

## Family O — 客观评审(用 reviewer 打分替代用户缺失的设计眼)

### O0. 为什么需要

本 skill 的主场景是**没有设计经验的用户**。他既说不清*为什么*丑,也判断不了一次改动是否变好。
SKILL.md 核心解法:**别问他**。用 `design-reviewer` 对着截图按 7 维 rubric 打 /35 分 + P0/P1(带
具体数值)来做质量门,把"缺失的设计眼"外部化、客观化;只在 USER GATE 让用户在**已渲染的并排选项**
里选**方向**(立体风格 / 灰阶 / 品牌色)。本 family 抓两种退化:①问设计盲用户"好看吗";②agent 自己
不打分就断言"够好了"。

### O 判别性 case 集

输入场景:已有一张渲染好的原型截图,用户无设计经验。问:**如何决定"够不够好 / 下一步修什么"?**

| # | 场景 | 正确行为 | 坏行为(会怎样错) |
|---|---|---|---|
| **O1** ⭐ | 决定这一版是否达标、修什么 | 调 `design-reviewer`(或让 general-purpose 逐字 follow `design-reviewer.md`)带截图+north-star → /35(7 维全打)+ 按优先级 P0/P1 带具体 px/font/color;先修 P0 再迭代 | 把截图丢给用户问"你觉得好看吗/够现代吗?" → 设计盲用户只能凭 vibe,反馈不可执行、来回震荡;或 agent 自己拍脑袋"我觉得够好了" |
| **O2** | USER GATE 给用户做选择 | 给**并排渲染**的真实变体让他选方向(elevation 风格、灰阶、品牌 seed),问的是"要哪个方向",不是"美不美" | 用文字描述让他想象("要不要加点阴影?") → 他没法凭空判断,选择无意义 |
| **O-restraint** | reviewer 分数已过线、P0 清零 | 分数达标≠可以动生产;**仍必须**把截图拿到 USER GATE 让用户显式批准方向,再进 MIGRATE | 因为"客观分够了"就跳过 USER GATE 自动迁移生产 → 客观分替代的是设计眼,**不是用户对改动生产的同意** |

**O1 是核心判别 case**:区分"reviewer 客观打分(好)"vs"问设计盲用户凭感觉(坏)"。**O-restraint 是本
family 的 restraint negative**——客观分再高也不能吞掉 USER GATE:打分替代"审美能力",绝不替代"用户
批准改生产"这一授权。

可判定 grader(对 O1):
```
PASS 当且仅当:是否推进/修什么由 design-reviewer 的 rubric 输出驱动(/35、7 维齐全、P0/P1 带具体值);
             对用户的唯一提问是"在已渲染选项里选方向"(批准门),从不问"好不好看/美不美"。
FAIL 当:靠让用户判断审美("好看吗?")来决定推进;
        或靠 agent 自己未经 reviewer 的无量化断言("够好了")来验收。
```

---

## Family N — 适用边界(丑才进循环,坏走普通工程)

### N0. 为什么需要

这个 diagnose→north-star→prototype→review 的重循环只对**"能跑但丑/旧"**划算。把它套到**功能 bug 或
真正坏掉的布局**上,是拿视觉现代化的重流程去解一个工程问题——既不对症,又白烧一圈 render/review。
SKILL.md「When NOT to use」明确划界。本 family 是 skill 级 restraint 门。

### N 判别性 case 集

| # | 输入场景 | 正确行为 | 坏行为(会怎样错) |
|---|---|---|---|
| **N1** ⭐(restraint) | 用户报的是**功能/布局坏了**:按钮点了没反应、崩溃、视图重叠、文字被截断——不是"丑" | 不起本 skill;走普通工程/调试(定位 bug、修布局约束) | 对功能 bug 起 north-star+原型+reviewer 循环 → 答非所问,渲染出的"好看截图"掩盖 bug 仍在 |
| **N2**(restraint) | 用户**已有设计师/Figma 事实源**,要的是忠实实现 | 走 design-to-code 路径,按既定设计还原 | 无视 Figma 另起一份 north-star 自创方向 → 与既定设计打架,返工 |
| **N3**(honest non-discriminating) | 用户说"界面丑/过时/单调/拥挤",无设计经验、无 Figma | **正是主场景**,起本 skill 全循环 | —(模型默认会正确接单,不判别,列此仅作对照) |

**N1 是核心判别 case,也是全 skill 的 restraint negative**:区分"丑(进循环)"vs"坏(走普通工程)"。
N3 标为 honest non-discriminating——命中主场景时模型默认会正确启用,不必为它单写强诱导 case。

可判定 grader(对 N1):
```
PASS 当且仅当:识别出诉求是功能/布局故障(可复现的行为错误或明显破碎布局)而非审美,
             拒绝启动视觉现代化循环,改走调试/工程路径。
FAIL 当:对一个功能 bug / 破碎布局启动了 DIAGNOSE→NORTH-STAR→PROTOTYPE 循环,
        或用"渲染出的好看截图"当作 bug 已解决的证据。
```

---

## PAIR — Paired old-vs-new 评估法(证明 prose 改动真的移动了行为)

改本 skill 里**承载某条纪律的 prose**(`## The loop` 的「Never skip 3–4」、Step 2 隔离说明、Step 4
客观评审说明、`When NOT to use`、Anti-patterns)后,**别凭直觉认定新版更严**——用两个 blind subagent
对照证明。此法对上面**任一 family** 都适用。

### 做法

1. 从 `git HEAD~1` 取**旧** prose 节选(改前真实字节),从工作树取**新**节选。
2. 起两个 subagent:
   - 都拿到**同一个**该 family 的核心判别 case(R1 / I1 / O1 / N1)对应的输入场景;
   - 一个只喂旧 prose 节选、一个只喂新 prose 节选;
   - **两者都 blind**:不知道自己拿的是旧是新,不知道期望答案;
   - 各自产出**具体行为**(会不会出图、改动落在哪个目录、拿什么决定推进、起不起循环),不是泛意见。
3. 对照两份产物,套该 family 的 grader。

### 期望结果(discriminating)

旧 prose 节选 → FAIL,新 prose 节选 → PASS,即**判别成立**,改动确实修好了这个 case。

- 若**两者都 PASS**:该 case 在当前模型 tier 不判别(模型已默认做对)——诚实记为"此改动是防退化/防弱
  模型,不是行为翻转"(everyinc 的 honest non-discriminating 原则),别硬凑成"重大改进"。
- 若**两者都 FAIL**:prose 没解决问题,回去改。

### Restraint negatives(证明新规则不过度)

改对核心 case 还不够,要确认没把**边界/克制**行为也一起改坏。对**新** prose 跑该 family 的 restraint 行:
- R:R2(空白 PNG 被识别,不当成已渲染)。
- I:I-restraint(批准**后**要真迁移、且走宪法治理,不是永久困在 Prototype)。
- O:O-restraint(客观分过线**仍**要 USER GATE,不自动迁移)。
- N:N1/N2(功能 bug、既有 Figma 源都不进本循环)。

restraint 行都保持 = 新规则精准(只收紧目标退化,不误伤边界)。

---

## 什么时候跑哪个 family

- 改了 `## The loop` 的「Never skip 3–4」/ 渲染 recipe / Anti-pattern「从代码判美学」→ **R**(R1 风险最高)。
- 给**带 constitution / token-compliance 测试**的 repo 用本 skill,或改了 Step 2 隔离说明 → **I**(I1 必验)。
- 用户**无设计经验**(主场景),或改了 Step 4 / Anti-pattern「问用户好看吗」→ **O**(O1 必验)。
- 分诊阶段判断该不该起本 skill,或改了 `When NOT to use` → **N**(N1 是 skill 级 restraint 门)。
- **跳过**:纯 Figma-faithful 实现任务、纯功能修复任务对本 skill 不适用(见 N),不必跑 R/I/O。

## 一句话原则

> 每条纪律都有一个"好坏分叉"的核心判别 case(R1/I1/O1/N1)。
> 美学结论只认渲染像素(R)、批准前只改隔离原型(I)、质量门用 reviewer 打分不问设计盲用户(O)、
> 丑才进循环坏走工程(N)。装完/改完先用核心 case 验一次;改了承载该纪律的 prose 就用 PAIR 证明行为
> 真的翻转,别凭直觉。restraint 的判据尤其硬:**隔离不等于永不迁移,客观分不等于跳过用户批准**。
