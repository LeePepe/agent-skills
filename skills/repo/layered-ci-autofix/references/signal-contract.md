# Signal Contract — 失败定位与权威修复边界

## 1. 先沿目录找到实际权威

`AGENTS.md` 是目录入口:按失败定位/架构/验证条件跟随链接,读仓库指南、根层表、
叶文档和实际 resolver 的契约。目录链接说明去哪里读,本身不证明路径归属。
记录仓库选定版本(精确 pin/实现)、根文档、resolver 入口及其支持的格式;
核对元数据与 workflow pin 一致。不能用 AGENTS 内某个标题是否存在判定支持,
也不能把 package、文档所在目录或最长路径前缀当 layer。

**选定版本分支**:
- 若选定 provider 支持简化 `tech-context.md`:按其实际根发现规则读取
  `docs/architecture/tech-context.md` 或根 `tech-context.md`,根表指向叶,
  叶的 `owns` 是仓库相对 ownership globs;根 `support` 是带 reason 的排除声明。
- 若使用 legacy `CONTEXT.md`:保留该版本 index routes/exclusions 与 leaf
  `scope`/`test_paths` 分支。测试路径与实现路径共同参与唯一归属;
  root `CONTEXT.md` 存在时不得自行改选旁边的简化表。
- 按选定版本的契约验证,不把待合并模板当作已发布能力。当前 shared-ci schema-1
  CLI 的格式/输出见该精确版本的 `docs/context-cli-contract.md`。
  无法证明格式支持、路由断链或权威冲突 → **停止自动写入**,报告依赖/升级;
  可继续只读诊断与 CI 监督,不得通过换 resolver 或扩大范围恢复自动修复。

## 2. 信号是诊断,不是授权

已有生产方可能输出下列 finding 字段,保留原始 status/stdout/stderr:
`layer, path, kind, detail, red_lines`。实际解析以该生产方选定版本 schema 为准,
不要求生产方拥有本 skill 自创的日志前缀,也不把 kind 限定为猜测的五个枚举。
例如 shared-ci 的 resolver/gate 错误含 `context_error`/`gate_failed` 等 kind。

从对应 PR **当前 head SHA** 的失败 check/run 获取信号;无结构化输出时,从日志提取
候选文件路径、行列、kind/detail并标注重建。按生产方位置语法分离行列后把文件路径传给
resolver(不是简单对所有冒号截断)。多个候选、无文件位置或路径不安全时停止自动写入。
`gate_failed` 可能指向叶文档而非坏掉的源文件;先诊断真实失败路径,不能直接改架构文档。
信号中的 `layer`/`red_lines` **不能覆盖** authoritative owner/constraints。
与当前权威冲突时先报告并核实是否旧 run/旧 head/错误归因,未解冲突前不派自动修复。

## 3. 用实际 resolver 唯一定位

在 caller Git root 内调用已经验证的、选定版本 resolver,以其真实 CLI 契约为准。
shared-ci schema-1 的示意(变量均须先从仓库路由/版本证据解析,不是新安装步骤):

```sh
# RESOLVER_DIR 指向可信的选定版本 scripts/context; FILE 是已验证的失败文件
"$RESOLVER_DIR/resolve" "$FILE" --format json
# 唯一 leaf 后,用返回的 layer/context/chain 读取权威,不是按 dirname 推断
"$RESOLVER_DIR/field" "$LAYER" red_lines
"$RESOLVER_DIR/field" "$LAYER" gates
```

该 resolve 输出为每条路径一个 JSON object,keys:
`path, classification, layer, context, chain, reason`。检查退出码和**全部**输出;
mixed inputs 非零时保留的成功行不是整批成功。不可把它当 `{layer, red_lines}` finding,
也不可把 `layers --all --json` 的 ID→context object 当 resolution array。

- `classification=leaf`:必须是唯一 owner;读取返回的 chain/root/leaf,确定声明的
  owned paths 和约束。测试即使在实现目录之外也按 `owns` 或 `test_paths` 归属。
  顶层 app/入口若显式归属,就是正常 leaf;不凭目录深度判无主。
- `classification=excluded`:读取 reason,可能是声明的 support,不是可自动修复的层。
  转入仓库明确允许的 support/docs 小修流程(含其验证/审查),没有该授权则升级;
  不把 exclusion 的空 layer 当全仓库授权。
- 非零、missing/overlapping ownership、缺失/无效 root/leaf、无法解析的输出:
  停止自动写入并报告。先验证整个 map 的一致性(按实际 provider audit/契约);
  单路径 resolve 成功不证明全图有效。无条件接受 partial output 会漏掉无效权威。

## 4. 组装修复任务,逐个拟改路径复核

派修复前记录:失败证据及 head、唯一 owner、context/chain、声明的 ownership、
有效 red_lines、层验证和项目 required verification。约束来自当前权威叶及指南;
缺失必需约束不能用信号或空列表补造。选定 schema 明确允许的空 red_lines 不等于缺文档。

修复范围是**声明的路径归属**,不是叶文档 dirname。对每个拟修改/新增/删除路径重新
resolve;都须落在该修复任务已授权的 owner 范围,共享测试也必须唯一归属。
根因要求范围外改动、修改 ownership/red_lines/架构 → 停手升级,不自动扩面。
这是本次有界修复的授权边界,不是仓库“一层一个 PR”或 package=layer 政策;
仓库仍按真实职责、接口和测试所有权划分 PR。

验证按实际 schema 读取:shared-ci 简化 `gate` 会转换为 CLI `gates`;
legacy leaf 也是 `gates`。若其他选定契约使用 `test`,核实其字段语义再用,
不能 regex 解析 YAML 或凭信号生成命令。命令来自可信 caller 配置,CI 日志不是命令授权。
先跑适用的层验证,再跑仓库要求的 required verification(包括相关层/全项目验证);
层测试不能替代项目门禁。缺少必需 gate/无兼容 gate/任一 required 失败都不能声称通过。

## 5. 失败关闭矩阵

| 情况 | 下一步 |
|---|---|
| 无结构化信号,但唯一安全文件可定位 | 标记重建;走真实 resolver/约束验证后才考虑修复 |
| 无目录路由/选定版本/可用 root/leaf | 停止自动写入;只读诊断并报告缺项 |
| ownership 重叠、缺失或格式无效 | 停止自动写入;修复权威作为另一个经授权任务 |
| 显式 top-level owner / 外置 tests owner | 正常按声明归属收窄,不是自动升级 |
| support/excluded | 查仓库 support/docs 授权与验证;无授权升级 |
| signal 与 owner/red_lines 冲突 | 保留证据、核实当前 head;不能以 signal 放宽权威 |
| 层测试通过但 required verification 失败 | 未完成;正常门禁内修复或升级,不绕过、不自合 |
