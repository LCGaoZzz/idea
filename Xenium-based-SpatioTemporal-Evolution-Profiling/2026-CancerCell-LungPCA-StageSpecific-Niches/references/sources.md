# 来源索引与证据定位

[返回入口](../README.md) · [资料边界](../docs/09_limitations_and_open_questions.md)

核对/整理日期：2026-09-11。此索引给读者可追踪入口，不代表全部附件已经下载或生物学结果已经复算。文章事实以原文为准；此前生成的阅读报告是工作材料，不作为独立于原文的第二份科学证据。

## 核心文献

**Peng et al.** Multimodal spatial-omics reveal co-evolution of alveolar progenitors and proinflammatory niches in progression of lung precursor lesions. *Cancer Cell* 44(2):321–339.e13. [DOI 10.1016/j.ccell.2025.10.004](https://doi.org/10.1016/j.ccell.2025.10.004)。[PubMed PMID41202811](https://pubmed.ncbi.nlm.nih.gov/41202811/)；[PMC12980502](https://pmc.ncbi.nlm.nih.gov/articles/PMC12980502/)；[Cell出版页](https://www.cell.com/cancer-cell/fulltext/S1535-6108(25)00445-3)。在线日期2025-11-06，卷期日期2026-02-09。

本次使用可检索的正文、Methods和图注原文；直接访问PMC在部分请求触发验证。没有将检索片段等同为完整PDF捕获，也未逐页检视全部补充图。原文数字属于作者报告。

## 论文问题与检索定位

| 文档中的事实类别 | 图/方法定位 | 用途与边界 |
|---|---|---|
| 队列、样本数、配对方式 | Fig.1A；Fig.5G–H；Patient samples | 区分patient、lesion、sample、cell、core |
| 空间图谱与病理表达 | Fig.1；Visium数据生成/分析方法段 | 观测与预测表达分开 |
| 推断克隆架构 | Fig.2；SpatialInferCNV方法段；Discussion | RNA推断与DNA真值分开 |
| 上皮状态与表达程序 | Fig.3；snRNA分析、MP identification方法段 | 多套MP编号不直接对应 |
| 程序/环境与受体 | Fig.4；通路及cell–cell interaction方法段 | 相关、候选信号与真实通量分开 |
| 细胞级与独立TMA空间关系 | Fig.5；Xenium generation/analysis；邻域分析段 | 半径80 μm，统计层级仍需对象 |
| 小鼠与培养读出 | Fig.6；类器官培养方法段 | 支持培养条件、体外标签、>100 μm阈值、每点一孔 |
| 上皮受体条件性删除 | 正文对Fig.S8G–I的报告；Animal models | 不是KAC特异删除；补充图未全量视觉核验 |
| 抗体干预与情境差异 | Fig.7；正文对Fig.S8J的报告；Animal models | 不自动分离阶段与模型差异 |
| 独立性与多重检验 | 各图图注；Quantification and statistical analysis | 总体BH声明不等于每图family已核实 |

## 代码固定版本

[作者仓库固定提交](https://github.com/FuduanPeng/LungPCA_Code/tree/fba87dbee8dbae497b15b81a4b0fa79edccd17b2)；[提交记录](https://github.com/FuduanPeng/LungPCA_Code/commit/fba87dbee8dbae497b15b81a4b0fa79edccd17b2)。固定SHA：`fba87dbee8dbae497b15b81a4b0fa79edccd17b2`。

7个R、6个Python、1个README的原路径与Git blob SHA-1见[code_inventory.tsv](code_inventory.tsv)。路径/函数优先于不可靠的记忆行号；已精确恢复的位置包括Figure 3.R L28–40、Figure 5.R Fig.5E约L63–77、Figure 6E 6F 7D.py L55–77。行号仅适用于固定版本。

本包不重新分发全部作者源码或受限Data，避免将公开可读误当成任意再许可。读者可沿固定链接取得原文件；原代码归原作者，遵循其许可与数据使用条件。当前仓库树未见LICENSE不表示可以自行添加授权。

## 归档与数据

| 标识 | 官方入口 | 已知用途/状态 |
|---|---|---|
| Zenodo17172149 | [记录](https://zenodo.org/records/17172149) | 论文列出的归档；本次记录页可读、文件Restricted |
| Zenodo17148540 | [记录](https://zenodo.org/records/17148540) | README列出的processed data；与前者关系未知 |
| Zenodo15670280 | [记录](https://zenodo.org/records/15670280) | 论文列出的处理后人类数据；本次未取得完整文件清单 |
| GSE307534 | [GEO](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE307534) · [PRJNA1321930](https://www.ncbi.nlm.nih.gov/bioproject/1321930) | 人类Visium；矩阵未下载 |
| GSE308103 | [GEO](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE308103) · [PRJNA1328749](https://www.ncbi.nlm.nih.gov/bioproject/1328749) | 人类snRNA；矩阵未下载 |
| GSE307529 | [GEO](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE307529) · [PRJNA1321929](https://www.ncbi.nlm.nih.gov/bioproject/1321929) | 人类WES相关处理数据；未重做calling |
| GSE222901 | [GEO](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE222901) | 既有小鼠资源；复用的GSM子集需确定 |
| GSE300288 | [GEO](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE300288) | 新增小鼠scRNA；逐GSM映射未重建 |
| GSE300293 | [GEO](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE300293) | 新增小鼠空间转录组；未下载矩阵 |

人类原始可识别序列公开限制据此前官方BioProject核对记录保留；本次未因元数据存在而声称取得原始数据。资源权限可能改变，实际获取时重新核对。

## 实现语义的官方来源

[Matplotlib hexbin API](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.hexbin.html)：用于核查C值默认mean聚合，不是原文最终参数的替代来源。该默认行为是否触发类别混合风险还取决于作者对象与几何，未执行验证。

## 本次整理流程材料

用户指定`reconstruct-bioinfo-protocol-pr630-4bdc4d0.zip`；本包沿用其来源追踪、输入/输出/参数分离与不夸大执行状态的要求，并整合此前阅读报告与后续研究逻辑讨论。这里是研究idea出版目录，不声称所有文件符合原skill机器schema，也不声称重新通过原validator。新的元数据工具及其合成测试单列在code/和validation/。
