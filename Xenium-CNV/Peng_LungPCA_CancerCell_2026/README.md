# LungPCA：从肺癌前病变的空间共现，到可检验的演进与生态位模型

**Peng et al.｜Cancer Cell｜完整 idea / 论文研究逻辑重建 / 数学统计与代码审计**

论文：*Multimodal spatial-omics reveal co-evolution of alveolar progenitors and proinflammatory niches in progression of lung precursor lesions*。DOI：[10.1016/j.ccell.2025.10.004](https://doi.org/10.1016/j.ccell.2025.10.004)。在线发表 **2025-11-06**，正式卷期 **2026-02-09，44(2):321–339.e13**；日期依据 [PubMed](https://pubmed.ncbi.nlm.nih.gov/41202811/)。整理日期：**2026-09-12**。

> 本目录不是已完成的论文计算复现。它把论文报告、公开代码、解释和新项目建议分别写清，并提供可实际运行的教学性敏感性检查。作者数据对象、上游完整分析和补充工作簿未取得；本次没有重算论文图、效应量或显著性。

## 从哪里开始

先读 [idea.md](idea.md)，理解这个项目的核心判断；随后按以下顺序深入。各章可以独立阅读，但共用本页的证据标签。

| 顺序 | 文档 | 要回答的问题 |
|---|---|---|
| 1 | [研究故事与关键设计](docs/01_story_and_design.md) | 作者为何这样设计？哪些对照真正排除了替代解释？少了哪个设计，就不能说哪句话？ |
| 2 | [方法与数据流重建](docs/02_methods_and_dataflow.md) | Visium、snRNA、WES、Xenium、NMF、通信和实验终点各自做了什么？参数知道到哪一步？ |
| 3 | [CNV、克隆与谱系的数学辨识](docs/03_cnv_and_identifiability.md) | 表达为何不等于拷贝数？共享标签为何不等于直接祖先？25 spot / 95% 阈值有什么后果？ |
| 4 | [统计单位、空间依赖与测量模型](docs/04_statistics_and_measurement.md) | 怎样处理分母、重叠邻域、组成约束、阈值、交互和多重检验？ |
| 5 | [五条可迁移启发](docs/05_transferable_insights.md) | 每条原则的原文依据、抽象过程、成立条件、最小动作和反证是什么？ |
| 6 | [13 份作者脚本的对应关系与审计](docs/06_code_audit_and_reexecution.md) | 哪些脚本真正计算，哪些只读结果？固定路径、函数和可核对的行号是什么？ |
| 7 | [对应分期小鼠 Xenium 项目](docs/07_mouse_project_and_actions.md) | 纯起始克隆、初中末期数据先检查什么？哪些结果才值得升级实验？ |
| 8 | [来源、参数身份和未解决问题](docs/08_evidence_and_boundaries.md) | 哪些是本轮重核，哪些来自既有审读？哪些冲突仍不能消解？ |

机器可读索引见 [证据追溯表](evidence/traceability.tsv)、[参数登记](evidence/parameters.tsv) 和 [来源清单](evidence/sources.json)。分析示例见 [代码说明](scripts/README.md)、[统计检查脚本](scripts/sensitivity_checks.py) 和 [测试](tests/test_sensitivity_checks.py)。

## 四种证据标签

- **[P] 论文事实**：作者正文、Methods 或图注的明确报告。会给出图号或小节。图注描述不等于本次已逐像素复核原图。
- **[C] 代码事实**：固定提交的活动代码、对象读取、显式参数或输出。不是本次实际执行的科学结果。
- **[I] 本文解释**：对研究逻辑、辨识条件、数学后果与替代解释的分析。
- **[T] 迁移建议／新假说**：为新项目提出的检查或模型。不是作者已完成的分析，也不是已在其他疾病成立的生物学结论。

作者代码固定为 [`fba87dbee8dbae497b15b81a4b0fa79edccd17b2`](https://github.com/FuduanPeng/LungPCA_Code/tree/fba87dbee8dbae497b15b81a4b0fa79edccd17b2)。引用路径均相对于该提交；不能用未来的 `main` 行号替代。公开仓库缺少许可证文件，因此这里提供永久链接与审计，不重新分发完整作者源码；新增示例代码明确属于本项目。

## 三个先读结论

**第一：本文主要用 Visium 表达推断 CNA / 克隆，而不是用 Xenium 原位读取突变或直接测量 DNA。** Xenium 的核心任务是细胞状态、形态定位和局部邻域。出处：Fig.2、Fig.5；Methods：Analysis of spatial copy number alterations / Xenium data analysis。

**第二：阶段特异性是需要解释的观察，不是可直接外推的规律。** 早期环境与晚期环境不同，并不自动证明“只有时间导致差异”；模型、接收状态、组织位置和取样也可能变化。

**第三：真正值得迁移的是可区分替代解释的比较，不是一组肺癌标签或显著性检验。** 用独立动物承载推断，用局部空间承载测量；把状态、遗传谱系和采样时间分开。

## 执行范围

只运行本项目新增代码的合成数据单元测试，不运行作者 R / Python 脚本，不反序列化不可信 pickle / RDS，不安装作者全套环境，不调用外部计算。测试通过只说明指定边界条件被程序检查，不能证明论文结论或真实数据上的统计校准。参见 [validation_report.json](tests/validation_report.json)。
