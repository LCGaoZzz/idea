# 08｜来源登记、固定版本与获取边界

[返回入口](../README.md) · [审计](02-code-audit.md) · [追溯表](traceability.tsv)

整理/复核日期：2026-09-11。本文不使用前次回答本身作为原论文事实的唯一出处；它是本会话提供的待整理材料，重要内容仍指向论文或固定源码。没有复制论文全文。

## P1｜正式论文身份、摘要与主图图注

[PubMed PMID 41990751](https://pubmed.ncbi.nlm.nih.gov/41990751/)。正式书目：Reyes J, Del Priore I, Chaikovsky AC, et al. *Cell*. 2026;189(10):2875–2897.e53. DOI：[10.1016/j.cell.2026.03.032](https://doi.org/10.1016/j.cell.2026.03.032)。在线发表 2026-04-15，卷期日期 2026-05-14。

本次重新读取元数据、摘要及可见主图图注。Figure 1–7 的身份、主要实验设计及部分面板统计单位据此核对。图注读取不是原图像定量复核。未将全部图号/时间/样本数合并为一个统一队列。

## P2｜对应正式版的 PMC 作者稿

[PMC13173668](https://pmc.ncbi.nlm.nih.gov/articles/PMC13173668/)。公开索引可读取 Results/Discussion 和部分方法指向；直接页面访问遇到浏览器检查。检索正文用于复核以下小节：

- Capturing cell states after spontaneous p53 loss；
- Rare progenitor-like cells exhibit peak oncogenic and tumor suppressive activity；
- Rewiring of communication creates a progenitor niche tissue circuit；
- Oncogenic KRAS inhibition dismantles the progenitor niche；
- p53 enforces resolution of progenitor-like epithelial states；
- p53 naturally collapses the progenitor niche。

Figure S6D–F 的状态匹配解释主要来自上述可检索正文，而非本次重跑相应 Notebook。全文本地归档、全部 STAR Methods、补充图和 Data S1–S5 均未完成获取/核验。不能把“本次未取得”表述为“作者未报告”。

## P3｜正式版归档记录

[CSHL repository 42207](https://repository.cshl.edu/id/eprint/42207/)。已复核身份及归档记录；没有成功获取并逐页检查完整正式版 PDF。因此本稿不声称做过 PDF 视觉核验。

## P4｜早期预印本，只作版本提醒

[bioRxiv 10.1101/2025.06.10.656791v2](https://www.biorxiv.org/content/10.1101/2025.06.10.656791v2)。预印本标题/图号/内容与最终版可能不同，不用于填补最终版未获得的数值参数。

## Z1｜作者 Zenodo 归档

[Zenodo 18892592](https://zenodo.org/records/18892592)，DOI `10.5281/zenodo.18892592`。标题和内容对应本研究，目录列出代码及面板相关文件。原请求提供的 `188925921` 未成功解析；不把末尾多出的字符保留为已核验 DOI。

归档目录可查不等于整个代码压缩包、面板文件已下载。Zenodo 与下述 Git commit 未做全量逐字节比较，不能当作完全相同版本。

## 作者 GitHub 固定快照

仓库：[dpeerlab/p53-niche-dynamics](https://github.com/dpeerlab/p53-niche-dynamics)。固定提交：[a97d1a42cede4c12416875a4aa50d3d63ee1fffd](https://github.com/dpeerlab/p53-niche-dynamics/tree/a97d1a42cede4c12416875a4aa50d3d63ee1fffd)，提交记录日期 2026-05-14。

以下 C 类是已读取内容；N 类是导航，不表示其具体算法已审计。

### C0｜完整原始 Xenium 导入 Notebook

[源码](https://github.com/dpeerlab/p53-niche-dynamics/blob/a97d1a42cede4c12416875a4aa50d3d63ee1fffd/transcriptomics/notebooks/Xenium_Preprocessing_step00_raw_tenx_to_adata_locked20260318.ipynb)。定位 cell id 4、5、8；`compile_adata` 调用。

前次资料包中的完整文件本次重新计算 Git blob，仍为 `0afb5641e707e2ad484c30a68e0aa02dd2a729d7`。这是源码身份核验，不是执行。

### C1｜README 与数据更新通知

[README](https://github.com/dpeerlab/p53-niche-dynamics/blob/a97d1a42cede4c12416875a4aa50d3d63ee1fffd/README.md)。数据入口与 2026-05-14 淋巴结注释更新说明来源。完整对象未读取，不能推断 obs/layers 内容。[数据清单](data_manifest.tsv)

### C2｜空间半径图的活动路径

[Step03](https://github.com/dpeerlab/p53-niche-dynamics/blob/a97d1a42cede4c12416875a4aa50d3d63ee1fffd/transcriptomics/notebooks/Xenium_Preprocessing_step03_compute_neighborhoods_simplified_locked20260410.ipynb)。已读取关键函数与 cell id 11 的活动参数：70 μm 候选、60 μm 最终筛选。函数：`compute_sample_neighborhoods`、`filter_neighborhood`、`compute_distances_within_neighborhood`。

本地前次包保留的是选定单元摘录，不是完整 Notebook；不能把摘录 SHA 当作上游文件 Git blob。保存输出不是本次运行日志。

### C3｜G–P 扩散组件

[Step08](https://github.com/dpeerlab/p53-niche-dynamics/blob/a97d1a42cede4c12416875a4aa50d3d63ee1fffd/transcriptomics/notebooks/Xenium_Preprocessing_step08_diffusion_components_locked20260318.ipynb)。定位 `get_diffusion_operator_cpu`、`getDiffusionComponents_cpu`，cell id 5、10、12、13、15。活动调用计算 20 分量，输出六列非平凡分量并对首列取负形成 `progenitor_DC`。

前次本地文件为明确摘录，不冒充完整上游源码或运行结果。

### C4｜通用聚合与 KNN helper

[neighborhood_utils.py](https://github.com/dpeerlab/p53-niche-dynamics/blob/a97d1a42cede4c12416875a4aa50d3d63ee1fffd/utils/neighborhood_utils.py)。平均函数 [L32–L44](https://github.com/dpeerlab/p53-niche-dynamics/blob/a97d1a42cede4c12416875a4aa50d3d63ee1fffd/utils/neighborhood_utils.py#L32-L44)；KNN 包装 [L113–L120](https://github.com/dpeerlab/p53-niche-dynamics/blob/a97d1a42cede4c12416875a4aa50d3d63ee1fffd/utils/neighborhood_utils.py#L113-L120)。本次重新读取后者范围。

helper 的接口风险不等于 Step03 半径主路径有同样问题。聚合函数的输入 X 含义仍须追踪调用端。

### C5｜完整 ATAC 初始脚本

[ArchR step00](https://github.com/dpeerlab/p53-niche-dynamics/blob/a97d1a42cede4c12416875a4aa50d3d63ee1fffd/multiome_Fig7_FigS6/notebooks/ATAC_processing/multiome_ATAC_step00_archR_preprocessing_locked20260318.R)。已完整读取，前次保存文件本次重新计算 Git blob 为 `3566525265b91759ee172a6325b039a916abfda6`。

显式导入阈值不等于最终 QC。`custom_QC` 交接表与下游过滤过程未完整恢复。

## N1–N8｜导航但未完成活动实现审计

精确路径和核验深度见 [code_manifest.tsv](code_manifest.tsv)。覆盖形态、Figure 2/3 和 Figure 3/5 生成、Milo、半径稳健性、p53 状态匹配、Calligraphy、human TMA 和后续 multiome。

其中 `Injury_shp53_GenerateFigure_Fig7_FigS6_locked20260204.ipynb` 连接器返回正文为空，raw 路径尝试也失败；本次容器全量抓取尝试因 DNS 失败。故继续保留“仅定位/未完整审读”，不能因为路径存在就补齐其参数。

## U1–U3｜本会话提供的整理输入

| 文件 | 字节数 | SHA-256 |
|---|---:|---|
| `reconstruct-bioinfo-protocol-pr630-4bdc4d0.zip` | 156829 | `66d407b3a8ea7cf3c30e5f5df4ccff143b6b54497588e67426d2fe543306483f` |
| `Reyes2026_p53_niche_论文详解与复现审计.zip` | 271336 | `25b6c2da8b9a0e4c264c0880d9048ac321514cfb3b46b5e73c648d83bd4d8067` |
| `Reyes2026_论文详细解读.md` | 40110 | `4547a96ad0c0499a63a28d0c996593e512b5388c2da7b7feee200537bbc52ae2` |

本次重新计算上述指纹。用户工作流用于保持证据分类和复现状态边界；没有将其全部验证器成功运行在本目录上。前次包的通过记录只属于前次包，不能转移为本次扩展内容的正式协议验证结论。

## 归档与许可边界

作者代码使用 MIT 许可；相关短源码引用通过固定位置追溯，许可文本保存在 [UPSTREAM_LICENSE](../code/UPSTREAM_LICENSE)。本稿不复制整篇论文、受限材料、大数据或 Notebook 内的大量原图输出，也不上传用户原始 Xenium 数据。

新增代码身份为“本稿新编”。唯一实际科学相关计算是对人工构造数值的代数/输入单元测试，不涉及作者数据或用户数据。其身份、命令和哈希见 [validation_report.json](validation_report.json)。
