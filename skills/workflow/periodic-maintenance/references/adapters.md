# 离线适配器与未来接线

`scripts/maintenance.py` 只有 `request`／`replay` 两个本地 JSON 入口，无网络、Codex CLI、Multica CLI、凭据读取或提交能力。
使用 Python 标准库；从仓根运行下面命令即可演练，输入为随源码提供的虚构仓库快照，无需 checkout 检查对象：

```sh
python3 skills/workflow/periodic-maintenance/scripts/maintenance.py request skills/workflow/periodic-maintenance/tests/fixtures/missing-implementation.json
python3 skills/workflow/periodic-maintenance/scripts/maintenance.py replay skills/workflow/periodic-maintenance/tests/fixtures/missing-implementation.json
python3 -m unittest discover -s skills/workflow/periodic-maintenance/tests -p 'test_*.py' -v
```

`request` 输出固定规则与单独标记的 `untrusted_snapshot`，声明 read-only 执行要求但不启动执行器；
`replay` 用模拟语义结论测试证据引用、范围／覆盖与普通 backlog 出口。返回码 0 表示离线输入处理完整，
2 表示存在未查／待澄清／交接映射缺口，1 表示非法输入；所有输出均 `mode: offline`、`delivery: not_submitted`。
不要用本地 0 退出码代替真实检查、Multica 接收或问题修复证据。

## 输入与适配边界

fixture 是测试用的内部交换格式，不是新平台 schema 或 Multica task 类型。

| 输入 | 含义／校验 |
|---|---|
| scope | 由运行配置独立提供的仓名→准确 repo HTTPS URL；只允许规则中的九仓名称。真实运行前须另外核实 Owner 范围和可见性，模型不能修改 scope |
| snapshot | 仓名、URL、public、完整 revision、expected_paths、files、gaps。缺失或不可读文件保留在预期路径及缺口中；元数据由未来可信采集器核实，不以模拟输入自报当线上证明 |
| files | path、role（current/code/history）、content、完整 commit、带时区 committed_at、可选 diff；仅仓内相对路径，历史不作为待更新对象 |
| review | 对应 revision、covered_paths、gaps、assessments；中断／未读路径不能出现在 covered_paths |
| assessments | 当前文档 statement、有效决定 decision（可空）、implementation 引用列表、state、outcome、reason、desired、acceptance；引用都是 path + 原文 quote |
| projects | 同一已核实 workspace 的 repo resource 记录（workspace/project/repo_url）；按 URL 唯一匹配，不猜标题，不接受模型指定 project |

引用必须存在于已检查快照的正确来源中，且 quote 匹配原文。实现问题需有效决定与代码证据，缺失则降为待澄清，
不会保留其原“补实现”验收。规则中的草案／future／HOLD 只接受 deferred，不能变开发需求；
这类条目缺决定证据时保留 deferred、记录缺口，不产生 backlog 草稿。
缺少有效决定时即使输入声称 consistent，也会降为 clarify；正文措辞、语义推理与决定有效性仍需独立 reviewer 判断。
日期不参与自动排序判案；提交时间和 diff 随证据输出供 reviewer 核对。结构检查无法证明模型覆盖了文件中的所有陈述。

## 输出与交接

结果含逐条 conclusions、covered_paths、gaps、普通需求 drafts 和已唯一匹配 project 的 backlog。
项目映射缺失／歧义时仍保留 drafts，backlog 为空且本轮 incomplete。找不到代码、覆盖缺失、历史不明都不输出无问题结论。
需求正文沿现有 Current behavior／Desired behavior／Evidence／Acceptance criteria／Out of scope 表达，
只生成 title、description、status=backlog、workspace、project，不产生 assignee、squad、todo 或 run 请求。
这只是可审查的本地草稿适配器，没有发送 API；没有新增维护专用 task 类型或下游修复管理。

若未来真实提交结果未知，按核对规则先查询原出口是否接收，再安全补交确认未接收项。当前没有实现此 transport／去重能力，
不能把重新运行 replay 当成安全重发，也不把 receipt_unknown 当未接收。

## 启用前仍需完成的工作

模板位于 assets 而非 Actions 发现目录，包含每周一次（示例 UTC 时间）和 workflow_dispatch；恒假 job、无权限且占位步骤失败。
它不使用 self-hosted runner label、不安装依赖、不 checkout／执行扫描对象，不包含 secrets 或真实 Multica 接线。
复制模板或删除恒假条件都不足以启用维护；实际执行步骤尚未实现。

后续获准解除启用 HOLD 后，另按正常源码 PR 与准确 head 审查落实：

1. 在原仓已存在的 Codex runner 上核对新用途的授权和最小权限；实现独立、干净会话与操作系统级只读快照隔离，
   扫描对象内容不作为指令执行，不授予修复写权限。复用目标仓实际固定合同，不以本 skill 替代 repo 规则。
2. 逐仓重新核实准确身份、公开可读性、文档入口／归档边界及固定版本；实现采集器并保存未读／未查／失败范围。
   私有 Skills、Financial、范围外仓仍排除；未就绪不能自动扩权或新建仓。
3. 接入真实语义 reviewer，验证请求、模型响应、超时与部分结果的适配；通过可复现样例后才认为核对能力可用。
   本版模拟场景验证代码边界，不衡量模型实际理解能力。
4. 在已核实 workspace 下确认 repo resource 唯一对应 project，验证普通 backlog 无指派、无 todo、无开发启动；
   实现接收回读及未知状态对账。凭据／settings 操作、运行隔离、调度启用各自按准确授权办理。

当前源码及测试通过不证明这四项完成，既有 HOLD、正常 hooks／required CI／review、PRM 与恢复职责保持。
