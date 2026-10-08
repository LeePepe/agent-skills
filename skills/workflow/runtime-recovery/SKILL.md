---
name: runtime-recovery
description: 运行恢复辅助——控制面、daemon、runner 不可用或执行者中断时，定位故障层并按已有授权恢复，由原责任方接回。用于 Multica 连不上、runner offline、review pending 或任务中断；不接管 PR 交付，不授权主机配置或凭据变更。
---

# 运行恢复

故障只阻塞依赖它的动作：本地开发、离线测试、文档可以继续。**不要在故障期间重复重试写操作。**
默认仅做下述只读诊断，回报证据与建议动作；调用本 skill 或发现故障本身不授予主机写入、服务控制或凭据操作权限。

## 1. 判断故障层（只读、有界）

| 现象 | 先查 | 能证明什么 |
|---|---|---|
| `multica ...` 超时 / server error | `multica daemon status`；一次只读 `multica project list` | 控制面是否可达；不证明任务状态 |
| daemon stopped | `launchctl list | grep multica`；daemon 日志 | 本机进程是否在跑 |
| PR 的 `codex-review-target` 长时间 pending | `gh api repos/<o>/<r>/actions/runners` 状态 | self-hosted runner 是否 online |
| 执行 agent 中断 | worktree `git status`、进程列表、最后 push 的 SHA | 是否有未推送工作、是否仍有写者 |

诊断/测试子进程设置执行时限，并在启动时创建、记录本任务专用进程组（例如 `subprocess.Popen(..., start_new_session=True)`）。
超时清理只向确认属于本任务的该组发送 `SIGTERM`，在限定宽限期后仍有成员才向同一组发送 `SIGKILL`，并有界等待、回收直接子进程。
直接子进程退出不代表组内后代已退出；不要按 `ppid` 递归查找清理，孤儿进程会被重新托管。无法确认组归属时报告阻塞，不向其他会话或未知归属的进程组发信号。

控制面不可达且无家庭直连时：把受影响动作标 **BLOCKED（等直连）**，写一行进台账，停止重试。

## 2. 自动恢复（MacBook）

**执行前核对单独授权。** 以下创建／修改／装卸 LaunchAgent、安装启动包装脚本、修改 runner 主机配置或环境变量名单、
启动／停止／重启服务，以及注册／重新注册 self-hosted runner 的动作，须有 Owner 批准或仍适用的已有准确授权，
明确覆盖目标主机、服务／repo 和具体操作；涉及注册凭据或密钥的读取、使用、写入须另在授权范围内。
复用已有准确授权，不重复索批；仅有故障报告、工具可用或文件可写不能代替授权。授权缺失、范围变化或无法核实时，
保留只读诊断结果和可审阅方案，向 Owner 报告缺口，在获准前不执行对应动作。已合法部署的自动恢复机制按原授权运行，
不因本 skill 而获得新的配置／凭据权限。

- daemon 与 self-hosted runner 各由一个 LaunchAgent 托管：`KeepAlive`（崩溃/登录后自动拉起）。
- runner 需重新注册或 repo 缺少 runner 时，按 [repo-kit 的 self-hosted runner 配方](../../repo/repo-kit/SKILL.md) 操作。
- 健康检查（同一 LaunchAgent 的定时任务，或 `StartInterval`）：睡眠唤醒、网络切换后，daemon 或 runner 连续失败则重启该进程。
- 恢复后按下方“接回”核对原任务；已部署的 Dev Team Flow Supervisor 只经既有 Autopilot 入口唤醒真正中断的原责任 agent。
  先核实该入口、部署与合法触发权限，不把 source 说明当现网能力，不触发 repo-wide PR sweep。
- NAS 侧 runtime 不在自动恢复范围内（Owner 暂缓）。

托管时的坑（首次托管前逐条核对）：

- **launchd 不继承交互 shell 环境。** `~/.zshrc`/`~/.bashrc` 里 export 的变量（如 agent CLI 经第三方 provider 调模型所需的 `OPENAI_API_KEY`）在托管进程里都不存在，症状是手动启动正常、托管后 agent 任务鉴权失败。托管进程必须**显式导入**所需变量：用一个启动包装脚本，按名单只导入需要的变量名（例如从登录 shell 或 keychain 读取）后再 `exec` 真正的进程。不要把密钥写进 plist 或日志。新增依赖某变量的 CLI 时同步更新名单。
- `KeepAlive={SuccessfulExit=false}` 只在异常退出（崩溃、`SIGKILL`）时拉起；`SIGTERM` 导致的干净退出不会被拉起，要靠健康检查兜底。演练时按 plist 语义选择信号。
- `launchctl bootout` 返回时 job 可能还没卸载完，紧接着 `bootstrap` 会报 `5: Input/output error`。安装脚本要在两者之间等待 `launchctl print` 失败（即 job 已卸载）后再 bootstrap。
- 替换 runner/daemon 的 plist 前先备份原件；其他安装器若按 SHA 校验 plist，替换后它的回滚会拒绝执行，需要先从备份恢复。

自托管 runner 调用本地模型 provider 时，可参考 [scripts/host-bootstrap.py](scripts/host-bootstrap.py) 的 launchd 包装器：默认 dry-run，写入需 plan-id 批准，并生成 rollback manifest。
`install --apply`、`secret-write` 和 rollback 同样须满足上述单独授权；plan-id 只绑定准确方案，生成或填入它不构成 Owner 授权。
非密钥 `host.json` 提供 `owner/default_runners/legacy_labels/known_prior_launcher_sha256/daily_config/python` 等主机配置；每个新 runner 使用独立的 `review_home`。
launchd 每次启动 runner 都读取默认 `~/.config/raven-actions/host.json`（不带 `--config` / `--owner`）；该文件缺失或无效时，所有 runner 都无法启动。
安装完成后再编辑默认主机配置，也可能使后续 runner 启动失败；安装时校验通过不保证之后每次启动仍可用。
`install --apply` / `secret-write` 在默认配置缺失或无效，或安装配置的 `owner/python` 与默认配置不一致时拒绝写入。
实际 LaunchAgent plist、主机配置与密钥属于本机私有数据，**不放进公开 repo**。

## 3. 写操作结果未知

先只读核对实际状态（PR/issue/ref），分为 已生效 / 未生效 / 未知。未知的不重放、不从另一个入口再写一次；保留原 owner 与已用重试次数。

## 4. 接回

恢复后由原 owner 重新读取权威状态（PR head SHA、issue 状态、worktree），确认唯一写者与既有继续条件。
按 [workflow 责任边界](../README.md#dev-team-flow-supervisor)：Dev Team Flow Supervisor 只唤醒已具备下一步却中断的原责任方，
不代执行、改派、修复或合并；正常等待／人工暂停不触发唤醒，接收未知先对账，实际接收后才报已唤醒。
subagent 仍由原主会话协调；非 Draft PR 交付仍归 PRM。已交 Owner 判断的查证结论不因环境恢复或新证据自动解锁。

## 演练（验收）

仅在准确隔离演练授权具备后执行一次 kill daemon、一次睡眠唤醒、一次 runner 停止：分别记录恢复时间、
原责任方的实际接收和后续任务证据；同时验证正常等待／人工暂停不会误唤醒，PRM／subagent 主会话未被接管。
主机恢复、唤醒接受、实现／PR 交付分别验收，不以发消息或 source 测试通过替代真实接续。
