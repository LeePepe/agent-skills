# Discovery Playbook — Phase 0/1 操作手册

**发现 = 本 skill 的命根子。** 发现太弱 → 任何项目都产出雷同泛泛蓝图(最大失败模式)。
本文给"扫什么、怎么读、怎么分类",外加**两个 worked example**(Financial / aidata)证明
同一方法在两个项目上必然分叉。

> 铁律:**先发现,后处方**。没扫完 Phase 0 不许写任何分层建议。对**主分支**扫,别信工作分支半成品。

---

## Phase 0 — 扫什么(自适应,按发现到的生态走)

### A. 数据结构定义(schema 的事实源)

```bash
# ORM 模型(最常见)
find . -maxdepth 4 \( -name 'models*.py' -o -name '*.model.ts' -o -name 'schema.prisma' \
  -o -name 'models.go' -o -name 'entity*.java' \) 2>/dev/null | grep -vE 'node_modules|\.venv|dist'
# 裸 DDL / 迁移
find . -maxdepth 4 \( -name '*.sql' -o -path '*migrations*' -o -name 'schema.rb' \) 2>/dev/null | grep -vE 'node_modules|\.venv'
# 活库 introspection(有 DB 文件/连接时最权威)
#   SQLite: sqlite3 <db> '.schema'   /   .tables
#   PG:     \d+ <table> ; select * from information_schema.columns where table_schema='public'
```

### B. 已有的派生/聚合服务(**决定 red-line 3**)

这是最容易漏、又最关键的一步:项目里**哪些指标已经在算、在哪算、是查询时现算还是持久化**。

```bash
# 聚合/派生逻辑的信号词
grep -rniE 'aggregate|group_?by|sum\(|snapshot|derive|rollup|recalc|materializ' \
  --include='*.py' --include='*.ts' --include='*.sql' . | grep -vE 'node_modules|\.venv|test' | head -60
# 服务层(业务逻辑常在这)
find . -type d \( -name services -o -name domain -o -name usecases \) 2>/dev/null
```

对每个命中问三件事:**(1) 它算什么指标? (2) 结果持久化了还是每次现算? (3) 算法在哪个函数、是不是唯一实现?**
→ 现算但被反复调用的聚合 = "该物化"候选;被多处调用的算法 = SSOT,数仓只能 build *from* 它。

### C. 接入/导入管线 + 幂等

```bash
grep -rniE 'import|ingest|sync|upsert|dedup|external_id|idempoten|on_conflict|unique' \
  --include='*.py' --include='*.ts' . | grep -vE 'node_modules|\.venv' | head -40
```
看:数据从哪进来、有没有不可变 raw、幂等键是什么、去重逻辑在哪。

### D. 已存在的分层/数仓痕迹(决定 greenfield vs retrofit vs audit)

```bash
ls dbt_project.yml profiles.yml 2>/dev/null
find . -maxdepth 3 -type d \( -iname 'warehouse' -o -iname 'dwd' -o -iname 'ods' \
  -o -iname 'marts' -o -iname 'l[1-5]_*' -o -iname 'analytics' \) 2>/dev/null | grep -vE 'node_modules|\.venv'
```
有完整分层 → **audit 模式**;有零碎 → **retrofit**;啥都没有 → **greenfield**。

**Phase 0 产物**:一张数据模型清单(实体 + 字段要点 + 关系 + 已有聚合 + 幂等键 + 现有分层痕迹)。

---

## Phase 1 — 分类:给每个结构打标签

对清单里每个结构,打一个(或多个)标签。判别启发式:

| 标签 | 判别信号 | 映射倾向 |
|---|---|---|
| **不可变事件/delta 源** | append-only、有 external_id/幂等键、一行=一个业务事件、不被 update | ODS→DWD 明细 |
| **anchor/快照 checkpoint** | 字段名含 anchor/snapshot/as_of、把"某时刻状态"钉下来、按时间点索引 | SCD Type 2 式历史 / 周期快照事实 |
| **维度/主数据** | 被多张表外键引用、描述性属性、变化慢(instrument/account/user/category) | DIM 一致性维度 |
| **已派生事实** | 由服务算出、可能持久化(net_worth_history 等)、是聚合结果 | DWS/ADS(或"该物化"的候选) |
| **指标/聚合** | 现算的 sum/rollup、报表口径、query_service 里的 group-by | DWS 指标 / ADS |

**诚实 grain**:对每个事实候选,写清"一行代表什么"。多个不同 grain → **多张事实表**,别硬拼成一张
(red-line 2)。**honest keys**:键不完美(近似 join、时区桶、缺失外键)如实标注,别假装干净。

---

## Worked Example A — Financial(greenfield:从派生服务建,别 fork 数学)

**发现到的**:SQLAlchemy ORM(`backend/app/models/models.py`)+ SQLite,**无任何数仓/dbt**。
两个 bounded context(现金账本 / 投资持仓),只在净值 roll-up 处相交。核心是 **Anchor+Delta 派生引擎**。

**分类结果**:

| 结构 | 标签 | 依据 |
|---|---|---|
| `LedgerEntry` / `Transaction` | 不可变 delta 源 | 一行=一笔流水/交易,`(account,source,external_id)` 幂等键 |
| `AccountBalanceAnchor` / `PositionAnchor` | anchor checkpoint | 按 `anchored_at` 钉状态 = SCD2 式历史留痕 |
| `Instrument` / `Account` / category | 维度 | 被流水/交易外键引用、变化慢 |
| `derived_net_worth_service`(每日净值/账户余额趋势) | **已派生事实但查询时现算** | 每次 forward-scan anchor+delta 重算,未持久化 |
| `NetWorthHistory` / `AccountBalanceHistory` | 已持久化快照事实 | 每日 00:05 scheduler 写一行 |
| `stats_service` / `query_service` | 指标/聚合 | 现算日/月收支、savings rate、group-by |

**该项目蓝图的独特结论**(与 aidata 完全不同):
- ODS = `LedgerEntry`/`Transaction`(不可变 delta);DIM = `Instrument`/`Account`/category。
- **周期快照事实表**(该物化的核心):把 `derived_net_worth_service` 现在**查询时现算**的每日
  净值 / 每账户余额 / 每持仓市值,**物化成 fct_daily_networth / fct_daily_account_balance /
  fct_daily_position**。这是 gap 分析的头号项。
- **red-line(项目专属)**:这些事实表必须 **build *from* `account_balance_service` /
  `position_service` / `derived_net_worth_service` 这些既有派生函数**,**绝不重抄 Anchor+Delta 加权
  平均成本的数学**——代码已把它们强制为 SSOT(连 L4 `explain_*` 都是同一函数的 trace,不是重实现)。
  蓝图若建议在 SQL 里重写这套数学 = 直接判失败(eval Family C)。
- anchor 表按 SCD2 理解:数仓的历史维/快照从 anchor 派生,不另造历史机制。
- DWS/ADS = `stats_service`/`query_service` 的口径,登记进指标口径表;CLI(`--json`/`--explain`)是消费口。

## Worked Example B — aidata(audit:已是 L1-L5,体检不重建)

**发现到的**:**已经是一条完整分层管线** `L1_collect → L2_normalize → L3_merge(星型) → L4_serve → L5_apps`,
`schema/warehouse.sql` 是**刻意的多 grain 星型**(fact_request / fact_turn / fact_issue / fact_task /
fact_pr / …,dim_model / dim_session),~14 源经 adapters 接入,幂等(watermark + PK dedup + snapshot hash),
memory 源刻意停在 L2。

**该项目蓝图的独特结论**(与 Financial 完全不同):
- **不是 greenfield,是 audit**。任务 = 检查分层纪律的偏移,产出 refine delta,**不推倒重来**。
- 逐项体检:① grain 是否诚实(多 fact 未被拍平成 OBT?✓ 符合 red-line 2)② 单向流是否守住
  (每层只读上一层?)③ 幂等是否完整(watermark/dedup/hash 覆盖所有 adapter?)④ **脱敏/secrets
  red-line**(L1 redaction 是否覆盖新源?)⑤ 时区(UTC vs CST 桶)一致?⑥ memory 停 L2 的边界是否被违反。
- 映射到标准术语(供跨项目沟通):L1≈ODS、L2≈DWD 清洗、L3≈DWD+DIM 星型、L4≈DWS/ADS、L5≈消费。
- gap 表列的是"哪个 adapter 缺幂等 / 哪个新源没进 redaction / 哪个 fact grain 标注不清",
  而非"该建什么表"。

> **两个 example 的分叉点**就是 eval Family D 的判据:Financial → 设计物化 + SSOT 红线;
> aidata → 体检既有分层 + 纪律 delta。若你的方法对两者产出雷同,就是发现太弱,回 Phase 0 重做。

---

## 常见发现陷阱

- **只读 ORM 不读服务**:漏掉"已有派生"→ 蓝图重复造轮子、踩 SSOT 红线。B 步必做。
- **把 anchor 当普通维度**:漏掉它的 SCD2/快照语义 → 历史留痕设计错。
- **把现算聚合当"已持久化"**:没分清查询时 vs 落库 → 漏掉最该物化的项。
- **假设 schema 干净**:不标 honest keys → 蓝图承诺做不到的 join。
- **不分主/工作分支**:把别的任务的半成品当既有分层 → 误判模式(greenfield/retrofit/audit 选错)。
