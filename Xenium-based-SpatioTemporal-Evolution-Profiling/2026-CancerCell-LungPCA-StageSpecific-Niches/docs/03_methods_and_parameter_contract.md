# 03｜方法与参数：从测量到图的完整对象链

[返回入口](../README.md) · [上一章](02_design_and_evidence_chain.md) · [下一章：逐图代码映射](04_figure_to_code_map.md)

> 【P】为 Methods 或图注报告；【C】为固定代码中活动调用；【H】为本整理建议。没有运行作者分析。未知参数保留未知，禁止把包的默认值变成“论文最终参数”。精确方法小节以 [PMC 作者稿 STAR Methods](https://pmc.ncbi.nlm.nih.gov/articles/PMC12980502/) 为检索入口；全文PDF与补充工作簿未完整取得。

## 1. 不能省略的五层对象

```text
读段/成像原始输出
  → 计数、坐标、分割、组织图像
  → QC/注释后对象与病理区域
  → CNA、程序、拟时序、邻域、通信结果
  → 制图表、序列化图对象、PNG
```

【C】作者 GitHub 主要从倒数第二层或最后一层开始。`readRDS()`、`load()`、`pickle.load()`加载出一个已有结果，不等于重新计算它。COMMOT方向摘要、统计调用和图层阈值是少数在公开脚本中继续进行的计算。

【H】每一层登记物种、基因命名、参考版本、sample/animal/section/core、矩阵方向、assay/layer、尺度、缺失值、是否整合/插补、上游文件及校验值。原始counts、SCT残差、标准化表达和预测superpixel不是可随意互换的矩阵。

## 2. Visium 主线

【P】Methods 报告的流程包括病理标注、QC、SCTransform、3,000高变基因、邻居图及resolution=0.8的聚类，随后区域表达和克隆/程序分析。QC文字涉及nUMI 500、nFeature 200及线粒体15%；原文过滤连接词不能未经代码确认就改成布尔AND或OR。[定位：Visium数据分析方法、Fig.1](https://pmc.ncbi.nlm.nih.gov/articles/PMC12980502/)

【C】`Figure 1.R`使用已有Seurat对象与表；没有显示上述QC和聚类实现。`Figure 1E 4F.py::plot_super`读取已保存的表达矩阵与mask并着色，不训练或调用iStar推理。[代码](https://github.com/FuduanPeng/LungPCA_Code/tree/fba87dbee8dbae497b15b81a4b0fa79edccd17b2)

【H】重建至少需要spot—病理表、每切片QC前后数量、assay说明、图像变换、降维参数和原始输入矩阵。iStar提高的是模型预测的空间细节，不能把更多superpixel计作更多独立测量。预测图与细胞实测应有不同证据标签。

## 3. 人类 snRNA-seq 与上皮子集

【P】使用相邻FFPE组织的核RNA数据；方法描述双重细胞处理、混合谱系排除、SCTransform、3,000高变基因，以及相应分析中的50 PCs/Harmony。上皮子集进一步识别AT1、AT2、AIC、KAC和肿瘤等状态。[定位：snRNA-seq generation/analysis、Fig.3](https://pmc.ncbi.nlm.nih.gov/articles/PMC12980502/)

【I】核RNA与细胞RNA检测背景不同。身份基因、损伤应激、恶性状态不应由一个总分包办。移除缺乏清晰谱系标记的细胞有助于注释，却也可能系统性移除真正过渡或去分化状态；本研究是否发生这种偏差需要被排除细胞和QC清单，不能直接宣布发生。

【H】补齐DoubletFinder参数、所有排除规则、各子集分辨率、Harmony协变量、种子、DE所用矩阵及患者层检验。不要将人类snRNA参数复制给Xenium或小鼠。

## 4. NMF与meta-program：多个分解空间要分开

【P】Visium按样本做NMF，k=2…18，各程序取top50基因，跨k与跨样本筛选后形成11个全Visium共识MP。snRNA按患者做NMF，k=2…11；负的中心化表达置零，形成全部细胞及上皮子集各自的9个MP。原文还报告跨程序重合筛选条件；完整筛选顺序、初始化和全部基因集需原始实现与Table S2核对。[定位：MP identification的Visium与snRNA方法段](https://pmc.ncbi.nlm.nih.gov/articles/PMC12980502/)

| 分支 | 报告参数/行为 | 不能自动推定 |
|---|---|---|
| Visium NMF | 每样本k=2…18；top50；跨k稳健性涉及35/50重合，另涉及10%规则 | 10%规则具体筛选顺序、每次初始化、重复与停止条件 |
| snRNA NMF | 每患者k=2…11；top50；负值置零；另涉及20%重合规则 | 与Visium完全同一筛选流程 |
| snRNA上皮MP映射 | AddModuleScore、按最高分赋标签 | 分数天然跨样本绝对可比、argmax即真实离散身份 |
| 全Visium MP分析 | GSVA评分、样本比例及相关性 | 可用任一评分法替换全部图且保持同一含义 |

【I】k求和为170或65只表示候选程序个数，不等于最终独立程序数。不同分解中的MP6不是同一个对象。Fig.4G中扩展显示的myeloid程序还可能使用不同显示编号，应按基因集身份追踪，不按数字拼接。

【H】保存完整载荷、gene sets、每细胞全分数、第一与第二高分及差值，允许不确定状态。面板覆盖缺失基因标记为未测量，不补零。自定义评分与作者评分各自成支，不称为原样复现。

## 5. SpatialInferCNV与空间克隆

【P】Methods 描述无参考初探、选取低变化/正常参考、患者内重新推断；明确参数包括`cutoff=0.1, cluster_by_groups=TRUE, HMM=TRUE, denoise=TRUE`，并涉及子树/祖先节点的人工选择。[定位：SpatialInferCNV方法、Fig.2](https://pmc.ncbi.nlm.nih.gov/articles/PMC12980502/)

【C】`Figure 2.R`读取树、CNA矩阵、注释和图对象；`Figure 2C.py`使用已有`Clone`、`Pseudotime`、`CytoTRACE_Score`，没有从表达计算CNA或生成系统树。[代码：Figure 2.R / Figure 2C.py](https://github.com/FuduanPeng/LungPCA_Code/tree/fba87dbee8dbae497b15b81a4b0fa79edccd17b2)

输入合同：表达尺度、基因顺序及参考基因组、reference barcodes、患者内病灶映射。输出合同：连续CNA、HMM状态、clone标签、祖先/子树选择、最终树。缺少这些对象时只可以审读图的生成路径。

【H】特别不要把该流程未经论证套到有限Xenium面板，并将RNA推断当作DNA真值。独立DNA可约束结果，但组织WES不能认证每个spot。

## 6. 拟时序和CytoTRACE

【P】Fig.3用这些工具补充状态连续性解释。【C】`Figure 3.R` L28–40读入monocle3对象后绘制；未显示`learn_graph`、根选择或CytoTRACE上游计算。[固定代码](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%203.R#L28-L40)

【H】应恢复细胞纳入、特征、降维、批次、图学习、root依据和患者间处理。用已知早期状态人为指定根后，不能再用同一轨迹的方向证明其早期性。CytoTRACE不是真实年龄；多个表达衍生算法一致不等于多个独立测量一致。

## 7. WES：辅助来源信息，不等于空间真值

【P】WES方法描述hg38、BWA-mem、重复标记/重校准、MuTect2及后续注释过滤，使用匹配正常组织。报告测序深度与变异过滤条件需要保持正常/非正常组语义。[定位：WES generation/analysis、Fig.2D](https://pmc.ncbi.nlm.nih.gov/articles/PMC12980502/)

【C】Fig.2D代码只有预计算变异矩阵的oncoPrint，没有读段到变异的实现。【H】必须拿到样本配对表、完整caller/filter配置、深度与VAF记录，区分生殖系排除、低频检测能力与真正阴性。本整理不把总体方法里的“default”扩展成一个已核验的完整运行环境。

## 8. Xenium：面板、配准与筛选改变能看到的世界

【P】发现队列为5K Prime加100基因；验证为298-gene lung panel加100基因，两套add-on分别设计。H&E经QuPath 0.5.1转为OME.TIFF，Explorer 3.2.0或更高版本进行图像配准，方法报告至少30组对应关键点，并人工勾画病灶/RPII区域提取barcodes。[定位：Xenium data generation](https://pmc.ncbi.nlm.nih.gov/articles/PMC12980502/)

【P】5K分析报告gene count<30排除及缺乏典型谱系特征的细胞排除；TMA为UMI<20或gene count<10排除，随后标准化和分层注释。这里保留原文gene count表述，未核查字段前不将其改写为UMI。[定位：Xenium data analysis](https://pmc.ncbi.nlm.nih.gov/articles/PMC12980502/)

【H】需保存原图、变换/控制点、边界、质心、转录本坐标、病理多边形、分割版本与排除清单。若未测某基因，应判为面板缺失而非生物阴性。用注释时同一组基因再“验证”该状态会形成循环，应另留不参与命名的响应特征。代表性UMAP下采样比例也不能被当成全部邻域分析的下采样比例。

## 9. 邻域矩阵与统计单位

【P】半径80 μm；每中心汇总邻居状态计数，再比较中心类型和病理组。Fig.5D/J为组成，Fig.5E/K涉及特定邻居分布。[定位：邻域方法段、Fig.5](https://pmc.ncbi.nlm.nih.gov/articles/PMC12980502/)

【H】为新分析明确定义：

```text
N_i(r) = 同一物理坐标域内，距离中心i不超过r的细胞集合
C_ik = N_i内状态k的数量
P_ik = C_ik / 所有保留邻居数
D_ik = C_ik / 有效组织邻域面积（仅面积确实可估时）
```

自身是否排除、距离等于r如何处理、是否跨core、mask边缘、分母包含哪些细胞，都必须显式决定；本公式不是对作者未知实现的补写。不同切片的相同数值坐标不得连边。数百万细胞不要建立稠密N×N距离矩阵，应逐坐标域使用空间索引并分块。

【H】优先样本内匹配背景，再输出每动物/患者效应。缺乏某中心类型时是无法估计该对比，不能填零。共享邻居导致中心非独立；core和病灶也不是患者。均值、密度和相对背景富集回答不同问题，应并列而非互相替代。

## 10. Ro/e、相关性与通路

【P】Ro/e为观察数除列联表独立假设下的期望数；总体统计说明涉及Kruskal–Wallis、Wilcoxon或t检验、Spearman、BH校正。[定位：Quantification and statistical analysis](https://pmc.ncbi.nlm.nih.gov/articles/PMC12980502/)

【I】Ro/e描述组成偏离，不是信号强度。MP比例受和为一的约束；相关边不等于细胞互作。总体声明BH不说明每张图的比较家族，需原始p值与完整检验表。

## 11. CytoSignal与COMMOT必须分开

【C】人类Fig.4E加载CytoSignal对象后调用`plotEdge(..., slot.use='GauEps-Raw')`；小鼠`Figure 6G.py`在预制对象上调用`communication_direction(..., database_name='cellchat', pathway_name='IL1', k=5)`，再绘流线。前者不展示上游推断，后者确实做方向摘要，但不展示完整原始通信求解。[代码](https://github.com/FuduanPeng/LungPCA_Code/tree/fba87dbee8dbae497b15b81a4b0fa79edccd17b2)

【I】`k=5`不是邻域的80 μm；流线不是被观测分子运动。`layers['counts']=X`不是原始计数的认证。旧版审计记录过Methods的`Cell-Cell Contact`筛选与IL1候选范围的疑点，当前未取得实际数据库表，列为待核实而非确定错误。

## 12. 小鼠、培养与成像读出

【P】小鼠scRNA方法涉及SCTransform、3,000高变基因及30 PCs，并说明未额外做批次调整；培养和受体删除的控制条件见第02章。Fig.6J/K每点为孔，Fig.7的细胞比例、组织core和mouse是不同层。[来源：小鼠分析方法、Fig.6–7](https://pmc.ncbi.nlm.nih.gov/articles/PMC12980502/)

【H】遗传背景相近不能逻辑上排除实验批次。应记录来源mouse、解离批次、孔、培养批次和图像区域。序列免疫荧光的分割、阳性阈值、core排除及mouse聚合需要原始图像和映射。

## 13. 参数登记的操作规则

| 参数来源 | 应写入的状态 | 禁止的行为 |
|---|---|---|
| Methods明确值 | paper_reported | 自动当成每个子分析都实际执行 |
| 固定源码活动调用 | code_explicit | 将显示参数当成推断参数 |
| 辅助函数默认值 | default_only | 没有调用证据仍写成论文参数 |
| 新方案选择 | proposed | 冒充作者设置 |
| 无法取得 | unknown | 用常用种子、维数或阈值补齐 |

版本表不是可运行锁文件。Seurat、NMF、Harmony、monocle3、GSVA等来自不同方法模块，不能把它们机械安装在一个新环境就声称恢复作者环境。种子未报告即保留null。原分析重建与更稳健的新分析必须分别记录输入、参数及输出。
