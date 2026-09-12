# 03｜CNV、变异与空间克隆：证据链和实现不能分开读

[目录](../README.md)｜[上一章](02_design.md)｜[下一章](04_boundary.md)

## 1. 输入合同：先确认对象，再讨论算法

【P】本文的遗传主线结合 WES、Visium 与配对单核/单细胞材料，Xenium 用于选定变异转录本的原位支持。相关方法包括 “WES data processing”“Mutation calling using WES”“InferCNV and CalicoST for CNV calling on Visium ST data”。

【I/H】每次分析至少需要确认：病例、组织块和切片是否对应；counts 来自哪个 assay；基因标识和排序参考是什么；正常参考是谁；CNV 状态编码是什么；变异坐标、转录本和基因组版本是否一致。只有一张彩色 CNV 热图，不能恢复这些决定。

对于原始变异分析，还需要 matched normal、候选位点与过滤记录；不能把作者已经由 DNA 数据选择的位点描述为 Xenium 无偏发现的全部变异。

## 2. inferCNV 的论文设置与脚本接线

【P】Methods 报告 Visium 的参考选择、151 基因平滑窗口和 sample 模式，去噪、HMM 及按输入组进行处理；单核/单细胞的参考和模式另述。〔P：Methods “InferCNV and CalicoST for CNV calling on Visium ST data”〕

【C】在 [C01：1_inferCNV_run.R](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure2/1_inferCNV_run.R) 中，顶部示例参数被 `parse_args` 后的值覆盖。CLI 默认模式为 `subcluster`，正常参考数量为 −1，Bayes 阈值为 0.5；顶部 sample、200、0.3 不能证明运行采用它们。活动 `infercnv::run` 另外显式传入 cutoff=0.1、denoise、HMM、cluster_by_groups 等。

【C】同一脚本的 `GetAssayData(..., slot='counts')` 未显式指定 assay。它取得哪个 counts 依赖输入对象的 DefaultAssay；“counts”这个槽名本身不是原始 Spatial 矩阵的充分证据。正常参考选择还可能受纯度排序并列及回退分支影响，必须恢复样本级参考 ID。

【H】完整复现保留原 argv、输入哈希和参考清单；迁移包装层可以修正路径和日志，但不能偷偷改变正常参考、平滑窗口或模式，然后称同参数复现。

## 3. CalicoST：工具公开不等于研究配置公开

【C】[C02：2_CalicoST_run.md](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure2/2_CalicoST_run.md) 只有工具指针，没有该研究的逐样本输入、argv 与完整结果绑定。

【P】论文描述了其在空间克隆流程中的用途，OCT 与 FFPE 的分组策略不同。〔P：Methods “Spatial subclone identification based on CNV profile similarity”〕

【I】准确状态是“方法可定位、研究运行链尚未恢复”，不是“作者没有使用该工具”。也不能把今天上游教程的默认值填入论文参数空格。

## 4. 论文的有符号相似度：先把区间划到同一张网格

【P/I】按 Methods 的符号和长度加权描述，若基因组被划为共同的非重叠小区间，区间长度为 w，状态 a、b 分别为 −1/0/+1，令 U 为任一方非中性的区间，则可写成：

$$S(A,B)=\frac{\sum_{i\in U}w_i a_i b_i}{\sum_{i\in U}w_i}.$$

同向异常为正，相反异常为负，一方中性贡献零。它不是普通 0–1 集合 Jaccard；全中性比较的分母为零，缺乏非中性身份信息。本档案的代数实现对此返回 NaN，属于显式的边界处理，不声称作者实际如此实现。〔P：Methods “Copy number profile similarity score calculation”〕

【H】真实区间需要先按染色体、边界和坐标规则统一，不得把两个长度不同、边界不齐的 segment 表逐行相乘。合并重叠区间和切分为共同原子区间是不同操作。还需要明确缺失区间究竟代表中性还是未测量。

## 5. 新增代码发现：同名辅助函数并没有实现同一公式

【C】本轮扩展读取了 [C06：3_CNV_jaccard_similarity.R](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure2/3_CNV_jaccard_similarity.R#L68-L155)。以下限于 commit `7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa`。

### 5.1 无概率函数的分母不对称

`CNV_profile_jaccard` 的分子统计同向扩增或同向缺失的交集；分母合并 A 的所有异常与 B 的缺失，未将 B 的扩增对称纳入。原代码中性用比值 1；本档案示例为清晰起见改用符号 0。

【I：反例】在两个等长、已对齐、无重叠窗口上，A=(+1,0)，B=(+1,+1)：

| 计算定义 | A 对 B | B 对 A |
|---|---:|---:|
| 论文有符号公式 | 0.5 | 0.5 |
| 该无概率辅助函数的网格等价逻辑 | 1.0 | 0.5 |

此外，单个同一窗口一方扩增、一方缺失时，论文公式为 −1，该辅助逻辑为 0。这是可核对的定义差异与不对称性，不需要患者数据才能构造反例。

### 5.2 概率函数不是简单修复后的论文公式

【C】`CNV_profile_jaccard_prob` 按 amp/del 分别建立区间并集，在 `mode='pred'` 下用预测状态一致性乘两方置信度加权。同一位置的相反事件可能进入两个状态轨道的分母；其分子不会变成论文公式的负项。

【I】在单一一致异常、两方概率均为 0.8 的例子中，自比较为 0.64，而不是 1。它可能是某种置信度加权相似度，但不能不说明就称普通距离。`as.dist` 会忽略对角线，所以这个自比较例子本身不证明作者的聚类计算故障。

### 5.3 必须追踪实际选择的分支

【C】同文件末端选择 `distmat_selected = jac_pred_mat`，再执行 `hclust`、`maptree::kgs`，并遍历 K=2…MAX_K 的候选切分与可视化。读取范围包括文件末端；并不是只发现了一个未调用的函数。

【P】Methods 则描述基于相似度的 Ward 聚类、按树高比例切分及人工检查。〔P：Methods “Spatial subclone identification based on CNV profile similarity”〕

【I】这构成论文描述与该公开候选工作流之间的材料差异。但无概率分支的不对称问题，不能直接被归因于末端选中的概率分支，更不能直接断言已改变论文最终克隆数。还缺最终脚本、人工决策、样本矩阵和运行记录。

## 6. WES 的两种角色不能混用

【C/P】FFPE 工作流中，WES 可用于限定保留的 CNV 事件；C06 也有在计算相似度前按 WES 区间重叠过滤的活动逻辑。〔C06；P：同上克隆识别方法〕

【I】如果一个数据源已经决定哪些事件被纳入，随后再次用它展示一致性，那么一致性仍有意义，但不是完全独立的外部验证。应分别报告筛选前后的一致性、未使用于筛选的事件证据，以及其他测量通道是否支持。

## 7. 从相似度到聚类之间还缺一道数学检查

【P】论文指定 `ward.D2`。〔P：同上〕

【I】“1−相似度”不自动是欧氏距离。第六章给出一个有负 Gram 特征值的明确反例，说明在一般有符号状态配置下，直接输入 `D=1−S` 不能自动获得 Ward 的欧氏最小方差解释。该问题与前述非对称辅助函数是两件事，不能混在一起。

【H】实际复核应检查矩阵对称性、有限性、对角线、欧氏性和样本顺序依赖；比较合理的 linkage 及参考集合后，观察克隆标签是否稳定。不要未经验证就把 D 改成平方根或对称平均后宣布修复完成。

## 8. 迁移至 Xenium 的条件

【H】面板支持 CNV 的关键不只是基因总数，而是染色体覆盖、共同表达、正常参考、基因剂量效应与其他表达程序是否可区分。面板偏向肿瘤/免疫标记时，基因组顺序信号可能与选择偏好耦合。

先对面板作染色体分布和可检测性审计；比较候选区域的广域连续事件是否能被独立基因子集或已有遗传信息支持。若状态区分主要依赖少量功能标记而非广域信号，优先使用“空间状态”称谓。不能机械照搬全转录组 Visium 的 151 基因窗口，也不能笼统声称所有 Xenium 都不能做 CNV。

## 9. 最低验收产物

【H】应保留：counts 与 assay 标识、参考 ID、gene-order、连续 CNV、离散状态、BAF/变异证据、共同区间表、相似度矩阵、聚类树、所有候选切分、最终区域—克隆映射及人工改动理由。只有最后的标签不够审查阈值稳定性。

实际完成情况：本档案阅读了指定源码并执行了限制在合成网格上的原创数学检查；未运行作者 R 函数、GenomicRanges、真实 CNV 推断或患者聚类。合成检查不能替代区间处理和生物学验证。

## 来源

[P：论文 Methods 与 Fig. 2](https://www.nature.com/articles/s41586-024-08087-4)；[R 的 hclust 说明](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/hclust.html)；[R 的 dist/as.dist 说明](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/dist.html)。当前 R 文档用于解释接口语义，不冒充作者环境版本。
