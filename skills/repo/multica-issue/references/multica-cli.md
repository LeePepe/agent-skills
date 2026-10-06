# Multica CLI 配方

用 `command -v multica` 定位当前 CLI。dev team 的工作输入是 **Multica issue**,
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
- workspace/project 绑定从当前 CLI 查询，不在公开规范保存个人绑定。

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

## spec 先入库门禁(dispatch 前置)

从执行配置确认 repo、remote 与 base，不假设远端名为 `github`。收集所有方案引用，包括 spec/plan/tasks/ADR/guide，
核对本版批准的内容与固定 ref。可在已核实的任务 worktree 用下列只读查询检查：

```bash
git cat-file -e "$EXECUTION_BASE:$REF_PATH"
git show "$EXECUTION_BASE:$REF_PATH"
git show "$APPROVED_REF:$REF_PATH"
```

这些变量由当前任务的已核实配置填入，逐文件比较方案内容。缺失或不匹配则保持待派发，按 `SKILL.md` 的
固定方案可读取门禁处理；不要 stash 他人内容、跳过 hooks 或自行合并。授权的文档 PR 经正常 gates/审批、PRM
推进后重新核验，才继续派发。多个 issue 可共用同一个必要文档 PR。

---

## dispatch / 收尾

先满足 `SKILL.md` 的准入、固定版本、唯一 owner、依赖和文档门禁，再派发。以下不是对未知状态的自动重试脚本。
所有命令使用已核实的 workspace；任何读取失败都不能解释为空结果。

Outcome Check 不进入本节:它保持 backlog,assign 给 wait owner,并以 `outcome_wait` metadata
记录 next event;不 assign Dev Team、不转 todo、不调用 rerun。

```bash
# dispatch(唤醒 pipeline)—— 三步:
#   1) assign 给 "Dev Team" squad(不是 Team Lead 个人;squad 内部路由 TL→FS→Reviewer→PR Manager)
#   2) status 转 todo(触发 run;光 assign 不会触发,issue 会停在 backlog、零 run)
#   3) 查询本次任务对应的 run，按实际状态回告
SQUAD_ID=$(multica --workspace-id "$WS" squad list --output json \
  | python3 -c 'import json,sys;print(next(s["id"] for s in json.load(sys.stdin) if s["name"]=="Dev Team"))')
multica --workspace-id "$WS" issue assign "$NEW_KEY" --to-id "$SQUAD_ID"
multica --workspace-id "$WS" issue status "$NEW_KEY" todo      # ← 这步才真正触发 pipeline

# 3) 先查询 issue，成功后从响应取出 ISSUE_UUID；失败则停止派发并报告接收未知。
multica --workspace-id "$WS" issue get "$NEW_KEY" --output json
```

将成功响应的 issue ID 与本次任务核对，再查询完整 run 历史。按 `SKILL.md` 第 4 步关联固定版本、原 owner
及本次派发记录；匹配的终态 run 同样证明接收，不能只筛 queued/running，也不能取任意旧 run 代替本次证据。

```bash
multica --workspace-id "$WS" issue runs "$ISSUE_UUID" --output json
# 零 run、关联不足或查询超时/失败保留接收未知，不自动 rerun。

# 用户明确暂存、尚未获准执行或前置条件未满足时保持等待，别转 todo。

# 收尾观察:
multica --workspace-id "$WS" issue get "$NEW_KEY" --output json          # 看状态/assignee/parent
multica --workspace-id "$WS" issue list --project "$PROJECT_ID" --output json  # 看 project 下全部 issue
multica --workspace-id "$WS" issue comment add "$NEW_KEY" --content-stdin < body.md # 追加说明(多行用 --content-stdin)
```

回告时分别写接收结论、实际 run 结果与交付证据。匹配的 `completed`/`failed`/`cancelled` 都是已接收，
失败/取消不是未派发或交付成功；由原执行方跟进，不以未接收为由重派。run completed 本身也不是交付验收。

**后续 pipeline**按目标仓合同及 [workflow 实现职责](../../../workflow/README.md#实现职责与当次输出)：
Planner 复用／补齐 → AI Reviewer 只读方案关 → TL 派 FS → FS 实现、必要验证及完整自检 →
AI Reviewer 准确 SHA 的 pre-push spec/architecture 只读审查 → 原 FS 推送／创建更新 PR → PRM 接管非 Draft 生命周期。
Reviewer 不运行／裁定测试、build、lint、CI，不跟踪 PR；缺口回原 FS，发送不等于已接受或已交付。
这个 skill **只负责起草 + dispatch**，不把 issue done 当作发布/实际消费已完成。

---

## 常见坑

- **默认 workspace 藏 project** → `project list`/`issue list` 只看当前 workspace,默认常是另一个 workspace,
  会静默隐藏别的 workspace 的 project。先 `workspace list` + `switch <slug>` 定位,再操作;
  `--workspace-id` 只吃完整 UUID(短 ID/slug 报 invalid)。个人项目多在 `my`。
- **project title 为 None** → 靠 repo url 匹配,不靠标题。
- **`--description` vs `--description-file`** → 多行/中文 body 一律用 file,`--description` 会解码
  `\n`/`\t` 转义,长文本容易踩坑。
- **assign/todo 不等于接收** → 按上节核对本次派发的 run，包括终态；接收、执行结果和交付分别报告。
  保留原任务/版本/执行方；只按已验证路径补派确认未接收的任务，零 run 不用 `rerun` 兜底，不创建第二写者或自动改派。
- **assign 目标是 "Dev Team" squad,不是 Team Lead 个人** → `--to "Dev Team"`(fuzzy)或
  `--to-id <squad-uuid>`(从 `squad list` 取)。squad 内部会路由到 TL→FS→Reviewer→PR Manager。
  CLI 参数是 `--to`/`--to-id`(不是 `--assignee`/`--assignee-id`)。
