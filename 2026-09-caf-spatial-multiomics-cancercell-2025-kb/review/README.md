# fable5.1 / 独立审阅者入口

先读上级目录的 [IMPORT_SCOPE.md](../IMPORT_SCOPE.md) 和 [PROVENANCE.md](../PROVENANCE.md)，再使用 [原审核提示词](FABLE51_REVIEW_PROMPT.md)。原提示词原字节保留，但其完整机器复验指令针对前次交付ZIP，不全部适用于当前知识库。

## 当前目录可以审核

主报告与6份知识/方法章节中的事实、逻辑、参数和结论强度；50条事实索引及其原始来源定位；27个分析目标的原状态摘要；对原图和补充材料可得性的诚实性；18项合成诊断代码、输出与回执。逐条列出“正确、需限定、事实错误、无来源、无法判定”，优先寻找能推翻本库批评的原始证据。

关键入口：[主报告](../ARTICLE_REVIEW_ZH.md)、[事实表](../evidence/parameter_facts.tsv)、[参考来源](../evidence/references.tsv)、[分析目标简表](../evidence/analysis_index.json)、[统计审计](../knowledge/02_statistics_audit.md)。

## 当前目录不能替代的审核

完整`reconstruction_manifest.json`、`traceability.tsv`、来源获取日志、原版通用验证器和原`SHA256SUMS`未导入。需要这些文件的完整机械审核，必须同时取得原交付ZIP；不能用本库简表代替，也不能把缺文件的命令失败解释为原ZIP本身验证失败。

本目录只可执行：

```bash
python diagnostics/diagnostic_examples.py
sha256sum -c integrity/IMPORTED_SHA256SUMS
```

这两条命令从知识库根目录运行。前者检验合成数学例子，后者检验导入文件一致性；都不能验证论文生物学结果。

## 评价边界

把“原论文可能的问题”“前次重建包可能的问题”“本次知识库导入范围”分成三栏。原文未取得的内容应回到期刊最终稿、补充文件或作者代码核实；不能因为本库没有完整作者代码，就判论文实现错误。也不要因本库24文件哈希一致而默认其中科学推断正确。
