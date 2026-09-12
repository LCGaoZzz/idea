# 03｜CNV、等位基因与空间克隆：从输入到结论的协议重建

[返回总目录](../README.md) · [上一章](02_data_and_measurements.md) · [下一章](04_state_boundary_and_interactions.md)

## 1. 分清三种不同任务

【I】本研究中的遗传分析至少包含：由RNA推断大尺度CNV；将候选DNA变异定位回空间RNA；用定制等位基因探针验证选定位点的位置。三者的测量对象、输入和盲区不同，不能统称“Xenium测CNV”。

【P】原文Fig. 2展示的是这三类证据围绕空间亚克隆的组合。OCT与FFPE保留不同信息，故克隆流程分路。依据：[Fig. 2](https://www.nature.com/articles/s41586-024-08087-4/figures/2)及Methods: Spatial subclone identification based on CNV profile similarity。

## 2. 总体依赖关系

```text
H&E与微区域标注 ───────────┐
Visium原始counts+基因坐标 ─┼→ RNA-CNV / BAF → 区域遗传轮廓 → 候选克隆
正常参考与纯度估计 ────────┘                         ↑
匹配WES ─→ DNA-CNV、候选体细胞变异 ──────────────────┘
                  └→ ST/snRNA BAM的位点映射 → 区域VAF比较
                                               └→ 选定位点Xenium支持
```

上图是【I】的依赖概括；具体顺序、筛选关系和输入与输出如下，不能由图假定所有样本都有全部分支。

## 3. WES：建立候选DNA事件，而不是直接得到空间克隆

【P】Methods记载WES预处理为TrimGalore 0.6.7（最短长度36），BWA-mem 0.7.17（`-M`）比对至GRCh38.d1.vd1，samtools 1.14及Picard 2.6.26整理比对文件、处理重复并建立索引。体细胞变异用Somaticwrapper 2.2整合多个caller，并要求相应候选由至少两个caller支持；肿瘤/正常最低覆盖14×/8×，一般VAF阈值为肿瘤≥0.05、正常≤0.02，另有邻近indel过滤与稀有候选救回规则。依据：Methods: WES data processing、Mutation calling using WES。

【P】WES CNV使用GATK 4.1.9.0，包括区间构建、CollectReadCounts、正常参考panel、DenoiseReadCounts、CollectAllelicCounts、ModelSegments和CallCopyRatioSegments；区间及基因映射另有长度加权处理。依据：Methods: CNV calling using WES。

【C】对应公开入口为[Figure2/4_WES_CNV.sh](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure2/4_WES_CNV.sh)。本目录只定位该入口，未逐命令闭合全套WES处理与最终输入。

**复现合同**：保留匹配tumour/normal标识、参考基因组、候选变异表、segment表、正常panel及过滤日志。WES的组织层面混合意味着小群体事件可能低于检出限；WES未检出不能无条件否定局部RNA信号。

## 4. Visium RNA-CNV：正常参考和区域标签是关键输入

【P】inferCNV 1.10.1使用QC后raw counts。对于Visium，选200个已标为non-malignant且ESTIMATE纯度最低的spot作为参考；恶性spot用microregion ID注释；声明参数包括：

```text
window_length = 151
analysis_mode = sample
cluster_by_groups = TRUE
denoise = TRUE
HMM = TRUE
```

单核/单细胞分支使用非恶性细胞参考，其模式文字另行记载，不能把Visium配置直接移用。CalicoST以微区域ID作为最小分析单元，Methods称使用默认参数并人工检查。依据：Methods: InferCNV and CalicoST for CNV calling on Visium ST data。

【C】活动脚本：[Figure2/1_inferCNV_run.R](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure2/1_inferCNV_run.R)。可确认`CreateInfercnvObject`和`infercnv::run`，后者包含`cutoff=0.1`、`mask_nonDE_genes=TRUE`、`resume_mode=FALSE`、8线程；这些是所读代码的活动参数，不自动是每个最终样本的参数。

### 四个不能省略的检查

**原始矩阵是哪一个assay？** `GetAssayData(obj, slot="counts")`未显式写assay，因此依赖输入对象DefaultAssay。必须核对实际矩阵，不能只看到counts就确信是未变换Spatial计数。

**参考真的来自正常区域吗？** 代码含参考不足时的回退分支；纯度最低不等于已获DNA正常证明。并列纯度还可能使按阈值选出的spot多于名义数量。

**谁覆盖了谁的参数？** 顶部示例、CLI默认值和解析后的参数并不相同。完整命令比顶部变量更接近实际调用，最终日志/对象才可绑定某个结果。

**不同模式的标签是否一致？** 参考筛选修改`Filtered_tumor_regions`，而另一个模式可能使用`tumor_normal`。必须检查真正交给inferCNV的annotation，而不是只检查对象里某一列。

【C】上述检查依据脚本的参数解析、参考选择和run调用；未用真实对象触发这些分支。

【C】[Figure2/2_CalicoST_run.md](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure2/2_CalicoST_run.md)只有上游工具链接，没有本研究样本配置。可以说明其角色，不能声称已恢复最终CalicoST命令。

## 5. 原文定义的有符号CNV相似度

【P】将两个样本的segment分割成可对应的基因组窗口。对每个窗口编码gain=+1、neutral=0、loss=−1；只在至少一方非中性的窗口集合U内计算：

\[
S(A,B)=\frac{\sum_{i\in U}w_i a_i b_i}{\sum_{i\in U}w_i}.
\]

其中w为窗口长度。依据：Methods: Copy number profile similarity score calculation。

【I】这不是普通0–1集合Jaccard。相同方向异常贡献正值，相反方向贡献负值，单方中性贡献0；若全部中性则分母为0，公式未定义，不能擅自当成完全相同。

【P】FFPE流程先与WES比较筛选可信空间事件，随后计算相似度，以`hclust(d=1-S, method="ward.D2")`聚类，`cutree(h=0.8*max(height))`切树，并人工审查。OCT则由CalicoST联合识别CNV并归组。依据：Methods: Spatial subclone identification based on CNV profile similarity。

**统计解释提醒【I】**：Ward聚类对距离几何有要求；有符号或概率加权相似度转成`1-S`后不应未经检查就认定为标准欧氏距离。应保存距离矩阵、检查对称性/对角/特征值，并以其他合理linkage或阈值做敏感性分析。此处是建议，不是本次已经完成的患者数据检验。

## 6. 本轮新增：公开活动实现不等于上述公式

【C】本轮审读了[Figure2/3_CNV_jaccard_similarity.R](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure2/3_CNV_jaccard_similarity.R)的两个函数及后续调用：

- `CNV_profile_jaccard()`：只对同向异常交集计正贡献；分母构造包含A全部非中性事件及B的缺失事件，未对称纳入B全部非中性事件。
- `CNV_profile_jaccard_prob(mode="pred"/"all")`：对扩增和缺失分别构造区间，并使用状态一致性与概率权重；与原文有符号乘积不是同一个统计量。
- 脚本实际生成`jac`、`jac_pred`、`jac_all`；后段`distmat_selected = jac_pred_mat`，随后以K=2…MAX_K探索并调用`maptree::kgs`。所读文件没有将这一选择与论文声明的最终0.8×最大树高切分闭合。

**必须分别保留两个判断**：硬调用函数存在明确的不对称构造风险；后续选中的概率矩阵与论文公式不同。不能把前者未经追踪直接说成最终克隆结果错误。

### 最小反例【I/T】

等长窗口：A在第一个窗口扩增，B在两个窗口扩增。

| 计算对象 | A,B | B,A |
|---|---:|---:|
| 原文公式 | 0.5 | 0.5 |
| 硬调用函数的单位格网等价逻辑 | 1.0 | 0.5 |

在同一个窗口A扩增而B缺失时，原文公式为−1；`mode="pred"`的单窗口等价逻辑为0。因此即使完全不讨论硬调用分母问题，概率路径也不能被直接称为原文公式的实现。

这些数值由本目录独立的[合成检查脚本](../scripts/evidence_sanity.py)核验。**脚本不是GenomicRanges的完整移植，没有执行原R函数，没有读取真实CNV矩阵。** 它证明例子中的定义差异，不证明原结果效应大小或标签改变。

## 7. 将WES变异映射到ST/snRNA

【P】作者使用scVarScan/10Xmapping跟踪覆盖候选位点的参考与变异reads及条码；Visium比对文件预筛`xf:i:25`。候选来自WES，不是在空间RNA上进行完全无偏的变异发现。见Methods: Mutation mapping to snRNA-seq and ST data。

【P】每个位点的空间覆盖超过30 reads后，汇总tumour与non-tumour区的变异reads/总reads，做以非肿瘤VAF为背景的单侧binomial test；不同空间克隆之间使用双侧`prop.test`；随后多重校正。见Methods: Spatial mutation VAF statistical test。

【C】入口：[Figure2/6_mutation_mapping.sh](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure2/6_mutation_mapping.sh)，本目录只确认路径，未完成scVarScan源代码及该样本的read/UMI处理审计。

【I】应明确计数单位是read还是去重分子。多个read、spot或同一患者的区域不是独立动物/患者。RNA VAF显著不同支持空间分布差异，但不能自动换算成DNA克隆占比。可进一步检查覆盖差异、表达丰度和等位基因偏倚。

## 8. Xenium位点验证：有力但目标受限

【P】作者依据预先选定转录变异位点设计WT与变异探针，并用匹配组织验证空间定位；具体探针可行性筛选在Methods: Xenium probe design。Fig. 2j是LDHB位点案例。

【I】它的价值在于对身份锚点增加原位测量，而不是把所有Xenium转录本都变成可用于全基因组CNV/BAF的测序reads。普通表达面板、定制等位基因探针、Visium RNA-seq BAM三个输入不能互换。

阴性结果需要同时考虑：该位点是否被测、该细胞是否表达、WT与variant检测效率、组织分割、背景和图像配准。一个位点支撑身份不等于说明该位点具有功能作用。

## 9. 应交付的遗传分析中间件

【H】真正复现应保存：raw counts身份及assay、正常参考ID、基因坐标版本、microregion标签、连续/离散CNV、BAF及覆盖、WES筛选前后事件、相似度矩阵、切树和人工复核记录、WT/variant原始计数、最终clone标签及不确定状态。

只有彩色克隆图，无法审查参考选择、阈值敏感性、事件被删除的位置或人工合并理由。缺少这些中间件时，可以精读研究逻辑和审读代码，但不能声称已复现最终亚克隆。
