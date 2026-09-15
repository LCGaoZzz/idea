# 预处理、表达验证与细胞类型回填：最终检索补全

本文为方法文字的重建，不是对作者源码的审读。[P01；F032、F041–F046]

## 已核实的步骤

单细胞空间 RNA 平台分别进行预处理与主要类型注释，不把不同面板直接混成统一表达矩阵。最初排除每细胞 feature counts 少于 20 的低质量细胞。这里保留原文的变量语义：未拿到 QC 表和代码，不能擅自认定这是 UMI<20 还是 nFeature<20。

初始分析报告 Seurat v4.3.1、SCTransform 归一化、把全部基因作为 PCA 特征，随后 FindNeighbors 与 FindClusters（resolution=0.5）。这和用于**空间邻域**分型的 NMF rank=5、Leiden resolution=0.1 是两套流程。

作者在针对基质区室进行批次校正前，识别并排除了上皮/肿瘤细胞。按样本分批，报告采用 RPCA 整合：SplitObject → NormalizeData → SelectIntegrationFeatures → ScaleData → RunPCA → FindIntegrationAnchors → IntegrateData。整合后还有 ScaleData → RunPCA → FindNeighbors → FindClusters（0.5）、UMAP 和标记注释。低 feature 均值的簇（每细胞平均少于100）及缺乏谱系定义标记的簇被剔除。DEG 使用 FindAllMarkers。

**不要推导成“肿瘤细胞从整个空间分析删掉了”。** 肿瘤邻居正是 s1 定义的关键组成。基质表达整合前的区室排除，不等于邻域组成矩阵排除 epithelial/tumor。这两个集合在实现中必须分别命名，并核对回填后的细胞总表。

## 当前仍不能唯一确定的实现

SCTransform 和后续 NormalizeData 在不同阶段都被报告；没有对象和真实调用，不能指定每个阶段的 assay/slot，更不能断言作者把 SCT residual 与 RNA count 错用。应索取每次 DefaultAssay、assay/slot 参数、整合前后细胞 ID 及肿瘤标签回填规则。

RPCA 的 PCA 维度、integration features 数、anchor 选择参数、reference 选择、最终图近邻数和随机种子未核实。方法明确称 RPCA；不能改写成 Harmony。FindAllMarkers 的函数名不等于已知采用何种检验、阈值和患者内依赖处理；不使用当前默认参数替代原始调用。

原文的首次 cell-level 20 阈值与之后 cluster-level 平均100阈值，作用单位不同，不应合并为“所有细胞至少100基因”。细胞数与平均基因数只作为作者报告值记录；本次没有从矩阵复算。

## 对表达验证的影响

空间标签由邻域组成定义；CAF 自身表达可提供另一维度证据，但表达检验仍需患者/样本层独立重复。若在整合 assay 上做差异表达，需核实所用数据能否支持该检验；目前不能在代码缺席时指控其确实如此。更稳健的新方案是将整合用于表示/注释，把患者层表达汇总和相应统计模型用于跨样本验证；这是建议而非作者已执行的步骤。

## Xenium 肿瘤状态证据链的补充

Results 报告 Ovarian xe1 的三种肿瘤状态。state1 的例示基因包括 CD47、CD44、CCL28、NT5E；state2 包括 TERT、ALK、SESN3；state3 包括 S1PR3、TMEM100。[F047；Fig5E] 这只是作者对差异表达的报道，不是本包复算，也不等同于功能激活测定。

按接近 s1 的区域划分，作者报告 state1 的占比为61.4%对15.4%；跨四张组织切片的基因重叠，三张共有55个、四张共有7个上调基因。[F048–F049；Fig5F–G] 不能将切片交集当作已经控制患者、癌种和检测能力的元分析；近远阈值、基因全集、DEG筛选规则与完整Table S6仍需获取。

作者在该卵巢癌例子中报告 THBS1–CD47 的推断通信概率较高。[F050；Fig5H] 模型输出可引导验证优先级，却不是测得的配体流量、结合强度或免疫抑制效应大小。应比较相同肿瘤状态与几何条件下的近远区域，以减少“肿瘤状态选择性分布”替代“CAF诱导”的解释。

## 本次修订的边界

早期检索只返回后半段预处理，故本次最终核对主动更新 F041–F050 和 A02/A07/A14/A19/A26。修订后已报告的参数不再标成未知；未知项收窄到对象语义和活动实现。检索漏掉一段不代表作者没有报告它。
