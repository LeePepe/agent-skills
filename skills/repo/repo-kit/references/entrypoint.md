# Init：目录入口合同

## 1. 实际权威

先记录目标 repo 的 manifest、lockfile、所有 shared-ci workflow caller 与维护中的版本文档。
从实际 caller 的完整 SHA 确认现有 provider；尚未接入时提出一个可获取的固定版本供采用，
不把 latest、分支或本文当版本选择。已有 pin 的升级另走 adopt，不随 init 隐式更新。

不从 AGENTS 正文推断依赖。读取实际 Package.resolved、package-lock.json 或该栈的 lockfile，
核对声明、解析版本与对应版本的 ai 文档；未观察到的格式标为未验证，不制造缺失依赖。
归属与 PR 单元沿用仓库架构/开发权威，测试随实现；目录链接不是 resolver 或依赖配置。

## 2. 版本分支

在所选完整 SHA 上读取合同、schema、检查器、模板与 bootstrap，记录各自能力证据；
“目录 audit 支持”不代表模板/bootstrap 已迁移。候选 PR 或别的版本的模板不能冒充所选版本。
格式不兼容时保留兼容基线，记录具体版本迁移依赖；不绕过 audit，不私改 provider，
也不复制旧 handbook 来掩盖缺口。

### Metadata-aware

仅在所选版本确实支持时使用 `.github/repo-contract.json`，按该版 schema 写
`schema`、`guide`、`shared_ci`、`dependencies`，不照抄候选字段。
guide 指向已有、维护中的实际规则正文，含该版所需的协议/验证/检查/红线/交付章节；
shared_ci 与所有 caller、保留的协议链接完整 SHA 一致，依赖版本与实际 lockfile/文档一致。
metadata 无效就修复或报告阻塞，不通过删除它静默降级。协调回滚需恢复记录的兼容基线。

将下面的目录形态适配为真实路径；示例不是 catalog 自身的接入状态。替换
`<provider-sha>` 与示例 leaf，并只在目标文件存在时保留条目：

```markdown
# Repository entrypoint

## Read first
- Before repository work: [architecture and constraints](docs/architecture/tech-context.md).
- For the affected layer: [leaf responsibilities and tests](src/core/tech-context.md).
- Before planning a PR: [development and PR units](docs/development.md).

## Protocol
- Before implementation: [versioned protocol](https://github.com/LeePepe/shared-ci/blob/<provider-sha>/ai/agent-protocol.md).

## Verify
- Before validation: [verification sources](docs/development.md#verification-and-review-sources).

## Required checks
- Before merge readiness: [required checks and protection evidence](docs/development.md#required-checks).
- When checking provider pins: [quality caller](.github/workflows/ci.yml).

## Red lines
- Before review: [repository rules](docs/development.md#red-lines).

## Delivery
- Before delivery: [delivery and setup holds](docs/development.md#delivery).
```

例中的 development guide 应是选定版本认可的完整权威，而不只是上述几个锚点。
AGENTS 仅保留标题、空行、带读取条件的链接；命令、检查名单、红线正文与依赖 inventory
留在各自维护中的权威。旧正文中的唯一事实先迁入适当权威，再删正文，避免另造重复手册。

### Legacy

没有 metadata 支持或尚未选择迁移时，按该固定版保留 Read first、Protocol、Verify、
Required checks、Red lines、Delivery 等机器必需目录标题及完整 SHA 协议指针。
使用该版本实际接受的链接/指针语法，不把 metadata 示例直接当 legacy 模板。
先按实际 lockfile 和该版 dependency 检查判断能否保持目录入口；
若旧版确实要求 AGENTS 依赖正文、或缺少需要的模板能力，保留现有兼容基线并报告
版本迁移依赖，不新增依赖 inventory 或假称 init 已完成。新增目录仍以真实 authority 为目标。

## 3. Reviewer 与保护边界

tool-free reviewer 不会展开 AGENTS 链接。Codex 与 Kimi caller 的 `rules-file`
应指向单个 tracked、protected、含实际规则正文的维护中权威；metadata 模式须与 guide 一致。
保留 trusted-base 加载，不执行 PR head 代码；首次添加的 guide 还未进入 trusted base 时，
报告 bootstrap 依赖，不声称本次 reviewer 已读到它。

检查实际生效的 CODEOWNERS 文件和最后匹配规则；按所选版本要求保护 AGENTS、metadata、
guide 和 policy/gate/pin/permission 等重要路径。文件被 tracked 或带 CODEOWNERS 条目
不等于服务端保护已生效，仍需 Owner 身份/权限与 required code-owner review 的真实证据。
普通测试变更保留理由、CI 与适用 AI review；不因测试编辑或删除新增 Owner 审批类别，
也不借宽泛测试路径匹配恢复这类条件。规则文件本身的 policy 变更仍按重要路径审查。

## 4. 验收与 setup hold

- 逐条从 AGENTS 跟到真实权威，确认本地目标 tracked、可读、非 symlink，锚点存在；
  外链由执行者读取并核对版本，链接校验不证明远端正文已读取。工具入口只指向 AGENTS。
- 比较实际 manifest/lockfile、版本文档、所有 caller、协议链接与 metadata（如启用）；
  用所选版本原生 audit 加本仓 verify/hooks/CI 验证归属、依赖、命令与路径，无替代 resolver。
- 收集当前 PR head SHA 上实际发出的 check、汇总 gate 和 required AI review 结果，
  与默认分支有效 required checks、code-owner review、权限与保护 readback 对照；
  一个普通 validate job 通过不是 required review 通过，旧 head 结果也不是新 head 证据。
- 无权限、保护不可读取、runner/review 未运行、首次 trusted-base 文档未就绪、
  bootstrap 仍写旧格式或 required-check 名称未证明时，明确标为 setup hold；
  分开报告本地 source 验证与 live 接入缺口，不据此跳过门禁。
- 需要 settings 变更时只提出 old→new/dry-run 方案，保留原有 required checks；
  仅在 Owner 批准具体变更后由获授权操作方执行并 readback。init 文档不是部署授权。
  全部证据齐备才报接入完成；未齐备则交付 source-ready + 明确 hold。
