# 05｜三维结构、Mushroom与CODEX：测得了什么，模型补了什么？

[返回总目录](../README.md) · [上一章](04_state_boundary_and_interactions.md) · [下一章](06_five_transferable_insights.md)

## 1. 本文有两条三维路线，不应混成一个算法

【P】最终Fig. 4是连续Visium微区域的连接拓扑；最终Fig. 5是局部多模态邻域及肿瘤接触关系。对应Methods: Serial section alignment and branching factor calculation，以及Neighbourhood identification相关小节。[Fig. 4](https://www.nature.com/articles/s41586-024-08087-4/figures/4)；[Fig. 5](https://www.nature.com/articles/s41586-024-08087-4/figures/5)

| 路线 | 起点 | 主要中间件 | 主要结果 | 不是 |
|---|---|---|---|---|
| PASTE2拓扑路线 | 相邻Visium切片、微区域标签 | 配准坐标、最近spot配对、跨层区域边 | 连通体、degree、loop | 活细胞谱系与迁移轨迹 |
| Mushroom邻域路线 | 已配准多模态组织特征 | patch表示、分层邻域概率、插值体积 | 邻域类别、接触比例、表面特征 | 连续实测的单细胞三维体积 |

【I】两条路线都应先确认z轴实际间距、组织截断与配准误差；仅知道切片编号U1、U2不能推断相同厚度或等距采样。

## 2. 路线一：PASTE2→相邻spot→微区域连接图

【P】作者对同一组织块的相邻切片两两配准，获得新坐标；为每个spot寻找相邻切片的最近spot；移除基质spot后，若两个区域在相邻切片间有超过3个共享/连接spot，就判为同一三维volume的一部分。依据：Methods: Serial section alignment and branching factor calculation。

【C】对应仓库旧目录[Figure5](https://github.com/ding-lab/ST_subclone_publication/tree/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure5)，具体路线：

```text
1_run_PASTE2/src/1_runPASTE.py
→ 2_PASTE2_analysis/2_get_matching_spot/script/1_get_matching_spot_batch2.r
→ 2_PASTE2_analysis/3_multi_section_regions_N_min_3/script/1_get_multi_section_regions.r
→ 2_PASTE2_analysis/4_mergeobj_and_3dcluster_N_min_3/script/1_merge_seurat_add3dcluster.r
→ 2_PASTE2_analysis/5_calculate_metrics/script/1_get_metrics.r
```

本轮确认以上路径及README处理关系，未逐行闭合整条运行链。`N_min_3`目录名本身不能证明实际判断是`>3`还是`>=3`；应检查活动谓词及最终调用。

### 图论量如何解释

【P】每个微区域是一个节点，跨相邻切片连接是边；degree为相邻连接数，volume最大degree表示局部最大分支连接。对单一连通体，loop量为：

\[
\beta_1=E-V+1.
\]

【I】若在多个连通分量上一次计算，一般形式为E−V+C，其中C为连通分量数。该量是图的独立回路数，不是细胞曾经绕行的次数，也不是进化树的回溯次数。

### 必须考虑的反例

两片之间真实的小连接可能恰好落在未采样区间；组织形变可能使最近spot配对产生跨区域连接；阈值从3变4可能使很小连通体合并或分开。这些并不使重建无价值，但说明拓扑应附带配准和阈值敏感性，而不是只展示一个最终Sankey图。

【H】最小检查是保存边表并比较数个合理连接阈值，记录主要volume是否稳定；同时保留未经插值的各切片证据。不同小鼠不同时间点之间不能因形状相似就沿用本路线连成一个肿瘤volume。

## 3. 路线二的起点：先配准，再学习邻域

【P】多模态配准使用BigWarp/Fiji，以DAPI或H&E选锚点；图像缩小5倍，逐相邻切片注册，每次4–20个关键点；导出的位移场放大后作用于原分辨率图像。依据：Methods: Registration of Visium, CODEX and H&E serial sections。

【I】逐层传播的形变可能积累误差。应保存landmark、位移场、配准前后图像、未用于配准的检查点和局部组织缺失mask。位移场不是普通坐标平移；配准后的距离也需明确属于哪个物理坐标系统。

## 4. Mushroom的输入表示

【P】Visium保留在跨切片至少5% spots中表达的基因并log2变换；各模态按特征标准化。CODEX/H&E patch取像素通道平均，Visium patch则对落入局部范围的spot按距中心距离加权。依据：Methods: Neighbourhood identification input preprocessing。

【I】此时分析单位已经从细胞或spot变为patch。patch表达是局部汇总，不能把邻域中某个高表达基因直接定位到具体细胞。不同模态的覆盖与尺度不一致，也不能靠共同输入张量自动消除。

## 5. 模型结构及损失的准确解释

【P】作者描述ViT骨干自编码器，将局部patch编码为表示，并通过分层codebook生成邻域概率；三层可容纳8、32、64个邻域，展示使用第3层。损失兼顾输入重建与z方向相邻patch的邻域一致性：

\[
L=\lambda_{NBHD}L_{NBHD}+\lambda_{MSE}L_{MSE}.
\]

重建权重为1.0；邻域权重从0线性增到最高0.01。依据：Methods: Neighbourhood identification model architecture、Model loss function。

【I】这意味着跨层一致性不是完全独立的发现，而部分是训练目标。Methods还包含关于编码分布及正态分布的描述；本次未审读完整损失实现，不能仅由这种文字给模型补写完整VAE/KL公式或宣称数学实现已验证。

【C】已读固定快照的[mushroom/mushroom.py](https://github.com/ding-lab/mushroom/blob/fde4dd8c91636629b1acab4473e1773468dcc1d8/mushroom/mushroom.py#L29-L74)含DEFAULT_CONFIG，例如`num_clusters=(8,4,2)`、`neigh_scaler=.01`、`recon_scaler=1`、batch size128、lr1e-4。它们是库默认值，不代表最终病例的全部训练参数。层级容量与每层细分数也不能混为一谈。

## 6. 实际训练notebook的边界

【P】Methods对HT397B1使用6张H&E、4张CODEX、2张Visium；对HT268B1使用4张Visium。不同模态分别训练后再整合，超参数指向Supplementary Table 4。

【C】[step3_train_mushroom_cancer_v2.ipynb](https://github.com/ding-lab/mushroom/blob/fde4dd8c91636629b1acab4473e1773468dcc1d8/notebooks/manuscript/submission_v1/step3_train_mushroom_cancer_v2.ipynb)可确认`Mushroom.from_config`、`train`、`embed_sections`和`generate_interpolated_volumes`的调用。已读快照中`cases`清单全部注释，配置依赖外部`registered/metadata.yaml`；有特定样本模态权重/切片排除映射和GPU设置。

因此，notebook展示了调用结构，但不是绑定最终病例及数据的开箱即跑入口。不能将邻域分辨率数组、训练步数辅助函数或DEFAULT_CONFIG直接列为论文最终超参数。

## 7. 插值、整合、邻域筛选与接触

【P】训练后对重叠tile推理，并取中心patch重拼；随后线性插值邻域分配概率以填充z方向间隙。多个模态的邻域组合构图后用Leiden整合。最终将spot中心映射到邻域标签。TME相关邻域筛选排除与肿瘤clone重叠>50%或跨切片覆盖少于10个spot的类别。依据：Methods: Model training and inference、3D neighbourhood construction and integration、Analysis and quantification of 3D neighbourhoods。

【P】clone边界采用最外层及向外扩展一层的联合区，论文以约100–150 μm描述该界面；clone相关接触比例又以最外层重叠统计。因此“边界用于什么分析、分母是什么”需要逐输出记录，不能只保留一个boundary标签。

### 尺度文字存在量纲冲突

【P】Methods一处写50 pixels μm−1，同时括号解释每个patch宽50 μm；Visium有类似100的表述。两者互为倒数关系而不是同一单位。本目录不悄悄改写成已确认的最终尺度。

【H】复现时必须用图像metadata、物理尺度、实际配置及已知距离核实`μm/pixel`与`pixel/μm`。这个问题与“默认配置用0.02、notebook使用50”不能仅靠数字相近自行解决；需要追踪转换函数。

## 8. CODEX：分割和门控也是测量的一部分

【P】作者把qptiff转成OME-TIFF，用DeepCell/Mesmer核＋膜分割；DAPI为核通道，多种可用膜相关通道取平均。每张图像人工设置marker强度阈值，再计算细胞内阳性像素比例；大于5%则认为该细胞marker阳性，依样本的AND门控顺序分类。缺失精细marker时退回更粗类别，全部不满足则unlabelled。依据：Methods: Cell-type annotation of CODEX imaging data。

【C】[multiplex_imaging_pipeline/segmentation.py](https://github.com/estorrs/multiplex-imaging-pipeline/blob/c351da1d41e284eef2f732b3553e5602438ed978/multiplex_imaging_pipeline/segmentation.py)的`segment_cells`调用Mesmer，并含切块、边缘删除和重叠合并逻辑。所读2025快照的默认膜通道列表与Methods列举的实际通道并不相同；不能用当前默认覆盖历史实验设置。

【I】门控阳性、耗竭marker升高和功能耗竭不是同一级证据。人工阈值可能缓解强度差异，也可能引入操作者依赖；应保存每图阈值、marker缺失情况、门控顺序及unlabelled比例。

## 9. 肿瘤表面mesh是多步骤派生对象

【P】HT268B1按邻域中clone标注spot比例>60%选肿瘤；HT397B1按CODEX上皮细胞比例>60%选肿瘤。二值体积随后Gaussian平滑（sigma=1.0），用marching cubes生成mesh；特征体积在z方向插值后为表面着色。依据：Methods: 3D tumour volume reconstruction and location quantification。

【I】相同“肿瘤表面”在两个病例中使用了不同判据；上皮比例也不自动等同于恶性比例。平滑可能合并细小间隙；着色值也不是该表面每一点的直接原位测量。

## 10. 哪些结果增强判断，哪些不能过度解释？

【P】HT397B1不同clone附近的TME邻域在T细胞、成纤维等特征上不同，并在配对CODEX和三维展示中得到支持。见Fig. 5e–h。

【I】最稳妥的结论是：局部生态差异与空间遗传群体相联系，并具有跨切片组织一致性。不能仅据此说某种成纤维状态造成克隆冷区，或immune-hot就意味着有效杀伤。

【H】最有区分力的复查包括：留出整张切片验证、减少跨层一致性权重、改变配准/连接/肿瘤阈值、仅在实测切片计算同一指标。只有训练目标中的连续性、没有留出数据支持时，应降低对具体拓扑的确信程度。
