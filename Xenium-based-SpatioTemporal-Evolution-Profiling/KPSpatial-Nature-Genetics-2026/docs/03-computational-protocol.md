# 03｜计算方法：从原始观测到演进解释的逐层解析

[返回阅读入口](../README.md) · 上一章：[设计](02-design-and-evidence.md) · 下一章：[代码审计](04-code-atlas-and-audit.md)

## 0. 阅读约定

本章结合此前已完成的参数来源登记、补充方法与已读代码，区分**方法声明、实际代码、解释和迁移建议**。完整登记见[103条参数表](../methods/parameter_registry.tsv)。该表中尚未确认的值保持空白；默认值不代表论文最终值。未取得的完整上游流程不以一般单细胞常规流程补写。

## 1. 先看依赖，而不是先看软件名

```text
表达 reads → 表达计数与QC → 空间映射／样本身份 → 类型注释与表达模块
谱系 reads → allele table → character matrix → 树拓扑 → 分支长度
                                 ↓可选插补              ↓
                                 空间图          fitness／plasticity
                                                        ↓
                           对齐：观测ID × 肿瘤 × 位置 × 状态 × 历史
                                                        ↓
                       邻域组成／同类型DE／LR候选／跨层和转移匹配
                                                        ↓
                             染色、共培养和外部数据提供不同层面的支持
```

【解释】一个 AnnData 可以装下多种结果，但共同存储不使这些结果变成同一种测量。pipeline 的任何一步改变分析对象，后面分数、分母与统计单位都可能改变。

## 2. 输入合同：先明确矩阵和ID的语义

【代码事实】谱系工具使用 `cellBC`、`intBC`、`UMI`、`readCount`、`r1/r2/r3`、`allele` 等字段，并将状态表与 AnnData 的观测名对齐。[C2、C3](../evidence/SOURCES.md#c2)。

【迁移建议】实际重跑前应明确下列合同，不能只检查文件存在：

| 对象 | 必须明确 | 常见错误与其后果 |
|---|---|---|
| 表达矩阵 | 原始counts、log值、scaled值分别在哪；基因名空间；物种 | 把已log的 `raw` 再归一化，或把scale值用于计数模型 |
| 观测ID | 是否全局唯一；条形码后缀；平台单位 | 跨库同名导致树叶错误对齐；spot被误称单细胞 |
| 谱系状态 | 缺失、未编辑、单状态、混合状态的编码 | 把缺失当成未编辑；把合法混合状态全部删掉 |
| 坐标 | 单位、轴向、每切片坐标系、校准和配准 | 在不同切片间直接建近邻图；像素误当微米 |
| 树 | 叶子集合、字符映射、priors、算法版本 | 只留pickle，无法独立确认输入与分组 |
| 实验设计 | animal／tumor／section／array／library 的对应 | 细胞级n被当成动物级n |

`raw` 只是槽名，不保证是真实原始计数。未知来源的 pickle 不应直接加载；建议同时保留 Newick、状态矩阵、priors与映射、leaf metadata及文件哈希。

## 3. 表达预处理：两个平台、不同支路，不能拼成一份默认配置

【论文报告】补充方法写明 Slide-seq 表达量化使用 `kb_python 0.27.3` 与 `mm10`，QC与归一化有平台特异设置。Slide-tags 另有 CellBender、库特异质量控制等步骤；注释采用参考映射支路。[P2，Slide-seqV2 gene expression quantification and quality-control；Slide-tags preprocessing；Cell annotation](../evidence/SOURCES.md#p2)。

【此前参数登记】Slide-seq 表达UMI门槛记录为150；这是表达通道，不是后面的谱系UMI门槛。参考注释记录4,750个HVG、scVI/scANVI的各自模型设置；这些是特定注释支路，不可搬到树求解或CNV支路。详细数值、出处及范围保留在参数表。

【代码事实】通用 DE 工具从 `adata.raw.to_adata()` 构建 `counts` 与 `logged`，归一化目标为中位文库量，再 `log1p`。默认 Wilcoxon不证明特定扩增邻域分析也用了Wilcoxon；补充方法对后者声明t-test。[C7](../evidence/SOURCES.md#c7)。

【解释】本文并不存在所有步骤共享一个 `target_sum=10000` 的证据：例如LR支路有其独立声明，共识模块脚本另用样本中位总量。工程迁移必须按支路保存归一化来源。

## 4. 谱系预处理：为什么混合状态不是可以一删了之的噪声

【论文报告】Slide-seq 中一个空间点可含多个细胞的编辑状态，因此作者针对混合观测比较并使用可处理多状态的策略。Slide-tags 的单核观测则采用另一套纠错与过滤。定位：[P2，lineage target-site processing；simulation benchmarks of lineage-tracing pre-processing](../evidence/SOURCES.md#p2)。

【代码事实】`create_character_matrix()` 可从allele table构造字符矩阵，提供 `resolve`、`collapse`、缺失过滤和插补等选项。[C2](../evidence/SOURCES.md#c2)。

【解释】记一个观测在某位点的状态为集合。强制保留最高频状态可以减少冲突，却可能删去混合细胞携带的有效信息；保留所有状态则增加求解难度。哪种策略合理取决于观测机制，而不是“单细胞流程通常如何做”。跨层匹配为了计算与高置信要求采用压缩策略，不意味着所有主树也应使用同一压缩。

【迁移建议】保存原始与过滤后的allele table、非插补矩阵、插补矩阵、状态映射及每次补值来源。状态0与-1必须遵守作者编码，不得把它们合并。

## 5. 空间插补：算法、已验证范围与未闭合问题

【代码事实】`impute_single_state()` 在空间图中遍历限定跳数的邻居；忽略缺失值，把tuple中的候选状态加入投票，返回众数、一致性和支持票数。外层调用端只接收两个值，存在接口不匹配。详见[代码审计I01](04-code-atlas-and-audit.md#i01)。

【论文报告】补充方法的真实数据留出基准遮盖10%已观测状态，在30 μm邻域恢复，使用一致性与支持数限制；ED2还比较恢复准确率与下游树结构。作者另在讨论中指出高迁移场景可能破坏空间一致性假设。[P1，ED2；P2，Benchmarks of imputation and reconstruction accuracy、extended discussion](../evidence/SOURCES.md#p2)。

【解释】应分开三个问题：接口能否运行？缺失状态是否恢复正确？下游生态位结论是否依赖空间先验？修复解包仅回答第一个；整体准确率主要回答第二个；第三个需要结论级敏感性分析。

【迁移建议】在共同可比较对象上比较原始高置信数据、完整插补流程、独立验证分支。随机留出测试局部缺失恢复，空间块留出测试区域泛化，动物留出测试个体泛化；不能互相替代。

## 6. 树求解：算法名称不是运行参数

【论文报告】Slide-seq 声明 Greedy + Neighbor Joining，采用适应多状态的距离；Slide-tags 声明 Greedy + ILP。后者包括LCA切换条件、潜在图约束及求解时间上限。罕见编辑的先验概率可参与权重。[P2，Phylogenetic reconstruction on Slide-seq/Slide-tags data](../evidence/SOURCES.md#p2)。

【代码事实】`reconstruct.py` 提供 `neighbor_joining`、`cassiopeia_greedy`、`cassiopeia_hybrid`、`cassiopeia_hybrid_neighbor_joining` 等入口。NJ hybrid工具的 `cell_cutoff` 默认500，方法声明的切换规模为1000；没有实际调用不能认定500是终刊参数。ILP时间12600秒是声明的上限，不是本次实测耗时。[C2；参数表](../methods/parameter_registry.tsv)。

【解释】求解器得到的是给定状态和假设下的树，而非拍摄到的分裂历史。不同叶子采样、缺失处理、先验和求解器可以影响树。本文未提供给本整理可直接重算的全输入，因此不报告树重建稳定性数值。

## 7. Fitness：树结构支持的相对扩增代理

【论文报告】`Phylogenetic fitness inference`（PDF第16–17页）区分平台：Slide-tags利用 `IIDExponentialMLE` 推断分支长度；Slide-seq使用有突变边为1、无突变边为0的较保守编码，之后估计局部分支相关的fitness。[P2](../evidence/SOURCES.md#p2)。

【代码事实】`score_fitness()` 在启用分支长度推断时调用MLE，随后调用 `LBIJungle()`，并将叶子分数除以该树最大值。Figure3实际脚本将 `grouping_var='tumor_id'` 且开启分支长度推断；不能用helper默认关闭来替代这个活动调用。[C1、C4](../evidence/SOURCES.md#c1)。

【解释】这是相对量：高分表达的是特定树及参照下的结构优势，不是某细胞每小时分裂次数。叶子取样、非均匀死亡、编辑可见性及树的不确定性都会影响含义。按肿瘤归一化后的分数不能未经校准就视为跨肿瘤绝对生长速率。

**实现警戒：**分组剪枝的集合差方向错误可能改变参与计算的树及归一化参照。修复后必须与原版并行比较，不能直接覆写原结果后声称原文已复现。

## 8. Plasticity：不是任意邻域多样性的别名

【论文报告】Slide-tags利用树上cell-type标签的小简约性，并以子树叶子数归一化后汇总；Slide-seq利用谱系近邻间community-score向量的L2距离。PDF第17页公式图像已核对：[P2](../evidence/SOURCES.md#p2)。

对于Slide-seq，可写为：

```text
L2_plasticity(i) = (1 / |N_phylo(i)|) * Σ ||C_i - C_k||_2
                                            k ∈ N_phylo(i)
```

其中 `C_i` 是community分数向量，`N_phylo(i)` 是谱系近邻集合，**不是空间近邻集合**。分数另经单位尺度归一化。

【解释】它量化亲缘近邻之间的状态差异，不直接等于转换次数或某状态未来能够产生多少后代状态。把普通Xenium的空间邻居代入同一公式，可以定义另一个量，但必须重新命名并解释；这不构成本文指标的复现。

## 9. Communities：发现、共识、打分是三个不同步骤

【代码事实】`score_consensus_hotspot.py` 读取已有模块表，按 `Community_Module` 分组，使用出现频数超过 `int(0.25 * len(unique_modules))` 的基因与当前数据求交集，再调用 `score_genes(ctrl_size=100, n_bins=30)`。之前按样本进行归一化、低检测基因过滤、log与scale。[C6](../evidence/SOURCES.md#c6)。

【解释】这里能审定的是给定共识基因集的评分，而不是从零发现Hotspot模块。完整模块发现和共识生成的图、参数、基因去重规则仍需完整notebook。论文的ED5提供去除共享基因后的对照，不能忽略这一已有控制，也不能据此认为所有基因重用问题均已解决。

【迁移建议】对panel数据必须记录原始基因集、实际测到的基因、覆盖率和得分贡献。覆盖率相同的两个模块可能覆盖了不同关键基因，不能只通过一个百分比断言功能含义相同。

## 10. 高低扩增区域、邻域和DE：分母决定解释

【论文报告】补充方法要求达到相应谱系观测数量的肿瘤参与fitness高低比较；Slide-seq使用固定30 μm邻域，Slide-tags使用最近20个细胞。邻域富集用局部细胞类型频率相对于阵列背景频率；同类型DE另有基因过滤、检验与多重校正阈值。[P2，Differential expression and abundance in neighbourhoods of high-fitness cells](../evidence/SOURCES.md#p2)。

【代码事实】已读Slide-seq邻域脚本使用 `RADIUS=28`；坐标单位转换链未闭合，不能把它自行解释为28 μm或与30 μm等效。其对稀少邻居还有回退行为，需与分析合同一起核对。[C5](../evidence/SOURCES.md#c5)。

【解释】固定半径保证名义物理尺度，邻居数随密度变化；固定k保证观测数量，物理半径随密度变化。两者不是同一问题。区域富集比上升也可能因为背景分母变化，而不只是局部绝对数量增加。

【迁移建议】输出局部计数、邻域总数、比例、背景比例、富集比和实际半径／k；在同类型细胞内分析表达，避免把组成与状态混合。重叠邻域共享细胞，不能当作独立样本增加n。按动物、肿瘤和切片处理重复结构。

**未解决：**高低fitness阈值的完整活动实现尚未逐cell核实；补充方法中相关函数命名和图注显著阈值还需对齐，不自动替作者修正为常见写法。

## 11. 空间LR与共培养：候选相互作用不等于已证实通路

【论文报告】LARIS基于空间邻近的表达生成LR分数，以位置打乱等比较识别空间特异模式，并结合细胞类型表达特异性排序。该支路声明 `target_sum=10000` 和最近20邻居等设置；不同函数的 `mu` 含义与数值分别登记。数据库写为最新mouse CellChatDB，但没有可由此唯一识别的快照号。[P2，Cell-cell communication analysis of Slide-tags data](../evidence/SOURCES.md#p2)。

【解释】这是基于表达、邻域和数据库的计算代理，不是实际扩散常数、信号通量或受体活化测量。更不能把负对数绘图与原始评分大小的方向未经查明就等同。氧条件与共培养干预能限制总体解释，但未对某LR轴做必要性/救援实验，就不能把整个候选网络写成已证实机制。

【代码事实】qPCR绘图脚本主要读取预先汇总列并作热图。本次没有看到由这段绘图代码完成交互检验的证据；图中的标签还存在分母文字不一致，见代码审计。没有从保存的notebook输出反推本次运行成功。

## 12. 跨层、转移共识与原发区域定位

【论文报告】跨层分析使用非插补状态，采用较高支持要求与缺失限制；为了计算，部分步骤取最高频等位状态。转移来源分析另有支持、共识出现比例和相关距离阈值，不能与跨层参数混用。[P2，Coarse-grained alignment of Slide-seq data及后续转移分析，PDF第19–20页](../evidence/SOURCES.md#p2)。

【解释】三个对象要分开：跨层两个观测的相似性，转移灶内部的共识谱系状态，原发观测与这一共识的距离。共识状态不是已直接观察的唯一祖先细胞。所谓距离阈值0.8只在原方法的0–2尺度上有意义，不是一般坐标欧氏距离。

【迁移建议】保存每个候选来源的实际共享位点数、缺失率、支持度、距离尺度、共识规则、被排除病灶及理由。分割和平滑可以帮助定位，但区域边界不等于真实克隆边界；可视化下采样不应改变分析分母。

## 13. 环境、复现与资源

【代码事实】代码存在个人绝对路径及多种外部依赖线索。不同求解器可能需要不同可选组件；ILP要核实求解器和许可，快速NJ要核实启用的实现。本文不根据当前Cassiopeia README直接锁定作者历史运行环境。[CASS；C2](../evidence/SOURCES.md#cass)。

【迁移建议】优先用处理后的一个明确肿瘤走通“字符矩阵→树→fitness→邻域汇总”，再扩大到多样本和完整reads。原代码与修复候选分目录记录，收集环境、输入哈希、活动参数、stdout/stderr、退出码和结果检查。

没有运行就不报CPU/GPU小时、最低显存或可复现精度；安装成功、脚本退出0和图像生成也不等于原文结论重现。详见[复现路线](../reproducibility/README.md)。
