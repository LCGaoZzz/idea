# 从空间克隆到组织界面：Mo 2024 的完整研究 idea 档案

**文章标题：** Tumour evolution and microenvironment interactions in 2D and 3D space

**文章链接：** [期刊原文](https://www.nature.com/articles/s41586-024-08087-4) · [DOI](https://doi.org/10.1038/s41586-024-08087-4)

**第一张主图（Figure 1）：**

[![论文 Figure 1](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41586-024-08087-4/MediaObjects/41586_2024_8087_Fig1_HTML.png)](https://www.nature.com/articles/s41586-024-08087-4/figures/1)

*来源：[Nature · Figure 1](https://www.nature.com/articles/s41586-024-08087-4/figures/1)。图片由出版社网站外链展示，版权归原作者及出版方。*

---

**核心问题：如何把遗传身份、细胞状态、细胞组成和组织几何分开测量，再研究它们之间的关系？**

本文档围绕 Mo, C.-K., Liu, J., Chen, S. et al. **Tumour evolution and microenvironment interactions in 2D and 3D space**, *Nature* 634, 1178–1186 (2024)，DOI [10.1038/s41586-024-08087-4](https://doi.org/10.1038/s41586-024-08087-4)，建立面向研究判断、设计迁移与代码复核的完整阅读路线。整理日期：2026-09-12。

> 这不是作者论文的逐句翻译，也不是已经跑通的论文复现包。论文事实、固定版本代码、我们的推导、迁移假说始终分别标记。实际执行的是本档案自编的 **24 项合成数学检查**；没有执行作者的患者数据流程、R/GenomicRanges 分析、Mushroom 训练或 PyTorch 模型。

## 从哪里开始读

| 阅读目的 | 入口 | 读完应能回答的问题 |
|---|---|---|
| 理解故事与不可替代的设计 | [01 研究故事](docs/01_story.md) → [02 设计与证据链](docs/02_design.md) | 每一步排除了什么解释，又留下什么解释？ |
| 理解分析如何实现 | [03 CNV 与变异](docs/03_cnv.md) → [04 状态、边界与通信](docs/04_boundary.md) → [05 三维与成像](docs/05_3d.md) | 每个输入、分析对象和中间产物是什么？ |
| 数学统计深读 | [06 数学、统计与识别条件](docs/06_math_statistics.md) | 相似度、距离、分母、独立重复和损失函数是否匹配主张？ |
| 提炼可迁移的研究判断 | [07 五条启发](docs/07_insights.md) | 哪些原则可迁移，哪些生物学结论不能外推？ |
| 应用到分时期 Xenium | [08 项目对应与最小行动](docs/08_xenium_project.md) | 先用现有数据区分哪些竞争解释？ |
| 审查实现与运行边界 | [09 代码审计](docs/09_code_audit.md) → [10 复现、行动表与未决问题](docs/10_reproduction.md) | 哪些是已确认实现、材料冲突或尚缺的运行证据？ |

[来源与固定版本](references/README.md)｜[图—代码对应表](tables/figure_code_map.tsv)｜[参数来源表](tables/parameter_provenance.tsv)｜[状态记录](evidence/status.json)｜[更新说明](evidence/CHANGELOG.md)｜[合成检查代码](code/run_checks.py)｜[真实测试记录](validation/synthetic_checks.json)

## 四种证据标签

**【P：论文事实】**：作者正文、图注或 Methods 实际报告的内容；来源使用最终发表图号和方法小节。不是本次重算的发现。

**【C：代码发现】**：指定 commit 的活动语句、函数或 notebook cell。只有默认配置时写“默认配置”；只有路径时写“仅定位”。固定版本不等于论文最终运行版本。

**【I：解释／数学推导】**：本档案对证据逻辑、识别条件、数学性质的分析。反例可以证明某性质不普遍成立，但不能自动证明患者结论发生了改变。

**【H：迁移建议／新假说】**：面向其他项目的可执行检查或待检验关系，不是作者做过的额外实验，也不是已经在其他疾病中成立的规律。

“已执行验证”只用于有实际日志支持的指定任务。本档案的原始数据复现仍然受阻，不能用文档完整、链接存在或单元测试通过来替代。

## 整篇研究的一条主线

【I】先定义形态与位置上的微区域；再用遗传证据辨别其身份；随后区分身份差异、细胞内状态和细胞混合；将边界变成共同坐标；最后检验二维分离是否在三维仍然成立，以及不同结构接触什么局部环境。

四个对象必须分开：**microregion 是组织几何单元，spatial subclone 是遗传证据支持的分组，volume 是跨切片连通体，neighbourhood 是局部多模态特征单元**。同一个聚类标签不能无条件代替它们。[P：Fig. 1–5；Methods，详见各章]

虽然存放于 `Xenium-CNV`，这篇研究并非只靠 Xenium 面板从头恢复全基因组 CNV，也不是早中晚纵向 Xenium 谱系追踪。Xenium 的选定位点原位证据与 Visium/WES/CNV 主线需要分别理解。

## 本版相对之前讨论新增的实质内容

【C/I】扩展审读 `Figure2/3_CNV_jaccard_similarity.R` 后，发现无概率辅助函数的分母不对称；概率分支与论文的有符号相似度也不是同一公式。脚本末端实际选择 `jac_pred_mat`，因此不能把无概率分支的问题直接归给最终克隆标签。

【I】给出 `D=1−S` 不总是欧氏距离的具体反例：对应双中心 Gram 矩阵有负特征值。因此 Ward 的最小方差解释不能仅凭调用 `ward.D2` 自动成立。

【C/I】扩展审读 Mushroom `SAE.forward` 后，确认其将 softmax 概率传入 `F.cross_entropy`；这与把未归一化 logits 传入该函数的语义不同。我们只验证了数学差异，没有量化其对论文模型或结论的影响。同时，层级分支 `(8,4,2)` 与累计邻域数 `(8,32,64)` 的关系得到实现层面解释，不再把它们列为数值冲突。

## 复用方式

阅读与设计迁移优先于重跑全部原始数据。先选一个结论，明确需要哪些输入、比较单位和最终参数，再恢复其完整依赖链。代码中的数学示例可运行，但**不是 CNV 调用器、Xenium 分析流水线或论文一键复现入口**。

所有作者代码以固定链接引用，不在本目录复制完整上游仓库；不再分发论文全文、修改后的原图或原始患者数据。本文包含原创建模讨论与审读意见，不能替代原文及作者最终运行记录。
