---
name: cancer-coevolution-knowledge
version: 0.9.0
description: Evidence-bounded Chinese knowledge base for genotype–phenotype mapping, single-cell phylogeny and state plasticity; with source-aware retrieval and project capability checks.
---

# 何时使用

用户询问该综述、GoT/GoT–ChA/TreeAlign/PATH 等方法的概念、测量强度、假设、限制，或希望把这些思想迁移到单细胞/空间项目时使用。

# 薄入口

先读根目录 `AGENTS.md`；执行 `tools/kb.py search` 或 `context`；遇到具体方法只读对应 M 方法卡与 C 论断；检查证据来源的 inspection_scope。

# 工具接口

本地 CLI 或 `tools/tool_server.py` 的 JSONL stdio 合同都可用。后者不是 MCP，没有自动注册，也不调用 LLM。宿主把 `agent/tools.json` 的参数转交给这些函数即可。

# 任务边界

本库是研究解释和方法审查资料；不是整合分析引擎，不会安装或执行作者软件。要运行生物数据应由宿主已有分析能力负责，并另外固定输入、版本和验收条件。

# 证据纪律

不补完未读正文；不把作者软件默认值当论文最终参数；不把同细胞关联当因果；不把来源支持范围扩成全平台通用结论。新增解释标注 ANALYSIS，新增建议标注 TRANSFER。
