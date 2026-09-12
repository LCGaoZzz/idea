# 04｜从癌细胞 pseudobulk 到 archetype 和 metaprogram

[返回](../README.md) · 论文位置：[Methods: Creating pseudo-bulk RNA-seq data / Performing NMF / Identifying archetypes / Identifying metaprograms of cancer cells](https://www.nature.com/articles/s41586-026-10469-9)。源码固定定位：[psbulk.fastNMF.R](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/scripts/psbulk.fastNMF.R)、[metamodule_fnmf.s2a.R](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/scripts/metamodule_fnmf.s2a.R)。

## 1. 先保证矩阵回答正确的问题

【P】Pseudobulk 按目标细胞群对原始 UMI 求和，多个组之间用 DESeq2 的 VST 处理。癌细胞 archetype 使用每患者癌细胞聚合矩阵，不使用整个肿瘤混合表达替代。`psbulk.prepare.R` 是聚合准备路径，`psbulk.fastNMF.R` 的活动输入是 `normalized.DESeq2VST.matrix.rds`。

【I】聚合原始 counts 与平均 log 表达不是等价操作。对计数 $y_{gc}$，$\log(1+\sum_c y_{gc})$ 不等于 $\sum_c\log(1+y_{gc})$，更不等于平均 z-score。VST 的目标是计数均值—方差关系，不会自动控制临床混杂或补偿低癌细胞回收数。至少导出每患者癌细胞数、总 UMI、gene coverage 和实际输入行列名。

## 2. NMF 的输入变换决定它能看见什么

【P／C】对基因在观测之间中心化，并把负值置零，再作非负分解。患者级代码扫描 rank 2–10，调用 `RcppML::nmf(mat,k=r,tol=1e-5,L1=c(0.05,0.05))`。来源：脚本 L72–109。

【I】实际输入可写成：

$$V_{gj}=\max\{Y_{gj}-\bar Y_g,0\},\qquad V\approx WH.$$

这里 WH 仅表示数学上的非负低秩近似；RcppML 返回对象包含缩放约定时，应保留其实际 `w,d,h`，不能只凭教科书公式重写输出。W 表示基因方向，H 表示观测负载，不自动是概率或组成。

该变换主要保留相对其他观测上调的结构。普遍高表达但变化很小的基因可能不参与分型；“不驱动 NMF 分类”不等于“不重要”。中心化依赖训练／发现队列，外部患者的变换也必须说明是重新中心化还是使用冻结参考。

## 3. 患者 archetype 的筛选与缓存冲突

【P】Identifying archetypes 写按表达均值和方差分别保留前 75% 基因。

【C】`psbulk.fastNMF.R:L54–80` 连续覆盖 `idx`，最后活动表达式是 `g_avg > mean(g_avg) & g_var > mean(g_var)`。前面的分位数表达式不再生效。整个筛选块仅在 `input.matrix.rds` 不存在时运行。

【I】两个问题应分开记录：源代码在无缓存时使用哪一个筛选器；发表结果实际使用了哪一个缓存。前者可确认，后者必须拿到输入矩阵和生成记录。代码被修改但缓存未失效，会造成“看似修复、实际不重算”。不能只删除缓存然后宣称已忠实复现原论文。

【T】采用 `input_hash + transform_parameters + code_commit + dependency_versions` 共同生成缓存键。保存 `source_exact`、`methods_declared`、`adapted` 三个分支；先比较基因集合、因子匹配、患者负载，而不是只比较两个 UMAP 是否相似。

## 4. 四个 archetype 既有主导，也有混合

【P】Fig. 2 与 ED2 把患者主要背景分为 LumSec-like、basal-like、IFN-responsive、AR-enriched，并用 Tau 和前二负载比描述专一性。Methods 写对指标拟合双成分 Gaussian mixture，再用低成分均值设定阈值，两个指标均低才判 ambiguous。

【I】主导标签方便解释，不能掩盖混合患者。NMF 具有因子排列与尺度非唯一性；跨队列因子对齐必须基于 W／参考样本，不可将“第3列”默认当 ARC3。以混合模型阈值分组也依赖队列分布，不是自然界固定边界。

【C】`ratio_of_top2`（L23–35）用 `max(x[x!=a])` 找分母；它求的是下一不同数值，而不是排序后的第二个负载。例 `[0.4,0.4,0.1,0.1]` 的真正前二比是 1，该函数给 4。真实 H 是否有并列值、本问题是否改变患者分组，尚未测量。

【I】Tau 为 $\sum_k(1-h_k/\max h)/(K-1)$。需排除全零、非有限值和 $K<2$；单一最大与精确并列不应混为同一种置信度。可保留 H、排序后前二比、Tau、混合模型参数和 final label，而不是仅存类别。

## 5. 为什么逐患者提取程序，再跨患者找重复？

【P】MP 方法排除平均 log 表达不高于 0.05 的基因和癌细胞不足20的样本；对每样本扫描偶数 rank 2–30，并以程序 marker 的 Jaccard 相似性合并。对 rank 超过细胞数的情况，Methods 明确不运行。位置：Identifying metaprograms、Performing NMF。

【I】把全部癌细胞一次性合并 NMF，可能首先学到患者、深度、CNA 和回收量差异。逐患者后寻找重复程序，是为了分开样本特异变化和共享状态。但同一患者在多个 rank 中重复出现，并不是多个独立生物学重复。汇报支持度必须回到独立患者数。

**脚本角色纠正。** 本地继承快照的 `metamodule_fnmf.s1.R` 实际读取已经产生的因子／marker 对象做 QC（如 `nCell>=2`、`nMarkerGene>=3`），不是从 counts 开始运行逐患者 NMF 的完整入口。此前宽泛地将 s1 标为“程序发现”不足以指导执行；还需要 `fastnmf.R` 的实际驱动命令和作者教程路由。QC 常数属于该代码块，不能自动当所有阶段的论文最终参数。

## 6. 跨患者合并：相似性、过滤和人工判断

【P】两个程序基因集合 A、B 用 $J(A,B)=|A\cap B|/|A\cup B|$ 衡量重叠；最相近其他程序的相似性低于0.25者被排除。Methods 描述 Ward.D2、cut 10到30的偶数方案，组内相似性小于0.1的组排除，组间相似性大于0.2且在较小 cut 中相聚者合并，迭代至稳定；再去除技术噪声程序。

【I】需要明确输入 hclust 的究竟是相似性、$1-J$ 还是对相似性行向量再求距离。对非欧氏距离使用 Ward 风格算法时，不能自动套用欧氏最小组内平方和的直观解释。本次不在未追完调用前断言某种变换已用于最终图。

程序长度、marker 选择、重复 rank 和人工删除都会影响 Jaccard。必须保存每轮 candidate、membership、merge reason、最终 marker，而不是只给十三个漂亮名字。

## 7. 新核对的边界案例：去掉“值为1”不等于去掉自己

【C】固定版 `metamodule_fnmf.s2a.R:L76–99` 计算 `max(x[x!=1])` 作为最相近非自身程序，再用0.25筛选。它也删除了与其他程序完全一致、Jaccard=1的值；这种一致本来可能是重复支持。该块还在有缓存时读取 `jaccard_mat.all_ranks.rds`，而非这里另存的 `...in_use.rds`。

【I】如果两个不同程序集合相同、与其他集合都不相似，这个最大值不等于“排除对角后最大值”。是否故意排除重复程序，以及后续是否另行去重／筛选，需要追踪最终对象；不能直接把局部边界行为宣布为全部 MP 错误。缓存路径也只是当前块的冷热路径不同，完整下游影响尚未运行。

【T】测试时按元素索引排除自己，并明确另设去重政策。把冷启动和缓存启动的候选 ID／矩阵哈希比较纳入测试。合成脚本包含该反例，不声称已改作者仓库。

## 8. 十三个程序如何读

| 程序 | 作者命名的概括 | 不能省略的替代解释 |
|---|---|---|
| M1-G2/M、M7-S | 周期 | 捕获和 RNA 含量变化；不是谱系 |
| M2-mito、M3-ribo | 线粒体／核糖体 | 质量、处理应激与技术相关 |
| M4-stress、M8-hypoxia、M13-ER stress | 应激／缺氧／ER 应激 | 解离与体内状态；转录代理不等于氧分压或通量 |
| M5-interferon、M6-HLA | 免疫响应 | 来源污染、外源刺激；表达不等于有效抗原呈递 |
| M9-basal、M10-EMT、M11-LumSec | 谱系／状态相关 | 正常谱系相似不等于起源；连续状态不等于新克隆 |
| M12-cholesterol | 胆固醇相关表达 | 转录信号不等于代谢通量 |

表中程序命名来自 Fig. 3／Supplementary Table 7；功能边界为 I 类解释。

## 9. 从 marker 到评分，再到阳性细胞

【P】Methods 使用 Seurat `AddModuleScore`，以匹配表达背景基因为对照；阳性频率采用 score≥0.1，分母是患者癌细胞数，无癌细胞记 NA。

【C】`metamodule_cell_frequency.R` 的所检查路径取前20个 marker 打分，另含患者内 z-score、binary、binary_v2 和可视化 dominant label。它们不能被合并解释为一个最终评分规则。已有 `addmodulescore.df.rds` 时直接读缓存，也要核对 Cells 顺序。

【I】模块得分不是概率；0.1依赖 assay、背景基因、归一化和样本组成。技术迁移到另一个面板时，照搬阈值不意味着保留相同灵敏度。程序阳性率可重叠，不应强行加总为100%。空间 dominant label 的丢失信息须保留在连续评分表中。
