# 04｜主图1–7：问题、方法、输入、代码与解释上限

[返回入口](../README.md) · [上一章](03_methods_and_parameter_contract.md) · [下一章：代码审计](05_code_audit_and_reconstruction.md)

> 本章便于按图复查，不替代第01–02章的研究逻辑。图的说明来自论文正文/图注和代码，不声称逐像素复核全部原图。所有`Data/`输入都是作者脚本**预期读取但本次未取得**的对象；所有`Results/`输出都是预期产物，不是本次产生的结果。
>
> 作者代码固定提交：`fba87dbee8dbae497b15b81a4b0fa79edccd17b2`。[固定源码目录](https://github.com/FuduanPeng/LungPCA_Code/tree/fba87dbee8dbae497b15b81a4b0fa79edccd17b2) · [论文正文与图注](https://pmc.ncbi.nlm.nih.gov/articles/PMC12980502/)

## Fig.1｜空间图谱建立的是研究对象，不是演进方向

【P】Fig.1A为设计；1B为病理/细胞区域的spot组成；1C–D展示区域表达；1E为高分辨率预测表达的组织定位。

【C】[Figure 1.R](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%201.R)读取`Figure 1B.rda`中的`sankeypt/barpt/boxpt`，调用Sankey、条形图和箱线图；1C读取`Figure 1C.downsample_25_percent.rds`后`DimPlot/FeaturePlot`；1D读取`Figure 1D.rds`后`pheatmap`。没有QC/整合/聚类上游实现。

【C】[Figure 1E 4F.py](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%201E%204F.py)的`load_pickle/load_image/plot_super`读取样本mask与gene矩阵，逐图min–max后输出。示例包含`P24_LUAD.AGER.pickle`、`P15_MIA.COL14A1.pickle`。不是iStar训练脚本。

【I】显示分离不等于病理分支；颜色鲜艳不等于跨样本表达更高；更多预测像素不增加独立测量。1C的`seurat_obj/dseurat_obj`命名风险详见下一章。

## Fig.2｜来源关系与状态关系应交叉，而非互相替代

【P】2B–C比较不同克隆结构及代表病例的树、CNA、病理、位置与状态排序；2D将变异信息对应到演进模式。

【C】[Figure 2.R](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%202.R)直接加载`Figure 2B.rda`中的`Pattern_1a_1`等绘图对象；`Figure 2C.P20.rda`、P3、P23对象含`PhyloTree/plot_mat`等；2D从预制矩阵调用`oncoPrint`，再拼图。

【C】[Figure 2C.py](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%202C.py)读`Figure 2C.pkl`；`plot_category`显示Histology/Clone；`plot_continuous`显示Pseudotime/CytoTRACE_Score。样本循环包括P3、P20、P23的配对病灶。没有重新求CNA、树、拟时序或变异。

【I】样本级WES旁证与spot级推断要分开。阴性共享检测可能来自采样或检测能力；“共同祖先”不等于“一份切除的癌前组织就是另一病灶的直接祖先”。

## Fig.3｜KAC/RPII的价值在于多层定位，不在于一个名字

| 面板 | 【P】问题/展示 | 【C】活动代码与预期对象 | 【I】不可升级的结论 |
|---|---|---|---|
| 3A | 上皮类型与中间状态 | `Figure 3.R`读`Figure 3A.rds`后DimPlot | UMAP中心位置不是必经祖先 |
| 3B–D | 类型、拟时序、潜能排序 | `Figure 3B-D.downsample.rds`→`plot_cells`；L28–40 | 没有上游图学习与root记录，不能验证方向稳健性 |
| 3E–G | 程序及不同状态的组成 | `Figure 3E.rda`、3F/3G rds→热图、饼图 | NMF程序不是已知生化通路 |
| 3H–I | 病理/患者中的程序分布 | 3H/3I rds→比例箱线/堆叠图 | 组成变化不唯一代表细胞状态转换 |
| 3J | RPII相关程序 | 3J rds→比例图 | 混合程序不证明不可逆恶变 |
| 3K–L | 程序、病理、克隆在空间对齐 | `Figure 3K 3N.py`及3L rds | argmax标签不意味着状态真实离散 |
| 3M–N | RPII克隆类别与KAC分数 | 3M rda；P12_AIS_RPII_clone | 标签冲突需核对，不能据源码宣布正式图错 |

源码：[Figure 3.R](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%203.R)、[Figure 3K 3N.py](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%203K%203N.py)。后者从`Figure 3K 3N.pkl`取`stacked_MPs`，逐像素按最高分对应颜色，不拟合NMF。

## Fig.4｜由状态程序生成候选环境解释

【P】4A为KAC相关通路；4B为MP与病理/组成及MP彼此关系；4C为配对关系汇总；4D为IL1R1；4E为CytoSignal空间边；4F为候选基因预测表达图；4G为程序空间叠加。

【C】[Figure 4.R](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%204.R)依次读4A rds、4B/4C rda、4D rds、4E rda。4B的`MPs_corr`与Ro/e表已存在；4E仅`plotEdge`，输入对象为`P24_AAH_cs/P24_LUAD_cs`，`slot.use='GauEps-Raw'`。4F复用`Figure 1E 4F.py`；[Figure 4G.py](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%204G.py)读取4G pkl并做最高分着色。

【I】通路富集不等于直接测量通路活性；转录本不等于分泌蛋白；空间边不等于真实信号通量。这里生成的应是有位置约束的候选解释，后续扰动才增加功能证据。

## Fig.5｜从样本均值走向中心条件化的空间关系

【P】5A–C定义细胞及肺泡状态；5D/E比较中心的邻域组成/特定巨噬细胞数量；5F组织和转录本定位；5G–L独立TMA验证。

【C】[Figure 5.R](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%205.R)读取：

- `Figure 5A.rds`：展示下采样对象，而非声明全部空间分析下采样；
- `Figure 5B 5C.rds`：lineage、KAC_signature、Inflammatory_pathway；
- `Figure 5D.rds`：center_cell_type×neighborhood_cell_prop；
- `Figure 5E.rds`：center_cell_type×Myeloid_C15；
- `Figure 5G.rds`：block_info$Pathology；
- `Figure 5H.rds`：验证UMAP；5J/5K rds：组成与Mac_C4_IL1B。

`geom_violin(adjust=15)`是密度显示平滑参数，不是空间邻域半径。源码未构建80 μm邻域，也未显示5E/5K图注全部检验。5F/5I/5L明确由Xenium Explorer制作。

【I】发现C15与验证C4不能按编号合并；炎症评分高不自动等于KAC身份；细胞/邻域/患者/病灶/core不同。论文有局部比较，但背景匹配、有效面积和独立样本效应还需原始对象核验。

## Fig.6｜跨物种位置、方向摘要及培养功能

【P】6A为设计；6B–D为小鼠状态/通路/受体相关特征；6E–F为病理与程序；6G为通信方向；6H–K为培养设计、图像和数量/大小终点。

【C】[Figure 6.R](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%206.R)读`Figure 6B 6D.rds`、6C rds、`Figure 6J 6K.rda`。数量/大小来自`number_mat/size_mat`，脚本调用两两t检验；不是从培养图像重新检测对象。

【C】[Figure 6E 6F 7D.py](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%206E%206F%207D.py)读预制pkl；6F各样本独立70/90分位，双高区域单独标记，其余按分数/规则显示。[Figure 6G.py](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%206G.py)读6G pkl后计算`communication_direction(k=5)`，再`plot_cell_communication`。这是计算方向摘要，不是整个COMMOT求解。

【I】培养支持条件、体外标签诱导和>100 μm计数阈值必须与结论一同携带。Fig.S8G–I受体删除是重要独立功能证据，应与主图一起读，不能因未出现在13个制图脚本中而遗漏。

## Fig.7｜干预是否改变病变与环境

【P】7A窗口；7B/C终点；7D空间组织；7E–G上皮状态；7H/I组织免疫成像及巨噬细胞比例。正文对S8J的阴性移植结果限制情境外推。

【C】[Figure 7.R](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%207.R)注明7B/C使用Prism，7H使用ImageScope。7D复用空间脚本；7E–G读`Figure 7E 7F 7G.rda`；7I读`Figure 7I.rds`与`macro.Frac`。`mat_7mo`标题仍为3 months是脚本冲突，不是运行时观察。

【I】比例下降与绝对细胞减少不同；状态下降与肿瘤下降共现不证明该状态是中介。core数量/分组与mouse映射见待解决问题。联用效果不等于已完成药理协同检验。

## 怎样使用这张地图

准备复现一张图时，先拿到此处列出的Data对象；若要复现该图支持的科学主张，还必须回到上一章的上游方法和第05章的缺口。任何一份制图输入都不能替代被它概括的原始证据。机器可读的27单元清单见[traceability.tsv](../references/traceability.tsv)。
