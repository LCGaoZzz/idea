# CAF 空间亚型与细胞邻域｜Cancer Cell 2025 知识库

**分类：空间组学 → CAF / 肿瘤微环境 → 空间邻域、统计审计与 Xenium 迁移。**

对象：Liu et al., *Conserved spatial subtypes and cellular neighborhoods of cancer-associated fibroblasts revealed by single-cell spatial multi-omics*. **Cancer Cell (2025)**，DOI：[10.1016/j.ccell.2025.03.004](https://doi.org/10.1016/j.ccell.2025.03.004)。论文身份元数据沿用原包的 [identity.json](reconstruction/evidence/identity.json)，本次归档没有重新审阅原论文。

> **证据边界：这是来源受限的论文重建、研究解读和方法学审计，不是作者官方代码库，也不是已完成的生物学复现。** 未取得的作者代码、完整原图和补充材料继续标为缺失；数学反例不证明作者实现发生了相同问题；新项目建议不归入论文事实。

## 从哪里开始

| 使用目的 | 入口 |
|---|---|
| 先确定已取得、未取得和不能声称的内容 | [PROVENANCE.md](reconstruction/PROVENANCE.md) |
| 理解主问题、研究设计和核心判断 | [中文主报告](reconstruction/ARTICLE_REVIEW_ZH.md) |
| 系统跟随研究逻辑与竞争解释 | [研究逻辑](reconstruction/knowledge/01_research_logic.md) |
| 了解邻域、NMF、图及 Visium 路径 | [数学方法重建](reconstruction/methods/01_mathematical_reconstruction.md) |
| 核对预处理与表达整合 | [预处理补全](reconstruction/methods/03_preprocessing_and_expression.md) |
| 检查伪重复、组成效应、循环验证与生存分析 | [统计审计](reconstruction/knowledge/02_statistics_audit.md) |
| 迁移到新的 Xenium / TME 项目 | [Xenium 迁移建议](reconstruction/knowledge/03_xenium_transfer.md) |
| 准备后续复现所需材料 | [复现蓝图](reconstruction/methods/02_reproduction_blueprint.md) · [数据入口](reconstruction/data/DATA_ACCESS.md) |
| 查询精确参数、证据位置和目标状态 | [参数事实表](reconstruction/evidence/parameter_facts.tsv) · [追溯表](reconstruction/traceability.tsv) · [结构化清单](reconstruction/reconstruction_manifest.json) |
| 交给 fable5.1 或其他独立审核者 | [独立审核提示词](reconstruction/review/FABLE51_REVIEW_PROMPT.md) · [审核指南](reconstruction/REVIEW_GUIDE.md) |

**连续阅读：** [READING_GUIDE.html](reconstruction/READING_GUIDE.html) 保留原来的单文件阅读版。GitHub 文件页主要展示源码；把仓库或文件下载到本地后，用浏览器打开该 HTML。直接在 GitHub 阅读请使用上表中的 Markdown 文件。

**Agent 入口：** 先读本目录 [AGENTS.md](AGENTS.md)，再按 [knowledge_base.json](knowledge_base.json) 的任务入口加载需要的材料，不必默认加载整个大型清单。

## 怎样区分四种内容

1. **论文实际报告：** 以事实表、原材料位置和来源版本为依据；当前来源覆盖受限。
2. **作者活动代码：** 原包没有取得，不得把 Methods 中的函数名写成实际代码调用，不得编造 commit 或行号。
3. **本包推导与审计：** 用来解释研究逻辑或提出可检验风险，不等同于证实论文错误。
4. **迁移建议与新假说：** 供新项目设计使用，不得回填为作者方法或原文结论。

对来源冲突保留两方记录；补充原始材料后允许撤回或修正本包判断。

## 归档结构

```text
2026-09-caf-spatial-multiomics-kb/
├── README.md                  # 人类阅读与分类入口
├── AGENTS.md                  # 薄 Agent 入口
├── knowledge_base.json        # 机器可读元数据与任务路由
├── SHA256SUMS                 # 本知识库的完整文件校验表（不含自身）
├── reconstruction/            # 原交付包的46个文件，逐字节保留
│   ├── ARTICLE_REVIEW_ZH.md
│   ├── PROVENANCE.md
│   ├── READING_GUIDE.html
│   ├── knowledge/             # 研究逻辑、统计与迁移
│   ├── methods/               # 数学重建、复现蓝图、预处理
│   ├── evidence/              # 事实、参数与来源索引
│   ├── diagnostics/           # 自写合成诊断及上一轮运行记录
│   ├── review/                # 独立审核入口
│   ├── data/                  # 数据入口和补充材料清单
│   ├── validation_tool/       # 原包保留的验证器
│   └── ...                    # 完整清单、报告和审计记录
├── archives/                  # 原始交付 ZIP，不改写
└── integrity/                 # 原交付验证回执与本次归档检查
```

原包内的相对路径保持原状；它自己的 `SHA256SUMS` 与清单仍在 `reconstruction/` 内。新增导航文件没有混入原论文重建的执行记录。

## 完整性与复核

从本知识库根目录执行：

```bash
sha256sum -c SHA256SUMS
cd reconstruction
sha256sum -c SHA256SUMS
```

需要重跑原包检查时，在可丢弃的副本中按 [REVIEW_GUIDE.md](reconstruction/REVIEW_GUIDE.md) 操作，避免新的运行输出覆盖已归档的原始回执。

本次仅做归档、字节与链接核对。上一轮验证器与18项合成诊断的结果见 [原交付回执](integrity/previous_delivery_verification.json)，**不冒充本次重新运行，也不算作论文生物学复现**。本次新核对见 [import_verification.json](integrity/import_verification.json)。原文件版权及第三方工具权利沿用 [PROVENANCE.md](reconstruction/PROVENANCE.md)，本次没有给它们重新授予许可。
