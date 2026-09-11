# 06｜原始代码逐层解析与复现审读

[返回总目录](../README.md) · [上一章](05_statistics_and_causal_inference.md) · [下一章](07_integrated_idea_and_execution_plan.md)

## 1. 版本与审读范围

专属仓库固定在 `BDBrownLab/Falcomata_PDAC_2026@da2fcf70b89c911728cdcd519e72a153f17e743b`。以下代码讨论均针对这一版本，不假设未来主分支相同。

代码位置优先用“文件路径＋函数名＋notebook cell id/标题”定位。notebook JSON 的行号包含输出、图片与元数据，不能简单当作展开后的 Python 行号。附带的获取脚本会生成保留 cell 编号与 id 的只读源码副本。[来源 manifest](../provenance/upstream_manifest.json)

本章是静态源码审读，以及少量隔离逻辑/语法的本地验证；不是对原始数据的完整重跑。原 notebook 中的保存输出也不能被当作本次执行结果。

## 2. 文件地图：从输入到论文问题

| 文件 | 主要输入 | 主要工作 | 对应问题 |
|---|---|---|---|
| `ScRNAseq/SERPINE1B2_per_patient_F5a-S10abgh.ipynb` | 已注释人类肿瘤单细胞 AnnData | 患者内阳性比例、强度、双阳性/并集 | 稀有来源状态是什么 |
| `ScRNAseq/SERPINE1B2_deg_F5bc.ipynb` | 恶性细胞表达及标签 | 阳性/阴性差异与通路富集 | 来源状态携带什么转录程序 |
| `Visium/01-visium_preprocessing.ipynb` | 原始 Visium | 预处理入口；需保留 counts | 空间输入准备 |
| `Visium/02-visium_integration_decon.ipynb` | 多队列空间对象、scRNA 参考 | 特征对齐、参考训练、cell2location | 推断空间细胞构成 |
| `Visium/03-visium_paper_analysis.ipynb` | 解卷积后空间对象 | compartment、阳性/阴性区域、组成差异 | 来源状态与局部环境关联 |
| `Perturb-map/CyCIF_mixing/ROI_TME_mixing.ipynb` | CyCIF 坐标、表型、图像 ID | 多边形/ROI、混合度、组成及采样 | 少数群体的局部影响 |
| `Perturb-map/Tissue_clonality_analysis/01_single_image_clonality.R` | 单图像坐标和 `gene.filtered` | kNN 混杂、mean-shift 焦点、频率 | 扰动群体如何占据空间 |
| 同目录 `utils_spatial_clonality.R` | 坐标与标签 | 有向图与不同标签邻居比例 | 上一项的实际计算定义 |
| `Perturb-map Multi-modal/Perturbmap_MM_deconvolute_procodes_Final.ipynb` | 细胞/细胞核 AnnData 与配置表 | 背景、标度、表型和条码映射 | 将扰动身份链接到细胞 |
| 同目录 `Xenium_CyCIF_alignment+preprocess_Final.ipynb` | 原始多模态图像/空间数据 | 对齐与预处理入口 | 上游身份对应；本次未完整重跑/逐图验证 |

[固定版本仓库目录](https://github.com/BDBrownLab/Falcomata_PDAC_2026/tree/da2fcf70b89c911728cdcd519e72a153f17e743b)

## 3. 患者级来源汇总：代码的变量语义

[原文件](https://github.com/BDBrownLab/Falcomata_PDAC_2026/blob/da2fcf70b89c911728cdcd519e72a153f17e743b/ScRNAseq/SERPINE1B2_per_patient_F5a-S10abgh.ipynb)

入口依赖 `anno_sub` 中的恶性细胞注释、`tissue='tumor'`、`patient_id` 和 `source`。它并不在这里从零建立恶性细胞注释。

`n_cancer` 是所纳入恶性细胞数；`n_SERPINE1_pos/n_cancer` 是检测阳性比例；`mean_SERPINE1_in_SERPINE1_pos` 是条件均值。两基因状态另有四分类函数 `make_serpin_status`。

**复现检查：**必须确认筛选后的患者数与细胞数，记录每患者 malignant 数量，输出所有阳性计数和比例，核对 counts/log1p/.X 是否一致。无阳性群体的条件均值不要自动解释成生物学零。

## 4. 阳性状态 DEG：真实参数与容易误读的部分

[原文件](https://github.com/BDBrownLab/Falcomata_PDAC_2026/blob/da2fcf70b89c911728cdcd519e72a153f17e743b/ScRNAseq/SERPINE1B2_deg_F5bc.ipynb)

实际逻辑：限定肿瘤恶性细胞；用 `obs_vector(gene)>0` 定义阳性；去掉 MT-/RPS/RPL 前缀基因；根据交叉表最小群体规模设置表达过滤；`rank_genes_groups(..., method='wilcoxon', use_raw=False)`；筛选 `pval_adj<0.05`、`lfc>1` 且阳性组的基因；用 `Reactome_Pathways_2024` 做 Enrichr 分析。

这里是细胞级状态比较代码，不是明确的患者配对 pseudobulk 模型。移植为跨患者机制结论时，应增加患者级重复性检查或配对聚合分析；不能把大量细胞产生的小 P 值视为相同数量独立患者的证据。

`min_cells=int(0.05*smallest_population)` 取决于实际交叉表。若某格为零，门槛可变成零；应报告最终值。`gseapy.enrichr(cutoff=0.5)` 也不应被直接写成论文最终显著通路标准：需要核对完整输出、最终筛选和图注，而非只看 API 参数名。

## 5. Visium 解卷积：先固定输入表示，再解释结果

[原文件](https://github.com/BDBrownLab/Falcomata_PDAC_2026/blob/da2fcf70b89c911728cdcd519e72a153f17e743b/Visium/02-visium_integration_decon.ipynb)

### 5.1 实际设置

| 环节 | 这一版本代码中可见设置 |
|---|---|
| 特征 | 空间与参考共享特征，再通过 cell2location gene filter |
| gene filter | `cell_count_cutoff=10`，`cell_percentage_cutoff2=0.03`，`nonz_mean_cutoff=1.12` |
| 参考标签 | 将细注释合并为 `anno_broad`；宏噬细胞若干亚群仍分别保留 |
| 参考 setup | `batch_key='source'`，`labels_key='anno_broad'`，`categorical_covariate_keys=['treatment']`，`layer='counts'` |
| 参考训练 | `max_epochs=250`，`batch_size=2500`，`train_size=1`，`lr=0.002`，GPU |
| 参考后验 | `num_samples=1000`，`batch_size=2500`，CPU |
| 空间 setup | `batch_key='library_id'` |
| 空间模型 | `detection_alpha=200`，`N_cells_per_location=10` |
| 空间训练 | `batch_size=10000`，`max_epochs=2000`，`train_size=1`，GPU |

这些参数是代码事实，不是本目录建议的新默认。不得将其他项目常见的 `detection_alpha=20`、每 spot 20 个细胞等设置混入这里。

### 5.2 原文与代码不完全一致时怎么办？

原文方法描述参考训练使用 sample ID 作为批次；当前代码的明确值是 `source`（cell id `ed4f33e7`）。它们只有在实际 metadata 中指向同一划分时才等价，不能擅自替作者统一。[原文 Visium Methods](https://www.nature.com/articles/s41586-026-11002-8)

代码还保存了 10,983 与后续签名形状 10,984 等不同中间输出。保存输出的执行序号不连续；在没有重跑与输入对象时，不把这些输出当作同一次完整运行的证明。应核对实际 `var_names`、过滤集合及模型签名行数，保留差异记录。

### 5.3 已确认的语法阻断与最小修正

cell id `cc1b0050` 的 `ensure_feature_name` 包含：

```python
# 原始片段：会产生 unmatched ']' SyntaxError
for cand in "gene_symbol","gene_name", "features"]:
    pass
```

可用的最小语法修正示例：

```python
# 本目录建议修正；不是伪称原作者已经写成这样
for cand in ["gene_symbol", "gene_name", "features"]:
    pass
```

本地 Python 编译检查确认原片段失败、修正片段可解析，并纳入单元测试。**这证明该固定版本源码不能在这里原样解析，不证明已发表分析结论错误。**未修改作者仓库。

### 5.4 注释规范化被覆盖

cell id `64ab8ecf` 先对标签进行字符规范化并建立 `map_norm`，但末尾又将 `anno_broad` 赋值为未规范化 `anno_sub.map(map_dict)`。若输入含空格或 Unicode 差异，前面的修复可能被覆盖。最小处理是保留一种明确映射路径，并在最终赋值后再次检查未映射标签；是否影响本文原数据要用实际标签验证。

## 6. Visium 下游：三个层次不能混成“空间共定位”

[原文件](https://github.com/BDBrownLab/Falcomata_PDAC_2026/blob/da2fcf70b89c911728cdcd519e72a153f17e743b/Visium/03-visium_paper_analysis.ipynb)

第一层是 cell2location 推断丰度；第二层是把丰度合成 Cancer/CAF/Endothelial/Other compartment；第三层才是在某 compartment 内比较候选基因相关区域。

`label_compartments_from_abundance` 根据组成得分分类，并支持按样本外部肿瘤覆盖率校准。外部比例是一个先验/校准目标；达到该目标不能作为另一次独立准确性验证。

`gene_pos_neg_in_compartment` 提供 percentile 等阈值方式。默认分支使用 `g>=threshold`；若分位数为 0，零表达点会进入阳性。因此检查最终调用、阈值分布和 mask 比单看函数名重要。

`tme_pos_vs_neg_composition` 与 `..._by_dataset` 将非癌类型重归一化，输出均值差、Cohen's d 和相应检验/FDR。按 dataset 拆分不自动等于按患者处理相关性。只有一个 Cancer 汇总列时“排除癌”容易；若迁移后有多个恶性亚型列，只找第一个以 cancer 开头的列可能遗漏其他恶性类型，需要显式列清单。

`_counts_vec` 先把整个矩阵 `toarray()` 再取单基因列，可能造成不必要的大内存占用。更合适的移植实现先切列再稠密化，同时保留行顺序与 layer 明确性。

## 7. ROI 与多边形：同一 notebook 的两个区块不要混淆

[原文件](https://github.com/BDBrownLab/Falcomata_PDAC_2026/blob/da2fcf70b89c911728cdcd519e72a153f17e743b/Perturb-map/CyCIF_mixing/ROI_TME_mixing.ipynb)

前半部分读取已经存在的 `adata.uns['ko_islands']` 多边形，计算浸润和混杂；后半部分才是从中心建立圆形 ROI 的 subsampling。

前半部分需要“上游 island builder 已运行”的前提；`IMMUNE_LABELS=set()` 默认会使汇总免疫计数为零，迁移时必须填入明确标签。前半段对所有细胞建一个空间索引，在多张图坐标重叠且未进一步按 library 限定时存在跨图混算风险。后半段 ROI 代码已按 mouse/library 循环，不能把前一风险笼统归到所有 ROI 计算。

多边形区块还存在像素大小回退值；不得据此将后半段所有半径直接解释为物理单位。对应关系详见第 2 章。

## 8. 空间混杂 R：实际统计的是有向邻居计数

[01 脚本](https://github.com/BDBrownLab/Falcomata_PDAC_2026/blob/da2fcf70b89c911728cdcd519e72a153f17e743b/Perturb-map/Tissue_clonality_analysis/01_single_image_clonality.R) / [helper](https://github.com/BDBrownLab/Falcomata_PDAC_2026/blob/da2fcf70b89c911728cdcd519e72a153f17e743b/Perturb-map/Tissue_clonality_analysis/utils_spatial_clonality.R)

`k=50` 后还施加 `<75` 距离筛选，因此有效邻居不一定是 50。图是有向图，比例使用 `mode='out'`。helper 的图顶点由留下的边端点建立，完全孤立细胞可能不在图中；不能把缺失结果自动填成完全同质（0）。

入口脚本引用 `../R/utils_spatial_clonality.R`，而仓库中的 helper 与它位于同一分析目录；运行工作目录或文件组织需要适配。这是工程路径前提，不是分析公式的改变。

## 9. Pro-Code 表型配置的待核对问题

[去条码 notebook](https://github.com/BDBrownLab/Falcomata_PDAC_2026/blob/da2fcf70b89c911728cdcd519e72a153f17e743b/Perturb-map%20Multi-modal/Perturbmap_MM_deconvolute_procodes_Final.ipynb)的保存表型表输出中，可见 `CD8 T cells → Exhausted CD8` 与 Foxp3 阳性规则关联。

这应列为需要回到原 `phenotyping.csv`、标志定义和实际使用分支核对的配置项。**不能直接照搬作为可靠的耗竭定义，也不能据一个保存输出断言本文独立 scRNA 耗竭分析全部有误。**不同分析分支可能采用不同注释；不能相互冒名顶替。

同样，核条码强度、细胞表型门控、跨模态匹配与目标敲除身份均有独立配置，应分别记录。把所有 CSV 隐藏在 notebook 当前目录，会削弱复现性。

## 10. 分级审读台账

| 等级 | 问题 | 处理方式 |
|---|---|---|
| 确定的源码阻断 | `ensure_feature_name` 括号错误 | 隔离编译验证；提供最小修正 |
| 明确的文码差异 | 参考模型 batch 文字为 sample ID，代码为 source | 查 metadata；并列保留，不擅自选一个冒充原设置 |
| 明确的实现覆盖 | 规范化注释映射被末尾未规范化映射覆盖 | 检查最终标签与空值 |
| 条件性数据风险 | percentile=0、默认空免疫标签、跨图索引 | 制作边界测试和输入断言 |
| 几何/统计边界 | ROI 半径大于边缘排除带、重叠、每类均衡采样 | 有效面积、重叠图、患者层级与采样解释 |
| 语义风险 | q05 当均值/真计数；混合度当方向性暴露 | 字段命名与公式一起保存 |
| 配置待核对 | 保存输出的耗竭表型规则、缺少实验特异表 | 获取真实配置与运行记录 |
| 复现缺口 | Fig. 5l 拟合未在 ROI notebook 提供 | 不捏造算法/系数；将新模型标为扩展 |

## 11. 附带代码与原代码的关系

`code/niche_idea.py` 是新写的教学实现：患者级汇总、显式物理单位 ROI、逐图像处理、明确分母、最远点采样和供体级因子对比。它没有冒充作者的 alpha-shape、细胞注释、图像配准、cell2location 或完整统计复现。

`fetch_original_code.py` 负责固定版本获取与 SHA 校验；原始文件不被静默修补。`test_*.py` 测的是教学程序与已识别的边界行为，而不是论文生物学。[运行说明](../code/README.md)

**最好的迁移不是机械复制 notebook，而是保留科学定义、修复工程前提，并让所有偏离原方法的地方可见。**
