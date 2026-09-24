# Multica CLI 配方

`multica` 是真实 CLI(`/opt/homebrew/bin/multica`)。dev team 的工作输入是 **Multica issue**,
不是 GitHub issue。本文件是本 skill 用到的命令配方。所有 `--output json` 都可管道给 `python3 -c`
取字段。

---

## 先确认 workspace(所有 project 操作的前提)

**在做任何 project/issue 操作前,先明确目标 workspace,并在命令上显式指定 —— 不要依赖当前默认 workspace。**
`multica project list` / `issue list` 只返回**当前 workspace** 下的东西;默认 workspace(常是另一个工作用 workspace)
会**静默隐藏**其它 workspace 里的 project,让反查扫空、白找一轮。

```bash
# 列出所有 workspace:列是 ID / NAME / SLUG,带 * 的是当前默认
multica workspace list

# 切换(接受 slug 或 ID 前缀):
multica workspace switch <slug|id-prefix>     # 例:multica workspace switch my
```

- `--workspace-id` 要**完整 UUID**;短 ID 或 slug 会报 `invalid workspace_id`。
- `switch` 接受 slug / 前缀,`--workspace-id` 不接受 slug。
- 个人项目多在 `my`(slug `my`,`6a90176a-...`),不在默认 workspace。
- **已知绑定**:AIDash → 项目 `396be26e`,workspace **`my`**(默认 workspace 里看不到)。

> 定位顺序永远是:**先 workspace,再 project**。跨项目通用,不只某一个 repo。

---

## project 反查(repo → Multica project id)

Multica project 通过 `project resource` 绑定 github repo。**先切到/确认正确 workspace(见上一节)**,再反查:

```bash
# 1. 当前 repo 的 github remote,规范化(去 .git、转小写)
REMOTE=$(git remote get-url origin 2>/dev/null || git remote -v | awk '/github.com/{print $2; exit}')
REMOTE_NORM=$(echo "$REMOTE" \
  | sed -E 's#git@github.com:#https://github.com/#; s#\.git$##' \
  | tr 'A-Z' 'a-z')

# 2. 遍历所有 project,找 resource 匹配本 repo 的那个
PROJECT_ID=""
for PID in $(multica project list --output json \
    | python3 -c "import sys,json;[print(p['id']) for p in json.load(sys.stdin)]"); do
  MATCH=$(multica project resource list "$PID" --output json 2>/dev/null | python3 -c "
import sys,json
target='$REMOTE_NORM'
for r in json.load(sys.stdin):
    url=(r.get('resource_ref') or {}).get('url','').rstrip('/').lower().removesuffix('.git')
    if r.get('resource_type')=='github_repo' and url==target:
        print(r['project_id']); break
" 2>/dev/null)
  [ -n "$MATCH" ] && PROJECT_ID="$MATCH" && break
done

[ -z "$PROJECT_ID" ] && { echo "本 repo ($REMOTE_NORM) 未绑定任何 Multica project。请手动指定 project id,或先 multica project resource attach。"; exit 1; }
echo "PROJECT_ID=$PROJECT_ID"
```

> `multica project list` 的 `title` 字段可能为 `None`,**不要靠标题匹配**;靠 resource 的 repo url。
> 已知:VitalStride → `7adf8b88-9b2b-46fe-95cc-2dcd32bcf6fb`(绑 `github.com/LeePepe/VitalStride`)。

---

## 创建 issue

`multica issue create` 关键 flag:

| flag | 用途 |
|---|---|
| `--title` (必填) | issue 标题。约定前缀:`[Bug] <layer>:`、`[T###] [Story]`(speckit task)、`[Arch]` |
| `--project <id>` | 挂到反查出的 project |
| `--description-file <path>` | **body 从文件读**,保留多行/中文,verbatim。**首选**,不用 `--description` |
| `--parent <issue-id>` | 挂到 parent issue(feature 总述下的 sub-issue) |
| `--stage <N>` | staged barrier:同 stage 全完成才唤醒 parent 的 assignee。对应 tasks.md 依赖组 |
| `--to "Dev Team"` / `--to-id <squad-uuid>` | assign 给 Dev Team squad(dispatch 第1步;第2步是转 todo) |
| `--priority <p>` | 优先级(bug 建议设) |
| `--status <s>` | `todo`=触发 pipeline 第2步;`backlog`=暂存不跑(即使已 assign squad) |

**body 用文件传**(避免转义):

```bash
BODY=$(mktemp /tmp/multica-issue-XXXX.md)
cat > "$BODY" <<'EOF'
## Category
bug
...(见 issue-templates.md)...
EOF

multica issue create \
  --project "$PROJECT_ID" \
  --title '[Bug] HealthKitService: 撤销权限后缓存未清' \
  --description-file "$BODY" \
  --priority high \
  --output json | tee /tmp/created.json

NEW_KEY=$(python3 -c "import sys,json; print(json.load(open('/tmp/created.json'))['identifier'])")
echo "创建: $NEW_KEY"
rm -f "$BODY"
```

---

## 问题历史、关系与 Outcome Check

### 搜索历史

```bash
multica --workspace-id "$WS" issue search "<product area + symptom>" \
  --include-closed --limit 20 --output json
multica --workspace-id "$WS" issue metadata get <candidate> \
  --key problem_fingerprint --output json
```

标题匹配只发现候选。确认 fingerprint 和 affected build 后,再写 `duplicate_of`、
`ineffective_fix_for`、`regression_of` 或 `related_to`。

### 给普通 Bug 写索引

```bash
multica --workspace-id "$WS" issue metadata set "$NEW_KEY" \
  --key problem_fingerprint --type string --value "$PROBLEM_FINGERPRINT"
multica --workspace-id "$WS" issue metadata set "$NEW_KEY" \
  --key problem_report --value "$PROBLEM_REPORT_JSON"
multica --workspace-id "$WS" issue metadata set "$NEW_KEY" \
  --key problem_relation --value "$PROBLEM_RELATION_JSON"
multica --workspace-id "$WS" issue metadata set "$NEW_KEY" \
  --key task_effectiveness --value '{"status":"pending_delivery"}'
```

`problem_report` 至少保留 source kind、observed_at、affected version/build 和 evidence ref。

### 创建不派发的 Outcome Check

```bash
multica --workspace-id "$WS" issue create \
  --project "$PROJECT_ID" \
  --title "[Outcome Check] $ORIGIN_KEY: <behavior>" \
  --description-file "$BODY" \
  --status backlog \
  --assignee "$WAIT_OWNER" \
  --output json

multica --workspace-id "$WS" issue metadata set "$CHECK_KEY" \
  --key outcome_wait --value "$OUTCOME_WAIT_JSON"
multica --workspace-id "$WS" issue metadata set "$CHECK_KEY" \
  --key task_effectiveness \
  --value '{"status":"pending_release"}'
```

Outcome Check 到此完成:保持 backlog,不 assign Dev Team,不转 todo,不调用 rerun。每次 release 或
使用结论先追加 comment 作为事件,再更新 `task_effectiveness` 当前索引。

---

## 依赖顺序 + staged barrier(feature 路径)

speckit 的 tasks.md 常有依赖组(Stage 1 数据层 → Stage 2 组件 → Stage 3 接线)。落法:

```bash
# 1. 先建 parent(feature 总述),拿到 PARENT_KEY
multica issue create --project "$PROJECT_ID" \
  --title '训练页自定义键盘(feature)' --description-file parent.md \
  --output json > parent.json
PARENT_KEY=$(python3 -c "import sys,json;print(json.load(open('parent.json'))['identifier'])")

# 2. 各 task 作为 sub-issue,按 stage 分组;blocker 先建
multica issue create --project "$PROJECT_ID" --parent "$PARENT_KEY" --stage 1 \
  --title '[T001] [数据层] Exercise 默认值' --description-file t001.md
multica issue create --project "$PROJECT_ID" --parent "$PARENT_KEY" --stage 2 \
  --title '[T002] [键盘] WorkoutNumericKeyboard 组件' --description-file t002.md
multica issue create --project "$PROJECT_ID" --parent "$PARENT_KEY" --stage 3 \
  --title '[T003] [接线] SetRow 接入键盘' --description-file t003.md
```

> 若某 task 显式依赖另一个具体 task,除了 stage,还可在 body 的 **Blocked by** 段写上真实 key
> (所以要 blocker 先建)。stage 管「批次唤醒」,Blocked-by 管「人读的依赖说明」。

---

## spec 先入库门禁(dispatch 前置,全自动)

FS agent 在隔离 workdir 从 `github/main` 起分支,只读 main 上已合并的文件。issue body 引用
`specs/`/`docs/adr/` 但文件没进 main → FS/Reviewer 踩空。dispatch 前自动补齐:

```bash
# 0) 收集所有待派发 issue 的 body,grep 引用的 spec/ADR 路径
REFS=$(printf '%s\n' "$BODY1" "$BODY2" ... \
  | grep -oE '(specs|docs/adr)/[A-Za-z0-9._/-]+\.(md|swift|html)' | sort -u)
[ -z "$REFS" ] && echo "无 spec/ADR 引用,跳过门禁" # 直接 dispatch

# 1) 查每个引用是否已在 main
git fetch github 2>/dev/null
MISSING=""
for p in $REFS; do
  git cat-file -e "github/main:$p" 2>/dev/null || MISSING="$MISSING $p"
done

# 2) 有缺失 → 自动开设计文档 PR
if [ -n "$MISSING" ]; then
  # 挡路的无关 tracked 改动先 stash(只 stash 那些文件,不动要进 PR 的)
  git stash push -- <无关的 tracked 文件> 2>/dev/null || true
  git checkout -b "feat/<slug>-design-docs" github/main
  git add $MISSING <这些 spec 依赖的规矩文件:宪法 bump / 新 ADR>   # 排除 firebase-debug.log / .specify/feature.json / 无关 specs
  git commit --no-verify -m "docs: <feature> spec + ADR 先行入库(pipeline 依赖)"
  git push --no-verify -u github "feat/<slug>-design-docs"
  gh pr create --base main --head "feat/<slug>-design-docs" --title "docs: ..." --body "..."
  # 监督 CI 到终态(auto-merge 开着就等自动合;Monitor 或轮询)
  gh pr checks <PR#>            # 全 pass 且 auto-merge → 自动 MERGED
  # 合并后复核文件确已落 main
  git fetch github; for p in $MISSING; do git cat-file -e "github/main:$p" && echo "✓ $p 已入 main"; done
fi
# 3) 文件都在 main 后,才走下面的 dispatch
```

**lint scope 注意**:VitalStride `.swiftlint.yml` `included:` 只含 app targets + `Packages`,**不含
`specs/`/`docs/`** → 纯文档 PR 不触发 `no_hardcoded_chinese`,CI 全绿。别的 repo 先核对其 `included:`。
**多 issue 共用一个 spec** → 一个设计文档 PR 覆盖全部,不要每 issue 一个 PR。

---

## dispatch / 收尾

**默认直接派发,让 pipeline 真的跑起来。三步,第 3 步必须确认为真:**

Outcome Check 不进入本节:它保持 backlog,assign 给 wait owner,并以 `outcome_wait` metadata
记录 next event;不 assign Dev Team、不转 todo、不调用 rerun。

```bash
# dispatch(唤醒 pipeline)—— 三步:
#   1) assign 给 "Dev Team" squad(不是 Team Lead 个人;squad 内部路由 TL→FS→Reviewer→PR Manager)
#   2) status 转 todo(触发 run;光 assign 不会触发,issue 会停在 backlog、零 run)
#   3) 验证 run 起来了(关键);零 run 用 rerun 兜底
SQUAD_ID=$(multica --workspace-id "$WS" squad list --output json \
  | python3 -c 'import json,sys;print(next(s["id"] for s in json.load(sys.stdin) if s["name"]=="Dev Team"))')
multica --workspace-id "$WS" issue assign "$NEW_KEY" --to-id "$SQUAD_ID"
multica --workspace-id "$WS" issue status "$NEW_KEY" todo      # ← 这步才真正触发 pipeline

# 3) 验证:issue runs 应有 queued/running。零 run → rerun 兜底,再查一次确认。
ISSUE_UUID=$(multica issue get "$NEW_KEY" --output json | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
RUNS=$(multica issue runs "$ISSUE_UUID" --output json 2>/dev/null)
echo "$RUNS" | grep -qE '"status":\s*"(queued|running)"' \
  || { echo "零 run,rerun 兜底"; multica issue rerun "$ISSUE_UUID"; multica issue runs "$ISSUE_UUID" --output json; }
# 没确认到 queued/running,就不算派发完成,不要回报「已派发」。

# 暂存不 dispatch(仅当用户明确说「先别跑 / 只暂存 / park」):保持 --status backlog,别转 todo。

# 收尾观察:
multica issue get "$NEW_KEY" --output json          # 看状态/assignee/parent
multica issue list --project "$PROJECT_ID" --output json  # 看 project 下全部 issue
multica issue comment add "$NEW_KEY" --content-stdin < body.md # 追加说明(多行用 --content-stdin)
```

**后续 pipeline**(见 `AGENTS.md` §FS/TL workflow):Dev Team squad 内 Team Lead 派 → Fullstack
Engineer 实现 + 开 PR(push `agent/<issue-key>-<task>` 到 github)→ AI Reviewer 审 → TL merge PR →
issue done。这个 skill **只负责起草 + dispatch**,不参与后续实现。

---

## 常见坑

- **默认 workspace 藏 project** → `project list`/`issue list` 只看当前 workspace,默认常是另一个 workspace,
  会静默隐藏别的 workspace 的 project。先 `workspace list` + `switch <slug>` 定位,再操作;
  `--workspace-id` 只吃完整 UUID(短 ID/slug 报 invalid)。个人项目多在 `my`。
- **project title 为 None** → 靠 repo url 匹配,不靠标题。
- **`--description` vs `--description-file`** → 多行/中文 body 一律用 file,`--description` 会解码
  `\n`/`\t` 转义,长文本容易踩坑。
- **dispatch 是三步,默认直接派发** → 光 `assign` 给 squad **不会**触发 pipeline(issue 停在 backlog、零 run);
  必须再 `issue status <key> todo` 才 enqueue;**再验证 `issue runs` 有 queued/running**,零 run 就 `rerun` 兜底。
  实测存在「assign+todo 后仍零 run」的卡死(follow-up issue 尤甚),没验证到 run 不算派发完成。
  只有用户明确说「暂存不跑」时才保持 backlog。
- **assign 目标是 "Dev Team" squad,不是 Team Lead 个人** → `--to "Dev Team"`(fuzzy)或
  `--to-id <squad-uuid>`(从 `squad list` 取)。squad 内部会路由到 TL→FS→Reviewer→PR Manager。
  CLI 参数是 `--to`/`--to-id`(不是 `--assignee`/`--assignee-id`)。
