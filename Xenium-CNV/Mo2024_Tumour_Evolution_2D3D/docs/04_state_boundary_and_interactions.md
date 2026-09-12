# 04｜转录状态、核心—边缘、细胞来源与空间通信

[返回总目录](../README.md) · [上一章](03_cnv_and_variant_protocol.md) · [下一章](05_3d_and_multimodal_protocol.md)

## 1. 先明确待解释的响应

【I】同一空间区域的表达量变化，至少可以由三个层面造成：参与测量的细胞类型权重改变；同一类细胞的表达状态改变；不同细胞类型对RNA总量的贡献改变。将它们压成一个module score，不能自动区分来源。

一个解释性混合模型是：

\[
X_{ig}\approx\sum_c w_{ic}\mu_{icg}+\epsilon_{ig}.
\]

其中w表示RNA信号贡献，不必等于细胞数量比例。这个模型是本目录的解释工具，不是宣称原论文采用了该生成模型进行参数估计。

## 2. 器官相关非恶性基因黑名单：解决什么，又可能删掉什么？

【P】作者合并乳腺、肾、肝、胰腺的单核参考，使用FindAllMarkers的wilcox选取非恶性类别marker；条件包括平均log2FC>2、至少一类pct expression>0.4、adjusted P<0.01。BRCA处理中，参考中的上皮类型合并，且不纳入该黑名单；其他器官使用跨器官汇总列表。依据：[Methods: Organ-specific gene blacklist for non-malignant cell types](https://www.nature.com/articles/s41586-024-08087-4#Methods)。

【I】它降低“非恶性细胞增多被误读为肿瘤内在表达”的风险，但不构成来源的完美判定。恶性细胞可以表达与间质共享的基因；参考缺失某种肿瘤状态时，这种状态可能被误删。迁移时应同时保留未过滤和过滤版本，检查结论是否完全由黑名单决定。

## 3. 微区域异质性与相关性

【P】作者以1−ROGUE表示转录异质性；对微区域间的表达相似性，比较top 250–1,500可变基因的稳定性后选择500。相关性使用Pearson，程序分析使用GSEA/Hallmark；module展示使用Seurat AddModuleScore。对应Extended Data Fig. 6–7及Methods: Microregion transcriptional profile analysis、Module score calculation。

【C】公开入口分别为：

- [Figure3/1_Heterogenity_score/script/calculate_ROGUE.R](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure3/1_Heterogenity_score/script/calculate_ROGUE.R)
- [Figure3/2_Correlation/script/1_plot_cor_heatmap.r](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure3/2_Correlation/script/1_plot_cor_heatmap.r)
- [Figure3/3_Pathway/script/GSEA_analysis.r](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure3/3_Pathway/script/GSEA_analysis.r)

这些入口本轮以路径定位为主，不把辅助函数默认值当作最终参数。尤其module score的实际含义还取决于Seurat版本、assay、基因集及控制基因处理，不能只凭Methods中的“average expression”改写其完整计算。

### 必须审查的统计依赖【I】

同一区域会出现在多个两两相关系数中，所以区域对并非独立样本。一个患者贡献很多区域时，相关系数数量会近似按区域数量平方增长。建议先在患者内获得同克隆/跨克隆对比摘要，再以患者为推广单位；这是新增建议，不是声称原文已经这样完成。

高相关性也不代表相同身份，可能来自共享细胞程序、细胞组成或同一CNV驱动的表达；低相关性可能来自覆盖和质量差异。解释应回到参考、基因选择与区域组成。

## 4. 核心—边缘深度分析：把位置变成变量

【P】Methods声明按相邻非恶性spot由外向内迭代赋层；排除受组织/捕获窗口/空洞边缘影响的点，以及少于3层或50个spot的微区域。仅检验超过50% spots至少有一个转录本的基因；深度按本区域最大层数归一化，并加入RCTD肿瘤比例或ESTIMATE纯度。作者使用“partial correlation”描述统计过程，结果段也有linear regression表述。依据：Methods: Spot-depth correlation analysis；Extended Data Fig. 8。

原文公式的结构是：

\[
Expression=\rho\times(layer/max\_layer)+b\times purity.
\]

【I】这是作者对分析的简式说明，不足以恢复截距、残差处理、缺失值规则及所用偏相关实现。不能仅照这个式子自行写一个回归，再宣称完全复现了作者的检验。

### 代码与Methods的两个边界

【C】[Figure3/4_Layer/2_layer_DEG_correlation.R，79–104行](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure3/4_Layer/2_layer_DEG_correlation.R#L79-L104)先筛大区域，随后使用`(FC-1)/(FC_max-1)`生成对象中的归一化深度，并读取已有`*_layer_*_DEG.tsv`进行后续作图和富集。

第一，已读脚本不是产生该统计TSV的完整上游。绘图中的stat_cor不能自动代替Methods中的纯度调整检验。

第二，`layer/max_layer`与端点归一化在单一区域内是正仿射变换，但混合不同最大深度的区域后，不是一个统一的全局变换。它们是否影响作者最终结果，须取得上游统计代码与对象后评估，不能仅凭作图脚本推定。

【I】另一个容易漏掉的问题：归一化坐标并不自动使大小区域具有相同统计权重。若仍逐spot拟合，大区域仍贡献更多点。要真正赋予每个区域或患者相同权重，必须明确抽样/加权/分层方式。

## 5. 深度相关结果如何汇总到队列

【P】Methods将不显著或未检验的相关系数置0；先在病例内平均切片，再在队列或癌种内平均。排序量采用`−log10(P) × rho`并作类似置零和平均。GSEA使用clusterProfiler 3.18.1、msigdbr 7.5.1、`pvalueCutoff=0.5`，最终另保留P<0.1的通路。依据：Methods: Spot-depth GSEA pathway enrichment analysis。

【I】这些规则可以形成作者定义的共识排序，但不是普通平均生物学效应。检测不足、未测量和不显著被合并后，排序也反映了检验资格及统计功效。应同时给出每个基因可检验样本数，并开展缺失保留、共同可测基因集和阈值敏感性比较。

【C】[3_layer_DEG_pathway_analysis.R](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure3/4_Layer/3_layer_DEG_pathway_analysis.R)中还存在不同setting的赋值和按方向计数流程。这是一个活动分析分支，不能仅凭文件名把其输出与Methods的所有平均排序结果完全等同。

## 6. RCTD：估计细胞组成，不是把spot变成真实单细胞

【P】Methods声明每张ST采用配对snRNA/Multiome参考、`doublet_mode='multi'`；比较六个层级的细胞比例，并以Wilcoxon及FDR比较克隆间分布。对应最终Fig. 3a–c和Methods: ST cell-type decomposition。

【C】[Figure4/1_RCTD_devolution.R](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure4/1_RCTD_devolution.R)明确读取参考RNA counts和空间Spatial counts，剔除Doublet/Unknown等标签；`MIN_CELL_COUNT_RCTD_REF=50`后实际条件为`>50`；将`_reg`去除以合并部分标签；运行`create.RCTD(...,max_cores=1)`和`run.RCTD(...,doublet_mode='multi')`。

不能把大于50写成大于等于50，也不能假定所有细胞亚群都以原始精细标签保留。参考漏掉的细胞状态可能被分配给相近类别；因此需要保存参考类别和阈值，而不是只保存最终比例。

【I】比例还存在分母约束：一个类别上升可以使其他类别比例下降，而绝对数量不变。迁移到Xenium后，建议同时报告实际组织面积内的密度和相应分母上的比例，二者回答不同问题。

## 7. 边界差异表达与来源归因

【P】边界以肿瘤最外层和紧邻TME层联合定义；作者进行boundary/tumour、boundary/TME、boundary/non-boundary比较，并用单核表达帮助判断来源。最终Fig. 3d展示的边界表达不能一概归于肿瘤细胞。[Fig. 3](https://www.nature.com/articles/s41586-024-08087-4/figures/3)

【C】[Figure4/4_border_DEG.R](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure4/4_border_DEG.R)有width=1、2、4分支，顶端WIDTH=2，但CLI默认4并随后覆盖；还包括leaveout邻近区域的比较。作者最终用了哪个分支，需要样本级命令及输出绑定。

【P】网页Methods对边界DEG的文字为“adjusted P value 0.25”，缺少明确比较符号；本目录不擅自补成`<0.25`或其他常规阈值。需要结合最终表格与作者确认。

### 表达去卷积的准确含义

【P】Methods: Spatial expression deconvolution利用配对单核中每类细胞的平均表达建立贡献矩阵Q，结合RCTD比例后重新归一化为每个spot的表达贡献，再分配空间表达。低于该基因最高平均表达5%的细胞类型先被过滤。

【I】以Q和比例进行分配，是参考驱动的估计，不是直接观察局部各细胞的表达。若实际局部状态与参考平均表达不同，来源分配可能产生偏差。需要保留原信号、预测贡献、被过滤类别和零分母状态；不要将这一步叫作真实单细胞重建。

## 8. COMMOT：空间表达约束下的候选互作

【P】Methods声明CellChat数据库、1,000 μm距离阈值，比较边界与非边界的发送/接收信号；差异>0.1且FDR<0.05为显著边界富集。原文Fig. 3e是候选通信家族，不是受体活性测量或干预结果。

【C】[Figure4/5_CCI_COMMOT.py](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure4/5_CCI_COMMOT.py)依次执行Visium读取、总量归一化及log1p；在HVG筛选前复制对象用于通信，因此不能误写“只用HVG推断所有LR”；LR过滤为`min_cell_pct=0.05`，`spatial_communication`启用heteromeric与pathway_sum。

### 活动脚本的接口风险

1. `dist_threshold`的OptionParser定义未显式指定数值type。默认值是数值，但用户显式传参可能得到字符串；需验证转换及下游类型处理。
2. 已读段把坐标和阈值直接送入函数，未见显式物理单位转换。不能仅由数值1000断言实际距离为1000 μm；也不能在未检查输入对象时断言作者单位算错。
3. 脚本改变当前目录；相对output路径存在后续拼接风险，迁移时应先解析为绝对路径。
4. 可选择CellPhoneDB，但部分绘图键名写死`cellchat`，使可选分支不一定完整。
5. 首轮绘图前，复制对象中的Leiden列是否已经存在需要检查；本轮未运行确认。

【I】这些是接口和可运行性问题，不等于生物学推断必然错误。真正的证据上限仍是：表达、先验LR知识与空间接近共同支持的互作候选。阳性结果不能单独确认发送细胞、接受细胞、信号方向、必要性或中介作用。

## 9. LINCS药物部分：候选生成，不是药敏实验

【P】作者选择十个多克隆病例，以subclone相对TME的DEGs对照Enrichr的LINCS_L1000_Chem_Pert_down基因集，并使用化合物metadata解释候选；DEG筛选包括adjusted P<0.01、平均log2FC>1、pct>0.4。依据：Methods: Spatial subclone-specific treatment response analysis。

【I】这一结果为扰动候选优先级提供线索，不能等同于IC50、组织药物暴露、克隆消除或临床获益。原文某些“respond”表述应按其计算设计降回“签名匹配所预测的候选响应”。

## 10. 这一章最重要的输出合同

【H】保存每个基因/程序的可测状态、原始及过滤后的表达、细胞组成、细胞内响应、距离、区域大小、参考和mask版本。每个主要关联同时给效应大小、不确定性、独立样本数和对阈值/分割/来源分配的敏感性。没有这些，增加更多通路名和通信边不会改善研究判断。
