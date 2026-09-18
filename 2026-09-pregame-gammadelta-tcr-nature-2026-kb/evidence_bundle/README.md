# PreGame / Nature 2026 — 证据分层重建包

论文：St. Paul, Hendrikse, Ying et al. **Identification of broadly tumour-reactive γδ TCRs from multiple myeloma**. Nature，2026-09-16，DOI: 10.1038/s41586-026-11055-9。

## 从哪里开始

可直接在浏览器打开 `reports/COMPLETE_RECONSTRUCTION_ZH.html`，它包含全部四篇报告、目录和嵌入式理论图，不依赖外部图像服务。

- `reports/DEEP_RECONSTRUCTION_ZH.md`：完整中文研究逻辑、方法、数学、统计审计和迁移边界。
- `reports/FIGURE_ATLAS_ZH.md`：主图与扩展图的输入、变换、图形语义、统计单位和验证任务。
- `reports/MATHEMATICAL_AUDIT_ZH.md`：估计对象、分数/阈值、分组验证、max聚合、伪重复、组成与临床推断的数学附录。
- `reports/REPRODUCTION_ROADMAP_ZH.md`：数据字典、实际缺口、获取代码后应逐项核查什么。
- `tables/`：参数、性能、数据登录号、补充表转录与冲突清单。
- `scripts/` 与 `code_guidance/`：**本次新写的审核工具及运行说明，不是作者代码，不是 PreGame 实现**。
- `audit/`：实际执行的独立算术检查、测试结果和获取失败记录。
- 根目录的 `reconstruction_manifest.json`、`traceability.tsv`、`REPORT.md` 和 `validation_report.json`：用户所给 protocol 的机器可读交接材料。

## 交付边界

已经通过浏览工具逐段读取最终文章正文、Methods、主图和扩展图图注、公开审稿往返的相关部分、补充表解析文本，并目视核查审稿文件 PDF 第69页的供者留出 ROC，以及 Reporting Summary 的关键页。**没有取得作者 Zenodo 代码字节、模型权重、原始分析矩阵或 source-data XLSX；没有运行作者分析。** 原文图片的大部分像素也没有取得，因此图形解读明确以 caption 为主。

原始 PDF / HTML 下载到容器失败。浏览器读到的内容和本地原始文件不是同一件事；`provenance/WEB_READING_LEDGER.md` 记录在线定位，`tables` 是人工结构化摘录，不冒充出版方原始文件。正式 protocol 的全量来源获取阶段仍为 partial，后续执行门没有开放。深入报告属于**已读取公开材料的文献重建与独立评议**，不表示全套原始材料重建流水线已经通关。

核心状态：**材料冲突 + 原作者代码/数据复现受阻**。机器 validator 通过只表示交接材料内部一致，绝不等于论文正确性、临床效用或运行复现通过。

本包不自动上传到 GitHub，不修改用户任何仓库。网页状态以本次读取为准。来源访问失败不等同于作者没有公开代码。
