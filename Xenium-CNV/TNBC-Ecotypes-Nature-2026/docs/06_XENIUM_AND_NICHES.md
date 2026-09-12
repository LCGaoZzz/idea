# 06｜Xenium：从标签转移到空间组织，而不是再画一张彩色细胞图

[返回](../README.md) · [P：Methods](https://www.nature.com/articles/s41586-026-10469-9) 的 Identifying cell types and cell states in Xenium data、Spatial niche analysis in Xenium data。[C 标签脚本](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/scripts/xenium/xenium.celltype.TransferLabel_EvalMode.R)、[空间作者路由](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/xenium.spatial_niche.md)。

## 1. 空间平台提供的是新的测量约束

【P】论文在44位患者中使用约5k靶向基因的 Xenium 数据，以单细胞参考转移细胞类型／状态，并结合 marker 原位表达与 H&E。与 Visium／VisiumHD 的辅助空间材料应分开记录。

【I】新平台可以验证组织位置和部分来源，却不是对全部状态的完全独立再发现：标签词典来自 scRNA。应分别说明独立的是患者、技术、基因、病理判读还是标签。投射后重现参考名称，本身不构成全部状态真实性的独立证明。

面板缺失、低检测和生物学阴性都可能表现为0；注释不能强迫区分面板根本无法分开的状态。肿瘤／免疫交界处还需核查细胞边界和转录本归属，避免相邻信号被误认为目标细胞内程序。

## 2. 十折“交叉验证”的折是什么？

【P】参考按癌细胞程序和 TME 状态至多抽取1000个细胞并选择面板基因；把基因分成十组，每次留出一组，其余九组运行 label transfer。主类型要求十次一致；细状态的票数阈值结合 UMI、gene count、预测分数与人工最低门槛。来源：Xenium Methods。

【C】`xenium.celltype.TransferLabel_EvalMode.R:L39–50,L83–125` 读取 gene portion，使用30个维度；`param.run_TransferData_genes=FALSE` 控制的留出基因表达预测分支在所检查版本未默认启用。

【I】这检验标签对部分基因扰动的稳定性，而不是十个独立患者的准确率。各次使用大量重叠基因、相同参考和目标细胞；十票一致可以表示一致性，但不等于“准确率100%”。文件名 EvalMode 也不能证明关闭分支真的执行。

对真正未见状态，十次都错投到同一旧标签也可以高度一致。必须另设 unknown／unresolved 和分数间隔，而不是把一致投票当绝对真值。

## 3. Unknown 不应该只在展示前被删掉

【T】至少保存 `label_raw, label_consensus, votes, runner_up_votes, probability, margin, unknown_reason`。绘图和组成分析报告 unknown 占比及其空间位置。

【I】若低RNA、坏死边界或新状态更容易 unknown，删除会造成有方向的空间选择。去掉全部不确定细胞之后出现清晰边界，既可能提高标注纯度，也可能人为制造结构。敏感性分析应比较“排除未知”“保留为独立标签”“可信范围内的概率归属”，并明确三种估计对象不同。

## 4. 从坐标到局部组成的精确对象

【P】Spatial niche Methods 对每个中心细胞计算半径30 μm区域内状态百分比，癌细胞用最高且>0.1的程序作为标签。每患者先聚类局部组成，通过 Seurat SketchData／ProjectData 加速，再用 ConsensusClusterPlus 合并样本内与跨样本相似社区，形成十类 recurring niches。CellTrek `scoloc(use_method='DT')` 用于空间共定位关系，见 Fig. 5d–k、ED8e–g。

【I】设同一连续组织区域内的邻域为：

$$\mathcal N_r(c)=\{u:d(u,c)\le r\},\quad A_{cs}=\sum_{u\in\mathcal N_r(c)}1(L_u=s),\quad P_{cs}=A_{cs}/\sum_tA_{ct}.$$

该式是解释性定义，不是对未查到源码细节的声明。原方法的中心细胞是否计入、距离端点、跨ROI规则、组织边缘修正和 unknown 分母须由具体 step1／helper 确认。counts、proportions、z-score 和 CLR 不是等价输入。

按坐标聚类得到位置块，按表达聚类得到状态，按邻域组成聚类才回答局部环境；三者不能互相替换。

## 5. 为什么“30 μm、十种 niche”不是可照搬答案？

【I】半径改变生物学尺度，也改变邻居数量和测量精度；密度不同的区域在同一半径内拥有不同样本数。边缘、空洞与破碎组织使有效观察面积减少。一个“免疫少”的邻域可能只是能观察的组织少。

【T】保存邻居数、有效面积、距组织边界、区域类别、未知比例。选择少量预先规定尺度做敏感性分析，报告关系在何种尺度成立。不要扫很多半径再报告最显著者；若做探索，就把尺度选择放入独立确认步骤。

niche 数目受状态字典、半径、抽样平衡与合并规则影响。迁移项目不应强行指定十种以“复现文章”。匹配不同项目的 niche 要比较组成中心和功能，不按数字ID直接对齐。

## 6. 空间零模型必须回答特定问题

【T】若问“髓系是否进入癌区”，应保留组织 mask 并比较实际进入与空间机会；若问“在已经共处癌区的癌细胞和髓系中，特定状态是否相互偏好”，应尽量保持父谱系位置，并在同一动物／区域／父谱系内置换状态。

【I】后一个条件零模型把谱系分布与部分组织背景固定，估计的是额外状态关联，不是总体空间效应。如果组织区域是阶段作用的中介，条件化后效应消失不代表没有生物学，只说明它可能主要通过区域重构实现。

置换依赖交换性。简单随机标签置换会破坏状态空间自相关，可能过于容易给出显著性。需要按假说使用分块、相似区域匹配或能保留空间结构的模型；不存在一个适用于所有组织的万能置换。带边界修正的点过程、距离统计或图邻近各有不同估计对象。

## 7. 有几十万个中心细胞，不等于几十万个独立重复

【I】邻域重叠，细胞共享动物、区域和技术条件。若用普通独立样本检验比较每个中心细胞，标准误通常不反映真正的不确定性。应先在动物／患者层面计算效应或使用明确的层级模型，再讨论跨个体可重复性。

【P】Fig. 5f 用 ecotype×niche 计数表的卡方 Pearson residual 展示关联。残差可以定位超出独立性期望的组合；若用于推断，需面对细胞的空间依赖、不同患者权重与低期望计数问题。

【T】患者级报告每个候选关系的效应、支持率与区间；展示汇总图同时给出患者分面或分布。最大切片不能在不知情情况下主导所有结论。

## 8. 来源、共定位与功能的不同反证

【I】目标细胞内表达消失于保守边界处理，削弱来源解释；额外邻近在控制组成后消失，削弱独立局部组织解释；空间关系只在一位动物存在，削弱外推；关系跨动物稳定仍不确立作用方向。即使介入某细胞后邻域改变，也要区分细胞数减少、共同环境改变与特定相互作用受损。

## 9. 可恢复的作者 step 路由

【C：作者文档路由，非所有脚本均完整审读】

`step0.prepare_inputs.winner.R` → `step1.make_ROIs.winner.R` → `step2a.initiate_niche_assay.R` → `step2b.propose_niche_each_sample.R` → `step2c.propose_MetaNiche_from_niches.across_samples.R`，位于 `analysis/scripts/spatial_niche/`，另依赖 `util.ConsensusClusterPlus.R`。

【T】依次验收 ID／单位、邻域手算例子、每行组成与 unknown、样本内映射、跨样本中心和每患者支持。不要在缺少 step 输出时用一张重画的散点图代替整个链条。数据集规模、空间索引和稀疏存储决定成本；本次未运行全量，未提供伪精确内存或耗时估计。
