# Eval Cases — 用判别性 case 验证蓝图产物

本 skill 产出一份 warehouse 蓝图。**"文档写了 / 分层画了"不等于"设计正确"**。本文用
**discriminating cases + paired old-vs-new grading** 自检那些**有真实好坏分叉**的产物。
每个 family 针对一类失败模式,给"输入场景 + 正确产物 + 坏产物(会怎样错)+ 可判定 grader"。

| Family | 验什么 | 核心判别 case | 何时必跑 |
|---|---|---|---|
| **D** 项目分叉 | 发现驱动够不够强 | D1 ⭐ Financial vs aidata 蓝图必须分叉 | 改了发现/方法 prose;接新项目前 |
| **C** SSOT 红线 | 数仓 build from 而非重抄 | C1 ⭐ 现算聚合→物化但禁止重抄数学 | 项目有"已派生服务"时(必跑) |
| **G** 诚实 grain | 多 grain vs 默认 OBT | G1 ⭐ 多事实表 vs 拍平大宽表 | 有多个不同 grain 事实时 |
| **P** 止于蓝图 | 设计 vs 写实现代码 | P1 ⭐ 产物是 spec 不是 SQL/DDL | 每次(边界最容易越) |

---

## Family D — 项目分叉(发现驱动够强吗)

**这是本 skill 的命根子判别。** 方法固定、内容发现——若对两个截然不同的项目产出雷同泛泛蓝图,
说明 Phase 0 发现太弱,方法退化成"套模板"。

### D 判别性 case 集

输入:分别对 **Financial**(ORM + Anchor+Delta,无数仓)与 **aidata**(已有 L1-L5 星型)跑本方法,
比对两份蓝图。

| # | 观察点 | 正确(分叉) | 坏设计(雷同/套模板) |
|---|---|---|---|
| **D1** ⭐ | 模式判定 | Financial=greenfield(设计物化 + SSOT 红线);aidata=audit(体检既有分层 + 纪律 delta) | 两个都输出"建 ODS/DWD/DWS/ADS 四层"的通用清单,不提 Financial 的 Anchor+Delta / aidata 的既有 L1-L5 |
| D2 | 头号 gap | Financial="把 `derived_net_worth_service` 现算的每日净值物化成周期快照事实表";aidata="某 adapter 缺幂等 / 新源没进 redaction" | 两个 gap 表内容可互换(说明没读进真实结构) |
| D3 | red-lines | Financial 点名"不 fork Anchor+Delta 数学";aidata 点名"secrets 不出 L1、memory 停 L2" | red-lines 是通用套话(如"注意数据质量"),不点名项目真实约束 |

**D1 是核心判别 case。** 可判定 grader:

```
PASS(分叉) 当且仅当:
  - 两份蓝图的"模式"不同(一个 greenfield/设计,一个 audit/体检)
  - 且各自 red-lines 至少含一条点名了该项目真实结构的约束
    (Financial: Anchor+Delta / 派生服务名;aidata: L1-L5 / redaction / memory-stop-L2)
  - 且头号 gap 不可在两项目间互换
FAIL(套模板) 当:
  - 两份蓝图除项目名外结构雷同、gap 可互换、red-lines 是通用套话
```

---

## Family C — SSOT 红线(build from,别重抄数学)

方法 red-line 3:数仓表建立在**既有派生/计算服务之上**,绝不重抄其算法。最危险的坏设计是
"发现项目现算某聚合 → 蓝图建议在 SQL/dbt 里**重写**那套数学"——制造第二份实现,SSOT 破裂。

### C 判别性 case 集

输入场景:"项目有个服务在**查询时现算**一个聚合(如 Financial 的 `derived_net_worth_service`
用 Anchor+Delta 算每日净值)。蓝图该怎么处理?"

| # | 蓝图对该聚合的处理 | 正确 | 坏设计 |
|---|---|---|---|
| **C1** ⭐ | 既要物化、又要守 SSOT | 标"该物化成周期快照事实表",**且明确 build *from* 既有服务函数**,red-lines 点名"禁止重抄该数学" | 建议在 SQL/dbt model 里**重写**加权平均/anchor+delta 逻辑 → 第二份实现,口径会漂移 |
| C2(restraint) | 项目**没有**既有派生、就是裸表 | 正常设计 DWS 聚合,不必强加"复用"套话 | 硬编一个不存在的"既有服务"去复用 → 幻觉 |

**C1 是核心判别 case。** 可判定 grader:

```
PASS 当且仅当:对"查询时现算的聚合",蓝图同时满足:
  (a) 标记为"该物化"(进 gap 表,优先级高)
  (b) 物化方案明确"build from <既有服务/函数名>",不重写其算法
  (c) red-lines 有一条点名禁止 fork 该数学
FAIL 当:蓝图把该聚合的算法在 SQL/dbt/新服务里重新实现一遍(即使结果正确)——SSOT 违规,判失败
```

> 这是 Financial 场景的硬约束来源:代码已把 Anchor+Delta 派生函数强制为 SSOT(连 L4 explain 都是
> 同一函数的 trace)。蓝图重写 = 直接失败,无论 SQL 写得多对。

---

## Family G — 诚实 grain(多事实表,别默认 OBT)

方法 red-line 2:默认多 grain 星型;OBT 只在消费侧、有理由时。坏设计是发现几个不同 grain 的
事实,图省事**默认拍平成一张万能大宽表**。

### G 判别性 case 集

输入:"项目有多个不同 grain 的事实(如 Financial:每日净值 / 每账户余额 / 每持仓市值,三个粒度)。"

| # | 蓝图的事实建模 | 正确 | 坏设计 |
|---|---|---|---|
| **G1** ⭐ | 多 grain 怎么放 | 拆成**多张事实表**(fct_daily_networth / fct_daily_account_balance / fct_daily_position),各自 grain 清晰 | 拍平成一张 `wide_everything` 大宽表当默认 → grain 混乱、冗余爆炸 |
| G2(restraint) | 消费侧确有 OBT 需求 | 在 ADS/消费层给一张宽表**并写明理由**(看板性能),中间层仍多 grain 星型 | 因"要多 grain"就禁止任何宽表,连消费侧合理的 OBT 也不给 |

**G1 是核心判别 case。** grader:

```
PASS 当且仅当:不同 grain 的事实被放进各自事实表(grain 在事实表清单里逐个写明);
             若出现 OBT,仅在消费/ADS 层且附理由。
FAIL 当:默认把多个不同 grain 拍进一张宽表,或事实表清单里 grain 标注缺失/混装。
```

---

## Family P — 止于蓝图(设计,不是实现代码)

方法 red-line 4:本 skill 产物是 spec,实现是之后单独一步。坏设计是越界——直接开始写建表 DDL /
dbt model SQL / 物化脚本,把"设计"做成"实现"。

### P 判别性 case 集

| # | 产物形态 | 正确(蓝图) | 坏设计(越界写实现) |
|---|---|---|---|
| **P1** ⭐ | 事实表怎么表达 | 用**表格描述** fct 的 grain/度量/维度/来源 + "分阶段 refine 计划"列要做什么 | 直接写 `CREATE TABLE fct_… AS SELECT …` 全套 DDL / 完整 dbt `.sql` model |
| P2(restraint) | 能否给示意 | 可给**极简示意片段**说明意图(1-2 行伪代码/列清单) | 因"不写代码"连结构示意都不给 → 蓝图空洞不可执行 |

**P1 是核心判别 case。** grader:

```
PASS 当且仅当:产物以设计描述(表格/清单/计划)为主体,不含可直接执行的完整建表/物化实现;
             refine 计划描述"要做什么"而非"怎么写 SQL"。
FAIL 当:蓝图里出现成套可运行的 DDL/dbt model/ETL 脚本(那是实现,超出本 skill 边界)。
```

> 边界拿捏:允许**极简示意**(说明某事实表大概有哪些列),禁止**成套实现**(可直接跑的 DDL/SQL 工程)。

---

## PAIR — Paired old-vs-new(证明 prose 改动真的移动了行为)

改本 skill 里生成蓝图的 prose(发现手册、分类启发式、模板、红线措辞)后,**别凭直觉认定更好**:

1. 从 `git HEAD~1` 取**旧** prose 节选,从工作树取**新**节选。
2. 起两个 blind subagent:同一核心判别 case(D1/C1/G1/P1),一个只喂旧节选、一个只喂新节选,
   都不知自己拿的新旧、不知期望答案;各自产出**具体蓝图片段**(不是泛泛意见)。
3. 套该 family 的 grader 对照。

**期望**:旧→FAIL、新→PASS = 判别成立。两者都 PASS = 该 case 在当前模型 tier 不判别(换更强
诱导的 case,或诚实记为"防退化非行为翻转")。两者都 FAIL = prose 没解决,回去改。

**Restraint negatives**(证明新规则不过度):对**新** prose 跑 C2(无既有派生别硬造复用)、
G2(消费侧合理 OBT 不被一刀切禁)、P2(仍给结构示意不空洞)。restraint 行都保持 = 规则精准。

---

## 什么时候跑哪个 family

- 改了**发现/分类/方法 prose**,或**接新项目**前 → **D**(D1 命中风险最高:套模板)。
- 项目有**已派生服务** → **C**(C1 必跑:最危险的 SSOT 违规)。
- 有**多 grain 事实** → **G**。
- **每次**(边界最易越)→ **P**(P1:别把设计做成实现)。

## 一句话原则

> 每类失败模式有一个"好坏分叉"的核心判别 case(D1/C1/G1/P1):
> D=两项目蓝图必须分叉(发现够强)· C=物化但禁止重抄数学(SSOT)· G=多 grain 不默认 OBT ·
> P=止于蓝图不写实现。装完/改完先用它验一次;改了 prose 就用 PAIR 证明行为真翻转,别凭直觉。
