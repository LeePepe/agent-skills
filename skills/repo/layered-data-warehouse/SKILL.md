---
name: layered-data-warehouse
description: 给一个项目把数据仓库"分层重构/梳理成型"——先扫描项目真实的数据模型(ORM/DDL/DB/已有派生服务/导入管线),再套标准数仓分层(ODS/DWD/DIM/DWS/ADS,附 medallion 与 dbt 交叉映射),产出一份可演进的 warehouse 蓝图:分层清单、一致性维度、指标口径登记、SCD 与增量幂等策略、血缘、项目专属 red-lines、gap 分析与分阶段 refine 计划。产物是设计蓝图不是实现代码。方法固定、内容永远来自发现——同一份 skill 对 aidata(AI 用量遥测、已是 L1-L5 星型)与 Financial(个人财务 ORM + Anchor+Delta 派生引擎、尚无数仓)产出完全不同的蓝图。当用户想"把某项目的数据仓库分层搭起来/梳理/重构/refine、按 收集→整理→分析→总结→消费 组织、做 ODS/DWD/DWS/ADS 或 bronze/silver/gold 分层设计、给现有数仓做分层体检、设计事实/维度/指标口径/SCD"时使用。
---

# Layered Data Warehouse

给一个项目把数据仓库**分层梳理成型**:读它**真实的**数据模型,套标准分层骨架,产出一份
**可演进的 warehouse 蓝图**(设计,不是实现代码)。适用任意语言、任意存储。

先读理论底座:`references/layering-model.md`(标准分层 ODS/DWD/DIM/DWS/ADS + 收集→整理→分析→
总结→消费 主线 + medallion/dbt 交叉映射 + 事实表/SCD/指标口径,含已核查的纠偏)。发现与分类
的操作手册:`references/discovery-playbook.md`。产物骨架:`references/blueprint-template.md`。
判别性自检:`references/eval-cases.md`。

## 什么时候用(设计-time,产物是蓝图)

这是**把结构想清楚**的 skill,**不写实现代码**。三个触发场景:
1. **greenfield**:项目有数据但无数仓分层(如 Financial)——设计从零该怎么分层、哪些查询时聚合该物化。
2. **retrofit/refine**:已有部分分层,梳理成体系、补缺、纠偏。
3. **audit/体检**:已有完整分层(如 aidata 的 L1-L5)——检查分层纪律(grain 是否诚实、幂等、脱敏红线),报告偏移 + refine delta,**不推倒重来**。

## 五个红线(方法的脊梁,别违反)

1. **先发现,后处方**:任何分层建议之前,必须先读真实数据模型;**绝不假设 schema**。跳过 Phase 0 = 违规。
2. **诚实的 grain**:事实表按真实粒度多表建模;**默认星型/多 grain,不默认拍成一张大宽表(OBT)**;OBT 只在消费侧、有明确理由时用。
3. **单一事实源(SSOT)**:数仓表**建立在项目已有的派生/计算服务之上**,绝不重抄它们的算法。
   (Financial 的教训:Anchor+Delta 派生数学被代码强制为 SSOT,数仓只能 materialize *from* 它,不能 fork。)
4. **蓝图不是代码**:本 skill 止于 spec;实现是之后单独一步(可由本蓝图驱动)。
5. **方法固定、内容发现**:每个项目同一套 phase;实体/指标/grain/red-lines 永远来自 Phase 0,不来自模板。

---

## 执行流程

### Phase 0 — 发现真实数据模型(不发现就不许处方)

按 `references/discovery-playbook.md` 扫描,产出一张**数据模型清单**:
- ORM 模型 / `schema.sql`·DDL / 活库 introspection(`sqlite`、`\d`、information_schema)
- **已有的聚合/派生服务**(哪些指标已在算、在哪算、是查询时还是持久化)
- 导入/ingestion 管线、幂等键、去重逻辑
- 已存在的分层/数仓目录(有没有 dbt、warehouse/、快照表)

> ⚠️ 对**主分支**探测,别信当前工作分支的半成品。发现结果决定后面一切——发现太弱 → 两个项目会产出雷同的泛泛蓝图(这是本 skill 最大的失败模式,见 eval Family D)。

### Phase 1 — 分类来源与粒度(grain)

给每个发现的结构打标签(判别启发式见 playbook §分类):
**不可变事件/delta 源 · anchor/快照 checkpoint · 维度/主数据 · 已派生事实 · 指标/聚合**。
识别每个事实的**诚实 grain**(一行代表什么),标注不完美的键(honest keys)。

### Phase 2 — 映射到分层

把每个结构放进 ODS/DWD/DIM/DWS/ADS(并注 medallion bronze/silver/gold + dbt staging/intermediate/marts 的对应)。
- 保持**多 grain 星型**;DIM 抽成一致性维度;**别默认 OBT**。
- 映射只是**跨体系类比**,不是官方对照——如实说明(见 layering-model 的纠偏)。

### Phase 3 — Gap 分析(现状 vs 分层理想)

逐项 diff,产出 gap 表(格式见 blueprint-template):
- 查询时聚合**该物化**却没物化(如 Financial 的 `derived_net_worth_service` 每次现算)
- 算法被**重抄**而非复用(SSOT 违规)——最高优先级红旗
- 缺一致性维度 / 缺数据质量校验 / 未处理 SCD / 缺血缘 / 缺幂等

### Phase 4 — Refine 蓝图(最终产物)

按 `references/blueprint-template.md` 产出 warehouse spec:每层表/模型定义、一致性维度、
**指标口径登记表**、SCD 策略、增量+幂等策略、血缘图、**项目专属 red-lines**、gap 表、
**分阶段 refine 计划**。落到目标 repo 的 `docs/`(路径先问用户确认,`AskUserQuestion`)。

**收尾**:产物只到蓝图。若用户要落地实现,那是下一步单独任务——蓝图里的"分阶段计划"就是它的输入。

---

## 关键原则(别违反)

- **每个项目产物必须不同**:aidata → 对已有 L1-L5 做体检 + refine delta;Financial → 设计把查询时快照物化成事实表、且**从派生服务建、不 fork 数学**。若两者产出雷同 = Phase 0 发现太弱,回去重做。
- **grain 诚实优先于"好看"**:多 grain 事实表 > 一张万能宽表。
- **SSOT 是硬约束**:数仓 build *from* 既有派生,不重实现。
- **止于蓝图**:不写 SQL 模型 / 不建物化表 / 不建 dbt 工程——那是实现,超出本 skill。
- 装完/改完用 `references/eval-cases.md` 的判别性 case 自检(尤其 Family D:两项目蓝图必须分叉)。
