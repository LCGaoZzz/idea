# 06｜代码对应、实现审计与可复算边界

[返回入口](../README.md) · [上一章](05_transferable_insights.md) · [下一章：项目迁移](07_mouse_project_and_actions.md)

**[C] 固定来源：** [`FuduanPeng/LungPCA_Code@fba87dbee8dbae497b15b81a4b0fa79edccd17b2`][ROOT]。全部路径均相对此提交。当前目录树包含 7 个 R、6 个 Python 和 README，没有 Data 目录、完整锁文件或许可证文件。本项目不重新分发作者完整源代码；提供永久链接、输入输出映射和审计。

本次审读没有执行作者脚本、加载作者 RDA/RDS/pickle、拟合模型或重画正式图。以下“执行风险”是静态审读结论；若依赖运行输入，明确保留条件。引用以真实脚本注释、函数名和固定版本为主，未确认的行号不编造。

## 1. 全部13份脚本的映射

| 固定脚本 | 输入／活动代码 | 输出面板 | 没有在该脚本实现的关键步骤 |
|---|---|---|---|
| [Figure 1.R][F1] | `load Figure 1B.rda`；`readRDS` 1C／1D；DimPlot、FeaturePlot、pheatmap | 1B–D | 原始QC、SCT、聚类、病理注释 |
| [Figure 1E 4F.py][F1E] | masks与基因pickle；`plot_super` | 1E、4F | iStar 训练、推理与跨样本绝对表达校准 |
| [Figure 2.R][F2] | 保存的 Pattern 图、PhyloTree、CNA矩阵、变异表；pheatmap、oncoPrint | 2B–D | inferCNV、参考选择、克隆赋值、WES calling |
| [Figure 2C.py][F2C] | `plot_category`、`plot_continuous`；已有 Histology/Clone/Pseudotime/CytoTRACE | 2C空间图 | 克隆、轨迹、CytoTRACE上游推断 |
| [Figure 3.R][F3] | Seurat／Monocle对象、MP表；plot_cells、pheatmap、ggplot统计展示 | 3A–J、3L–M | 注释、图学习、NMF程序筛选与完整统计输入构造 |
| [Figure 3K 3N.py][F3K] | `plot_category`；`stacked_MPs`的最大值标签；已有RPII clone对象 | 3K、3N | NMF、iStar、克隆发现 |
| [Figure 4.R][F4] | enrichment、MPs_corr、Ro/e、LR表、CytoSignal对象；`plotEdge` | 4A–E | 程序富集、相关表构建和完整通信估计 |
| [Figure 4G.py][F4G] | `plot_category`、预计算MP数组取最大值 | 4G | 原始程序拟合与高分辨率表达预测 |
| [Figure 5.R][F5] | Seurat对象、邻域表、TMA病理表；DimPlot／ggplot | 5A–E、5G–H、5J–K | 80μm邻域构建；5F/5I/5L注明Explorer |
| [Figure 6.R][F6] | 小鼠Seurat、富集表、number_mat／size_mat；显式成对t.test | 6B–D、6J–K | 小鼠QC/注释、培养图像检测、供体到孔映射 |
| [Figure 6E 6F 7D.py][F6E] | 已保存病理；score数组及样本内分位规则 | 6E–F、7D | 数据预处理、分数生成、完整图像配准 |
| [Figure 6G.py][F6G] | pickle对象；`communication_direction(...k=5)`再算方向摘要，随后流线图 | 6G | 从原始表达完成全部LR/OT通信拟合 |
| [Figure 7.R][F7] | 保存的Seurat、3/7mo比例、巨噬细胞比例；t.test | 7E–G、7I | 7B/C注明Prism；7H注明ImageScope；无完整终点计数过程 |

每个文件的 Git blob SHA 见 [来源清单](../evidence/sources.json)，可用于核对内容是否被替换。

## 2. 代码真正做了什么：几个决定解释的例子

### 2.1 不要把加载推断结果视为重新推断

**[C]** `Figure 2.R` 的 `# Figure 2C`：先 `load` 患者 RDA，再显示 `PhyloTree`，对 `plot_mat` 使用 `pheatmap`。热图颜色断点为0.9–1.1；`cluster_cols=FALSE` 下出现的绘图选项不能被当成原始克隆发现参数。

**[I]** 这条脚本只能证明作者提供了如何展示保存结果的代码。树的距离、根、节点选择和克隆稳定性仍需上游材料。加载同一个对象重现相似图，也不能验证对象自身正确。

### 2.2 图像自归一化隐藏绝对量变化

**[C]** `Figure 1E 4F.py::plot_super` 对每幅输入减去自身最小值，再除以自身最大值。`truncate` 的标准化／截断分支只有非空参数时启用，活动调用没有传入它。确切基因示例包括 COL14A1，不能与泛指基质的 COL1A1 静默替换。

**[I]** 两个样本相同颜色不代表相同表达量；弱信号样本也可被拉到饱和色。要比较跨样本量级，应另外保留原始范围和共同色标，但这是新分析建议，不是作者已采用的策略。

### 2.3 最高MP标签是硬分类，不是确定的细胞本质

**[C]** `Figure 3K 3N.py` 与 `Figure 4G.py`：`max_scores=np.nanmax(...)`，再 `np.where(...==max_score)[0][0]` 选第一个最高分，颜色依赖 MP 字典顺序。

**[I]** 近似相等的两个分数会被强制分开，完全平局受顺序影响。分数是否跨程序可比也依赖上游定义。可检查 margin、连续分布和未定义区域，不能把所有色块边界当生物离散边界。

### 2.4 小鼠叠加图具有精确的分位显示规则

**[C]** `Figure 6E 6F 7D.py` 的 Fig.6F 段分别计算两种分数的70%、90%分位：两者均超过自身90%时显示重叠色；两者均低于自身70%时显示黑色；其他位置显示最高分对应颜色。不是“任一分数低于70%就隐藏”。

**[I]** 这突出每个样本自身的高分区域，不能据此比较不同样本中绝对高信号面积，也不能把90%交集直接当成生物学相互作用显著区域。

### 2.5 COMMOT脚本不是纯画图，但不是完整通信流水线

**[C]** `Figure 6G.py:8–19` 读取保存对象，令 `layers['counts']=X`，调用方向摘要并绘流线。`k=5`、`normalize_v=True`、`.995` 是活动调用参数。

**[I]** `X` 是否真是原始counts取决于保存对象，代码赋名不能证明；方向摘要依赖的底层通信矩阵未在本脚本生成。论文Methods所述数据库类别与IL1展示对应关系仍需作者生成代码和对象确认。

## 3. 审计发现：确定问题与条件风险分开

| 发现 | 证据位置 | 能确认到什么程度 | 不能进一步声称什么 |
|---|---|---|---|
| Fig.1C读取`seurat_obj`，DimPlot引用`dseurat_obj` | Figure 1.R，Fig.1C段 | 变量引用不一致；若RDA没注入相应变量会报错 | 未读取前面RDA，不能说本次实际运行失败 |
| Fig.3M比例变量标KAC score，score变量标RPII比例 | Figure 3.R，Fig.3M段 | 代码标签与变量语义冲突 | 未逐图复核正式图，不能宣布正式发表轴也错 |
| 7个月对象图题仍为3 months | Figure 7.R，`p2` | 明确脚本标题冲突 | 不能自动扩大成数据分组错误 |
| `plot_category`的subset分支用未定义`score` | 多个空间Python函数 | 被触发时有未定义引用风险 | 活动调用没使用该分支，不是已观察主路径故障 |
| 类别整数经hexbin聚合 | `plot_category` | 若一个bin含不同类别，可产生类别平均的显示风险 | 没有坐标和gridsize，不知道实际是否发生 |
| 多数科学上游不在仓库 | 13脚本和目录树 | 公开代码覆盖不足以端到端重算 | 不等于作者没有做过这些分析 |
| 成对t检验与面板通用统计说明 | Figure 6.R、7.R | 活动调用显式方法；一些面板无多层模型代码 | 不能仅凭绘图脚本判定所有原论文统计均伪重复 |
| GUI部分未提供完整操作记录 | Figure 5/7注释 | Explorer、Prism、ImageScope参与输出 | 不等于图不可复核，只是需要额外输入／操作记录 |

## 4. 参数身份必须标明

`cutoff=0.1` 是 Methods 报告的 CNA 参数；80μm是Methods邻域定义；`k=5`是COMMOT方向函数调用；`adjust=15`是小提琴图平滑；`truncate=None`是函数默认且活动调用未启用；“其余默认”是版本依赖的未完全恢复信息。

这些参数的身份不同。不能把绘图参数改写为科学模型参数，不能把未调用的分支写成论文最终处理，不能用当前包默认替代当时环境。

## 5. 安全、可追溯的复算路径（尚未执行）

**[T]** 下面是材料齐备后的行动顺序，而不是本次完成记录。

首先获取固定代码并核对提交，不执行作者脚本：

```bash
git clone https://github.com/FuduanPeng/LungPCA_Code.git
cd LungPCA_Code
git checkout --detach fba87dbee8dbae497b15b81a4b0fa79edccd17b2
git rev-parse HEAD
```

然后恢复作者Data对象及来源许可、校验和、表结构。RDA可注入多个全局变量；pickle反序列化可能执行代码，应只处理可信来源并在隔离环境审查。不要以“加载成功”代替数据真实性和版本核对。

建立每个面板的输入schema：对象类型、必要字段、细胞／spot ID范围、assay／layer、坐标单位、患者／动物映射、上游生成版本。环境优先从作者sessionInfo或锁文件恢复；本仓库没有完整锁文件，所以不能自行声称找到了确切可复现环境。

先执行一个输入明确的小面板，比较输出与原图；再回溯上游计算、比较中间结果和统计。没有输入时给 `blocked_missing_input`，没有上游时给 `blocked_upstream`，材料有冲突给 `conflict`，不要全部标成功。

## 6. 本项目新增代码的责任范围

[sensitivity_checks.py](../scripts/sensitivity_checks.py) 不是作者13份脚本之一，不是新的inferCNV，也不产生论文图。它实现文字阈值的数学例子、理想未检出上限、Ro/e、BH、空间域内半径计数和等宿主描述对比。

所有测试使用合成数据；没有从作者或用户真实数据取得新结论。脚本不会联网、不会读取pickle/RDS、不会自动安装软件。运行说明及边界见 [scripts/README.md](../scripts/README.md)，真实测试记录见 [validation_report.json](../tests/validation_report.json)。

[ROOT]: https://github.com/FuduanPeng/LungPCA_Code/tree/fba87dbee8dbae497b15b81a4b0fa79edccd17b2
[F1]: https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%201.R
[F1E]: https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%201E%204F.py
[F2]: https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%202.R
[F2C]: https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%202C.py
[F3]: https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%203.R
[F3K]: https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%203K%203N.py
[F4]: https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%204.R
[F4G]: https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%204G.py
[F5]: https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%205.R
[F6]: https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%206.R
[F6E]: https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%206E%206F%207D.py
[F6G]: https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%206G.py#L8-L19
[F7]: https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%207.R
