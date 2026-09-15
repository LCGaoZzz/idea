# Agent reading contract

本目录是来源受限的科研审计知识包，不是作者官方仓库，也不是已经执行的生物学分析。

先读 PROVENANCE.md 和 ARTICLE_REVIEW_ZH.md；精确事实查 evidence/parameter_facts.tsv 与 references.tsv，再查 reconstruction_manifest.json 对应 Axx。必须分开：论文报告、可见活动代码、本包推导、本包新建议。本包没有作者活动代码；不得编造 commit、脚本路径、补充表内容或原图视觉观察。

回答数字问题时给 fact_id 和来源小节；回答“是否复现”时读取 validation_report 与 execution_records，不以 diagnostics 通过替代生物复现。遇到源文本冲突，保留两边，不擅自消除。数学反例只支持一般可发生的风险，不证明原文实现一定发生。

可用诊断：在本包根目录运行 `python diagnostics/diagnostic_examples.py`。它只使用合成数据和标准库。不运行作者数据，不向外发请求，不修改原始来源。

继续工作时先补缺失源材料，不重复从摘要补写方法。若有新代码或最终PDF，应逐项重新判定 F024–F028、A23–A25 等相关结论，允许新证据推翻本包批评。不要把当前文档当不可更改的权威。
