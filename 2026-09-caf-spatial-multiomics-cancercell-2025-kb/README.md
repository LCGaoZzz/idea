# CAF 空间多组学｜Cancer Cell 2025 知识库

**主题分类：空间组学 → CAF 空间生态位、肿瘤微环境与统计审计。**

围绕 Liu 等的 *Conserved spatial subtypes and cellular neighborhoods of cancer-associated fibroblasts revealed by single-cell spatial multi-omics*，组织研究逻辑、方法重建、证据边界、数学诊断与 Xenium 迁移建议。论文 DOI：[10.1016/j.ccell.2025.03.004](https://doi.org/10.1016/j.ccell.2025.03.004)。

> **本目录是知识库阅读版，不是原始审计 ZIP 的完整镜像。** 原包中的24份核心文档、事实表和诊断代码保持原字节；另外增加导航、Agent入口、分析目标简表和导入核验。完整机器审计清单、通用验证器及合并HTML没有纳入此版本，详见 [IMPORT_SCOPE.md](IMPORT_SCOPE.md)。
>
> **科学边界：来源受限的研究重建与方法学审计，不是论文生物学复现。** 原始工作没有取得完整连续的期刊最终全文、全部原图/补充材料、作者代码与生物数据。18项通过的是自写合成诊断；原论文生物学分析执行数为0。原文事实、代码证据、独立推导和迁移建议不可互换。

## 阅读路径

| 目的 | 入口 |
|---|---|
| 先了解取得了什么、没有取得什么 | [导入范围](IMPORT_SCOPE.md) · [原工作来源边界](PROVENANCE.md) |
| 完整阅读研究故事、设计与关键判断 | [中文主报告](ARTICLE_REVIEW_ZH.md) |
| 理解竞争解释、证据阶梯和未检验假设 | [研究逻辑](knowledge/01_research_logic.md) |
| 重建邻域、NMF、Leiden、Visium、距离和分母 | [数学方法](methods/01_mathematical_reconstruction.md) |
| 核对SCTransform、RPCA和表达验证 | [预处理与表达](methods/03_preprocessing_and_expression.md) |
| 审查伪重复、组成闭合、循环论证及生存泄漏风险 | [统计审计](knowledge/02_statistics_audit.md) |
| 迁移到新Xenium项目、肿瘤内部与零T区域 | [Xenium迁移建议](knowledge/03_xenium_transfer.md) |
| 明确忠实复现需要的输入、未知参数与停止条件 | [重建蓝图](methods/02_reproduction_blueprint.md) · [作者报告参数](methods/author_parameters.json) |
| 按事实或分析目标检索 | [50条事实索引](evidence/parameter_facts.tsv) · [27个分析目标简表](evidence/analysis_index.json) |
| 寻找论文、补充文件和数据线索 | [参考文献](evidence/references.tsv) · [数据可得性](data/DATA_ACCESS.md) · [补充材料索引](data/supplement_inventory.tsv) |
| 运行可独立执行的数学反例 | [诊断说明](diagnostics/README.md) · [Python代码](diagnostics/diagnostic_examples.py) |
| 交给fable5.1或其他审阅者复核 | [知识库版审核入口](review/README.md) · [保留的原审核提示词](review/FABLE51_REVIEW_PROMPT.md) |
| Agent按需读取 | [AGENTS.md](AGENTS.md) · [knowledge_index.json](knowledge_index.json) |

## 使用时不能丢失的区别

空间CAF标签描述邻域情境，不直接等于细胞自身的分子状态。单细胞空间分支与Visium分支分别重建；上皮/肿瘤从基质表达整合中排除，不等于从空间邻域中删除。文中统计批评保留条件式和反驳条件，尤其不能在缺少作者代码时把结局泄漏风险写成已证实的实现错误。

原审计登记27个目标，其中26个“受阻”、1个“材料冲突”。这些状态描述原重建证据的完整性，不是对27项科学结论的真伪判决。简表没有替代原完整机器清单。

## 可运行检查

在本目录下运行：

```bash
python diagnostics/diagnostic_examples.py
sha256sum -c integrity/IMPORTED_SHA256SUMS
```

第一条只运行确定性合成反例，不下载数据、不调用作者代码、不生成论文结果。第二条核对24个原字节导入文件；不认证论文事实。Windows可用Python的hashlib根据同一清单核对，不要求安装额外生物信息学软件。

导入时已将远端Git blob身份与原ZIP字节比较：24/24一致；在本地重新运行合成诊断：18/18通过。具体范围见 [导入核验记录](integrity/import_verification.json)。这不是GitHub Actions CI，也没有重新执行原包通用验证器。

## 与仓库其他知识库的关系

[多细胞生态系统Xenium知识库](../2026-09-multicellular-ecosystems-xenium-kb/README.md)提供通用方法背景；[serpin–ECM–myeloid研究框架](../2026-09-serpin-myeloid-spatial-niches/README.md)是相邻机制案例；[Xenium时空演进](../Xenium-based-SpatioTemporal-Evolution-Profiling/)关注分时期空间组织。交叉链接仅作导航，不将其他论文的机制结论移植成本论文事实。
