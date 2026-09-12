# 02｜数据、测量尺度、样本层级与可测性

[返回总目录](../README.md) · [上一章](01_story_and_design.md) · [下一章](03_cnv_and_variant_protocol.md)

## 1. 队列概览与不能强行合并的分母

【P】摘要与“Spatial microregions across cancers”报告131张Visium切片、78个病例、98个组织块、48份匹配单核RNA数据和22份匹配CODEX数据。六个癌种的切片数分别为BRCA 54、CRC 30、PDAC 23、RCC 12、UCEC 5、CHOL 7；它们合计131。[Fig. 1a–b与正文](https://www.nature.com/articles/s41586-024-08087-4/figures/1)

这不是131个独立患者，也不是每个病例都有所有模态。不同模块使用不同子集：Fig. 2b图注为125张可检测CNV切片、74个病例；Fig. 2c图注为60张OCT切片、29个病例上的变异映射。必须逐模块恢复样本名单，不能把总体数字填入每一个检验的n。

### 原文计数存在尚未闭合的口径问题

以下保留原文各位置的原意，**不选择一个数字替其他位置纠错**：

| 主题 | 公开正文/图注中出现的表述 | 当前处理 |
|---|---|---|
| 空间队列 | 正文写50个spatially distinct sections、82个diffuse samples；二者数值相加为132而非131 | 单位或重叠未闭合；等待逐样本Supplementary Table 1核对 |
| 三维材料 | 摘要写48 serial ST sections from 16 samples；前部正文写15 tissue blocks；三维结果段写11 ST specimens参与PASTE2 | 可能涉及子集与单位差异，但没有可核清单前不推定解释 |
| COMMOT | 结果段写18 cases、39 sections；Fig. 3e图注另出现25 spatially distinct cases | 不将其中一个数字当所有通信分析的统一样本量 |

依据：[原文摘要、“Spatial microregions across cancers”、“3D tumour structure and TME interactions”及Fig. 3图注](https://www.nature.com/articles/s41586-024-08087-4)。这些是**材料口径待核**，不是已证明样本造假，也不意味着所有结果不可读。

## 2. 各模态实际测了什么

| 模态 | 测量对象 | 本研究主要作用 | 关键不可见部分 |
|---|---|---|---|
| H&E | 形态与组织结构 | 定义恶性区域、判断结构、提供配准锚点 | 不直接测基因型与功能 |
| Visium | 多细胞spot的转录本或探针计数 | 空间CNV、表达程序、去卷积、区域关系 | 本队列并非单细胞分辨率；RNA不等于DNA |
| snRNA/Multiome中的RNA | 离散细胞核的表达 | 参考注释、表达来源、CNV辅助 | 原位邻接丢失；参考可能缺失状态 |
| WES | 组织层面DNA变异与拷贝数 | 候选遗传事件、CNV支持与部分筛选 | 混合样本中稀有/局部事件受检出限制 |
| CODEX | 多通道蛋白图像及分割细胞 | 细胞组成、蛋白层支持、三维组织环境 | 面板和门控限制标签分辨率 |
| 定制Xenium | 选定基因/等位基因转录本位置 | Fig. 2j位点特异性原位支持 | 未被选中、未表达或探针不可行的变异不可见 |

【P】范围、用途及限制来自原文Fig. 1–5、Discussion、Methods: ST preparation and sequencing、Mutation mapping、Xenium probe design、Cell-type annotation of CODEX imaging data。[原文](https://www.nature.com/articles/s41586-024-08087-4)

【I】“多模态”只有在错误路径相对不同、且数据依赖关系被记录时才增加验证价值。WES先参与事件筛选，再与筛选结果比较的一致性，不是完全独立的外部验证。

## 3. 必须分开的八类单位

| 单位 | 含义 | 统计和解释边界 |
|---|---|---|
| case / participant | 病例/患者 | 跨人推广通常需要回到这一层级 |
| tissue block / piece | 同一患者的取材块 | 同一人的不同块不是独立患者 |
| section | 某个z位置的切片 | 连续切片是重复空间观测，不是时间点 |
| microregion | 形态及位置定义的恶性区域 | 不自动等于克隆；多个区域可能属同克隆 |
| spatial subclone | 遗传证据支持的区域分组 | 检测分辨率有限；clone 1跨患者无对应关系 |
| tumour volume | 跨层相连的区域集合 | 几何连通体，不是祖先—后代链 |
| neighbourhood | 局部多模态特征组成的类别 | 不是细胞类型、基因型或预先存在的真值 |
| spot / cell / patch / voxel | 不同测量和模型网格单元 | 不能彼此换算成独立细胞或重复 |

前五类与三维单位定义依据原文Methods；统计边界为【I】。分析结果至少应保留患者、组织块、切片、区域、局部单位的嵌套关系。

## 4. 面积不是捕获圆面积

【P】原文的微区域面积使用每个Visium格点平均覆盖面积8,660 μm²，而不是直径55 μm捕获圆本身的面积：

\[
A_{region,mm^2}=n_{spots}\times8660/10^6.
\]

这是依据100 μm中心间距的六角格网面积定义。参见Methods: Average spot area and microregion size calculation。

【I】以捕获圆面积代替会改变区域大小和密度的分母。迁移到Xenium时也不能继续按“每个细胞等于一个固定面积”计算肿瘤面积；应使用可分析组织mask与物理坐标。

## 5. 深度既有几何意义，也有选择机制

【P】原文分层从邻接非恶性区域的恶性spot开始；对受到捕获窗口、组织边缘和空洞影响的点进行排除，并排除少于3层或50个spot的区域。参见Methods: Spot-depth correlation analysis。

【I】这意味着深度分析主要描述可形成足够深度、且未严重截断的区域。它不直接描述弥散、小癌巢或被窗口切断的所有肿瘤。跨时期比较时，早期更多小区域而晚期更多大区域，就可能产生分析资格随时期改变的问题。

需要保存排除前后的区域数、面积、细胞数与排除原因，而不只是最终一张差异表。

## 6. 数据处理的边界不能由“常规流程”补齐

【P】Methods记载Space Ranger 1.3.0、2.0.0、2.1.0及GRCh38 reference 2020-A；Seurat载入后使用SCTransform，并用前30个主成分构建聚类。基因组CNV分析使用原始计数。[Methods: ST data processing; InferCNV and CalicoST for CNV calling](https://www.nature.com/articles/s41586-024-08087-4#Methods)

【C】仓库还含有名为`spaceranger.v2.1.1.sh`的文件。文件名和论文版本文字不是同一层证据，也不自动代表所有样本实际用了2.1.1。

【I】SCTransform的存在不构成批次已被充分消除的证明。本文没有核清的QC界值、最终命令和对象版本继续记为未知，不补入其他项目常用的线粒体比例、UMI数、Harmony设置或Leiden分辨率。

## 7. 必须保存的最小元数据

【H】[sample_manifest.tsv](../templates/sample_manifest.tsv)是迁移用模板，不是作者原始列名。最低需要：

`biological_id, timepoint, block_id, section_id, z_um, modality, preservation, batch_id, panel_id, raw_data_path, coordinate_unit, reference_id, annotation_version`。

对于候选基因/程序，另用[measurement_status.tsv](../templates/measurement_status.tsv)区分未测量、测量但不可检验、检验后证据不足和有方向性证据。不能把面板未覆盖、低表达与生物学无效应统称为0。

## 8. 数据获取与当前范围

【P/C】原论文Data availability及主仓库`Data_access/README.md`、`Sample_ID_Lookup_table_v1.xlsx`给出HTAN、GDC等数据对应入口。参考入口：[主仓库Data_access](https://github.com/ding-lab/ST_subclone_publication/tree/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Data_access)。

本次没有取得或逐行核验全部公开原始数据与完整样本对照表；“有访问入口”不等于“已下载且校验”。补充PDF及表格入口已定位，但本轮获取失败，涉及它们的具体数值不自行补写。所有额外数据和代码访问限制集中记录于[缺口表](../evidence/gaps.tsv)。
