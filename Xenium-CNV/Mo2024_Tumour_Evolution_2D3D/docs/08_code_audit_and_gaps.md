# 08｜固定版本代码审计：实际看到了什么，哪里仍未闭合？

[返回总目录](../README.md) · [上一章](07_xenium_timecourse_project.md) · [下一章](09_execution_and_acceptance.md)

## 1. 审读范围与版本边界

本次通过GitHub连接器读取公开文件、目录及指定提交。运行环境中的直接网络下载未成功，因此没有得到四个仓库的完整本地快照。下面的“已读”仅指所列文件或片段；没有扫描所有依赖、全部notebook输出或提交历史。

| 仓库 | 审读固定提交 | 范围 |
|---|---|---|
| ding-lab/ST_subclone_publication | `7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa` | 主要R/Python入口和部分活动函数；其余路径分开标注 |
| ding-lab/mushroom，subclone-resubmission | `fde4dd8c91636629b1acab4473e1773468dcc1d8` | README、训练notebook关键段、mushroom.py配置段 |
| estorrs/multiplex-imaging-pipeline | `c351da1d41e284eef2f732b3553e5602438ed978` | README和segmentation.py |
| ding-lab/morph | `ba1db03976a72f0da0558e87207054ef9404309b` | README；另查看一个发表日期前历史候选快照 |

这些是已审读快照，不统称论文最终运行版本，也不以“最新”保证其仍为每个分支当前tip。完整链接见[repository_pins.tsv](../evidence/repository_pins.tsv)。

## 2. 图号映射先纠正

主仓库保留旧稿目录：`Figure1`对应最终Fig. 1；`Figure2`对应最终Fig. 2；`Figure3`包含主要进入Extended Data Fig. 6–8的转录/深度分析；`Figure4`对应最终Fig. 3的TME/边界分析；`Figure5`对应最终Fig. 4的PASTE2拓扑；`Figure6`转到Mushroom，对应最终Fig. 5。

这是按README、活动内容与最终图注交叉定位的模块级映射，不声称每个面板的最终拼版脚本均已找到。[主README](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/README.md)

## 3. 新增重点：CNV相似度的定义与选择路径冲突

原文Methods: Copy number profile similarity score calculation采用−1/0/+1有符号状态乘积，允许负值；FFPE分群声明以0.8×最大树高切分。来源：[原文Methods](https://www.nature.com/articles/s41586-024-08087-4#Methods)。

公开[Figure2/3_CNV_jaccard_similarity.R](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure2/3_CNV_jaccard_similarity.R)则包含以下活动链：

```text
CNV_profile_jaccard         → jac_mat
CNV_profile_jaccard_prob(pred) → jac_pred_mat
CNV_profile_jaccard_prob(all)  → jac_all_mat
                         ↓
distmat_selected = jac_pred_mat
hclust(..., method=ward.D2)
maptree::kgs(..., alpha=2, maxclus=MAX_K)
for K in 2:MAX_K: cutree(k=K)
```

### 3.1 硬调用函数的对称性问题【C】

`CNV_profile_jaccard`将CNV>1和<1分别作为扩增/缺失；同向区间交集为分子，分母为A非中性事件与B缺失事件的union。B扩增若超出A，会被分母遗漏。另在A没有非中性事件时直接走空union分支。

单位格网例子A=(gain,neutral)、B=(gain,gain)给A,B=1和B,A=0.5。该构造不符合期望的对称区域相似度。相反方向事件也没有论文公式的负贡献。

### 3.2 选中的概率路径也不同，但不是同一个问题【C】

概率函数按amp/del分别构造区间，并以同向状态及概率乘积加权；`mode='pred'`在同窗口gain/loss对照中为0，而论文式为−1。相同非中性状态且双方概率均为0.8时，单窗口值为0.64，不是1；这提示其含义为置信度加权一致性而非标准化身份度量。

最终所读选择是`jac_pred_mat`。**不能把3.1的硬调用分母错误直接说成最终选定概率矩阵的不对称，也不能据此认定最终亚克隆全部错误。**

### 3.3 后续选择尚未绑定最终结果【C/I】

公开文件探索多个K并调用kgs，未闭合到论文声明的最终切树规则；仍有人工复核和外部标签表。需要作者最终矩阵、配置、人工合并记录及面板来源才能决定哪个分支生成最终结果。

### 3.4 本次做了什么检查【T】

[独立脚本](../scripts/evidence_sanity.py)只使用合成对齐窗口和简化单位格网，核对论文式、硬调用逻辑及概率路径的有限反例。9项测试通过。没有执行R/GenomicRanges，没有读取作者真实矩阵；因此结论是“定义与公开实现存在可展示的差异”，而非“论文标签已被实证推翻”。

## 4. 其他已确认的代码与接口边界

| ID | 位置 | 代码事实 | 影响/限制 |
|---|---|---|---|
| C01 | `Figure2/1_inferCNV_run.R`参数解析 | 顶部示例、CLI默认和解析后赋值不同 | 不能把顶部样本/参考数/模式当最终设置 |
| C02 | 同文件CreateInfercnvObject之前 | `GetAssayData(...,slot='counts')`未写assay；参考选择含回退 | 实际矩阵和参考需对象/日志确认 |
| C03 | `Figure2/2_CalicoST_run.md` | 仅上游工具入口 | 缺样本级最终配置 |
| C04 | `Figure3/4_Layer/2_layer_DEG_correlation.R`79–104行 | 端点归一化后读取预计算TSV | 不是完整偏相关生成代码 |
| C05 | `Figure4/1_RCTD_devolution.R` | 参考类别>50细胞，移除部分标签，multi模式 | 不应保留不存在的精细类别或改写阈值 |
| C06 | `Figure4/4_border_DEG.R`64–111行 | CLI width默认4，覆盖WIDTH；存在1/2/4分支 | 最终边界宽度须实际命令 |
| C07 | 同文件输出目录段 | 重新指定output_dir；对存在样本目录递归unlink | 迁移直接运行可误删输出，先隔离路径 |
| C08 | `Figure4/5_CCI_COMMOT.py`参数段 | dist_threshold未显式数值类型 | 显式CLI值可能为str，需测试/转换 |
| C09 | 同文件坐标、推理段 | 未见局部显式物理尺度转换 | 数值1000不自动是μm；未核输入不得断言算错 |
| C10 | 同文件作图段 | 部分键固定cellchat，改变cwd；Leiden赋值时序待核 | 可选数据库/相对路径/首次绘图可能受影响 |
| C11 | Mushroom训练notebook | cases为空，依赖外部metadata.yaml | 已读快照不能直接训练最终病例 |
| C12 | mushroom.py DEFAULT_CONFIG | 默认batch/lr/分辨率等存在 | 库默认不等于论文最终参数 |
| C13 | MIP segmentation.py | Mesmer、切块、边缘删除、重叠合并 | 默认通道与Methods不同；参数须样本绑定 |
| C14 | Morph README及历史候选 | 当前README含Xenium示例；发表前候选快照仅很薄的operators | 不能用更新后的能力补写历史运行链 |

C01–C10固定路径均在主仓库提交`7067cd…`。主要逐行链接：[inferCNV](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure2/1_inferCNV_run.R)、[depth L79–L104](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure3/4_Layer/2_layer_DEG_correlation.R#L79-L104)、[boundary L64–L111](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure4/4_border_DEG.R#L64-L111)、[COMMOT](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure4/5_CCI_COMMOT.py)。

C11–C14链接见[来源索引](../evidence/source_index.md)。历史Morph候选`c284634abdeebc567c39a6367515d8decbf13af3`来自默认历史线的日期查询，**不代表所有分支当时的内容，也未被作者确认为论文运行提交**。

## 5. 只是定位、不能声称已完成源码审计的部分

WES完整调用链、scVarScan的read/UMI统计实现、ROGUE及GSEA辅助函数、PASTE2完整入口和区域连接谓词、Mushroom全部模型/损失实现与最终step7邻域分析notebook，均未在本轮逐行闭合。对应路径存在或README可达，不等于作者所有运行上下文可得。

特别注意外部`helper_global.R`、Google Sheet tracking、服务器绝对路径、预生成Seurat对象、黑/白名单和参考映射。它们可以决定实际样本及参数，是流程的一部分，不是可随意替代的工程噪声。

## 6. 原文文字与数字也需要独立审查

样本计数口径见[第二章](02_data_and_measurements.md)；边界DEG阈值文字缺比较符，见[第四章](04_state_boundary_and_interactions.md)；Mushroom尺度单位存在互为倒数的描述，见[第五章](05_3d_and_multimodal_protocol.md)。本轮PDF/表格获取未成功，无法排除部分网页转写问题，也无法恢复全部样本级设置。

这类情况应写“待核”，不为了让协议看似完整而填常见阈值，也不因为出版物等级高就忽略。

## 7. 数学/统计解释的额外检查

**RNA-CNV与表达关联不是完全独立通道。** 当两者都来自表达矩阵，共享测量和基因位置可以加强相关。WES或位点证据能减少歧义，但也应说明是否参与了预筛选。

**层深归一化不是重复单位校正。** 它改变横轴，不自动减轻大区域的spot权重，更不自动处理空间自相关。

**成对相关不等于成对独立。** 同一区域出现在很多pair中，患者贡献可不均。

**算法可运行与科学归因是两种验收。** 即使接口问题全部修复，局部表达相邻仍不能证明信号因果方向。

上述为【I】的统计审查原则，不是本次真实数据重算结果。

## 8. 当前证据状态

CNV相似度/切树的原文—公开活动实现关系为**材料冲突**；其他主要模块因输入、配置或上游计算缺失仍为**受阻**。合成检查是独立范围的**已执行验证**，不能把整个研究状态升级。

优先补齐的不是更多展示图，而是最终样本清单、CNV相似度矩阵与标签生成记录、深度统计TSV生成代码、补充超参数和门控、空间尺度与配准文件、运行版本和日志。详细条目见[gaps.tsv](../evidence/gaps.tsv)。
