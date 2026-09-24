---
name: runtime-recovery
description: W6 运行恢复——Multica 控制面/NAS/Azure 链路、本机 Multica daemon、self-hosted GitHub runner 不可用或执行者中断时，定位故障层、暂停依赖动作、自动拉起 daemon/runner、恢复后触发 Supervisor 巡检并由原 owner 接回。用于“Multica 连不上 / daemon 挂了 / runner offline / PR 卡在 codex-review pending / agent 中断后接续”。
---

# W6 运行恢复

故障只阻塞依赖它的动作：本地开发、离线测试、文档可以继续。**不要在故障期间重复重试写操作。**

## 1. 判断故障层（只读、有界）

| 现象 | 先查 | 能证明什么 |
|---|---|---|
| `multica ...` 超时 / server error | `multica daemon status`；一次只读 `multica project list` | 控制面是否可达；不证明任务状态 |
| daemon stopped | `launchctl list | grep multica`；daemon 日志 | 本机进程是否在跑 |
| PR 的 `codex-review-target` 长时间 pending | `gh api repos/<o>/<r>/actions/runners` 状态 | self-hosted runner 是否 online |
| 执行 agent 中断 | worktree `git status`、进程列表、最后 push 的 SHA | 是否有未推送工作、是否仍有写者 |

控制面不可达且无家庭直连时：把受影响动作标 **BLOCKED（等直连）**，写一行进台账，停止重试。

## 2. 自动恢复（MacBook）

- daemon 与 self-hosted runner 各由一个 LaunchAgent 托管：`KeepAlive`（崩溃/登录后自动拉起）。
- 健康检查（同一 LaunchAgent 的定时任务，或 `StartInterval`）：睡眠唤醒、网络切换后，daemon 或 runner 连续失败则重启该进程。
- 恢复后触发一次 Pipeline Supervisor sweep，让被中断的 issue 继续。
- NAS 侧 runtime 不在自动恢复范围内（Owner 暂缓）。

托管时的坑（首次托管前逐条核对）：

- **launchd 不继承交互 shell 环境。** `~/.zshrc`/`~/.bashrc` 里 export 的变量（如 agent CLI 经第三方 provider 调模型所需的 `OPENAI_API_KEY`）在托管进程里都不存在，症状是手动启动正常、托管后 agent 任务鉴权失败。托管进程必须**显式导入**所需变量：用一个启动包装脚本，按名单只导入需要的变量名（例如从登录 shell 或 keychain 读取）后再 `exec` 真正的进程。不要把密钥写进 plist 或日志。新增依赖某变量的 CLI 时同步更新名单。
- `KeepAlive={SuccessfulExit=false}` 只在异常退出（崩溃、`SIGKILL`）时拉起；`SIGTERM` 导致的干净退出不会被拉起，要靠健康检查兜底。演练时按 plist 语义选择信号。
- `launchctl bootout` 返回时 job 可能还没卸载完，紧接着 `bootstrap` 会报 `5: Input/output error`。安装脚本要在两者之间等待 `launchctl print` 失败（即 job 已卸载）后再 bootstrap。
- 替换 runner/daemon 的 plist 前先备份原件；其他安装器若按 SHA 校验 plist，替换后它的回滚会拒绝执行，需要先从备份恢复。

LaunchAgent plist 与脚本属于本机私有配置，**不放进公开 repo**。

## 3. 写操作结果未知

先只读核对实际状态（PR/issue/ref），分为 已生效 / 未生效 / 未知。未知的不重放、不从另一个入口再写一次；保留原 owner 与已用重试次数。

## 4. 接回

恢复后由原 owner 重新读取权威状态（PR head SHA、issue 状态、worktree），确认只有一个写者后继续。主 agent 只观察与报告，不手工替代 Supervisor/PRM。

## 演练（验收）

一次 kill daemon、一次睡眠唤醒、一次 runner 停止：分别记录自动拉起时间、被中断任务是否由 Supervisor 接续。
