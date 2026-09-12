# 04｜细胞状态、边界与通信：把混合、位置和响应分开

[目录](../README.md)｜[上一章](03_cnv.md)｜[下一章](05_3d.md)

## 1. 从表达矩阵到研究对象，中间不能跳步

【P】论文比较微区域转录异质性，并以核心—边缘位置分析基因和通路变化；同时借助器官相关非恶性基因参考、配对单核数据及纯度信息减少混合影响。〔P：Methods “Microregion transcriptional profile analysis”“Organ-specific gene blacklist for non-malignant cell types”“Tumour intrinsic and non-tumour gene categorization”〕

【I】基因黑名单、细胞类型参考和纯度回归解决的是不同问题。黑名单限制哪些基因参与比较；参考表达帮助判断来源；纯度是组成的一个汇总量。没有一种方法自动恢复每个恶性细胞的真实表达。

某基因在间质中表达，不代表它不可能由肿瘤细胞表达；参考中没出现某状态，也不能证明它在空间样本中不存在。对参考的缺失和归类误差，需要在结果措辞中保留。

## 2. 异质性与相似性不是一个指标

【P】作者采用与 ROGUE 有关的转录异质性度量，并比较微区域转录谱。〔P：Methods “Microregion transcriptional profile analysis”；Extended Data Fig. 6〕

【I】一个区域内部的表达离散程度、两个区域均值的相似性、以及它们是否属于同一遗传分组，是三个不同量。内部异质性低不代表与其他区域不同；均值相似也可能掩盖不同状态混合。

【H】跨区域比较应同时保存区域平均/伪bulk表达、区域内状态分布和细胞组成。高变基因集合若随样本而改变，相关系数比较还会受到特征选择影响。先统一估计目标和基因集合，再决定是否进行跨样本汇总。

## 3. 核心—边缘：测量坐标如何产生？

【P】作者从邻接非恶性区域的一层向内定义深度，并排除可能因组织截断、边缘或深度不足造成的问题观测；较小或较浅微区域不进入相应深度分析。〔P：Methods “Spot-depth correlation analysis”；Extended Data Fig. 8〕

【I】这一设计真正提供的是从组织界面出发的离散位置坐标。它不一定等于到肿瘤几何中心的欧氏距离；弯曲、分支和空洞会改变两者关系。

【H】新项目应分别保存绝对距离、相对深度、区域大小与边界可信度。绝对距离回答物理作用范围，相对深度回答不同大小对象的内部位置。不要用一个归一化坐标代替所有科学问题。

【C】[C07：2_layer_DEG_correlation.R](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure3/4_Layer/2_layer_DEG_correlation.R#L79-L110) 使用 `(FC−1)/(FC_max−1)` 创建绘图对象，并读取预先存在的相关统计 TSV。文件名虽含 correlation，已读文件不能恢复该 TSV 的完整上游偏相关生成过程。Methods 的层数归一化描述与此端点归一化不完全相同，缺少上游记录时不裁定论文实际采用哪一版。

## 4. 纯度校正后，剩余效应是什么？

【P】论文的深度分析纳入纯度，来源可为匹配数据的 RCTD 或 ESTIMATE。〔P：Methods “Spot-depth correlation analysis”〕

【I】加入纯度后得到的是在该模型和测量条件下的条件关联，不是自动识别肿瘤内源程序。纯度估计仍可能与位置、细胞状态和测量误差相关。

一个值得检查的具体问题是：论文使用 rho 一词，同时以线性表达式描述分析。偏相关系数与回归斜率不是同一个量，不能根据符号自动互换。第六章给出残差公式；真正确定输出语义需要生成结果表的函数与标准化方式。

## 5. 通路汇总：共识排序不是平均效应

【P】跨样本深度通路分析将未通过指定显著性条件及未检验的基因相关贡献设为零，再进行分层汇总和富集。〔P：Methods “Spot-depth GSEA pathway enrichment analysis”〕

【I】这定义了一种优先展示反复出现信号的统计策略。但它把检测能力、样本量、缺失与生物学效应共同带入排序。原始平均相关、显著性加权共识和跨个体平均效应回答不同问题。

【H】迁移时保留每个样本—基因的可测状态，至少比较置零排序与保留所有可估计效应的结果。富集背景应反映实际可测基因；靶向面板不能默认以全基因组为可发现背景。

## 6. RCTD：活动调用和参考决定可分辨什么

【C】[C03：1_RCTD_devolution.R](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure4/1_RCTD_devolution.R) 明确读取 RNA 与 Spatial counts，去除若干 doublet/unknown 标签，保留细胞数严格大于 50 的参考类型，将标签中的 `_reg` 删除，活动运行模式是 `multi`。

【I】因此，不能从这个脚本直接宣称单独估计了保留原标签的 Treg，也不能把 >50 写成 ≥50。输入被合并或剔除的类别不可能在输出中凭空获得可靠独立估计。`max_cores=1` 与 BLAS 线程配置属于不同并行层，不据此估计端到端速度。

【H】恢复匹配参考及预处理后的标签表，记录未纳入类型。对于细胞已分割的 Xenium，优先在真实细胞对象上研究组成与状态，不把 Visium 去卷积当作所有空间数据的必需步骤。

## 7. 基因来源的参考辅助分配

【P/I】论文的空间表达分配可整理为：给定过滤后的参考类型均值 r_gc 与位置的组成 p_cs，先计算相对贡献，再分配总信号：

$$q_{gcs}=\frac{p_{cs}r_{gc}}{\sum_c p_{cs}r_{gc}},\qquad \hat{x}_{gcs}=x_{gs}q_{gcs}.$$

〔P：Methods “Spatial expression deconvolution”〕

【I】这个公式在分母正值时守恒，但守恒不等于来源正确。若参考均值不适用于该局部状态，信号也会被守恒地分错。分母为零应输出无法归属，不应静默给已有类别。

【P/I】该 Methods 的示例中，总量 20 与所列分配比例对应的第一类约为 11.43，而文字写为 10.42。这是示例算术不一致，不证明真实分配程序也同样出错。我们的合成检查只验证了代数守恒。

## 8. 边界差异表达：先定义比较集合，再解释统计量

【P】最终 Fig. 3d 围绕边界表达及来源展开。〔P：Methods “Gene expression at the tumour boundary”〕

【C】[C05：4_border_DEG.R](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure4/4_border_DEG.R#L64-L180) 提供宽度 1、2、4 的不同集合，并计算边界相对于肿瘤、TME 等对比；顶部宽度 2 会被 CLI 值覆盖，CLI 默认为 4。某些相邻层还可以被排除为 Leaveout。

【I】多种分支的存在不是最终运行宽度的证明。不同边界宽度改变的不只是样本数，也改变了待估计的空间过程。如果边界相对于两侧都有高表达，还要检查混合比例和细胞来源，而不是立即称“界面诱导”。

【C】脚本会覆盖输出目录参数，并对已存在样本输出目录进行递归删除。不得未经隔离在用户数据路径试跑。Methods 网页的某个边界 DEG 阈值表达缺少完整比较符号，不能自行补成惯常的 FDR<0.05。

## 9. COMMOT：箭头的证据等级

【P】作者使用空间通信推断寻找边界相关候选通路。〔P：Fig. 3e；Methods “Spatial cell–cell interaction at tumour boundary”〕

【C】[C04：5_CCI_COMMOT.py](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure4/5_CCI_COMMOT.py) 在 HVG 截取之前复制全基因对象用于通信，因此不能声称通信只用了 HVG。`adata_dis500` 是变量名，真正阈值来自命令行。注释中的 TradeSeq/随机森林示例不属于活动计算。

【C】该段未显式完成物理坐标转换；距离 CLI 未声明数值类型；已有固定名 h5ad 会被直接复用，未在该段绑定输入与距离/数据库哈希。需要真实对象、库版本与运行命令才能判定实际行为。

【I】通信模型的方向性来自配体—受体定义和表达/空间约束，不等于直接观察到蛋白结合、受体激活或迁移方向。空间接近、共同上调和通信分数可以共同支持候选，但仍可能由共同环境驱动。

【H】迁移时优先检验：相关基因在面板中是否可测、表达来自哪些细胞、关系是否超过局部可接触机会、是否在独立样本成立。不要先对缺失配体或受体做插补再将其当成实测通信证据。

## 10. 本分支的复现门槛

【H】最低中间产物是区域/层深表、纯度来源、预处理参考、每个样本可检验基因、原始和校正统计、比较集合、效应量及多重检验家族。恢复最终图表不等于验证这些上游推断。

## 来源

[P：论文全文与 Methods](https://www.nature.com/articles/s41586-024-08087-4)。C03/C04/C05/C07 固定链接见各段及[来源索引](../references/README.md)。
