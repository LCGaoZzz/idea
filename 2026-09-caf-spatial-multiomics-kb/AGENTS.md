# CAF spatial multi-omics knowledge base: agent entry

先读 `README.md` 和 `reconstruction/PROVENANCE.md`。按 `knowledge_base.json` 的任务入口按需读取，不要把分类标签或本知识库的解释当原文事实。

精确数字查 `reconstruction/evidence/parameter_facts.tsv`，给出 fact_id、来源小节与不确定性。必须区分论文报告、作者代码、本包推导、迁移建议。没有取得作者活动代码，不能补写路径、commit、默认参数或已复现结果。

独立审核先读 `reconstruction/review/FABLE51_REVIEW_PROMPT.md`。源文本冲突保留双方，允许新证据推翻原有审计判断。合成诊断不是生物学复现。

`reconstruction/` 是46个原交付文件的字节级快照。续作时记录变更并更新新版本，不把新运行结果回写成历史回执；运行原包验证前先校验哈希，具体要求见其中的 `AGENTS.md` 和 `REVIEW_GUIDE.md`。
