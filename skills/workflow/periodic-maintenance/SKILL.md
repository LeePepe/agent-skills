---
name: periodic-maintenance
description: 06 周期维护的未启用源码入口：按有效决定核对公开仓当前文档与相关实现，准备有证据的普通 backlog 或待澄清草稿。用于维护规则审查和离线演练；真实运行仍受启用 HOLD 约束。
---

# 06 周期维护（启用 HOLD）

本版只交付规则、离线适配器、隔离测试和模板。承载仓为 agent-skills；未来采用 Actions 每周一次及手动触发，
由原仓既有 Codex runner 独立只读核对。源码存在、安装 skill 或质量 CI 通过均不解除运行 HOLD。
本版不能调用 runner 做维护、连接真实 Multica、配置凭据／settings 或启用调度。

## 离线演练

1. 读 [核对规则](references/review-rules.md)，按目标仓 AGENTS→guide 和实际固定 shared 合同确定当前文档、代码与历史边界。
   使用人工构造的内存快照及模拟 review；本版不采集真实目标仓、不执行被检查内容中的命令。
2. 按 [适配器说明](references/adapters.md) 生成独立核对请求、回放语义结论并检查覆盖缺口。
   适配器验证引用与保守出口，不以结构校验或模拟 review 冒充真实语义核对。
3. 输出普通需求草稿及本轮覆盖结果：每条保留当前陈述、有效决定、实现／diff 证据、期望行为及验收。
   复用 [普通需求表达](../../repo/multica-issue/references/issue-templates.md)；不调用其 dispatch 全链入口。
   对应 project 必须由准确 repo resource 唯一匹配；输出固定为未指派的 `backlog`。
4. 完成时分别报告已查、未查／未知、需求草稿与交接状态。离线结果一律 `not_submitted`，不是需求已接收或问题已修复。

## 未来启用的边界

[工作流模板](assets/periodic-maintenance.yml) 保存在 assets，job 另有恒假开关；它不是已部署流程。
启用需要 Owner 分别解除 HOLD，并满足准确 head 审查、现有 runner 新用途、范围／公开可读性、身份／最小权限、
真实只读执行隔离和 backlog 出口核验。具体运行前置见 [适配器说明](references/adapters.md)。

维护只提出普通需求／待澄清，不修文档、补实现、删代码、指派团队、转 todo、关闭积压或追踪 PR／修复效果。
开发与 PR 交付仍由原 workflow／PRM 承担；运行恢复沿既有 runtime-recovery 权限，不因维护失败自动修 runner。
反复／未修复的展示留给 AIDash 后续，本版不增加团队、主管、task 类型、平台 schema 或审批层。
