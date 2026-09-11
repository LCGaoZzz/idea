# 04｜G–P 扩散轴、空间邻域和区室聚合：数学与活动代码

[返回入口](../README.md) · [固定来源与代码表](../05-evidence/01-sources.md)

> 【代码事实】均指固定 commit `a97d1a42cede4c12416875a4aa50d3d63ee1fffd` 中已读取的函数和单元。公式是对这些片段的数学转写。未运行作者代码；对主图生成的完整平滑/分箱实现不作补写。

## 1. 三个对象必须首先分开

**表达图**连接表达状态相近的细胞，用于表达嵌入、扩散坐标或表达状态差异丰度。

**物理空间图**连接同一切片上实际距离较近的细胞，用于局部环境聚合。

**实验设计矩阵**由独立动物/患者、处理、阶段及协变量构成，用于组间推断。

这三个对象即使都被称为“neighborhood”或有相似行数，也没有相同统计含义。不能用物理图替换 Milo 的表达图，也不能把空间图的节点数替换设计矩阵中的独立重复数。

## 2. G–P 轴的输入与活动配置

定位：[Step08 完整固定文件](https://github.com/dpeerlab/p53-niche-dynamics/blob/a97d1a42cede4c12416875a4aa50d3d63ee1fffd/transcriptomics/notebooks/Xenium_Preprocessing_step08_diffusion_components_locked20260318.ipynb)，重点为 cell id 5、10、12、13、15。

| 字段 | 活动值 | 严格含义 |
|---|---|---|
| `selected_tier` | `tier3` | 样本子集编码，成员仍须查 manifest |
| `selected_subset` | `Premalignant0` | 特定上皮状态集合，不是所有细胞 |
| `selected_layer` | `raw_in_nucleus` | 上游对象选择标签，不能替代整个预处理审计 |
| `use_log` | `False` | 该活动分支的配置 |
| `explained_var` | `0.75` | 用于定位/选择 PCA 产物，不是固定 PC 数 |
| `cluster_n_neighbors` | `30` | 表达邻居配置 |
| `umap_n_neighbors` | `10` | 对应可视化产物配置 |
| `umap_min_dist` | `0.1` | 同上 |
| 扩散活动调用 | `n_components=20` | 覆盖函数默认的 10 |
| 特征求解 | `eigs(..., tol=1e-4, maxiter=1000, v0=v0)` | 显式参数；未列的库默认值不擅自写成论文选择 |
| 随机初始化 | NumPy seed 0 | 只对应相关随机源 |
| 输出截取 | `n_DCs=7`，切片 `1:7` | 实际保存六列非平凡分量 |

`Premalignant0` 字典包含 `progenitor1`、`progenitor2`、`gastricprogenitor`、`gastric`、`gastric_pit`、`gastric_chief`、`gastric_Ccn2`。这是代码中的集合，不说明其中每个标签都是独立谱系或相互必然转化。

## 3. 扩散核的准确转写

### 3.1 从前置表达 KNN 取局部尺度

函数 `get_diffusion_operator_cpu(adata)` 读取 `adata.obsm['indices']` 和 `adata.obsm['distances']`。设每个细胞有 k 个记录的邻居：

```python
adaptive_k = int(np.floor(k / 3))
sigma_i = np.sort(distances[i, :])[adaptive_k - 1]
```

局部尺度来自邻居距离排序中的一个指定位置。其意义依赖前置 KNN 是否包含自身以及实际距离分布，不能只根据 k 推断数据中的物理或表达尺度。

### 3.2 核、对称化与 Markov 归一化

对已有表达 KNN 边：

\[
W_{ij}=\exp(-d_{ij}/\sigma_i),\qquad K=W+W^T,
\]

\[
T=\operatorname{diag}\left(1/\sum_j K_{ij}\right)K.
\]

【代码事实】指数里是距离除以局部尺度，不是常见的距离平方高斯形式。将其替换成 `exp(-d**2/(2*sigma**2))` 会改变算法，不能还称为源码等价。

【审计提醒】局部尺度为零时该片段没有明确保护。重复表达向量、极小邻居数、多连通分量或非有限距离，都可能使谱结构或计算行为异常。不能靠随意加入 epsilon 后仍宣称是原始结果；修复需要独立版本和差异记录。

### 3.3 特征分量与方向

`getDiffusionComponents_cpu` 调用特征求解，取实部、按特征值降序排列，并对每列向量作 L2 归一化。导出时：

```python
adata_output.obsm['X_diff_comp'] = adata.obsm['X_diff_comp'][:, 1:n_DCs]
adata_output.uns['diff_comp_eigenvalues'] = adata.uns['diff_comp_eigenvalues'][1:n_DCs]
adata_output.obs['progenitor_DC'] = -adata_output.obsm['X_diff_comp'][:, 0].copy()
```

【逻辑解释】去掉首列、数组第零列、数学上的首个非平凡分量，是不同编号约定。`1:7` 是六列，不能说导出七个非平凡分量。负号是方向约定；特征向量的符号本身不携带生物时间。

【迁移建议】新数据上先检查端点 marker 和独立组织信息，不要仅沿用负号。直接调用 DPT 并指定 root 不是同一方法；用 UMAP 一条轴替代也不是。

### 3.4 CPU 函数不代表 Notebook 无 GPU 依赖

【代码事实】Step08 开头无条件导入多种 CuPy/RAPIDS 模块，尽管后续所用特征计算函数名称和实现走 CPU。原 Notebook 能否冷启动，取决于全部导入而不是一个函数名。Python `random.sample` 绘图抽样与 NumPy seed 也分开，不能声称全项目所有随机性都已固定。

## 4. 物理空间邻域的活动路径

定位：[Step03 固定文件](https://github.com/dpeerlab/p53-niche-dynamics/blob/a97d1a42cede4c12416875a4aa50d3d63ee1fffd/transcriptomics/notebooks/Xenium_Preprocessing_step03_compute_neighborhoods_simplified_locked20260410.ipynb)。重点函数 `compute_sample_neighborhoods`、`get_spatial_polygon_neighborhood`、`filter_neighborhood`；活动单元 cell id 11。

### 4.1 候选搜索与最终半径

```python
outer_radius_expanded = 70
outer_radius = 60
spatial_neighbors = compute_sample_neighborhoods(
    adata, 'slide_id', 'cell_type_0',
    selected_cell_types=[], outer_radius=outer_radius_expanded, inner_radius=None
)
spatial_neighbors_updated = filter_neighborhood(
    adata, spatial_neighbors, min_radius=0, max_radius=outer_radius
)
```

作者注释解释：圆的多边形近似可能遗漏边界附近真实邻居，先扩大候选集，再使用欧氏距离精确裁剪。因而不能把 70 μm 写为最终生态位半径，也不应把它列成未解决的参数冲突。

设 \(r_i\) 是空间质心，\(s_i\) 是切片编号，则对应的最终语义为：

\[
A_{ij}=1\{s_i=s_j,\ \|r_i-r_j\|\le60\ \mu m\}.
\]

这是活动代码的理想化最终定义。是否因坐标、几何实现或输入缺失导致实际对象不满足该定义，仍须读取产物检查。

### 4.2 样本隔离与条码对齐

活动函数按 `slide_id` 循环，并将切片内索引映射回全对象索引。不同切片即使坐标相同，也不应连边。结果写为稀疏 CSR、`uint8`，保存在 `obsp['spatial_neighborhood']`，同时沿用 `obs_names`。

【迁移建议】加载发布图时，不能只检查矩阵大小一样。应验证条码集合、顺序、唯一性与切片映射；顺序错位可以产生看起来很平滑、实际完全错误的局部聚合。

### 4.3 自环与零邻居

`min_radius=0` 没有显式去除对角线；按质心查询的代码语义，锚点通常会进入自身邻域。实际发布矩阵是否有自环，本次未读取验证。不能按个人习惯静默删除自环，因为它会改变上皮状态均值和比例分母。

对于某个特定区室，局部邻居数可以为零，即使全细胞邻居数非零。此时该区室平均表达不可定义，不能用 0 假装是低表达。

## 5. 生态位坐标与区室表达：先明确分母

设 \(e_j\) 表示被纳入坐标定义的上皮细胞，\(z_j\) 是 G–P 值：

\[
n_{i,E}=\sum_j A_{ij}e_j,\qquad
q_i=\frac{\sum_j A_{ij}e_jz_j}{n_{i,E}}.
\]

\(q_i\) 是局部上皮状态的平均值，不是距离肿瘤中心的位置、也不是样本时间。只有当相关上皮状态可测且分母有效时才定义。

对区室 c 与基因 g：

\[
n_{i,c}=\sum_j A_{ij}1(c_j=c),
\]

\[
m_{i,c,g}=\frac{\sum_j A_{ij}1(c_j=c)X_{jg}}{n_{i,c}}.
\]

对应 helper：[neighborhood_utils.py，L32–L44](https://github.com/dpeerlab/p53-niche-dynamics/blob/a97d1a42cede4c12416875a4aa50d3d63ee1fffd/utils/neighborhood_utils.py#L32-L44)，`get_average_neighborhood_expression`：先选锚点行与邻居列，再按选定邻居数归一化。`get_total_neighborhood_expression` 则不做这一步除法。

**同一个 helper 可以接收不同尺度的 X。** 函数签名不能说明传入的是 counts、归一化表达还是变换后的矩阵；必须追踪具体调用端。本稿只在活动证据充分处归因参数。

## 6. 三种不同问题，至少保留三种输出

| 输出 | 回答什么 | 分母/单位风险 |
|---|---|---|
| 局部数量 \(n_{i,c}\) | 这个区室有多少细胞？ | 面积、密度、切片边缘和有效组织缺失 |
| 局部比例 \(p_{i,c}=n_{i,c}/\sum_jA_{ij}\) | 这个区室占多少？ | 其他区室减少也会使其比例增加 |
| 区室内表达 \(m_{i,c,g}\) | 已有该类细胞内部状态如何？ | 零邻居、低覆盖、尺度与细胞亚状态混合 |

【迁移建议】再保留 q 的方差/分位数、有效锚点数、组织区域、动物 ID。相同平均 q 可以来自“全是中间状态”，也可以来自“两端各占一半”；它们未必是同一生物学环境。

## 7. 平滑与统计不能藏在绘图参数里

沿轴曲线涉及分箱、带宽、权重、最低覆盖、样本平衡和区间估计。主图生成代码的完整活动分支尚未核验，本稿不将 GAM、LOESS 或任意默认带宽写成作者实际方法。

【迁移建议】每个轴区间同时给出独立动物覆盖及效应方向。一个轴末端只有某一只动物支持时，不能把平滑曲线当作跨动物规律。邻域高度重叠也意味着局部行数远大于独立信息量。

## 8. 实现审计的明确范围

`utils/neighborhood_utils.py` 的 `get_spatial_knn(adata,k=30)` 没有把 k 传给 `neighbors_gpu`（[L113–L120](https://github.com/dpeerlab/p53-niche-dynamics/blob/a97d1a42cede4c12416875a4aa50d3d63ee1fffd/utils/neighborhood_utils.py#L113-L120)）。这是 helper 的接口风险；**它不是上述半径邻域的活动主路径，不能据此断言论文 60 μm 图错误**。

Step03 残留输出中的系统内存读数来自 `psutil.virtual_memory()`，不能当成本次测得的进程峰值 RSS，也不能据其声称最低硬件要求。

上述空间和扩散代码都未在真实数据上执行。本稿给出的是可追溯方法解析，不是结果复现或资源性能基准。
