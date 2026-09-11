# 04｜见解三：让邻居成为功能基因组学的筛选终点

[返回总目录](../README.md) · [上一章](03_ecm_as_signal_surface.md) · [下一章](05_statistics_and_causal_inference.md)

## 1. 从“敲除后自己怎样”到“敲除后局部生态系统怎样”

普通增殖筛选的主要终点是扰动细胞是否减少。空间功能筛选扩展为：扰动细胞的位置、周围细胞的组成与状态、相关胞外材料，以及这些改变最终如何反馈到扰动群体。

作者用 Perturb-map 将扰动身份留在组织读取中，并将多模态分析用于转录与蛋白层面的空间表型。[原文 Fig. 1、3 及 Extended Data Fig. 6](https://www.nature.com/articles/s41586-026-11002-8) / [专属仓库 README](https://github.com/BDBrownLab/Falcomata_PDAC_2026/blob/da2fcf70b89c911728cdcd519e72a153f17e743b/README.md)

这个设计特别适合提出“作用在邻居身上”的问题，但不意味着所有分泌因子都会被无偏检出。若邻居可以补偿，混池甚至可能掩盖真实作用。

## 2. 候选集应服从问题，而不只是服从表达排名

本篇研究利用肿瘤细胞表达、胞外/表面定位及较弱的体外依赖性富集候选，之后再用组织环境检验功能。[原文候选筛选部分](https://www.nature.com/articles/s41586-026-11002-8)

移植时可使用如下逻辑，但它是设计模板，不是必须照搬的固定筛选器：

```text
研究问题是否指向细胞间/材料层面的作用？
    ↓
来源细胞是否可靠识别？候选是否在该来源中存在？
    ↓
是否有可解释的胞外作用途径，而不仅是高表达？
    ↓
体外依赖性会不会让体内结果无法区分内在生长与环境作用？
    ↓
选择有限候选并保留互补的阳性/阴性与技术控制
```

若需要发现兼具内在生长和微环境功能的基因，就不应简单排除所有体外依赖性强的候选，而应设计能拆分两种作用的比较。

## 3. Pro-Code 的角色：身份桥梁，不是功能读数本身

数据结构的关键是每个细胞有可追溯的连接：

```text
image_id + cell_id
  ├─ 坐标与分割质量
  ├─ 细胞身份
  ├─ Pro-Code / 扰动身份与置信度
  ├─ RNA / 蛋白状态
  └─ 周围细胞及材料特征
```

读到条码并不直接证明目标被充分敲除；没有读到靶基因 RNA 也不能直接证明某个细胞是 KO。条码识别、目标扰动验证与功能终点是三个独立环节。

对应作者代码：[Perturbmap_MM_deconvolute_procodes_Final.ipynb](https://github.com/BDBrownLab/Falcomata_PDAC_2026/blob/da2fcf70b89c911728cdcd519e72a153f17e743b/Perturb-map%20Multi-modal/Perturbmap_MM_deconvolute_procodes_Final.ipynb)。

## 4. 多模态数据如何被连接？

原文描述 Xenium 与后续 CyCIF 处理同一组织，借助图像流程、分割和跨模态对齐生成细胞级数据。专属仓库包含：

```text
Perturb-map Multi-modal/
    Xenium_CyCIF_alignment+preprocess_Final.ipynb
    Perturbmap_MM_deconvolute_procodes_Final.ipynb
```

[固定版本目录](https://github.com/BDBrownLab/Falcomata_PDAC_2026/tree/da2fcf70b89c911728cdcd519e72a153f17e743b/Perturb-map%20Multi-modal)

本次详细审读集中在去条码与下游表结构；没有用原始图像重新运行配准 notebook，也没有重新评价所有图像配准质量。因此不在这里编造未核实的变换矩阵、最优配准参数或匹配准确率。

去条码输入包含分开的 `cycif_cell_anndata.h5ad`、`cycif_nuclei_anndata.h5ad`，并保存了 `match_distance`、形态和坐标字段。方法上，跨模态匹配误差可以把真实来源状态贴到错误邻居身上，直接制造或削弱空间关系。因此，匹配距离、重复匹配和低质量区域应作为分析输入的一部分，而不是预处理后丢弃。

## 5. 去条码代码：从强度到扰动标签

### 5.1 实际依赖的配置

notebook 读取表型门控、背景校正和 Pro-Code—基因对应表，例如 `phenotyping.csv`、`background_correction.csv`、`gene_procode_guide_smap.csv`。这些是实验特异配置；仅复制 Python 包环境不能替代它们。[原 notebook](https://github.com/BDBrownLab/Falcomata_PDAC_2026/blob/da2fcf70b89c911728cdcd519e72a153f17e743b/Perturb-map%20Multi-modal/Perturbmap_MM_deconvolute_procodes_Final.ipynb)

### 5.2 标签间分离度

代码设置 `delta = 0.01`，使用若干核定位标签信号进行组合识别。按强度排序后，关键分离度可写成：

$$\Delta=P_{(3)}-P_{(4)},$$

其中 P(3)、P(4) 指第三强、第四强标签。实现还检查前三强信号为正。这样做是为了区分“明确的前三个标签”与含糊、接近的组合。

### 5.3 为什么要标准化标签名与组合顺序？

字典构建会规范化例如 VSVg 的大小写/连字符，并展开组合排列。这是在避免同一标签集合因字符串排列不同被当成不同身份。改写代码时也可使用排序后的规范集合键，但必须保留上游映射语义，不能随意重命名实验标签。

这些参数只在对应强度表示、背景校正和标度下有意义。不能把 0.01 当作所有平台通用的门控常数。

### 5.4 什么不能从字典直接推断？

映射字典可含额外控制或未进入某次分析的组合。原文关注的实验库规模与 notebook 字典键数不必完全相同；判断实际实验组应结合样本配置与纳入规则，不应只数代码中出现了几个基因名。

## 6. 两种空间图，不是同一种分析

### 6.1 扰动标签的混杂图

作者 R 文件：[01_single_image_clonality.R](https://github.com/BDBrownLab/Falcomata_PDAC_2026/blob/da2fcf70b89c911728cdcd519e72a153f17e743b/Perturb-map/Tissue_clonality_analysis/01_single_image_clonality.R)。

原代码关键调用：

```r
test.graph <- knn_from_coord(
  matrix_to_use = img_filtered %>% select(x, y) %>% as.matrix(),
  cell_names = img_filtered$cell_id,
  k = 50,
  distance_thresh = 75
)
```

helper 先建立有向 kNN，删除距离不满足条件的边，再按向外邻居计算不同标签比例：

$$H_i=\frac{\#\{j\in N_{out}(i):g_j\ne g_i\}}{|N_{out}(i)|}.$$

该比例高表示周围标签更混杂；低表示同标签聚集。边的 distance/weight 与统计量是否实际使用要分开看：helper 虽保存权重，`calc_nonGroupMembers` 这里计算的是邻居数量比例，不是加权平均。[utils_spatial_clonality.R](https://github.com/BDBrownLab/Falcomata_PDAC_2026/blob/da2fcf70b89c911728cdcd519e72a153f17e743b/Perturb-map/Tissue_clonality_analysis/utils_spatial_clonality.R)

同一脚本使用 mean-shift（bandwidth 250）识别空间焦点，过滤小于 50 个细胞的簇，并生成中心周围半宽 200 的示意方框。图上方框不是自动证明频率统计严格按方框归属完成；代码中的频率按 `focal_point` 聚类标签汇总。实际单位取决于输入坐标。

### 6.2 免疫邻域富集图

另一个问题是某免疫类型与某扰动群体相邻是否超过随机背景。原方法使用空间邻接与置换富集，而不是上面的同标签混杂比例。[原文 MICSSS neighbourhood Methods](https://www.nature.com/articles/s41586-026-11002-8)

概念量为：

$$Z_{ab}=\frac{N_{ab}^{obs}-\operatorname{mean}(N_{ab}^{perm})}{\operatorname{sd}(N_{ab}^{perm})}.$$

Squidpy 官方实现确实根据邻接计数与置换均值/标准差计算该量；其 `library_key` 可用于按图像限制标签置换。[官方实现](https://squidpy.readthedocs.io/en/stable/_modules/squidpy/gr/_nhood.html)

这不是配体—受体通信强度，也不直接等于因果效应。尤其不能跨样本混合坐标建边，然后仅靠在统计阶段加 sample_id 来补救。

## 7. 混池干扰：邻居补偿可能使重要基因成为假阴性

设一个细胞自身的扰动为 g，邻域暴露为 E。对于非细胞自主作用，结局更适合写为：

$$Y_i=Y(g_i,E_i),$$

而不是只写 Y(g_i)。

如果邻居仍能提供胞外因子或维持已有材料，KO 细胞可能被补偿。在混池中“没有掉队”，不一定代表该基因没有环境功能。相反，野生型邻居也可能受 KO 引发的免疫变化影响。

因此要设计两类比较：同一自身基因型、不同邻域暴露；以及不同自身基因型、相似邻域暴露。独立 KO、混合比例、空间窗口和时间分层都是拆解这一问题的互补手段。

**这里的干扰不是应无条件消除的噪声，而是研究对象。**但若忽视它，普通的细胞级独立处理假设就会被破坏。

## 8. 移植到其他基质丰富实体瘤前的可行性判断

先评估三个尺度：候选作用范围、群体区域大小、成像/测序分辨率。若作用范围远大于整个可测组织，局部暴露几乎没有变化，ROI 设计辨别力有限；若作用范围远小于分割和配准误差，则可观察的局部差异可能被技术误差抹平。

再评估读出是否覆盖：来源状态、指定材料、髓系响应、T 细胞终点。只有 RNA 不能自动回答全部材料问题；只有条码丰度不能直接解释邻居机制。

最后，保留独立宿主/患者与正交验证。增加单个肿瘤中的细胞数量主要提高组织内采样密度，不替代独立重复。伦理、动物模型和实验资源属于开展真实实验的前置条件，不由代码演示代替。

## 9. 一个合理的研究顺序【拟议扩展】

先在现有患者空间数据中识别有可重复局部关联的候选状态；再确认源细胞身份和材料证据；随后用有限候选的扰动研究环境效应，而不是一开始就无差别扩大库规模。初筛阳性需要独立扰动、邻居补偿与功能验证；初筛阴性则需检查读出缺失、来源不足、作用范围不匹配和群体补偿。

这样，筛选规模服从可识别性。一个较小但能解释邻域机制的设计，可能比一个无法区分内在增殖与共享环境的巨大筛选更有价值。

## 10. 本章的结论

**原位功能基因组学的增量，是为每个扰动同时测量“自己”和“邻居”，并把空间与时间作为因果问题的一部分。**不是把普通培养筛选搬到动物体内就自动获得这种增量。
