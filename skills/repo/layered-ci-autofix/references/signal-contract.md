# Signal Contract — CI 失败信号怎么解析成"按 layer 收窄的修复范围"

本 skill 的自动修复靠**结构化失败信号**收窄范围。信号的**生产方**是 layered-agent-context
铺的 CI required(方法论 §5.1);**消费方**是本 skill。本文定义:信号长什么样、从 CI 里怎么取、
取不到时怎么降级、以及怎么把它映射成一个"只在某层内、带该层 red_lines"的修复任务。

## 1. 信号的规范形状(生产方保证)

layered-agent-context 方法论 §5.1 规定 CI 失败要能解析出**定位 + 约束**:

```jsonc
{
  "layer":      "<失败落在哪个 layer>",     // 由失败路径映射(见 §3)
  "path":       "<出错文件:行>",
  "kind":       "test | lint | build | typecheck | arch-lint",
  "detail":     "<失败摘要:哪个测试 / 哪条规则 / 哪个反向依赖>",
  "red_lines":  ["<该 layer tech-context frontmatter 的 red_lines>"]  // 修的时候不能踩
}
```

`layer` + `red_lines` 是关键:无论谁来修,都能**只在该层内、带着该层红线**修——避免"修好了
测试却违反铁律"。一次 CI 失败可能产出**多条**信号(多个 layer 各挂各的),逐条按其 layer 修。

## 2. 从 CI 取信号的三条路径(按可得性降级)

生产方**理想**情况会把上面的 JSON 作为 job 产物(step summary / artifact / check output)直接吐出来。
现实里不一定,按可得性降级:

### 2a. 首选:CI 直接吐结构化信号

若 CI job 把 `{layer,...}` 写进了 **step summary / job output / artifact**,直接取:
```bash
# 例:从失败 run 的 job 日志里抓本 skill 约定的信号块(生产方用 ::layered-signal:: 包裹)
RUN_ID="$(gh run list --branch "$(git branch --show-current)" --limit 1 --json databaseId -q '.[0].databaseId')"
gh run view "$RUN_ID" --log 2>/dev/null | sed -n 's/.*::layered-signal::\(.*\)/\1/p' | jq -c '.' 2>/dev/null
```
> 若你也在维护生产方(改 CI workflow),**约定一个稳定前缀**(如 `::layered-signal::<json>`)
> 让本 skill 可靠抓取,比解析自由格式日志稳得多。

### 2b. 次选:从 check 名 + 失败日志重建信号

CI 没吐 JSON,但 check 名/路径能定位。取失败 check + 日志,自己重建 `{layer,path,kind}`:
```bash
gh pr checks --json name,state,bucket,link | jq -r '.[] | select(.bucket=="fail") | .name'
gh run view "$RUN_ID" --log-failed 2>/dev/null | tail -80      # 别 | tail 太狠丢掉 error: 定位行
```
`kind` 从 check 名/日志推断(测试框架报错→`test`;linter→`lint`;编译器 `error:`→`build`/`typecheck`;
架构 lint 报反向依赖→`arch-lint`)。`path` 从日志里的 `文件:行` 抓。`layer` 走 §3 映射。
`red_lines` 走 §4 补齐。

### 2c. 兜底:只有失败日志

连 check 名都不结构化 → 从原始日志抓 `path:line`,再走 §3 映射 layer、§4 补 red_lines。
**这是最弱路径,准确度靠日志质量;此时应提示用户信号不可靠。**

## 3. path → layer 映射(定位的核心)

把失败文件路径映射到 layer,事实源是 **AGENTS.md 的 Layer 索引**(或各层 `tech-context.md` 的位置):

```bash
# 失败文件
FAIL_PATH="packages/data/src/repo.ts:42"
FILE="${FAIL_PATH%%:*}"
# 每层 tech-context 所在目录就是该 layer 的根;找**最长前缀匹配**的那层
#   layer-glob 按生态:SPM=Packages/*/CONTEXT.md;JS=packages/*/tech-context.md;…
best=""; best_len=0
for tc in <layer-glob>; do
  [ -f "$tc" ] || continue
  root="$(dirname "$tc")"
  case "$FILE" in
    "$root"/*) [ "${#root}" -gt "$best_len" ] && { best="$(basename "$root")"; best_len=${#root}; } ;;
  esac
done
echo "layer=$best"    # 空 → 该文件不属于任何 layer(顶层代码,见下)
```

> **顶层代码没有 layer**(app 入口、平台壳、`cmd/`、多个 app target)——map 结果为空。
> 这类失败**不能按 layer 收窄**:修复范围退化为"该顶层目录",且**没有层级 red_lines** 可带,
> 只能带全局宪法红线。对这类失败更保守:优先**升级给人**,而非自动大改。

## 4. layer → red_lines / test(约束的核心)

拿到 layer 后,从该层 `tech-context.md` 的 frontmatter 取 `red_lines`(修时不能踩)和 `test`
(修完只跑这个验证):

```bash
TC="$(dirname <该 layer 的 tech-context 路径>)/tech-context.md"   # 或 CONTEXT.md,按 repo
python3 - "$TC" <<'PY'
import sys,re
t=open(sys.argv[1]).read()
m=re.match(r'^---\n(.*?)\n---\n', t, re.S); fm=m.group(1) if m else ""
# red_lines(YAML list)
rl=re.search(r'^red_lines:\s*\n((?:\s*-\s*.+\n)+)', fm, re.M)
lines=re.findall(r'-\s*(.+)', rl.group(1)) if rl else []
test=re.search(r'^test:\s*(.+)$', fm, re.M)
print("RED_LINES="+" | ".join(l.strip() for l in lines))
print("TEST="+(test.group(1).strip() if test else ""))
PY
```

`red_lines` 缺失 → 用全局宪法红线兜底(更宽,更该保守/升级)。
`test` 缺失 → 无法"只跑本层验证",退化为跑更大范围的测试(慢,且失去收窄意义)——提示用户补 frontmatter。

## 5. 组装成一个"收窄的修复任务"

把上面拼成派给修复 subagent 的输入(与 SKILL.md 第 3 步的 prompt 骨架对应):

```jsonc
{
  "scope_layer":  "<layer 或 '__toplevel__'>",   // 修复只能碰这个范围
  "failure":      { "kind": "...", "path": "...", "detail": "..." },
  "must_not_break": ["<red_lines...>"],           // 一条都不能踩
  "verify_cmd":   "<该层 test 命令>",             // 修完只跑这个,贴通过证据
  "on_cross_layer": "escalate"                    // 根因在别层 → 不跨层改,升级
}
```

**不变量(修复方必须遵守)**:
- 改动文件路径必须落在 `scope_layer` 根目录内(顶层失败则落在该顶层目录内)。
- 修完 `verify_cmd` 必须绿;绿之前不 push。
- 触任一 `must_not_break` / 根因跨层 / 需改 red_lines 或 tech-context → **停手升级**,不偷改。

## 6. 降级矩阵(信号缺哪块 → 怎么退)

| 缺什么 | 影响 | 退化行为 |
|---|---|---|
| CI 不吐结构化信号(§2a 无) | 定位靠重建 | 走 2b/2c,准确度下降,提示用户 |
| 无 AGENTS.md layer 索引 | path→layer 映射失据 | 整仓库级修复,**无法收窄**,强烈建议先跑 layered-agent-context |
| 某层无 `red_lines` | 修复无层级约束 | 用宪法红线兜底,更保守/优先升级 |
| 某层无 `test` | 无法只跑本层验证 | 退化为更大范围测试,提示补 frontmatter |
| 失败落在顶层代码(无 layer) | 无法按层收窄、无层红线 | 范围限该顶层目录 + 宪法红线,**优先升级**而非自动大改 |

> 一句话:**信号越结构化,自动修越能收窄、越安全;信号越弱,越该保守、越早升级给人。**
