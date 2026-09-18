# 从文献重建到真实复现：有序任务与验收

## 当前界限
本包已完成可获得文献的结构化阅读、逐图契约、数学/统计审计与独立辅助检查。尚未获得作者Zenodo归档、模型权重、原始/处理单细胞矩阵、FCS、受控临床数据和源数据XLSX。下面所有作者分析任务均未执行；建议参数不冒充论文参数。

## 1. 先恢复不可替代的身份表
首先安全取得Zenodo 20028241，记录DOI版本、原始文件名、大小与SHA-256；若仓库仍在更新，同时固定commit。只静态审读，不直接执行下载脚本和notebook顶层代码。查找README、environment、27列feature schema、冻结模型及入口，并确认权重的生成日期与论文最终版本关系。

必须形成`donor ↔ biological sample ↔ timepoint ↔ multiplex run ↔ library ↔ barcode ↔ paired clone ↔ full sequence ↔ construct ↔ functional assay`关系表。EGA sample数、患者数与文库数不能互相替代。ALQ-19-019的缺失基线单列。声明每个字段的唯一性和一对多关系，保留原始键，不做有损覆盖。

**验收**：跨样本裸barcode无冲突；每细胞标注唯一；每paired clone与fullsequence映射可解释；每实验构建可回到天然受体；同一delta链关联多个paired clone时显式保留。

## 2. 原样重建single-cell与自定义VDJ
先按各队列原版CellRanger运行，保留demultiplex置信度与被排除barcodes。按G/M/GM三分支产出contig/key映射和每一决策原因。保存pair/orphan/dual类别及冲突前后数量，逐阶段统计cell、clone、fullsequence数量。

依论文QC、SCTransform/CLR和Harmony处理；未知PC数、resolution、ADT异常值规则不能补成常用默认值。若无法取得，流程在这些参数处停止而不是自动“最优猜测”。输出每患者QC和富集/分选范围，而不是只报合并细胞数。

**验收**：S4及正文计数的口径能解释；672与766不要求先验强行相等。若因不同alignment模式产生差异，应使用命名输出分别保存。检查MiXCR及VDJ库中物种、基因名、CDR3核酸/蛋白字符串的一致性。

## 3. 功能真值的重新建立
导入原始FCS或源数据，读取作者门控和构建排除记录；确认GFP百分点差、GFP+CD69+双阳性等不同终点。锁定13/15精确边界、背景负值及四舍五入规则。保存TR/NTR/borderline/unknown/expression_failure独立状态。

**验收**：每个最终监督标签可追溯到受体×靶系×独立实验原始读出；未测克隆不能被编码0；候选替补可回溯；同一clone的多细胞共享同一功能标签但不增加独立实验数。

## 4. PreGame的两条并行路线

### A. 忠实复现路线
恢复最终27列和有序列名、归一化assay/slot、cell-cycle计算、Phase编码和缺ADT路径；重现作者的cell-level CV、SMOTENC、RF选择、max聚合与阈值。在清楚标注泄漏风险前提下，这条路线回答“作者流程能否得到作者报告”，不是替作者修正方法。

**验收**：模型输入、类别列索引、依赖版本、种子、每fold样本清单、预测和AUC计算方向与作者代码一致；允许数值差异时预先声明容差及来源，不看结果后修改。

### B. 泛化审计路线（新分析）
外层group以供者定义，混样供者按同batch合组。外层测试完全隔离；内层完成RNA/ADT特征筛选、变换拟合、缺值处理、SMOTENC和RF调参。克隆在所有折之间检查不重叠。新供者表达可用固定reference映射，不能全数据整合后默认为inductive setting。

比较gene-only、protein-only、全模态、去cell-cycle、no-SMOTE及class-weight方案。固定所有方法的外层划分、评价集合和调参预算。小样本导致折内单一类别时显式报NA并调整预定义分组方案，不能删掉困难fold提高平均值。

同时报告AUROC、AUPRC、每供者表现、校准、PPV@K、每真阳性实验成本。单一最终候选库不宜用“细胞级每次重复的方差”充当跨供者区间。置换检验在供者/clone合法层级进行，不能打乱单细胞后破坏相关结构。

**验收**：每个out-of-fold score只能来自未看到该group标签的全部训练过程；根据外层测试表现再选择特征/阈值需另有锁定验证集，不能回写外层估计。

## 5. 下游生物学审计
重复原论文的clone cap=30方案，同时运行供者×标签pseudobulk/clone-level分析；使用Vdelta亚型匹配、每供者等权、留一供者和克隆大小匹配。分开“通过模型选择后实测标签”的样本与完全独立抽取样本。报告方向、效应和不确定性，而非仅显著gene清单。

Morisita-Horn核验是否为similarity=1-distance；RF应明确read还是UMI molecule，以及分母包含哪些链/克隆。delta链映射需要一对多审计，不能以join重复行累加同一分子的RF。

**验收**：分组单位合法；contrast方向正确；基因与蛋白命名空间不碰撞；100/1000和Bonferroni/FDR真实实现被定位；随机重复的P平均只描述稳定性，不冒充已证明全局错误率。

## 6. 临床重建
先恢复实际入组矩阵与timepoint规则，再重画Fig1/5/ED1/8。单列baseline缺失、baseline为零、C2D1缺失及以C6D1替代的病例。对治疗后指标做明确landmark；保留连续变化指标并报告患者级区间。因单臂设计，不把一般预后关联叫作治疗特异预测。

**验收**：PFS起算点、删失规则、KM风险人数和图注n一致；多个cell subtype/timepoint的检验全部保留；不拿重复血液collections当独立患者。若患者数过少，报告描述性结果和无法稳健调整的混杂，不堆积高自由度模型。

## 7. HLA/KIR机制重建
先审阅源数据和流式门控，再核查KO/OE效率、受体表达、同型对照、独立实验配对、HLA分型与Bw4状态。定量与代表性流式必须来自同一分析集合。TCR65一个克隆的DE与供者效应分开讨论。

进一步正常组织安全、匹配供者原代细胞、不同HLA/Bw4背景、蛋白和体内验证均属于新研究，不是本次已完成结果。不要把人类机制未经实验直接套到小鼠或缺少受体配对信息的空间数据。

## 推荐恢复顺序
优先拿到代码归档、模型与27列特征、候选/标签表以及分析入组矩阵。这些材料比立即下载全部FASTQ更能判断复现价值和关键障碍。之后再按数据访问权限逐阶段恢复原始序列；所有模型重训、图形复刻和临床重算均建立独立运行日志。

## 本包辅助脚本的定位
`scripts/audit_candidate_table.py`检查身份、标签、split泄漏和delta配对歧义；`scripts/arithmetic_audit.py`验证S4转录的算术、二项区间及理论max效应。它们是本次独立编写的审计工具，**不是作者PreGame实现或替代模型**。合成测试只能证明这些检查器在测试条件下工作，不能证明作者代码正确。
