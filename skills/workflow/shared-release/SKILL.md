---
name: shared-release
description: W5 共享库发布与消费者升级——shared-* 仓合并后打不可变版本，随版本发布 ai/ 合同，在外部消费者验证，再为每个消费 repo 开独立 pin 升级 PR。用于“发布 shared-ci/telemetry/design-system/tokens/VoxKit 新版本 / 让产品升级到新版共享库 / 回滚共享库版本”。
---

# W5 共享库发布与消费者升级

适用 Shared 层 repo（shared-ci、shared-telemetry、shared-design-system、shared-design-tokens、VoxKit）。
provider 改动与消费者改动是**不同 PR、不同 owner**；不在消费者里复制 provider 代码冒充接入。

## 1. 发布前（provider PR 内）

- 公开 API / schema / 配置变化同步到该库 `ai/`：`USAGE`、`INTEGRATION`、`COMPATIBILITY`、`MIGRATION`、`registry.json`。
- breaking change 写入 `MIGRATION.md`：from→to、步骤、验收、回滚、不可逆限制。
- docs gate：`ai/` 内链接可解析；标记为可编译的示例在 CI 中真实编译。

## 2. 发布

1. provider PR 按 W4 合并。
2. 打版本：SPM/npm/Python 用 semver tag；shared-ci 以 **完整 40 位 commit SHA** 作为消费引用（tag 仅作人读别名）。
3. 外部消费者验证：在临时目录用**发布产物**（tag/包，不是工作树路径）接入并 build/test：
   - SPM：临时 package 依赖 `.package(url:, exact:)`，`swift build`（Apple UI 库在声明平台上 build）。
   - npm：`npm pack` → 临时项目安装 → 类型检查。
   - Python：构建 wheel → 临时 venv 安装 → 能定位随包 `ai/` 资源。
   - shared-ci：一个真实 caller repo 用新 SHA 跑通汇总 gate，并有一个负例被拦。
4. 在 provider repo 的 release notes 记录版本、SHA、验证结果链接。

## 3. 消费者升级

- 每个消费 repo 一个 PR，只改：实际 manifest/lockfile/caller 中的依赖 pin（exact 版本 / 完整 SHA）、维护中的版本文档引用/机器元数据、必要适配代码。
  AGENTS 保持条件式链接目录，仅在入口目标变化时更新链接；依赖信息由实际配置与对应版本文档维护。
  核对版本文档与实际 pin 匹配，所有 shared-ci caller 与协议链接的完整 SHA 一致。
  旧固定版本保留该版支持的目录标题/完整 SHA 指针并按该版合同验证；仅在所选已发布版本支持时采用新机器元数据。
  真实不兼容交 provider owner，不绕过 audit。
- 按新版本的 `MIGRATION.md` 执行；消费者自己的 required CI 通过即完成。依赖 pin 升级属于**重要 PR**，需 Owner approve。
- 消费者之间互不等待；某个消费者失败只阻塞它自己，provider 缺陷回到 provider 修，新版本再发。

## 4. 回滚

消费者 revert pin PR 回到上一版本；provider 不删 tag、不改写历史。不可逆的数据/schema 变化必须事先写在 `MIGRATION.md`，并单独获 Owner 授权。
