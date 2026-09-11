# 参数表使用说明

[返回入口](../README.md) · [计算方法解析](../docs/03-computational-protocol.md) · [来源](../evidence/SOURCES.md)

`parameter_registry.tsv` 保留前次精读审计包的103条登记，传输时将CRLF统一为LF；单元格、行顺序与来源分类不变。该表是证据登记，不是一份能直接运行的配置，也不是全部参数已经与终刊活动代码闭合的声明。

| 字段 | 含义 |
|---|---|
| analysis | 分析类别 |
| scope | 平台、分析支路、benchmark或helper范围 |
| parameter / value | 原登记中的参数与值；未知值保持空白 |
| provenance | reported=论文／补充材料声明；active_code=源码活动表达式；code_default=函数默认；unverified=未确认 |
| source_id / locator | 对应来源表及方法、函数或物理PDF页 |
| notes | 分母、单位、版本、默认差异及其他限制 |

`active_code`只表示读到了活动源码，不表示代码被作者用于某个终刊panel，更不表示本次执行过。`reported`不自动覆盖同名helper默认值；`code_default`不自动升级为论文运行值。

实际复现前应为一个明确目标选择对应scope，补齐调用覆盖、输入、软件和数据库快照，再生成运行配置。不同支路的UMI、邻域、mu、归一化目标或高低分组阈值，不得因为名称相似就合并。

本文方法、Reporting Summary和部分图注之间已有待对齐项，见[代码审计I08](../docs/04-code-atlas-and-audit.md#i08)。完整终刊补充表和实际生成链未取得时，保留差异而不是选择较常见的参数。这里没有把全部未确认条目补成习惯值。
