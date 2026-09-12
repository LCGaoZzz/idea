# 来源注册表、固定版本与读取边界

[返回](../README.md)。本目录的链接用来追踪证据，不代表所有文件都已取得完整字节、完整依赖或完成运行。文中P/C/I/T含义见根README。网络材料最后核对日期为2026-09-12。

## 1. 主要文献与方法来源

**P1 正式版。** Yan Y, Lin Y, Kumar T, et al. *Ecotypes of triple-negative breast cancer in response to chemotherapy*. Nature 654, 1088–1097 (2026). DOI [10.1038/s41586-026-10469-9](https://www.nature.com/articles/s41586-026-10469-9)。[PubMed 42129561](https://pubmed.ncbi.nlm.nih.gov/42129561/)用于文献身份交叉核对。正式网页报告发表于2026-05-13。

读取方式：正式版HTML正文、Methods和图注；部分页面通过`?error=cookies_not_supported`读取。没有下载完整出版社PDF，没有逐张审计全部原始图像，没有全部Supplementary Tables或source-data字节。

**P2 图示定位。** [Fig.1](https://www.nature.com/articles/s41586-026-10469-9/figures/1)、[Fig.2](https://www.nature.com/articles/s41586-026-10469-9/figures/2)、[Fig.3](https://www.nature.com/articles/s41586-026-10469-9/figures/3)、[Fig.4](https://www.nature.com/articles/s41586-026-10469-9/figures/4)、[Fig.5](https://www.nature.com/articles/s41586-026-10469-9/figures/5)。本文用图号／图注定位，不能理解为每个图像像素已重新检验。分类器正式位置为Extended Data Fig.10；旧教程Fig.6编号不直接沿用。

**P3 既有统计原则。** Ambroise C, McLachlan GJ. *Selection bias in gene extraction on the basis of microarray gene-expression data*. PNAS (2002). [PMID11983868](https://pubmed.ncbi.nlm.nih.gov/11983868/)。仅支持筛选必须纳入验证过程的成熟方法论背景，不把它写成本篇TNBC研究的新发现。

Methods定位尽量使用小节名称而非未经核对的网页锚点：Study participant details from the ARTEMIS Trial；Filtering of scRNA-seq data；Identification of aneuploid cells；Creating pseudo-bulk RNA-seq data；Performing NMF；Identifying archetypes；Identifying metaprograms of cancer cells；Cell frequency of the metaprograms and TME cell states；Co-occurrence of cell states and metaprograms；Determining ecotypes；RCOP相关小节；Identifying cell types and cell states in Xenium data；Spatial niche analysis in Xenium data；The gene-based classifier and overall survival。

## 2. 上游代码版本

统一固定到 [navinlabcode/tnbc-chemo@fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb](https://github.com/navinlabcode/tnbc-chemo/tree/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb)。这是核对的快照，不声称所有历史运行使用该提交，也不将默认分支未来更新视为已检查。

| ID | 固定位置 | 证据范围／状态 |
|---|---|---|
| C1 | [copykat_mix.R:160–235](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/scripts/copykat_mix.R#L160-L235) | 先前本地完整快照与远端blob匹配；本项目复审判定与350–475中间列。函数`decide_aneuploid`。 |
| C2 | [psbulk.fastNMF.R:23–115](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/scripts/psbulk.fastNMF.R#L23-L115) | 先前完整快照blob匹配；Tau／top2、筛选覆盖、缓存、NMF调用。 |
| C3 | [psbulk.prepare.R](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/scripts/psbulk.prepare.R) | 继承选定快照，未重新完整远端比对。 |
| C4 | [metamodule_fnmf.s1.R](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/scripts/metamodule_fnmf.s1.R) | 继承快照，本次纠正其是因子QC而非NMF原始入口。 |
| C5 | [metamodule_fnmf.s2a.R:76–99](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/scripts/metamodule_fnmf.s2a.R#L76-L99) | 本次连接器重新读取70–106；blob `3d1a1afd9606340f92ca21c8f96cb1429d5de218`；Jaccard排除值1及缓存分支。 |
| C6 | [metamodule_fnmf.s2c.R](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/scripts/metamodule_fnmf.s2c.R) | 继承快照，未完整重新校验依赖闭包。 |
| C7 | [metamodule_cell_frequency.R](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/scripts/metamodule_cell_frequency.R) | 继承完整快照和前轮连接器选段；评分／多标签／展示分支，未运行。 |
| C8 | [ecotype_0_create_feature_corr.R:15–23](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/scripts/ecotype/ecotype_0_create_feature_corr.R#L15-L23) | 前轮完整读取与blob匹配；Spearman／缺失／helper调用。 |
| C9 | [ecotype_1_define.R:12–76](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/scripts/ecotype/ecotype_1_define.R#L12-L76) | 前轮完整读取与blob匹配；siglist未接图、1.8、共识。 |
| C10 | [ecotype_3_contexts.response.R](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/scripts/ecotype/ecotype_3_contexts.response.R) | 前轮连接器读取；helper未完整取得，论文RCOP公式本次补充。 |
| C11 | [scML_classifier.v3.R:89–204](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/scripts/scML/scML_classifier.v3.R#L89-L204) | 前轮读取1–250及重点段；没有最终运行对象；明确上游信息流。 |
| C12 | [ML13g/build_ML_model.R](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/scripts/ML13g/build_ML_model.R) | 前轮读取1–275，候选构造而非完整最终系数。 |
| C13 | [Xenium EvalMode](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/scripts/xenium/xenium.celltype.TransferLabel_EvalMode.R) | 先前完整快照blob匹配；39–50、83–125及开关分支。 |
| C14 | [Xenium consensus_decision](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/scripts/xenium/xenium.celltype.TransferLabel_EvalMode.consensus_decision.R) | 继承快照；helper、最终门槛和votes对象未全部取得。 |
| C15 | [空间niche作者文档](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/xenium.spatial_niche.md) | 作者路由／历史捕获，不声称所有step脚本完整审读。 |
| C16 | [CellChat作者文档](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/cellchat_ligand_receptor.md) | 作者路由与Methods，无本次真实通信运行。 |
| C17 | [fastnmf.R](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/scripts/fastnmf.R) | 继承快照；仍需调用命令与输入才能恢复逐患者入口。 |
| C18 | [数据README](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/data/README.md) | 本次完整连接器读取；blob `d185bdbb6afb9f54f79dca062a07b9b9d8f3ed67`。 |

这些状态明确区分先前已核对与本次新核对。链接存在不代表本次下载了所有字节；本地快照存在也不代表已执行。函数／行号以固定源码原始行计，不以聊天工具输出外层JSON的行计。

## 3. 数据入口与未取得对象

C18在该固定版本提供 [CELLxGENE入口](https://cellxgene.cziscience.com/e/6f9de485-58cd-4342-bfc4-b3d3dd223aa8.cxg/) 用于scRNA浏览／下载；空间数据说明需要联系作者获取链接，特别涉及高分辨率H&E，列出了Xenium对象、标准输出、H&E与配准、Visium／HD对象目录。这是所读版本的说明，不保证未来访问政策不变。

本次没有下载全体患者矩阵、临床表、原始空间边界／H&E、全部补充表、最终13基因系数和模型RDS。未取得不等于不存在或作者拒绝提供。恢复时先要精确的处理对象与metadata，再决定原始大文件获取。

## 4. 继承材料与校验

**H1** 先前本对话产物 `TNBC_Ecotypes_Deep_Dossier_ZH.md`，本次读取、重新组织并纠正；SHA-256 `ec3c226f78f6798f15aa3763351e6dc80bf5102f1944dd83ae66d984cc15d32b`。这是二次分析，不可替代正式原文证据。

**H2** `tnbc-chemo-reconstruction-2026-08-07.zip`，SHA-256 `d6f1ecd3a5aeec36125f03b82a550762f114f4482beceac99bcd5a9f74750407`。含历史源码与整理；部分vignette是重建记录，不自动声明字节等于作者原文。

**W1** 用户指定 `reconstruct-bioinfo-protocol-pr630-4bdc4d0.zip`，SHA-256 `66d407b3a8ea7cf3c30e5f5df4ccff143b6b54497588e67426d2fe543306483f`。用作证据合同与模块化整理依据；本项目未声称通过了该包所有原生JSON schema或生物学验收。

上述SHA在当前容器重新计算。原ZIP和原始论文／整库源码不随此idea公开复制。所有新的辅助脚本为本项目原创分析工具，许可问题不被误用为作者整库可以任意再分发的声明。

## 5. 如何继续维护

新增来源应记录来源ID、固定版本、读取范围、用来支持的具体主张与实际运行状态。把冲突解决记录附在[audits](../audits/ISSUES.md)，保留旧观察，不悄悄把缺失字段补成默认值。新结果应单独命名实际分支和输入，不覆盖“论文报告值”。
