# Multica CLI 配方

执行前读当前 `multica <command> --help`;help 是参数事实源,不是旧命令缓存。
以下按 0.4.44 核对。目录:workspace/project → 创建 → 历史/Outcome → spec 门禁 → dispatch。

## workspace 与 project 反查

```bash
multica workspace list --output json
multica workspace list --full-id
multica --workspace-id "$WS" project list --output json
multica --workspace-id "$WS" project resource list "$PROJECT_ID" --output json
```

`workspace list --output json` 返回含 `id`、`name`、`slug` 的数组。选择目标 workspace 的完整
UUID 作为 `WS`,每条 workspace-scoped 命令显式带 `--workspace-id`;不更改全局默认 workspace。
从当前 repo remote 规范化 GitHub URL(SSH/HTTPS、尾部 `.git`、大小写),逐 project 匹配
`resource_type == github_repo` 的 `resource_ref.url`。不缓存真实 workspace/project ID。
唯一匹配才继续;多命中、未命中或查询失败停下报告,不猜 project、不把 API 错误当未绑定。

## 创建 issue

```bash
multica issue create --help
multica issue assign --help
multica issue status --help
multica issue runs --help
multica issue rerun --help
```

| 操作 | 参数与约束 |
|---|---|
| create | `--title`、`--project`、`--description-file`、`--status`、`--priority` |
| create 时指定 owner | `--assignee` / `--assignee-id`;不是 assign 子命令的参数 |
| assign 已有 issue | `--to` / `--to-id`;`--no-start` 只变更 ownership |
| status | 状态 key;`--no-start` 只改状态,不启动 agent |
| 分层 tasks | `--parent`、`--stage N`;parent/blocker 先建,依赖方引用真实 key |

body 用 `--description-file` 传 UTF-8 文件。默认只允许当前目录内文件;任务临时文件在外部时,
先核对其绝对路径和内容,再明确带 `--allow-external-file`。也可用 `--description-stdin`。
临时 body/响应不提交到 repo。

```bash
multica --workspace-id "$WS" issue create \
  --project "$PROJECT_ID" --title '[Bug] <layer>: <symptom>' \
  --description-file "$BODY" --status backlog --priority high --output json
```

先读成功响应中的 issue ID/key。此时保持未指派,就绪后走下文 dispatch。不要把创建、
assignment、status、rerun 连成不读回状态的链。显式 park/human pause 时在此结束。

## 问题历史与 Outcome Check

```bash
multica --workspace-id "$WS" issue search "<area + symptom>" --include-closed --output json
multica --workspace-id "$WS" issue metadata get "$ISSUE_ID" --key problem_fingerprint --output json
multica --workspace-id "$WS" issue metadata set "$ISSUE_ID" \
  --key problem_fingerprint --type string --value "$PROBLEM_FINGERPRINT"
```

按 `problem-history.md` 核验 fingerprint、affected build 和关系,再写 `problem_report`、
`problem_relation`、`task_effectiveness`。标题相似只用于发现候选。

```bash
multica --workspace-id "$WS" issue create \
  --project "$PROJECT_ID" --title "[Outcome Check] $ORIGIN_KEY: <behavior>" \
  --description-file "$BODY" --status backlog --assignee "$WAIT_OWNER" --output json
```

WAIT_OWNER 必须是明确的人,不是 agent/squad。记录 `outcome_wait` 的 next event/wake condition
和 `task_effectiveness`。Outcome Check 到此完成:不 assign Dev Team,不转 todo,不调用 rerun。
已有 issue 需要调整等待负责人/状态时用 `--no-start`。事件先追加 comment,再更新当前 metadata。

## spec 先入库门禁

在 task worktree 核验 repo remote 与默认分支,不要假定 remote 名为 github 或默认分支总是 main。
下列 `REMOTE_NAME`、`DEFAULT_BRANCH`、`SPEC_PATH` 必须来自已核验的目标与 issue 引用。

```bash
git remote get-url "$REMOTE_NAME"
git fetch "$REMOTE_NAME" "$DEFAULT_BRANCH" || exit 1
BASE_SHA="$(git rev-parse --verify FETCH_HEAD^{commit})" || exit 1
git cat-file -e "$BASE_SHA:$SPEC_PATH"
```

先确认 fetch 成功,立即固定这次 FETCH_HEAD 的完整 SHA,再逐个核验 body 所有 spec/plan/tasks/ADR
引用;不用可能过期的 remote-tracking ref 代替本次读取。引用路径按 Git tree 字面值核对。
缺失时:

1. 按目标 repo W3 建/复用专用分支与 task worktree,核验绝对路径、base 和唯一 writer。
   Owner checkout 的分支、index、working tree 和未跟踪文件保持原样。只复制已授权设计内容;
   有冲突或来源不清停下,不 stash 或切换 Owner checkout。
2. 只提交缺失设计及必要依赖,正常 hooks + `scripts/verify`;失败修根因或报告 blocker。
   计划变更保留适用的 AI Plan-Review;产品/宪法/policy/permission 等独立决定才等待对应 Owner 授权。
   普通范围内测试变更的审查边界按 workflow 索引,不把 AI 计划关间接变成测试类 Owner 执行 hold。
3. 用目标 PR 模板创建默认分支 PR,把 URL/head/验证/hold 交 W4 PR Manager。
   重要路径或显式 hold 保持 Owner 审核;保护尚未生效时 Draft,不启用可立即执行的 auto-merge。
4. W4 确认 merged 后,刷新默认分支并逐路径复核。PR 存在或 CI 绿不等于设计已进入执行基线。

多个 issue 共用一个设计 PR。完整内联设计没有外部引用时无需路径检查,但保留 repo 的批准要求。

## dispatch / 收尾

只对前置批准/设计基线/依赖都就绪的实现 issue 执行。Outcome Check 或显式 human pause/Owner hold
保持 backlog,不触发任何 agent。默认派发不覆盖这些 hold。

1. 读取 issue 当前状态/assignment,查询本 issue 与关联 family 的在途工作:

   ```bash
   multica --workspace-id "$WS" issue get "$ISSUE_ID" --output json
   multica --workspace-id "$WS" issue runs "$ISSUE_ID" --active --output json
   multica --workspace-id "$WS" issue runs "$ISSUE_ID" --siblings --output json
   ```

   每次都要求成功退出、可解析 JSON、无截断警告。`--active` 包含 queued、dispatched、running、
   waiting_local_directory。已有本 issue run 直接观察;family 有重叠 scope writer 就等待原 owner。
   `--siblings` 只是观察,不是锁,截断时不能由短列表推断没有 writer。
2. 确认没有在途重叠且依赖就绪后,从该 workspace 的 `squad list` 解析唯一 Dev Team squad ID。
   用 `issue assign "$ISSUE_ID" --to-id "$SQUAD_ID" --no-start` 设 owner,读回确认未启动。
   再检查 active/family runs;仍为空才 `issue status "$ISSUE_ID" todo` 请求一次启动。
3. 读回 `issue runs --active` 和完整 `issue runs`。有 run 就回报真实 run ID/状态:
   queued/dispatched 是已接收,不是正在实现;waiting_local_directory 要报告目录阻塞。
   快速完成的 run 查其时间/产物,不可因为不再 active 就重跑。
4. 启动结果不明时先有限次只读复查。超时、API 错误、无效 JSON、未知状态都不是空列表;
   状态未知停下交 Supervisor/W6,不调用 rerun。只有成功完整读回确认无 live run、当前 assignment
   有效、没有已完成的新交付、没有 hold,且确需重新 enqueue 时才允许一次
   `issue rerun "$ISSUE_ID"`;调用前立即再查 active/family runs,调用后读回确认。
   rerun 失败/仍无可确认 run 则报告 blocker,不循环启动。

回报 key、URL、run ID/状态、evidence、next owner/hold。W2(TL/Planner/FS/AI Reviewer)
产出 PR 后交 W4 PR Manager;本 skill 只负责 issue 与受控 dispatch,不 merge、不代替接管验收。
