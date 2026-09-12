# 08｜来源、参数身份、未解决冲突与完成边界

[返回入口](../README.md) · [上一章](07_mouse_project_and_actions.md)

## 1. 文献身份与本次访问边界

[P] Peng et al., *Multimodal spatial-omics reveal co-evolution of alveolar progenitors and proinflammatory niches in progression of lung precursor lesions*。DOI：[10.1016/j.ccell.2025.10.004](https://doi.org/10.1016/j.ccell.2025.10.004)；[PubMed](https://pubmed.ncbi.nlm.nih.gov/41202811/)；[PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12980502/)。在线日期2025-11-06，卷期2026-02-09，44(2):321–339.e13。

本轮结合正式来源的可检索正文／Methods、PubMed图注、固定代码和既有审读材料。PMC直接访问存在验证页面，部分内容通过网页索引读取；没有取得完整原论文PDF、补充图PDF、补充表工作簿或作者Data对象。因此不能声称逐像素看完主图、完全核验图中每个点、重数细胞或完成数值复现。

既有中文整理是工作底稿，不是一级证据。关键设计、CNA分类、Xenium邻域、类器官条件、遗传模型、药理窗口和代码逻辑在本轮复核；一些细粒度QC/NMF参数仍明确记为既有Methods恢复、未由活动上游代码再核验。无来源值不补默认。

## 2. 固定代码来源

[C] [`FuduanPeng/LungPCA_Code@fba87dbee8dbae497b15b81a4b0fa79edccd17b2`](https://github.com/FuduanPeng/LungPCA_Code/tree/fba87dbee8dbae497b15b81a4b0fa79edccd17b2)。目录包含13脚本和README；各blob身份见 [sources.json](../evidence/sources.json)。本项目提供链接与审计，不镜像整份作者源码。

固定提交只保证读的是某一版本，并不保证它就是生成所有最终图的唯一版本。Methods版本、保存对象版本和依赖环境仍需对照。作者脚本导入了某包不等于本轮安装／调用了它。

## 3. 数据登记与下载状态

| 登记 | 作者声明的角色 | 本次状态 |
|---|---|---|
| [Zenodo17172149](https://zenodo.org/records/17172149) | 代码／处理后结果相关材料 | 官方记录可读，文件标restricted；未获得Data对象 |
| [Zenodo15670280](https://doi.org/10.5281/zenodo.15670280) | 处理后人类数据相关材料 | 本轮未成功取得完整记录／文件，权限与内容未确认 |
| [GSE222901](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE222901) | 作者列为小鼠数据 | 本目录保留官方入口，未下载表达文件或逐GSM重建 |
| [GSE300288](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE300288) | 小鼠数据 | 同上 |
| [GSE300293](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE300293) | 小鼠数据 | 同上 |
| [GSE307534](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE307534) | 处理后人类数据 | 未逐文件核验，不擅自指定其对应每个面板 |
| [GSE308103](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE308103) | 处理后人类数据 | 同上 |
| [GSE307529](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE307529) | 处理后人类数据 | 同上 |

来源：论文 Data and code availability；Zenodo17172149的访问标记来自2026-09-12官方记录。没有下载不等于数据不存在；记录公开不等于所有文件开放；文件开放也不等于所有分析输入完整。

## 4. 未解决冲突登记

| ID | 观察到的冲突／歧义 | 解释上限与所需材料 |
|---|---|---|
| U01 | Xenium发现队列Results 4,598,777，Methods 4,760,267，相差161,490 | 可能涉及集合／版本但未确认；不自行解释为QC前后。需细胞manifest与Table S1 |
| U02 | Patient samples的一处Xenium“6 samples”与6患者／12组织的叙述单位不同 | 保留单位歧义；不能自动将sample改为patient |
| U03 | Fig.7I图注总数96 cores；列出的30、23、23、18合计94 | 算术差异可确认；哪项文字或纳入数应改未知。需原始core表／最终图注 |
| U04 | COMMOT方法数据库类别文字与IL1展示的对应不清 | 需生成对象、LR子集与版本，不能默默换数据库类别 |
| U05 | Figure3M代码轴标签与变量语义不符；Figure7F的7mo对象标题3months | 代码层面冲突；正式图是否相同未视觉核验 |
| U06 | Figure1C对象引用名不一致 | 先前RDA可能注入变量；未执行，不能称为已观察报错 |
| U07 | Visium QC阈值的布尔组合不明确；若干算法写“默认” | 需活动过滤语句和当时环境，不能用当前默认填充 |
| U08 | 手工克隆子树与图像配准记录未恢复 | 需节点、参考、landmarks和变换，不靠文字概述补造 |
| U09 | core／well／细胞到生物个体的完整输入映射未取得 | 不能量化统计依赖影响，也不能断言所有作者分析都正确或错误 |

U01/U03仅为作者报告数值的算术核对，不是下载数据后的重计数。所有冲突都应在后续获得材料时更新，不因为文档完整或测试通过而被抹去。

## 5. 参数身份分类

| 身份 | 示例 | 正确用法 |
|---|---|---|
| paper_reported | CNA cutoff0.1、80μm、类器官>100μm | 说明作者报告，不声称活动代码已复算 |
| active_code | COMMOT方向k5、图像70/90%分位 | 限定具体函数／面板，不推广全流程 |
| dormant_branch | `plot_super`的truncate分支 | 说明活动调用未启用，不列为最终处理 |
| unpinned_default | Methods“其余默认” | 标版本依赖缺口，不自动填值 |
| reconstructed_note | 既有审读恢复的细粒度NMF／QC | 提供来源小节并保留未再核验状态 |
| proposed | 新项目半径敏感性、宿主等权比较 | 明确是建议，不称原文方法 |
| tested_runtime | 本轮新脚本Python／NumPy／SciPy版本 | 只证明测试环境，不称作者原环境 |

## 6. 本次完成与没有完成

**已完成：** 可获得证据的逻辑重建；主图1–7及重要补充分支的设计定位；13份脚本覆盖与实现审查；数学统计解释；5条逐项展开的迁移启发；小鼠分期Xenium动作表；来源、参数和缺口表；新增合成示例及真实单元测试。

**没有完成：** 作者全量数据下载；原始分析环境恢复；CNA／NMF／轨迹／邻域／通信／WES重算；正式图像逐面板视觉认证；原始p值与效应量重估；用户真实数据分析；任何动物／培养实验。

新增代码的30项单元测试不是30个论文结果验证。其作用是检查指定数值规则、输入防护和合成空间例子。没有估计真实数据的FDR／覆盖率／效能，也不代替科学同行评审。

## 7. 优先向作者补充取得什么

第一优先是能改变结论的材料：最终参考与克隆子树节点；输入／输出spot clone表；细胞与病灶／患者关系；空间邻域的生成代码和edge/self规则；来源数据的QC集合；实验core／well与动物／供体映射。

第二优先是能复算数值的材料：每幅图输入表、统计检验族与校正、sessionInfo／环境版本、NMF筛选顺序与种子、通信数据库子集、图像配准landmarks及变换。

不应先要求大量无关原始文件再模糊“无法复现”。按具体图的阻塞点请求最小缺失对象，更容易将审读推进为真正复算。

## 8. 外部方法学来源和本项目自创部分

[Zimmerman et al., 2021](https://www.nature.com/articles/s41467-021-21038-1) 用于说明单细胞中的独立重复问题；[SciPy cKDTree文档](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.cKDTree.query_ball_point.html) 用于新增代码的空间计数接口。它们不是LungPCA的额外结果来源。

RNA混合观察模型、未检出概率推导、邻域协方差、不同加权目标、阈值示例、交互对比和迁移设计属于本项目解释／建议。它们没有在论文数据上拟合；不声称创新性，也不把数学公式的正确性等同于其假设在真实组织成立。

## 9. 如何使用结构化证据表

[traceability.tsv](../evidence/traceability.tsv) 将正文主张、图、方法、代码、输入输出和阻塞原因放在一行。表中的`受阻`指作者计算重执行受阻，不等于没有读到论文；`材料冲突`指现有来源不可静默合并。新代码测试另存，绝不回填成论文分析`已执行验证`。

[parameters.tsv](../evidence/parameters.tsv) 保留参数身份与未知项；[sources.json](../evidence/sources.json) 保留版本、入口与访问状态。后续更新时，保留历史冲突及纠正依据，使另一个读者能知道结论为什么改变。
