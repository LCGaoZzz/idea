# 04｜固定版本代码地图、参数解释与实现审计

[返回入口](../README.md) · [方法章](03-computational-protocol.md) · [复现路线](../reproducibility/README.md)

## 0. 版本和审计资格

审计对象：`mattjones315/KPSpatial-release@c2fa7568ee48a9e35bbc6ecd88378c6768b23e00`。下文行号是这个提交的原文件行号，不是聊天摘录或本地重排文本的行号。Notebook优先用文件、cell id和source内容定位，避免JSON中输出图片导致行号误读。

已读关键utilities、部分Figure2/3脚本、Figure4 qPCR source与小表及主图目录；**未逐cell审计全部notebook，未取得终刊归档逐文件比对结果，未执行作者科学分析**。README仍指向预印本v2，这只是要求核对终刊一致性的线索，不证明代码必然遗漏全部终刊更新。[R1、R2](../evidence/SOURCES.md#r1)。

## 1. 代码地图：从研究问题找入口

所有路径均相对上游仓库；固定链接在[来源表](../evidence/SOURCES.md)。

| 问题／输出 | 路径与函数 | 已读范围／证据性质 | 不应误解为 |
|---|---|---|---|
| 状态矩阵、树 | `utilities/reconstruct.py`；`create_character_matrix`与各solver入口 | 关键源码与调用分支 | 一份可直接重跑全部图的总pipeline |
| 单状态插补 | `utilities/target_site_utilities.py::impute_single_state` | 函数实现已读 | 插补对所有下游结论均无偏 |
| fitness | `utilities/phylodynamics.py::score_fitness` | 函数实现、分组、归一化已读 | 直接测量的生长速率 |
| 实际fitness调用 | `reproducibility/Figure3/scripts/slidetags_fitness.py` | 活动调用L82已读 | 终刊的实际运行日志 |
| community评分 | `reproducibility/Figure2/scripts/score_consensus_hotspot.py` | 评分源代码已读 | 共识模块的完整发现算法 |
| 邻域汇总 | `reproducibility/Figure3/scripts/score_neighborhood_abundances.py` | 源代码已读 | 固定常量已按物理单位核验 |
| 通用DE | `utilities/differential_expression.py::differential_expression` | 默认与实现已读 | 特定panel最终使用的检验 |
| 塑性计算 | `reproducibility/Figure3/scripts/compute_slideseq_plasticities.py`、`compute_slidetags_plasticities.py` | 文件定位；完整活动链待补 | 两平台使用同一个指标 |
| 参考与空间注释 | `reproducibility/Figure1/infercnv_slidetags.ipynb`、`reproducibility/Figure2/plot_slidetags.ipynb` | notebook定位 | 全部参数及输出已复核 |
| 扩增与演进图 | `reproducibility/Figure3/evolution.ipynb`、`slidetags.ipynb`、`analyze_human_visium.ipynb` | notebook定位 | 主图panel一一生成关系已确认 |
| LR | `reproducibility/Figure4/ligand_receptor_analysis.ipynb` | 定位，主要方法来自补充材料 | 已复算LARIS分数与数据库 |
| qPCR图 | `reproducibility/Figure4/plot_qpcr.ipynb` | 读取数据与热图source已读 | 原始Cq处理、统计及细胞纯度完整可查 |
| 转移来源 | `reproducibility/Figure5/map_metastasis.ipynb` | 定位，主要方法来自补充材料 | 唯一founder和完整转移路线已验证 |
| 配准／远端表达 | `reproducibility/Figure5/register_curio_slideseq.ipynb`、`metastasis_expression_mouse.ipynb`、`plot_xing_metastasis.ipynb` | notebook定位 | 全部手工分割和坐标变换已取得 |

同一行中省略目录的后续文件沿用该行的目录前缀。完整定位不等于已取得全部输入和运行记录。

## 2. 已确定的问题与其范围

<a id="i01"></a>
### I01｜插补返回三个值，调用端只接收两个

【代码事实】调用位于 [`reconstruct.py L504–513`](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/utilities/reconstruct.py#L504-L513)，返回位于 [`target_site_utilities.py L147–167`](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/utilities/target_site_utilities.py#L147-L167)。函数的有票、无票分支均返回状态、一致性和支持数三个元素。

【解释】在该版本、该调用实际触发且成功返回时，两变量解包会出错。代码语义可以由最小Python反例说明，但这不等于执行了真实插补，更不说明终刊图来自该CLI。

【修复候选，未应用到作者仓库】接收第三个支持数，并按目标分析合同决定最低支持；不能为了通过解包就忽略支持数。正式数据、模拟基准对状态0的允许规则也须分开。此修复需真实数据与上游调用验证后才能升级为方法一致的实现。

<a id="i02"></a>
### I02｜按肿瘤分组，但删除集合方向相反

【代码事实】[`phylodynamics.py L64–102`](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/utilities/phylodynamics.py#L64-L102)先把表达观测与树叶取交集，再在L87使用 `np.setdiff1d(query_cells, tree.leaves)`。此时query通常已是tree leaves子集，该差集为空，不能删除其他分组的树叶。上游 [`slidetags_fitness.py L80–88`](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/reproducibility/Figure3/scripts/slidetags_fitness.py#L80-L88)确实启用 `tumor_id` 分组和MLE，不是未使用helper的孤立发现。

【修复候选，未运行真实树】

```python
keep = np.intersect1d(tree.leaves, query_cells)
if len(keep) == 0:
    raise ValueError('No leaves remain in the requested group')
subtree = tree.copy()
subtree.remove_leaves_and_prune_lineages(np.setdiff1d(tree.leaves, keep))
assert set(subtree.leaves) == set(keep)
```

还需检查输出索引唯一、每组metadata对齐、单肿瘤与不分组路径的一致性。后面统一删除非肿瘤细胞，不等价于事先剪成每个肿瘤再估计分支长度和fitness。

【影响与边界】树拓扑、分支长度、相对分数和拼接都可能受影响；实际影响大小需要原版／修复版对照重算。不能仅凭这条发现宣称论文全部fitness结论错误。

<a id="i03"></a>
### I03｜spot总UMI筛选使用了intBC阈值变量

【代码事实】[`reconstruct.py L414–419`](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/utilities/reconstruct.py#L414-L419)打印 `minimum_spot_umi_support`，但对 `umi_per_cell` 的实际比较使用 `minimum_intbc_umi_support`。改变前者不会按其名字影响这一步。

【迁移建议】分别命名spot总量、intBC总量、intBC-allele行支持。测试应构造能区分这些阈值和行／组级过滤的对象，确认筛选条件与日志一致。更上游是否已过滤未知，因此影响不自动推广到所有作者数据。

<a id="i04"></a>
### I04｜PercentUncut过滤结果被覆盖

【代码事实】[`reconstruct.py L421–438`](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/utilities/reconstruct.py#L421-L438)先以 `PercentUncut` 计算 `overlapping_cells`，随后以全部AnnData观测和另一集合重算同名变量，实际筛选未继承第一步条件。

【解释】只能确定这条局部路径没有保留该条件；不能推断上游输入必然完全未做同类过滤。阈值变量名字、fraction与percent单位及比较方向也须以明确合同为准，不按变量名字猜生物学含义。

<a id="i05"></a>
### I05｜筛选cellBC不等于筛选该cellBC里的所有allele行

【代码事实】同一范围内，代码从通过UMI条件的行取出cellBC，再用 `cellBC.isin(...)` 保留该细胞全部行。因此一条高支持行可以使同cellBC的低支持行继续存在。[C2，L433–438](../evidence/SOURCES.md#c2)。

【解释】实际实现是“这个观测至少存在一条通过的记录”，不等于“每条保留allele记录都通过”。是否要改动必须先核对作者的期望合同，不能擅自删除可能代表合法混合状态的记录。

<a id="i06"></a>
### I06｜路径常量没有插值

【代码事实】`score_neighborhood_abundances.py` 用 `pd.read_csv("{HOMEDIR}/hotspot_modules_consensus.scores.v2.tsv", ...)`，没有f-string或format。[C5](../evidence/SOURCES.md#c5)。

【迁移建议】用 `Path(HOMEDIR) / filename`，先验证文件、delimiter、表头和索引，再计算。仅替换HOMEDIR不会改变带花括号的字面路径。

<a id="i07"></a>
### I07｜生产者写空格，消费者读制表符

【代码事实】`score_consensus_hotspot.py` 对同名评分文件使用 `sep=' '` 写出，邻域脚本使用 `sep='\t'` 读取。[C6、C5](../evidence/SOURCES.md#c6)。

【解释】这是可核实的接口差异，但中间是否有人工转换未知。应读实际中间文件，不能只凭 `.tsv` 扩展名判断格式，也不能据此说作者最终计算必然失败。

<a id="i08"></a>
### I08｜参数差异必须按作用域判读

| 事项 | 方法或图注 | 可见代码或其他材料 | 正确判定 |
|---|---|---|---|
| Slide-seq邻域 | 30 μm | `RADIUS=28`，单位链未闭合 | 待核坐标与实际输入，不能默认为近似相同 |
| NJ hybrid切换 | 1000 | helper默认500 | 默认差异；可能被调用覆盖，不能定为实际运行冲突 |
| 插补一致性 | 特定基准0.8 | 通用helper默认0.7 | 基准与正式分析、声明与默认分开 |
| DE方法 | 特定邻域t-test | 通用工具默认Wilcoxon | 未连接调用前，不归因给该panel |
| DE显著阈值 | 方法FDR<0.01、绝对log2FC>1 | ED7图注登记为0.05、边界≥1 | 保留并列，需完整输出和终刊绘图链对齐 |
| Scanpy | 补充方法1.11.5 | Reporting Summary1.10.0 | 环境／分析范围待核，不造唯一锁定环境 |
| 动物性别 | Replication出现female | Reporting on sex出现both | 实验范围待核，不合并成已知全研究性别 |

来源：[参数表](../methods/parameter_registry.tsv)，[P1–P3、C2、C5、C7](../evidence/SOURCES.md)。

<a id="i09"></a>
### I09｜qPCR图的第四列标签与数据列分母文字不同

【代码事实】`reproducibility/Figure4/plot_qpcr.ipynb`中，选择数据的cell id为 **`8ccaef73-353a-465e-afd2-3cdda91e321b`**，source为 `cols = ['FC (LT-HT)', 'HG vs HT', 'FC (LG-HG)', 'LG-HG / LT-HT']`，第四列名为 `LG-HG / LT-HT`。绘图cell id为 `86138f88-8f08-4ba7-9eb0-6e26b7e9cdc9`，xtick第四项却写成 `(LG vs HG) / (LT vs LG)`。绘图source定位原JSON [`L427–434`](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/reproducibility/Figure4/plot_qpcr.ipynb#L427-L434)。

`5cd45d42-11cc-474c-8968-281ec6a046e2`是上一个查看 `qpcr.columns` 的cell，不是上述选择列的cell；这里按实际source区分，避免用execution_count混淆cell身份。

【解释】可确定的是显示标签与被选择数据列不一致。不能仅从标签错误推出数值计算错误；应以实际列、生成公式和终刊图核对。热图本身也不等于完成交互作用统计检验。小表不是终刊全部原始Cq与重复设计表。[C8、C9](../evidence/SOURCES.md#c8)。

<a id="i10"></a>
### I10｜原始counts、pickle、环境和个人路径仍是执行门槛

【代码事实】通用DE再次处理AnnData.raw；多个脚本使用个人绝对路径；多个结果来自预先生成的h5ad、pkl或模块表。已定位文件不能替代这些输入。[C1–C7](../evidence/SOURCES.md)。

【迁移建议】先建输入清单与哈希，核实raw/layers语义，只从可信来源读取pickle。运行时显式记录环境和实际参数；不把notebook保存的输出当成本次执行，不把当前库文档版本当作作者版本。

## 3. 哪些是逻辑演示，哪些是科学重跑

本目录的 `preflight.py` 不导入Cassiopeia，不载入h5ad，不进行LR或DE，不访问网络。其测试中的集合、返回值和设计表是人工最小例子，证明的是逻辑或数据合同，不是原论文统计结果。对真实公共文件进行的检查仅限阵列元数据及其字节来源。

文档中修复片段是建议，不是已应用的patch，更不是生产可运行认证。真正比较原版／修复版必须固定输入、环境、种子、求解器路径、分析集合，逐级比较矩阵、树、分数和最终结论。

## 4. 对这篇论文的结论

**公共代码中的确定问题，值得在复现前修复和验证；它们既不应被高影响力期刊光环忽略，也不能在没有终刊生成链的情况下被升级为整篇论文被推翻。**
