# KPSpatial｜从空间谱系研究到可检验的肿瘤时空演进 idea

**论文：** Jones MG, Sun D, Min KHJ, et al. *Spatiotemporal lineage tracing reveals the dynamic spatial architecture of tumor growth and metastasis*. **Nature Genetics** 58, 2398–2410 (2026). DOI：[10.1038/s41588-026-02739-z](https://www.nature.com/articles/s41588-026-02739-z)。正式发表日期：2026-09-02。

**整理日期：2026-09-11。性质：论文精读＋研究设计重建＋固定版本代码审计＋项目迁移方案；不是已完成的科学复现。**

## 这份 idea 要回答什么

一张空间图只能显示采样时的组织状态。相似细胞可能来自共同祖先，也可能在相同环境下趋同；某个扩增区域与低氧共存，也可能由扩增、环境选择、双向反馈或取样共同产生。本文的重要性，是把**历史、位置、状态、环境**放进同一研究框架，并以不同设计逐步约束这些解释。本文的技术主体是 **Slide-seq、Slide-tags 与独立谱系记录**，不是普通分期 Xenium。

这里不只复述作者的结论，而是解释每一步设计增加了什么信息、少了哪一步就不能写哪一种结论，以及读者如何用自己的现有数据先做有决策价值的检查。

## 从哪里开始读

| 阅读层次 | 文档 | 读完应能回答的问题 |
|---|---|---|
| 1. 故事与逻辑 | [01 研究故事与竞争解释](docs/01-story-and-identifiability.md) | 为什么仅有空间图不够？作者真正缩小了哪些解释之间的差距？ |
| 2. 设计与证据 | [02 研究设计与图证据索引](docs/02-design-and-evidence.md) | 操纵、测量、对照和推断分别是什么？主图、扩展图各承担什么任务？ |
| 3. 方法与算法 | [03 计算方法逐层解析](docs/03-computational-protocol.md) | 表达、谱系、树、fitness、plasticity、邻域、通信、转移匹配如何连接？ |
| 4. 代码与实现 | [04 固定版本代码地图和问题定位](docs/04-code-atlas-and-audit.md) | 去哪个文件看？方法声明、默认值和活动调用是否一致？ |
| 5. 可迁移启发 | [四条启发总览与反向审查](insights/README.md) | 哪些判断原则值得带到完全不同的项目？ |
| 5a | [历史与状态必须分开](insights/01-history-versus-state.md) | 表达连续性何时不能被解释为后代转变？ |
| 5b | [背景条件可能决定效应](insights/02-context-dependent-effects.md) | 阴性或阳性结果是否取决于培养与组织背景？ |
| 5c | [预处理不是独立验证](insights/03-information-reuse.md) | 空间插补、平滑与基因重用如何影响结论资格？ |
| 5d | [参照集合和独立重复](insights/04-units-and-reference-sets.md) | 到底是在比较细胞、区域、肿瘤还是动物？ |
| 6. 项目落地 | [分期 Xenium 对应方案](project/01-xenium-translation.md) | 单一起始克隆、早中晚期样本能回答什么，不能回答什么？ |
| 7. 研究决策 | [行动表与实验升级门槛](project/02-decision-and-action-table.md) | 明天先检查什么？什么结果才值得增加实验？ |
| 8. 复现准备 | [分阶段复现路线](reproducibility/README.md) | 从哪里开始重算最短关键链？现在缺什么？ |

## 查参数、查出处、查状态

- [103 条参数来源登记](methods/parameter_registry.tsv)：分别标记 `reported`、`active_code`、`code_default`、`unverified`；**不是可直接运行的统一配置**。保留此前审计包中的完整登记，不将跨平台或跨支路参数拼接。
- [来源、版本与访问范围](evidence/SOURCES.md)：终刊、补充方法、Reporting Summary、固定提交、归档线索及本次未取得内容。
- [主张证据表](evidence/claims.tsv)与[15 条分析追踪表](reproducibility/traceability.tsv)：把结论、图、方法、代码、输入输出及缺口连接起来。
- [可执行的元数据与逻辑检查](scripts/preflight.py)及[测试](tests/test_preflight.py)：只检查数据合同、公开阵列元数据及最小集合逻辑，不运行作者科学分析。
- [实际执行记录](validation/receipt.json)：记录本目录提供的检查做到了什么；没有论文重算结果。

## 全文的四类标记

**【论文报告】** 作者在可取得的终刊页面、图注、补充方法或 Reporting Summary 中实际写出的内容。图标题只能支持问题定位，不能替代未取得的完整 panel 证据。

**【代码事实】** 固定提交中的可见实现、常量、参数默认值和活动调用。静态代码不等于作者生成终刊结果的执行日志。

**【解释】** 本整理对研究逻辑、识别条件及替代解释的分析，不冒充作者预先登记的假说。

**【迁移建议】** 面向其他项目的检查、设计原则或新假说；跨项目有效性需要重新检验，不声称新颖性。

## 必须保留的边界

已取得的是终刊公开摘要、主图标题、扩展图图注、补充方法在线文本、部分公式图像，以及关键代码和阵列元数据。**没有完整终刊 Results、全部主图原图、完整 Supplementary Tables、完整代码归档比对、处理矩阵或全 notebook 执行链。** GitHub qPCR 小表已读，不等于终刊补充表已获得；重复单位与终点细胞来源仍待核清。

代码审计固定于 `mattjones315/KPSpatial-release@c2fa7568ee48a9e35bbc6ecd88378c6768b23e00`。本文没有改动作者仓库，没有声称复现任何树、P 值、效应量或论文图片。最小检查通过，只能证明相应数据合同或逻辑事实。

## 本 idea 的中心结论

> **最值得迁移的是让竞争模型给出不同预测的设计，不是把原文最后一张演进示意图换成自己的疾病名称。**

对只有分期 Xenium 的项目，优先构建带真实阶段锚点的组织状态与生态位重组模型；精细祖先—后代关系需要相应历史证据。区域不等于克隆，拟时序不等于真实采样时间，树上相对 fitness 不等于直接测量的绝对增殖速度。

新增文稿、代码和表格的范围见 [CHANGELOG](CHANGELOG.md)。原文和上游代码的权利归各自作者；本目录不重新发布付费全文、原论文图片或大型数据归档。
