# 多药耐药的肿瘤—基质界面生态位｜Cell Reports Medicine 2026

> **版本：2026-09-17，代码证据版 source-limited v0.1；本目录归档完整交付包，不是删减阅读核心版。**
> 完整保存原证据 ZIP 的 **23/23 个文件**；为归档改用 `tar.xz`，内部路径和每个文件的字节内容保持一致。正文、STAR Methods、原图图注、补充材料及受控矩阵的缺口原样保留。**没有完成论文全文重建或生物学复现。**

## 文章信息

**原文标题：** [Single-cell and spatial multi-omics reveal a recurrent multicellular niche at the tumor-stroma interface in multidrug resistance](https://www.cell.com/cell-reports-medicine/fulltext/S2666-3791(26)00469-6)。

**期刊 / 标识：** Cell Reports Medicine；PII `S2666-3791(26)00469-6`。题名与期刊关联来自作者仓库 README 的既有核验记录；本次入库没有补写作者名单、发表日期或 DOI。

**作者代码：** [KangjieShen/MDR_Code 固定快照](https://github.com/KangjieShen/MDR_Code/tree/f0fd6fc17654541fa97e49dbaf93cde583ee55a7)，commit `f0fd6fc17654541fa97e49dbaf93cde583ee55a7`。文件哈希和来源见 [源码清单](evidence/repository_file_manifest.json)。

**数据声明入口：** [HRA016493](https://ngdc.cncb.ac.cn/gsa-human/browse/HRA016493)、[OMIX014772](https://ngdc.cncb.ac.cn/omix/release/OMIX014772)、[MTBLS15322](https://www.ebi.ac.uk/metabolights/MTBLS15322)。记录 accession 不代表取得或检查了矩阵；材料获取状态以原包日志为准。

### 原文第一张主图（Figure 1）

**状态：未取得可核验的原图及图注。** 本目录保留 Figure 1 位置，不猜测图片地址、不以原创示意图冒充原图；请通过上述原文入口核对。解读中的 panel 定位来自代码注释，尚未与出版图注交叉验证。

## 阅读与使用入口

| 需求 | 入口 |
|---|---|
| 深入理解研究逻辑、主图脚本、Xenium 定义与统计边界 | [完整中文深度解读](knowledge/DEEP_REVIEW_ZH.md) |
| 查看协议派生的状态报告 | [REPORT.md](REPORT.md) |
| 取得全部日志、manifest、证据、HTML 阅读器及原创测试 | [完整证据归档](archives/MDR_CellReportsMedicine_complete_evidence_20260917.tar.xz) |
| 理解本次入库范围与原包限制 | [IMPORT_SCOPE.md](IMPORT_SCOPE.md) · [原始 scope](evidence/scope_boundary.json) |
| Agent 定位与继续审读 | [AGENTS.md](AGENTS.md) · [knowledge_index.json](knowledge_index.json) |
| 核验所有 23 个成员及在线镜像 | [完整性清单](integrity/complete_bundle_manifest.json) · [校验脚本](integrity/verify_archive.py) |

## 当前证据级别

已完成的是固定源码的静态审读、公开元数据核验与原创方法学分析。A01–A12 的**论文重建状态仍全部受阻**；原包的 9 个原创合成语义检查不是作者代码运行，也不是论文数据验证。此处“完整”描述交付文件保全，不描述文章事实已全部取得。

重点导读：Xenium 展示标签与原始计数统计标签不同；邻域聚类与严格三方共现不同；驻留比例与背景校正富集不同；距离受目标密度影响；空间剖面不是时间轨迹；公开临床脚本中的单因素 Cox 不等于独立预后证明。具体来源、行号和适用边界在深度解读中逐项给出。

## 本地校验与完整解包

在本目录运行：

```bash
python integrity/verify_archive.py
mkdir -p complete_evidence
# 解包保留原交付的全部内部路径，不覆盖本目录的导航文件。
tar -xJf archives/MDR_CellReportsMedicine_complete_evidence_20260917.tar.xz -C complete_evidence
```

完整 HTML 阅读器位于解包后的 `complete_evidence/MDR_deep_review.html`；完整 Agent 入口位于 `complete_evidence/agent/README.md`。原包 README 与本目录 README 是不同用途，前者保存在完整归档内，不被导航文档覆盖。

## 仓库分类与相关条目

主分类：**空间组学 → 多细胞生态系统、TME 与促纤维炎症**。交叉标签：`MDR`、`Xenium`、`Visium`、`scRNA-seq`、`tumor-stroma-interface`、`CAF`、`myeloid`、`TREM2`、`AXL`、`spatial-statistics`、`methodology-audit`、`agent-kb`。

与 [通用多细胞生态系统知识库](../2026-09-multicellular-ecosystems-xenium-kb/README.md)、[CAF 空间多组学案例](../2026-09-caf-spatial-multiomics-cancercell-2025-kb/README.md)、[serpin–ECM–myeloid 案例](../2026-09-serpin-myeloid-spatial-niches/README.md) 交叉导航；这些主题联系不表示不同研究中的状态已被证明等价。返回 [仓库分类索引](../CATALOG.md)。
