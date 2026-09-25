---
name: layered-ci-autofix
description: 运行时(run-time)闭环:把改动 commit/push、开 PR、监督 PR 的 required CI、失败时读结构化失败信号 {layer, path, kind, detail, red_lines} 做**按 layer 收窄的自动修复**,修完再 push、重新等 CI,直到绿灯或触发升级。它是 repo-kit(setup-time 脚手架)的**运行时消费者**——消费后者铺好的 CI 信号与每层 red_lines/test;门用 auto-review-merge,不自己重造。当用户想"项目改完自动 commit、监督 PR CI、CI 挂了自动修、跑通再合"时使用。用于:一次任务收尾的 push→监督→修复闭环。不用于:装脚手架(那是 repo-kit)、纯搭 CI 门(那是 auto-review-merge)。
allowed-tools: Read, Write, Edit, Bash, Agent
---

# Layered CI Autofix

一个**运行时闭环**:改动做完后,`commit → push → 开/定位 PR → 监督 required CI →
CI 失败读结构化信号做**按 layer 收窄的自动修复** → 修完 push → 重新等 CI`,直到绿灯或升级。

**Announce at start:** "我在用 layered-ci-autofix skill。"

## 定位:这是 run-time,不是 setup-time

三个相邻 skill/agent 各管一段,别混:

| | 管什么 | 时机 | 本 skill 关系 |
|---|---|---|---|
| **repo-kit** | 铺分层脚手架:三层文档、AGENTS.md、frontmatter、**三段门禁 + 结构化失败信号** | setup-time(一次) | **本 skill 消费它的产物**:读每层 `red_lines`/`test`,读 CI 吐的 `{layer,path,kind,detail,red_lines}` |
| **auto-review-merge** | 装 PR 自动 review + 门过自动合并(self-hosted runner 上的确定性 merge 门) | setup-time(一次) | **本 skill 复用它当门**:不自己重造 review/merge 门;它红本 skill 就修,它绿就放行 |
| **本 skill(layered-ci-autofix)** | **运行时**把改动推上去、盯着门、门红了按 layer 自动修 | run-time(每次任务收尾) | 闭合前两者留下的"谁来修"这一环 |

> **为什么单独成 skill 而非塞进 repo-kit**:后者明确划了 setup/run-time 边界——
> "hook 只发现+结构化报告,**不内联跑 agent**;谁来修由消费方决定"。**本 skill 就是那个"消费方"**:
> 它在运行时读信号、派修复。把它塞回 setup-time skill 会破坏那条边界。

## 前置(precondition):目标 repo 应已被 repo-kit 铺过

本 skill 的自动修复**靠分层信号收窄范围**。理想前置:

- `AGENTS.md` 链接到维护中的 **layer map/resolver**(失败路径 → layer 的映射源),无需在入口内嵌表格。
- 每层 `tech-context.md` frontmatter 有 **`red_lines`(修的时候不能踩)+ `test`(只跑本层的验证命令)**。
- CI required 会吐**结构化失败信号**(见 `references/signal-contract.md`)。

**缺前置时降级(不硬失败)**:
- 无 layer 索引 / frontmatter → 退化为"整仓库级"修复:仍能监督 CI + 尝试修,但**不能按 layer 收窄、
  不能带 red_lines**,风险更高。**先提示用户"建议先跑 repo-kit 再用本 skill"**,
  用户坚持再降级跑。
- 无 auto-review-merge 门 → 只盯**原生 CI required checks**(`gh pr checks`),跳过 review 门那一路。

## 执行流程

### 第 0 步:探测 + 确认(AskUserQuestion)

```bash
REPO="$(git rev-parse --show-toplevel)"; cd "$REPO"
git remote -v | head -1                                   # 有无 remote(无则只能本地,PR 那段跳过)
gh auth status 2>&1 | head -3                             # gh 是否登录
BASE="$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||' || echo main)"
test -f AGENTS.md && echo "先沿 AGENTS 链接读取实际 layer map/resolver;确认目标存在后再判断是否降级"
gh pr status 2>/dev/null | head -20                       # 当前分支有无已开 PR
```

问用户(只问有歧义的):
1. **修复的自治边界**:CI 红了 → (a) 自动修并 push(推荐,真正闭环)/ (b) 只诊断出 `{layer, 修复建议}`
   报给用户、不自动改代码。**破坏性/外向操作默认 (a) 也要在每轮 push 前让门把关,不直接 merge。**
2. **重试上限 N**(默认 3):同一 layer 连修 N 轮仍红 → 停手升级给人,避免无限烧。
3. **合并策略**:全绿后 (a) 交给 auto-review-merge 的 auto-merge 自动合(推荐)/ (b) 停在"全绿待人工合"。
   本 skill **不自己点 merge**——merge 由门(auto-review-merge)或人决定。

### 第 1 步:commit + push + 开/定位 PR(机制委托,不重造)

commit/PR 的**机制**(commit 规范、PR 模板、base 分支探测)交给 `git-monitor` 式的做法——
读项目约定(`CLAUDE.md` / `.claude/team.md` 的 commit/PR 格式),默认 Conventional Commits。
**本 skill 只负责闭环,不重新发明 commit 规范。** 可直接派 `git-monitor` agent 做这步:

```
Agent(subagent_type: "git-monitor")  # 若环境有该 agent:staging+commit+push+gh pr create,返回 pr_url/ci_failures
```

无该 agent 时的最小内联(仍遵守项目约定):
```bash
git add -A && git status --short
git commit -m "<type>: <imperative summary>"              # 遵守项目 commit 约定
git push -u origin "$(git rev-parse --abbrev-ref HEAD)"   # push 会触发本地 pre-push 快门禁
gh pr create --base "$BASE" --fill 2>/dev/null || gh pr view --json url -q .url   # 已开则复用
```
> ⚠️ push 会触发 repo-kit 装的 **pre-push 快门禁**(秒级)。若它红,是**本地**信号,
> 当场按同一套"按 layer 收窄"修(见第 3 步),别 `--no-verify` 绕过——CI 照样拦。

### 第 2 步:监督 required CI(直到有结论)

用 `gh pr checks` 轮询到所有 required check 有终态。**别只等成功——要覆盖所有终态**
(success / failure / cancelled / timed_out),否则崩溃/挂起看起来和"还在跑"一样。

推荐用 Monitor 工具持续盯(每次 check 落地一个事件,全终态覆盖):
```bash
# 轮询 gh pr checks,发出每个非 pending check 的结论,全部有终态即退出
prev=""
while true; do
  s="$(gh pr checks --json name,state,bucket 2>/dev/null || gh pr checks 2>&1)"
  cur="$(echo "$s" | jq -r '.[]? | select(.state!="PENDING" and .state!="IN_PROGRESS") | "\(.name): \(.bucket // .state)"' 2>/dev/null | sort || true)"
  comm -13 <(echo "$prev") <(echo "$cur")               # 只发新落地的 check
  prev="$cur"
  # 全部有终态(无 pending/in_progress)→ 退出
  echo "$s" | jq -e 'all(.[]?; .state!="PENDING" and .state!="IN_PROGRESS")' >/dev/null 2>&1 && break
  sleep 30                                                # 远端 CI:30s+,别更快(rate limit)
done
```
> 用 Monitor 工具包这段(`persistent:false`, timeout 视 CI 时长),grep 覆盖 `failure|cancelled|timed_out|success`,
> 别只 grep success——那样 CI 崩了你会以为它还在跑。

### 第 3 步:CI 红 → 读结构化信号 → 按 layer 收窄自动修(核心)

CI 失败**不是**丢一坨日志就去猜。按 `references/signal-contract.md` 解析出结构化信号:

```
{ layer, path, kind: test|lint|build|typecheck|arch-lint, detail, red_lines }
```

拿到信号后,**每个失败落到它的 layer**,派一个**只在该层内工作**的修复(当前 agent 直接修,
或 `Agent()` 派 subagent),严格遵守 repo-kit 方法论 §5.2 的两条修复约束:

1. **只在失败所在 layer 内改**;根因在别层 → **不跨层改**,记为新任务并**升级给人**(不自作主张扩面)。
2. **带着该层 `red_lines` 修**;修完**只跑该层 `test`** 验证(frontmatter 里的命令),再 push。

派修复 subagent 的 prompt 骨架(把信号字段填进去):
```
你在修复 CI 失败,严格限定在 layer=<layer> 内。
- 失败:<kind> @ <path> — <detail>
- 本层 red_lines(修的时候一条都不能踩):<red_lines>
- 修完只跑本层验证:<该层 frontmatter 的 test 命令>,贴出通过证据再返回。
- 若根因不在本层 → 不要跨层改;返回 {escalate: true, reason, suspected_layer}。
```

> **red_lines 是硬约束**:典型反面教材是"为了过测试把敏感数据打进日志 debug",而该层 red_line
> 明写"敏感数据禁止进日志"。修复 subagent 必须带着 red_lines,**过测试不是唯一目标**。

### 第 4 步:修完 → 回到第 1 步 push → 重新等 CI(有界循环)

一轮修复 = 一次"改(单层)→ 本层 test 绿 → commit → push → 重新监督 CI"。循环直到:

- **全绿** → 进第 5 步。
- **同一 layer 连修达重试上限 N** → **停手升级**(附:每轮改了什么、本层 test 结果、仍红的 check)。
  别无限重试烧预算。
- **根因跨层 / 需改 red_lines / 需改 tech-context(架构变更)** → **停手升级**,记为新任务。
  架构性变更应先走 repo-kit 的维护/ADR,不在自动修里偷改。

> **每轮 push 都要重新过门**(pre-push 快门禁 + CI required + auto-review-merge 的 review 门)。
> 本 skill **不 `--no-verify`、不 admin-merge 绕过**——闭环的价值正是"每轮都真过门"。

### 第 5 步:全绿 → 交给门决定合并(不自己合)

- 若装了 **auto-review-merge** 且用户选了自动合:全绿后 GitHub auto-merge 会自己 squash 合,
  本 skill 只需确认门全绿、把 pr_url + 最终状态报给用户。
- 否则停在"**全绿待人工合**",把 PR 链接 + 通过的 check 清单交给用户。
- **本 skill 任何情况下都不主动点 merge / 不 admin override**——merge 归门或人。

### 第 6 步:收尾报告

给用户一张表:
- PR 链接 + 最终 CI 状态(全绿 / 升级 / 待人工合)。
- **每轮自动修复**:第几轮、落在哪个 layer、改了什么、带的 red_lines、本层 test 结果。
- **升级项**(如有):为什么停手(跨层根因 / 超重试 / 触红线),建议的新任务。
- 降级说明(如有):无 layer 索引 → 整仓库级修复,风险提示。

---

## 关键原则(别违反)

- **run-time 消费者,不是 setup 脚手架**:读 repo-kit 铺的信号,不重铺脚手架。
- **门不自造**:review/merge 门是 auto-review-merge 的事;本 skill 只对门的红/绿**反应**。
- **修复严格按 layer 收窄**:只在失败层内改、带该层 red_lines、只跑该层 test;跨层根因**升级不偷改**。
- **有界自治**:重试上限 + 触红线/跨层/架构变更即升级;**不无限烧、不绕门、不自己 merge**。
- **监督覆盖全终态**:盯 CI 要覆盖 failure/cancelled/timed_out,不只 success(否则崩溃=看似还在跑)。
- **每轮真过门**:不 `--no-verify`、不 admin-merge;闭环价值在"每轮都真过门"。
