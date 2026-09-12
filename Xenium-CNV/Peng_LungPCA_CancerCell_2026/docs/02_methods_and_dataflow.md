# 02｜方法与数据流：从测量对象到结论，而不是从软件名到软件名

[返回入口](../README.md) · [上一章](01_story_and_design.md) · [下一章：CNV 辨识](03_cnv_and_identifiability.md)

主来源：[论文][P]、[PMC][M]、[固定代码][C]。本章的参数是作者报告或代码显式使用的参数；没有取得完整上游代码的模块不补写为可执行原始流程。参数身份详见 [登记表](../evidence/parameters.tsv)。

## 1. 首先区分五层对象

```text
原始测量：图像、reads、counts、质心／边界
    ↓ 原始预处理与QC
分析对象：Seurat／AnnData、病理区域、参考注释
    ↓ 模型拟合与规则选择
推断结果：CNA、clone、MP、pseudotime、communication
    ↓ 汇总与统计
绘图输入：比例表、相关表、预计算RDS／RDA／pickle
    ↓ 绘制与人工排版
图、正文数值与生物学解释
```

**[I]** 读到了最后两层，不等于恢复了前三层。尤其是一个 pickle 同时包含原始表达和预计算通信结果时，重新画流线不能证明通信推断可以从头复算。软件包可用、脚本可解析、图像能输出，分别只是工程层面的不同条件。

## 2. 模态分工与主输入输出

| 模块 | 输入与测量单位 | 作者使用的主要步骤 [P] | 关键输出 | 本次可核验到的层级 |
|---|---|---|---|---|
| Visium | counts、H&E、spot／切片／患者 | 病理注释、QC、SCTransform、聚类、iStar | 病理位置和表达结构 | Methods + 下游绘图代码 |
| RNA-CNA | 患者内空间上皮表达、参考 | SpatialInferCNV、参考迭代、手工子树选择 | 推断 CNA、clone、共享类别 | Methods + 预计算树／矩阵展示 |
| WES | 病灶和正常 DNA reads | 比对、体细胞变异筛选 | 样本级变异支持 | Methods，未取得 FASTQ／VCF |
| snRNA | 核表达、样本信息 | QC、Scrublet、Harmony、注释、NMF、轨迹 | KAC 等状态、MP、拟时序 | Methods + 已保存对象绘图 |
| Xenium | 定向面板转录本、细胞分割、质心、图像 | QC、注释、配准、80 μm 邻域 | 细胞状态和局部组成 | Methods + 下游表和 Explorer 展示 |
| 通信 | 表达、类型、位置、LR 数据库 | 不同模块分别使用 CellChat／CytoSignal／COMMOT | 候选相互作用和方向摘要 | 有些脚本只画图，COMMOT 脚本确实再算方向摘要 |
| 扰动实验 | 小鼠、培养体系、药物或遗传操作 | 比较病变与细胞／类器官终点 | 背景限定的功能证据 | 正文、Methods、图注；无原始终点表重算 |

出处：Fig.1A、2–7；STAR Methods 对应小节。**Xenium 并不是本文的突变探针或直接 DNA 克隆测量模块。**

## 3. Visium：病理、混合和预测分辨率

### 3.1 作者报告的流程

**[P]** 作者使用 SCTransform、3,000 个高变基因、前 30 个主成分、FindNeighbors／FindClusters，报告 resolution 0.8；有患者内的处理与病理对应。定位：Visium 数据分析方法、Fig.1、S1。关于 nUMI 500、nFeature 200、线粒体 15% 的 QC 文字，其布尔组合在可获得文本中不够清楚；本目录不擅自生成 AND／OR 过滤表达式。

**[C]** `Figure 1.R` 直接读取 `Figure 1B.rda`、`Figure 1C.downsample_25_percent.rds`、`Figure 1D.rds`。这不是创建 Seurat 对象、执行 QC 或聚类的脚本。`Figure 1E 4F.py::plot_super` 给已保存基因矩阵着色，没有调用 iStar 训练／推理。

### 3.2 必须恢复而当前未恢复的对象

患者、切片和病理标签映射；QC 前后细胞／spot ID；counts 与 SCT 数据的具体使用位置；iStar 所用图像和分辨率；组织有效掩膜；原始与变换后的坐标系；各分析的随机数种子与人工调整。

**[I]** 一个 spot 可同时包含多个细胞。若相邻正常与肿瘤混合比例改变，表达推断 CNA 也会改变。iStar superpixel 是预测后的细分，不是增加了同样数量的独立组织测量；不能拿 superpixel 数代替独立 spot 或患者数。

## 4. SpatialInferCNV：模型之外的人工选择同样是方法

**[P]** Methods 的空间拷贝数分析先作 reference-free 推断，以较低 CNA 且与正常肺泡病理一致的区域迭代选择参考，再进行最终分析。明确参数为 `cutoff=0.1`、`cluster_by_groups=TRUE`、`HMM=TRUE`、`denoise=TRUE`。作者使用 `SelectingSubTreeData` 手工挑选树的祖先节点，并把后代 spots 归入克隆。出处：Fig.2、Methods：Analysis of spatial copy number alterations。

**[P]** 病灶特异类别的文字规则为：对侧病变少于 25 个 spots，且本侧占该克隆超过 95%；反向对称；其余归为 shared。这是观测后的分类，不是模型直接测得的真谱系。严格不等号、零计数处理及取样效应见 [第3章](03_cnv_and_identifiability.md)。

**[C]** `Figure 2.R` 的 `# Figure 2C` 加载 `PhyloTree` 和 `plot_mat` 后绘图；`Figure 2C.py` 读取已有 `Clone` 字段。没有看到该仓库实现从 counts 到 inferCNV、手工节点或完整树构建的上游过程。

**[I]** 恢复这条链至少需要最终参考细胞集合、每次迭代原因、基因位置表、输入 assay／slot、最终树及选定节点、spot 克隆表、低置信度处理和所有版本。仅知道四个显式参数不足以复算。不能自行加入“作者用某种距离／建树算法／根节点”而无来源。

## 5. WES：重要旁证，但不是同一细胞的真值

**[P]** 作者报告 WES 比对到 hg38，并采用 BWA、GATK／Mutect2 等处理和多个读段、VAF、群体频率与注释过滤，具体见 Methods 的 WES 分析段。Fig.2D 和 Fig.S2B 将变异／CNA 结果与空间克隆结构比较。

**[I]** 即使 WES 与 RNA-CNA 在一个病灶上相容，也只是在对应分辨率上的旁证。WES 组织体积、Visium 切面和 Xenium 细胞可能不完全相同；不能把患者级／样本级突变平均赋给每个细胞。阴性 VCF 需要考虑深度、纯度和过滤，不是所有细胞均无突变。

本次未下载 reads、BAM、VCF 或完整捕获区域文件，也没有执行比对与变异调用。本目录不将 Methods 罗列的软件自动展开为一条已验证命令。

## 6. snRNA：状态定义、批次与轨迹

**[P]** 作者采用核级 QC、**Scrublet** 双细胞筛查、降维及 Harmony 整合；既有审读恢复的主要阈值为基因数低于 500、读数低于 1,000、线粒体比例达到 20% 的排除，以及 3,000 高变基因和 50 个 PC。完整过滤顺序、所有子集阈值、种子和实际 assay 未由公开上游代码复核；这些参数不应被解释成足够的执行合同。出处：snRNA-seq data analysis、Fig.3。早期整理中的 DoubletFinder 记述已纠正，不再沿用。

**[C]** `Figure 3.R` 从 `monocle3_obj` 读取保存好的 `Pseudotime` 和 `CytoTRACE`，调用 `plot_cells`。没有执行 root 选择、轨迹图学习或 CytoTRACE 计算。

**[I]** 根节点、起始状态定义和纳入细胞影响方向；实际采样时间与算法排序需要分列。用注释定义根、再把轨迹方向当作注释正确性的独立证明，会形成循环。整合改善批次并不自动保证生物信号未被过度消除；未整合也不因“遗传背景相近”而自然没有技术批次。

## 7. NMF／meta-program：多套词典与不同分数

**[P]** Visium 与 snRNA 使用不同 NMF 范围。既有 Methods 审读恢复：Visium 在样本内考察 rank 2–18，程序取前 50 基因，涉及 35 个基因重叠和跨样本筛选；snRNA 在患者内考察 rank 2–11，进行中心化后将负值置零，并有另一套程序稳定性／合并规则。Visium 全组织最终 11 个 MP；上皮 snRNA 最终 9 个 MP。定位：Methods 的 NMF／meta-program analysis、Fig.3E–G、4B。

**[I]** rank 2–18 产生的候选列数总和为 170，2–11 为 65，这只是候选分解列数的算术，不是 170／65 个真实独立生物过程。涉及 10%、20% 的跨样本重叠规则在不同步骤有不同角色，当前缺完整上游实现；不要仅凭阈值数字自行串成最终筛选程序。

**[P/C]** 作者使用 GSVA／AddModuleScore 等完成不同层级映射；实际 Figure 3／4 代码展示的是已计算 `MP_mat`、比例和相关矩阵。`Figure 3K 3N.py` 与 `Figure 4G.py` 对 `stacked_MPs` 取最大值并着色，不拟合 NMF。

**[I]** 必须保存每套 MP 的基因列表、背景基因集、计算对象、score 方法、归一化和命名空间。不能把 Visium MP5、上皮 MP5、髓系 MP5 当成同一个对象，也不能把不同评分体系的最大值比较当成概率比较。数学与不确定性见下一章及统计章。

## 8. Xenium：面板、配准、注释和邻域是四个不同环节

### 8.1 面板和 QC

**[P]** 发现队列为 Human 5K Prime 加 100 定制基因；独立验证为 298 基因肺面板加另一套 100 定制基因。作者报告发现队列以低于 30 的基因检测阈值过滤；TMA 则排除 UMI 少于 20 或基因少于 10 的细胞。出处：Xenium data analysis、Fig.5。不能把“基因数 30”写成“UMI 30”。

**[P]** 注释使用 SCTransform、由 ElbowPlot 等确定维度，在主要细胞谱系内处理，并按 slide 使用 Harmony。没有一个由公开活动代码支持的“所有数据统一固定 PC 数”；不要补成 30 或 50。

**[I]** 跨面板验证首先要检查可测基因交集。面板没测到的基因是结构性缺失，不是生物学零表达。注释一致并不意味着全部功能分数可直接比较。不能把 C15、C16 与验证 C4 的编号当作一对一细胞身份。

### 8.2 组织图像与病理区域

**[P]** 作者使用 QuPath 0.5.1、OME-TIFF、Xenium Explorer，配准时使用至少 30 对手工 landmarks，并以病理多边形关联细胞条码。出处：Histopathological processing / Xenium histology alignment。

**[I]** 原始图像、landmarks、变换矩阵、掩膜和多边形都是复现输入。二维相邻切片并非完全相同细胞；配准误差可能在边界附近造成错误归属。不要因图像叠得整齐就认为配准不确定性为零。

### 8.3 中心细胞邻域

**[P]** Methods 明确按细胞质心，以 **80 μm 半径**逐中心构建邻域。Fig.5D–E、5J–K 比较不同中心状态附近组成和目标巨噬细胞。

**[C]** `Figure 5.R` 读取 `neighborhood_cell_prop`、`Myeloid_C15`、`Mac_C4_IL1B` 等预计算列，没有构建坐标索引或半径图。

**[I]** 仍需知道中心是否计入自身、切片／core 是否严格隔离、边缘截断如何处理、零邻居如何表示、先汇总再比率还是先比率再平均、每个患者的权重。未知不能填为作者参数。本项目新增脚本要求显式 self policy、空间域和半径，不把默认值伪装成原文复原。

## 9. 通信：别把三个包、三种输出混为一种证据

**[P]** 论文不同部分使用 CellChat、CytoSignal 和 COMMOT。Fig.4E 为相应空间信号可视化；Fig.6G 为小鼠空间通信方向展示。论文 COMMOT 方法文字出现数据库 `Cell-Cell Contact` 筛选，而主要展示 IL1；本次没有获得生成对象与确切数据库子集，无法消解这一对应关系，不能默默替作者改成另一类别。

**[C]** `Figure 4.R` 载入 CytoSignal 对象，用 `plotEdge(...,slot.use='GauEps-Raw')` 展示。`Figure 6G.py` 则在保存对象上确实调用 `ct.tl.communication_direction(...,pathway_name='IL1',k=5)`，随后流线绘图，并使用 `normalize_v=True`、`normalize_v_quantile=0.995`。前者不是完整重算，后者也不是从原始数据开始完成全部最优传输／LR 分数。

**[I]** k=5 是该方向摘要函数的活动参数，不是 80 μm 邻域参数；显示归一化也不是生物信号强度归一化的真值。距离截断、数据库版本、表达层和通路集合未知时，不能把“其余默认”变成版本无关的确定方法。

## 10. 实验终点与统计层级

**[P]** 类器官统计直径大于 100 μm 的数量和大小；其培养背景包含支持性细胞与生长条件。基因扰动采用 CCSP-Cre／Kras／Il1r1 相关遗传模型；药理实验有 IgG、抗 IL-1β、抗 PD-1 和联合组。出处：Fig.6H–K、7、S8G–J，Animal models／Organoids／治疗方法。

**[I]** 孔、类器官、core 与小鼠的层级必须保留。数量可因越过阈值而增加；比例可因分母变化而减少。多个孔来自同一个供体时，孔不是新的供体。遗传操作覆盖范围必须与细胞特异因果语言一致。详细统计见 [第4章](04_statistics_and_measurement.md)。

## 11. 可复算合同与停止条件

**[T]** 在获得材料后，先恢复 `patient/animal → sample → section/core → cell/spot` 的映射，再为每个图列：输入文件校验值、表结构、参数来源、版本、种子、人工操作、输出和统计单位。优先复算一个有明确输入的小面板，然后逐层回溯上游，不从最后 PNG 看起来相似就宣布成功。

遇到以下情况应停止强结论：关键 Data 对象缺失；最终参考／手工节点未知；阶段与批次完全重合；坐标域混合；只有细胞级 p 值而独立宿主不足；面板无法测量候选机制；补充图数字与表无法勾稽。停止的是相应结论，而不是整项研究。

[P]: https://doi.org/10.1016/j.ccell.2025.10.004
[M]: https://pmc.ncbi.nlm.nih.gov/articles/PMC12980502/
[C]: https://github.com/FuduanPeng/LungPCA_Code/tree/fba87dbee8dbae497b15b81a4b0fa79edccd17b2
