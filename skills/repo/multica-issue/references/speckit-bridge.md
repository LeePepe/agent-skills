# Speckit bridge —— 功能 / 架构路径的完整流程

本入口把已定方案**桥接**到 Multica issue，不兼任规划内容 owner。目标仓采用 Spec Kit 时，
由获分配的 Planner 使用已装好的 speckit 能力补缺项；仓库原生 plan／issue 也可作为固定依据。

参照 `specs/README.md` 的既有约定。先复用、校验、补齐已有 spec/plan/tasks；以下生成步骤只用于缺失产物，
已有计划继续走必要 spec/plan 审查。规划 worker 形成设计修改/workflow refine 的方案，原入口路由必要决定，再交原实现者；沿用 [公共合同](../../../workflow/execution-contract.md) 的责任与授权。

---

<a id="功能路径specify--clarify--plan--tasks--逐-task-落-issue"></a>
## 功能路径：复用方案，按 target 桥接 issue

### 1. specify

仅当仓库采用 Spec Kit 且缺少当前 spec 时，由规划者执行；已有原生或 Spec Kit 基线则直接进入 target 映射。

```
/speckit-specify <用户的功能描述>
```
产出 `specs/NNN-name/spec.md`(NNN 自增,看 `ls specs/` 现有最大编号 +1)。

### 2. clarify(grilling 风格)

```
/speckit-clarify
```
打磨 spec 里的模糊点。风格纪律(distill 自 mattpocock grilling):
- **一次只问一个问题**,等回答再问下一个(一次抛一堆会让人懵)。
- **每个问题附上你的推荐答案**。
- **能靠读代码回答的,先读代码,别问用户**。

### 3. plan + tasks

```
/speckit-plan     # → specs/NNN-name/plan.md
/speckit-tasks    # → specs/NNN-name/tasks.md,task ID 形如 [T###] [Story]
```

**两条硬约束**(写进 plan/tasks,也是 review 时会被 gate 的点):
- **reference constitution 章节**,不重述规则(如「见 Constitution §II Swift 6 Strict Concurrency」)。
- **按目标、真实依赖和目标仓 PR 单元拆**，不以 layer 数机械切任务。plan 记录本次方案版本、任务、依赖、
  完成条件与下一动作，引用适用版本的 repo guide/shared 文档；通用政策留在这些来源。

<a id="4-逐-task-落-multica-issue不跑-speckit-implement"></a>
### 4. 按 target 落 Multica issue（不跑 speckit-implement）

实现已明确交给 Multica，才进入此桥接。用 `multica-cli.md` 的配方映射受审 target：

1. 一个 target／仓库交付单元对应一个实现 issue，body 引用准确方案版本、owner、内部 task ID 与验收映射。
   跨层且必须原子成立的改动保留在同一 target，不将 tasks.md 每一行自动建成 sub-issue。
2. 单 target 不强制 parent。多个独立交付 target 分别建 issue；确需汇总时才建 parent，
   `--stage N` 仅表达真实 target 依赖，不直接照搬内部 task 顺序或层次。
3. blocker 先建，依赖方引用真实 key；已有 issue 与在途执行者沿原记录继续。
4. **spec 先入库门禁**：引用的 spec/plan/tasks/ADR 或原生方案须在实际执行基线可读并匹配批准版本。
   缺失时保持待派发，交获授权的文档实现者完成必要文档 PR，经既有 gates／审批后复核。
   完整内联方案无需虚构外部文件；详见 `SKILL.md` 第 4 步及 `multica-cli.md` 对应门禁。
5. 授权、依赖与唯一写者检查齐备后，只派发已就绪的 target issue 并验证对应 run，不因汇总 parent 存在重复启动实现。

> 若 repo 装了 speckit 的 `/speckit-taskstoissues`,它是用 **GitHub MCP** 建 GitHub issue 的
> —— 与本 workflow(Multica issue)**不同**,**不要**用它。本 skill 走 Multica CLI。

---

<a id="架构路径先改-tech-context--宪法再落-issue"></a>
## 架构路径：内容 owner 定方案，原实现者改文档

判断改动性质,二选一。

### C1. 纯 tech-context 补充/修正(不违反红线)

例:补一层 CONTEXT.md 的说明、修正一条 test 命令、澄清数据流。

1. 规划／技术内容 owner 核对对应层 CONTEXT 或仓库 guide 的事实、约束与验证入口，确定本版修正内容。
2. 归入已有 target，或按仓库交付单元形成 `[Arch]` issue（模板 3），由原实现者在核实的任务 worktree 修改文档。
   原有 frontmatter 防腐 hook／CI 与内容审查继续有效；桥接入口不先写源码再补记。

### C2. 改架构方向 / 违反现宪法

例:加 layer、换依赖方向、放松并发或隐私约束。

先确认规划者已定基本方案、必要 Owner 决定与执行授权；政策/权限变化另需明确授权，不能为了实现自行放松红线。
超出当前约定的新方案回到同一需求沟通入口，Owner 确认该版可以执行后才交接；当前执行版不被讨论自动改写。

1. **先**由对应内容 owner 准备所需宪法／ADR 变更，再由获授权的实现者按仓库流程提交与接受审查：
   - 跑 `/speckit-constitution` 更新 `.specify/memory/constitution.md` + 版本 bump;或
   - 写 `docs/adr/NNNN-<slug>.md`(记录 Decision / Context / Consequences / 例外原因)。
   - 依据:`specs/README.md`「与 Constitution 冲突 → 先改 Constitution(走 ADR + 版本 bump),
     再写 spec」+ constitution「例外仅限……且必须在 ADR 中显式记录原因」。
2. **再**落实现 issue(模板 3),body 的 `## ADR / Constitution` 段指向第 1 步的产物。
3. 若架构变更有多个交付目标 → 复用功能路径，按目标仓合同和依赖安排 sub-issue，不按 layer 数切分。

---

## 降级(无 speckit)

目标 repo 无 `.specify/` 时:
- 功能路径使用固定的仓库原生 spec／plan／issue，明确 target、内部 task 与验收映射；
  单 target 直接使用模板 2，无需初始化 Spec Kit 或重做已有规划。必要依据确实缺失才交 Planner 补齐。
- 架构路径退化为「在 issue body 内联记录 Decision/Consequences」,提示补建 `docs/adr/`。
