# KPSpatial｜空间谱系论文 DeepAudit 知识库

**文章标题：** Spatiotemporal lineage tracing reveals the dynamic spatial architecture of tumor growth and metastasis

**文章链接：** [期刊原文](https://www.nature.com/articles/s41588-026-02739-z) · [DOI](https://doi.org/10.1038/s41588-026-02739-z)

**第一张主图（Figure 1）：**

[![论文 Figure 1](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41588-026-02739-z/MediaObjects/41588_2026_2739_Fig1_HTML.png)](https://www.nature.com/articles/s41588-026-02739-z/figures/1)

*来源：[Nature Genetics · Figure 1](https://www.nature.com/articles/s41588-026-02739-z/figures/1)。图片由出版社网站外链展示，版权归原作者及出版方。*

---

Jones、Sun 等 · *Nature Genetics* (2026) · DOI `10.1038/s41588-026-02739-z`  
镜像整理日期：2026-09-16

这是从用户提供的 `KPSpatial_DeepAudit_2026-09-16(1).zip` 整理到 GitHub 的**深度审计知识库镜像**，不是前一版只有结论摘要的目录。源 ZIP 的范围与 SHA256 见 [`BUNDLE_INVENTORY.md`](BUNDLE_INVENTORY.md)。

它包含研究逻辑重建、固定提交的代码审读、真实运行的局部反例检验、空间统计与因果边界、转移分析，以及分期 Xenium 的迁移框架。**不是整篇论文的端到端复现。** 当前范围约束见 [`audit/delivery_scope.json`](audit/delivery_scope.json)。

## 推荐入口

1. [`docs/01_范围版本与结论.md`](docs/01_范围版本与结论.md) — 范围、版本和结论边界。
2. [`docs/02_研究故事与竞争解释.md`](docs/02_研究故事与竞争解释.md) — 从“共同祖先 vs 共同环境”重建研究故事。
3. [`docs/04_计算主干与数学对象.md`](docs/04_计算主干与数学对象.md) — lineage、fitness、plasticity、邻域的输入输出与数学对象。
4. [`docs/05_空间社区的完整解释.md`](docs/05_空间社区的完整解释.md) — Hotspot → 跨样本共识 → spot score；不是简单 cell-type KNN 聚类。
5. [`docs/06_代码审计与修复边界.md`](docs/06_代码审计与修复边界.md) — CNV permutation、fitness、插补、过滤和接口问题。
6. [`docs/07_实际执行与反例.md`](docs/07_实际执行与反例.md) — 实际运行了什么、没有运行什么。
7. [`docs/08_统计学与因果推断.md`](docs/08_统计学与因果推断.md) — 伪重复、空间依赖、组成/状态分离。
8. [`docs/09_转移来源与相互作用.md`](docs/09_转移来源与相互作用.md) — 转移来源、跨层匹配、LARIS 与因果上限。
9. [`docs/11_迁移到分期Xenium.md`](docs/11_迁移到分期Xenium.md) — 迁移到早/中/晚期 Xenium 的可反驳分析框架。
10. [`review/FABLE_REVIEW_PROMPT.md`](review/FABLE_REVIEW_PROMPT.md) — 给独立模型做反驳式审核的完整交接。

其余章节：[`03`](docs/03_逐图证据地图.md) · [`10`](docs/10_可复现实施与输入输出.md) · [`12`](docs/12_审阅交接与问题清单.md)。

## 审计与证据层

- [`audit/deep_audit_results.json`](audit/deep_audit_results.json)：22 项新增局部检测/回归检查的收据。
- [`audit/inherited_checks_rerun.json`](audit/inherited_checks_rerun.json)：旧包 10 项检查的本次重跑。
- [`audit/delivery_checks.json`](audit/delivery_checks.json)：交付结构/导航/浏览器等检查。
- [`audit/reader_browser_check.json`](audit/reader_browser_check.json)：离线阅读器渲染检查。
- [`REPORT.md`](REPORT.md)：15 项原论文分析的严格状态表；0 项被标记为“已执行验证”。
- [`SOURCES.md`](SOURCES.md) / [`sources_catalog.json`](sources_catalog.json)：论文、补充材料、代码、数据记录与固定版本来源。
- [`CODE_LOCATORS.md`](CODE_LOCATORS.md)：关键函数、脚本和表的定位。
- [`evidence/`](evidence/)：CNV 检验完整脚本、样本元数据、公开结果表、Cassiopeia 输出链及其他审计代码节选。

## 图与工具

`figures/` 保存 4 幅**可编辑 SVG**解释图：证据架构、Hotspot 社区流程、四叶树 permutation 反例、Xenium 迁移边界。它们是本次原创解释图，不是论文原图。

`tools/permutation_nn.py` 是独立的固定邻居图标签置换 helper，使用包含并列值的上尾概率、Monte Carlo `+1` 校正、显式种子和可选分块；它不构建谱系树，也不自动保证调用者定义的置换总体可交换。`tools/check_delivery.py` 只检查交付结构，不认证论文科学结果。

## Agent 入口

- [`agent/SKILL.md`](agent/SKILL.md)
- [`agent/knowledge_index.json`](agent/knowledge_index.json)

Agent 应始终区分：**论文报告 [P]、代码实现 [C]、本次解释 [I]、迁移/假说 [H]**。禁止把 audit 通过等同于论文复现成功，也禁止把普通 Xenium 的表达相似性直接升级为真实谱系。

## 二进制镜像边界

当前 GitHub 写入通道以文本/Git-data 操作为主，因此本次提交不声称源 ZIP 容器、原始合并 HTML/Markdown 阅读器以及四张 PNG 均已按原始字节逐一镜像。源 ZIP 的 SHA256 已记录；仓库已经提交完整 12 章正文、核心代码/表/审计收据和全部四张 SVG 等价图源。详见 [`BUNDLE_INVENTORY.md`](BUNDLE_INVENTORY.md)。

## 固定审计版本

- KPSpatial-release: `c2fa7568ee48a9e35bbc6ecd88378c6768b23e00`
- Cassiopeia: `1ee5959eb9d3f8d4d26e2af5678234493bf54d6d`

二者均未证明与终刊全部结果的最终运行环境逐字节等同。第三方来源与许可边界见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。
