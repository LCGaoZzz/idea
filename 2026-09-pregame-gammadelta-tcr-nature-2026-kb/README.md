# PreGame / γδ TCR｜Nature 2026 完整证据包

> **版本：2026-09-18，证据分层重建包归档版 source-limited；本目录归档完整交付 ZIP，不是作者代码复现。**
> 完整保存原证据 ZIP 的 **44/44 个成员**：原始字节保全于 [transfer/PreGame_Nature_2026_evidence_bundle.zip](transfer/PreGame_Nature_2026_evidence_bundle.zip)，完整解包树见 [evidence_bundle/](evidence_bundle/)。作者 Zenodo 代码、模型权重、原始分析矩阵与 source-data XLSX 未取得，相关缺口原样保留。**没有运行作者分析，没有生物学复现。**

## 文章信息

**原文标题：** [Identification of broadly tumour-reactive γδ TCRs from multiple myeloma](https://doi.org/10.1038/s41586-026-11055-9)（St. Paul, Hendrikse, Ying et al.）。

**期刊 / 标识：** Nature，2026-09-16，DOI `10.1038/s41586-026-11055-9`。

**作者代码：** Zenodo DOI `10.5281/zenodo.20028241`。论文引用了该 DOI，但本次获取失败、未检验其字节；获取失败不等同于作者没有公开代码。

**数据声明入口：** EGA `EGAS50000001889` / `EGAD50000002742` / `EGAD50000002743`（ALGONQUIN 研究）、`EGAS50000001888` / `EGAD50000002744` / `EGAD50000002745`（PreGame 研究）、临床试验 `NCT03715478`；完整清单与逐项核验状态见[数据登录号表](evidence_bundle/tables/accessions.tsv)。受控访问原始数据与患者临床表均未取得。

### 原文第一张主图（Figure 1）

**状态：未取得可核验的原图像素。** 图形解读以已读取的出版图注为主；本目录保留 Figure 1 位置，不猜测图片地址、不以原创示意图冒充原图，请通过原文入口核对。

## 阅读与使用入口

| 需求 | 入口 |
|---|---|
| 浏览器一站式阅读全部四篇中文报告、目录与嵌入式理论图 | [完整重建报告 HTML](evidence_bundle/reports/COMPLETE_RECONSTRUCTION_ZH.html) |
| 研究逻辑、方法、统计审计与迁移边界 | [深度解读](evidence_bundle/reports/DEEP_RECONSTRUCTION_ZH.md) |
| 逐图输入、变换与图形语义 | [图集](evidence_bundle/reports/FIGURE_ATLAS_ZH.md) |
| 估计对象、阈值、max 聚合与伪重复的数学附录 | [数学审计](evidence_bundle/reports/MATHEMATICAL_AUDIT_ZH.md) |
| 数据字典、实际缺口与获取代码后的核查清单 | [复现路线图](evidence_bundle/reports/REPRODUCTION_ROADMAP_ZH.md) |
| 参数、性能、登录号、补充表转录与冲突清单 | [tables/](evidence_bundle/tables/) |
| 机器可读交接材料与逐条追溯 | [REPORT.md](evidence_bundle/REPORT.md) · [DELIVERY.md](evidence_bundle/DELIVERY.md) · [traceability.tsv](evidence_bundle/traceability.tsv) · [reconstruction_manifest.json](evidence_bundle/reconstruction_manifest.json) |
| 实际执行的独立算术检查与测试记录 | [audit/](evidence_bundle/audit/) · [environment.md](evidence_bundle/environment.md) |
| 原始 ZIP 字节、导入与校验脚本、就绪标记 | [transfer/](transfer/) |
| 本次入库的校验记录 | [integrity/import_verification.json](integrity/import_verification.json) |
| Agent 路由、禁用断言与恢复优先级 | [AGENT_KNOWLEDGE_CARD.json](evidence_bundle/AGENT_KNOWLEDGE_CARD.json) · [AGENTS.md](AGENTS.md) |

## 当前证据级别

已完成的是公开出版材料的逐段读取（正文、Methods、主图与扩展图图注、公开审稿往返、补充表解析文本、Reporting Summary 关键页），加上独立算术检查、18 项原创单元测试与文献重建评议。A01–A19 的**作者分析核验全部受阻**，其中 A05（TR 标签边界比较符）与 A10（差异分析下采样迭代数）存在图注—Methods 材料冲突；qualifying successful executions 为 0。机器 validator 通过只表示交接材料内部一致，不等于论文正确性、临床效用或运行复现通过。

重点导读（来源、行号与适用边界见数学审计与冲突清单）：PreGame 不是只从 CDR3 序列预测；27 个有序特征未被恢复；0.864 不是供者留出 AUROC；10/10 极端候选不能外推普遍准确性；HLA-C/Bw4/KIR3DL1 安全性未经临床确立；无配对 VDJ 与 ADT 的 Xenium 数据不能直接兼容。

## 本地校验与重新解包

在仓库根目录运行：

```bash
python3 2026-09-pregame-gammadelta-tcr-nature-2026-kb/transfer/import_bundle.py
```

脚本会重验 ZIP 哈希（`4700b548…`）与包内 `SHA256SUMS`（43/43 项，自引用条目除外）、重建 `evidence_bundle/` 解包树并刷新 [integrity/import_verification.json](integrity/import_verification.json)；任何不一致都会非零退出，不会改动仓库文件。原始 ZIP 也可自行解包：内部路径与每个文件的字节内容与本目录解包树一致。

## 仓库分类与相关条目

主分类：**免疫学 → γδ TCR 与肿瘤反应性受体挖掘**。交叉标签：`multiple-myeloma`、`γδ T 细胞`、`PreGame`、`随机森林`、`TCR 挖掘`、`methodology-audit`、`evidence-bundle`、`agent-kb`。

与 [NISE / LASErMPNN 可信蛋白设计](../nise-lasermpnn-2026/README.md)同属"论文重建与可复查研究"路线，与 [CAF 空间多组学](../2026-09-caf-spatial-multiomics-cancercell-2025-kb/README.md)、[MDR 生态位证据包](../2026-09-mdr-tumor-stroma-niche-crm-2026-kb/README.md)共享"区分作者结果、独立推导与未执行复现"的立场；这些主题联系不表示证据状态等价。返回 [仓库分类索引](../CATALOG.md)。
