# KPSpatial｜Spatiotemporal lineage tracing in lung cancer

Jones、Sun 等，Nature Genetics (2026)  
DOI: `10.1038/s41588-026-02739-z`

这个目录把论文、公开代码与独立审计整理成一个可复用知识库。重点不是逐图复述，而是重建作者如何把 **谱系历史、转录状态、空间位置、局部微环境和转移来源** 放进同一证据链，并明确哪些结论来自论文、哪些来自代码、哪些来自我们的审计和迁移建议。

## 推荐阅读顺序

1. [`00_MASTER_KNOWLEDGE_BASE.md`](00_MASTER_KNOWLEDGE_BASE.md)：完整研究逻辑与核心方法。
2. [`01_CODE_AND_STATISTICS_AUDIT.md`](01_CODE_AND_STATISTICS_AUDIT.md)：固定版本代码审计与统计风险。
3. [`02_XENIUM_TRANSFER.md`](02_XENIUM_TRANSFER.md)：迁移到早/中/晚期 Xenium 的分析框架。
4. [`03_REVIEW_CHECKLIST.md`](03_REVIEW_CHECKLIST.md)：独立审阅者/Fable 审核清单。
5. [`04_SOURCE_AND_VERSION_MAP.md`](04_SOURCE_AND_VERSION_MAP.md)：论文、代码、数据、固定提交与证据边界。

## 结论先行

这篇文章真正重要的不是“空间聚类”，而是试图把三个通常混在一起的问题拆开：

- 某个区域相似，是因为**共同祖先**还是**共同环境**？
- 某个亚克隆扩增，是**历史事件**还是只是当前表达状态更强？
- 缺氧、ECM、免疫抑制和转移之间，是关联、条件依赖还是机制？

论文的最大方法学价值，是用演化型谱系记录限制空间解释；普通 Xenium 没有这层独立历史证据，因此可以迁移研究逻辑，但不能直接声称获得同等意义的谱系树、tree fitness 或真实祖先关系。

## 审计状态

本知识库包含对公开代码的静态审阅和局部可执行反例测试，但**不是整篇论文的端到端复现**。目前最实质性的发现包括：

- CNV 近邻纯度置换检验使用严格 `>`，遗漏并列值，可在合成输入中产生伪 `P=0`；
- `LBIJungle` 的接口名称不能直接等同于标准 LBI，所审调用链实际导出 `mean_fitness`；
- 按 `tumor_id` 分组计算 fitness 的剪树集合差方向存在逻辑问题；
- 插补 helper 返回 3 项，而一处调用按 2 项解包；
- 社区发现依赖 Hotspot 空间共变基因模块，不是简单 cell-type KNN 组成聚类；
- 5 个 Slide-tags 阵列在公开元数据中均来自同一只 SPC-11，阵列数不能当作动物数。

这些代码问题是否影响终刊中的具体数字，需要最终冻结代码、真实输入和运行环境才能判断，不能用局部反例直接宣布整篇论文失效。

## 代码固定版本

- KPSpatial-release: `c2fa7568ee48a9e35bbc6ecd88378c6768b23e00`
- Cassiopeia: `1ee5959eb9d3f8d4d26e2af5678234493bf54d6d`

这两个提交用于本次审计，不代表已经证明与论文终刊实际运行环境逐字节一致。
