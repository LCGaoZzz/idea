# 来源、固定版本与访问范围

[返回阅读入口](../README.md)

核查／整合日期：2026-09-11。本文档既使用本会话此前的精读审计包，也复核了关键公开来源。既往对话中的失效引用标记不作为这里的证据；正文使用下列真实链接、方法小节、原文件路径与固定提交。

## 1. 论文材料

<a id="p1"></a>
### P1｜终刊公开页面

[Spatiotemporal lineage tracing reveals the dynamic spatial architecture of tumor growth and metastasis](https://www.nature.com/articles/s41588-026-02739-z)，Nature Genetics，DOI 10.1038/s41588-026-02739-z。

取得范围：公开摘要、主图标题、扩展图图注、数据／代码声明和出版信息；本次通过可检索页面内容复核。直接打开页面遇到出版商身份重定向，未取得完整订阅正文。**主图标题不等于完整图注，公开摘要不等于完整Results。**

用于支持：论文总问题和作者摘要结论、Fig.1–5的议题位置、ED1–10公开图注中的设计／对照。没有重新计算任何图的数值。

<a id="p2"></a>
### P2｜Supplementary Information / Extended Methods

[补充讨论及方法PDF](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41588-026-02739-z/MediaObjects/41588_2026_2739_MOESM1_ESM.pdf)。共23页，以下页码是PDF物理页，从1开始，不是论文印刷页。

本次及前次已读取在线解析的相关补充方法；本次复核共培养、树派生指标、邻域、LR、插补基准与跨层部分。PDF第17页的L2 plasticity公式图像本次再次核对；其他未成功查看的公式不据乱码重建。容器下载原始PDF失败，因此本目录不提供其本地原件或伪造原件哈希。

关键定位：extended discussion（第2–5页，限制集中第4页）；`Establishing lung organoid co-cultures`（第8页）；表达预处理（第8–10页）；lineage processing / phylogenetic reconstruction（第10–12页）；imputation benchmarks（第12–13页）；annotation与CNV（第14–15页）；`Cell-cell communication analysis of Slide-tags data`（第15–16页）；`Phylogenetic fitness inference`（第16–17页）；`Single-cell clonal plasticity quantification`（第17页）；高fitness邻域（第17–18页）；`Coarse-grained alignment of Slide-seq data`及转移分析（第19–20页）。以方法小节名称优先，避免解析分页边界造成误定位。

<a id="p3"></a>
### P3｜Reporting Summary

[Reporting Summary PDF](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41588-026-02739-z/MediaObjects/41588_2026_2739_MOESM2_ESM.pdf)，7页。

取得范围：在线文本；本次重新定位，部分页面截图失败。用途：软件、空间插补、实验单位和设计报告；与补充方法中Scanpy版本及同文件性别范围的差异保留为待澄清，不自行统一。没有本地原件哈希。

### Supplementary Tables｜尚未完整取得

P1列出XLSX补充表入口，包括样本metadata、模块、DE、LR与qPCR等。**本次未取得完整XLSX**，不把GitHub局部小表当作全部终刊表格，也不对缺失内容推断其不存在。

## 2. 代码仓库与快照

<a id="r1"></a>
### R1｜README

[固定版本README](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/README.md)。其链接仍指向bioRxiv v2，并指向处理数据归档；这要求检查终刊一致性，不等于证明仓库所有内容只对应旧版。

<a id="r2"></a>
### R2｜固定代码树

[KPSpatial-release固定提交](https://github.com/mattjones315/KPSpatial-release/tree/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00)。提交SHA：`c2fa7568ee48a9e35bbc6ecd88378c6768b23e00`；查询到的提交时间为2026-04-25。

范围：仓库目录、关键utilities及部分脚本／notebook source；没有完整clone或全部notebook逐cell审计。本目录不将该快照等同于作者终刊执行版本。

<a id="c1"></a>
### C1｜fitness函数

[`utilities/phylodynamics.py`](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/utilities/phylodynamics.py)。Git blob SHA：`81ea9209e116a59cdb1661bfef678cf803dfe597`。

`score_fitness`／`_fitness_wrapper`，L31–60为分支长度、LBI和归一化；L64–102为输入交集、分组、L87剪枝及结果合并。源码读取，不是执行。

<a id="c2"></a>
### C2｜字符矩阵和树入口

[`utilities/reconstruct.py`](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/utilities/reconstruct.py)。Git blob SHA：`a6acdbf92bc830dcd4067ba7ef2f1e763dc873ec`。

各solver函数及 `create_character_matrix`；本次重查L390–445与L495–524。UMI阈值接线、PercentUncut变量覆盖、按cellBC回收行、插补返回值解包均可在此定位。默认值与活动调用分开登记。

<a id="c3"></a>
### C3｜单状态插补

[`utilities/target_site_utilities.py`](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/utilities/target_site_utilities.py)。Git blob SHA：`c45362338234eec8534c54fe9c410c5512468a3c`。

`create_target_site_meta`定义PercentUncut；`impute_single_state`，L147–167为投票和三个返回值。完整函数此前在本会话已读。

<a id="c4"></a>
### C4｜fitness活动调用

[`reproducibility/Figure3/scripts/slidetags_fitness.py`](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/reproducibility/Figure3/scripts/slidetags_fitness.py)。Git blob SHA：`2a94e8ff969b1a5dadf36707c3fd1e2922e5e219`。

L82调用 `score_fitness(..., 'lbi', 'tumor_id', None, True)`，说明该源文件明确启用按肿瘤分组和分支长度推断，但不是终刊运行日志。

<a id="c5"></a>
### C5｜邻域汇总

[`reproducibility/Figure3/scripts/score_neighborhood_abundances.py`](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/reproducibility/Figure3/scripts/score_neighborhood_abundances.py)。Git blob SHA：`2dcbde8fbf3f769941d02f2477bef6c5a3364db0`。

源码此前已读：`RADIUS=28`、字面HOMEDIR路径、tab读入及邻域汇总。坐标单位与中间文件尚未取得。

<a id="c6"></a>
### C6｜共识模块评分

[`reproducibility/Figure2/scripts/score_consensus_hotspot.py`](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/reproducibility/Figure2/scripts/score_consensus_hotspot.py)。Git blob SHA：`f4b9891b5920141545c38d158a15531a233471e2`。

此前已读源代码：按样本处理、基因选择和 `score_genes`，使用空格写出评分文件。它不独自提供最初模块发现过程。

<a id="c7"></a>
### C7｜通用DE

[`utilities/differential_expression.py`](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/utilities/differential_expression.py)。Git blob SHA：`103460a4eff3e5cd1f986a06575ccb513ec789a3`。

此前已读 `differential_expression`：AnnData.raw再次处理、默认Wilcoxon、表达比例和分类指标计算。未确认该helper生成了哪个终刊panel。

<a id="c8"></a>
### C8｜qPCR绘图notebook

[`reproducibility/Figure4/plot_qpcr.ipynb`](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/reproducibility/Figure4/plot_qpcr.ipynb)。Git blob SHA：`feedf1cc6929942246ee6a6ebd2d6ee7afaf6607`。

本会话已读数据读取、列选择与热图source。选择列的cell id为 `8ccaef73-353a-465e-afd2-3cdda91e321b`；绘图cell id为 `86138f88-8f08-4ba7-9eb0-6e26b7e9cdc9`。第四列数据名与xtick分母文字不同。没有执行notebook，不把其保存输出当作本次结果。

<a id="c9"></a>
### C9｜GitHub qPCR小表

[`reproducibility/Figure4/data/kpspatial_hypoxia_qpcr.txt`](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/reproducibility/Figure4/data/kpspatial_hypoxia_qpcr.txt)。Git blob SHA：`c865ef92b25832d7e1abe61a47c2c964b99b2c3d`。

此前已取得完整返回文本，包括编号列和fold-change列。仅据列编号不能确定生物学重复；不等于终刊全部补充表、原始Cq或终点细胞处理链已取得。

<a id="cass"></a>
### CASS｜Cassiopeia官方项目

[官方仓库](https://github.com/YosefLab/Cassiopeia)；[CassiopeiaTree API](https://cassiopeia-lineage.readthedocs.io/en/latest/api/reference/cassiopeia.data.CassiopeiaTree.html)。

README与当前API用于理解模块、可选依赖及删除叶子方法语义；不是本文冻结的运行环境。补充材料中的版本声明单列，不用当前master替代。论文表示代码采用MIT许可；本目录不重新分发完整上游源码。

## 3. 数据与归档

<a id="d1"></a>
### D1｜完整公开阵列metadata

[上游 `data/puck_meta.txt`](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/data/puck_meta.txt)；[本目录字节副本](puck_meta.txt)。

Git blob SHA `75b5f677202c1655fba4a7281df9cdd82261d403`；2043字节；SHA256 `f7aa374c7ead061592e4276bd827f54951da598a55b58915a00bb75f6e8e1e09`。保留原始换行，GitHub上传blob再次返回同一SHA。用途仅为该文件计数，不是对全部实验取样的普查。

### D2｜处理数据

[Zenodo记录19771805](https://zenodo.org/records/19771805)，由论文和README声明。大型处理归档未下载，未核实全部内部对象，不声称已有运行输入。

### D3｜论文代码归档DOI

[10.5281/zenodo.21263890](https://doi.org/10.5281/zenodo.21263890)。论文列出的代码归档链接。具体版本映射与归档字节尚未闭合；不默认与GitHub快照相同。

### D4｜此前检索到的版本线索

[Zenodo记录21263891](https://zenodo.org/records/21263891)。仅作为前次记录中的版本线索；未取得归档内容，未与D3建立已验证的完整版本关系。不能将此线索当成已下载的终刊代码。

### D5｜原始数据入口

[BioProject PRJNA1381728](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1381728)。来源为论文数据可用性声明，未核实全部样本表或下载reads。

### 外部验证数据入口

P1还列出KP-Tracer旧数据Zenodo 5847462、PBMA数据OMIX007088，以及人NSCLC空间数据E-MTAB-13530、GSE307534。它们在本目录是论文报告的入口线索，不是已下载、已整合或已重算的验证队列。

## 4. 本次整合的上游工作材料

用户指定 `reconstruct-bioinfo-protocol-pr630-4bdc4d0.zip` 工作流；此前生成 `KPSpatial_NatGenet_2026_论文精读与复现审计.zip`、`ARTICLE_GUIDE_zh.md`及后续启发讨论。本次保留完整103条参数登记，并将故事、方法、四条启发、代码与项目路线重新组织为可阅读文档。

旧包中的“未取得qPCR小表”在后续source阅读后不再适用，因此此处更新为“已读GitHub小表、未取得完整终刊补充表及重复/终点链”。旧包验证器成功不继承为新文档树的原工作流验证成功；实际检查见[receipt](../validation/receipt.json)。

## 5. 引用、许可与缺口规则

链接用于回查原作者材料；所有解释与迁移建议由本整理提出。公开代码的明确错误不等于整篇论文错误；没有取得的材料不能推断为作者未做。每条分析目前的缺口见[traceability](../reproducibility/traceability.tsv)。

本目录没有付费正文、原论文图、PDF原件、大型表达矩阵或归档源码；不对第三方材料重新授予许可。公共metadata保留作者路径与固定版本。新写检查脚本不是作者实现，不得引用为本文原始分析代码。
