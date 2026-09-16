# 从空间遗传身份到肿瘤界面与三维生态：一个可审查、可迁移的研究 idea

**文章标题：** Tumour evolution and microenvironment interactions in 2D and 3D space

**文章链接：** [期刊原文](https://www.nature.com/articles/s41586-024-08087-4) · [DOI](https://doi.org/10.1038/s41586-024-08087-4)

**第一张主图（Figure 1）：**

[![论文 Figure 1](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41586-024-08087-4/MediaObjects/41586_2024_8087_Fig1_HTML.png)](https://www.nature.com/articles/s41586-024-08087-4/figures/1)

*来源：[Nature · Figure 1](https://www.nature.com/articles/s41586-024-08087-4/figures/1)。图片由出版社网站外链展示，版权归原作者及出版方。*

---

**原始研究**：Mo, C.-K., Liu, J., Chen, S. et al. *Tumour evolution and microenvironment interactions in 2D and 3D space*. Nature **634**, 1178–1186 (2024). DOI: [10.1038/s41586-024-08087-4](https://www.nature.com/articles/s41586-024-08087-4)。在线发表：2024-10-30。

**本文档定位**：重建研究问题、设计、证据链、计算方法和代码实现，并据此提出能够改变研究判断的迁移方案。它不是原论文翻译，也不是已完成的患者数据复现。整理及补充核查日期：2026-09-12。

> **核心 idea：先分别定义遗传身份、细胞状态、细胞组成与组织几何，再检验它们如何共同解释局部表型。不要让一个表达聚类标签同时充当克隆、状态和生态位。**

## 先读懂三个边界

1. 本研究以人类 Visium 组织及配对分子/成像数据为主体；Xenium 在 Fig. 2j 提供特定位点的原位等位基因支持。**它不是仅用普通 Xenium 面板完成全基因组 CNV 检测的研究。**
2. 连续切片的连续是空间 z 轴，不是时间轴；三维连通体、推测的遗传关系和真实谱系追踪是不同对象。
3. 本次完成文献与固定版本代码的审读，并运行独立编写的合成数学检查；未运行原作者 R/Python 数据流程、未训练 Mushroom、未重新分割 CODEX、未复算患者面板。

以上研究范围参见原文 [Fig. 1](https://www.nature.com/articles/s41586-024-08087-4/figures/1)、[Fig. 2](https://www.nature.com/articles/s41586-024-08087-4/figures/2)、[Fig. 4](https://www.nature.com/articles/s41586-024-08087-4/figures/4)、[Fig. 5](https://www.nature.com/articles/s41586-024-08087-4/figures/5) 及 Methods。

## 阅读路线

| 顺序 | 文档 | 读完应能回答什么 |
|---|---|---|
| 1 | [研究故事、竞争解释与不可缺少的设计](docs/01_story_and_design.md) | 作者究竟减少了哪种解释歧义，哪些因果连接仍未检验？ |
| 2 | [数据、测量尺度与分析单位](docs/02_data_and_measurements.md) | case、block、section、microregion、clone、volume、neighbourhood有何不同？ |
| 3 | [CNV、突变与克隆识别的方法重建](docs/03_cnv_and_variant_protocol.md) | 遗传标签从何而来；原文公式和公开实现哪里不一致？ |
| 4 | [状态、核心—边缘与通信分析](docs/04_state_boundary_and_interactions.md) | 怎样分开位置、纯度、表达来源和通信候选？ |
| 5 | [三维结构、Mushroom与CODEX](docs/05_3d_and_multimodal_protocol.md) | PASTE2与Mushroom分别重建什么；哪些部分由模型补齐？ |
| 6 | [五条可迁移启发：逐条八项展开](docs/06_five_transferable_insights.md) | 哪些原则能迁移，迁移依赖什么，怎样被反驳？ |
| 7 | [对应分时期小鼠Xenium项目](docs/07_xenium_timecourse_project.md) | 先用已有数据排除什么解释，何时才值得新增实验？ |
| 8 | [固定版本代码审计与材料冲突](docs/08_code_audit_and_gaps.md) | 哪些代码读过；哪些只是定位；有哪些活动实现风险？ |
| 9 | [实施顺序、数据合同和验收](docs/09_execution_and_acceptance.md) | 哪些步骤现在能检查；真正复现还缺什么？ |

没有读过论文的读者按1→2→3→4→5顺序阅读，再看启发；已经了解空间组学的读者可以先读6→7→8。

## 证据标签

- **【P｜论文事实】**：论文正文、图注或Methods明确报告；作者解释若具有较强因果措辞，会单独注明为作者解释。
- **【C｜代码事实】**：固定快照中实际存在的活动语句、函数、默认值或文件结构；不代表它一定生成最终论文结果。
- **【I｜逻辑解释】**：本目录对研究逻辑、变量关系和证据等级的分析。
- **【H｜迁移建议/假说】**：新项目可检验的设计或解释，不是原作者已完成的实验。
- **【T｜本次局部检查】**：仅限独立编写的合成数学检查；它不升级原研究的复现状态。

重要主张给出最终发表图号、Methods小节或固定代码链接。仓库保留了旧稿的Figure编号，**不能直接照目录名推断最终图号**。

## 本轮新增且必须保留的审计发现

`Figure2/3_CNV_jaccard_similarity.R`不仅包含与论文有符号公式不同的相似度定义，活动选择还使用`jac_pred_mat`及一组K值探索。另一个硬调用函数存在分母只纳入B的缺失事件、未纳入B全部非中性事件的不对称逻辑。必须区分这两个路径，不能将硬调用函数的问题直接归因到最终选中的概率路径。

详见[代码审计](docs/08_code_audit_and_gaps.md)与[合成检查](scripts/evidence_sanity.py)。在本次Python 3.13.5环境中，9项合成检查通过；**没有执行原R函数，也没有证明原论文的克隆标签错误**。

## 机器可读与可执行辅助材料

- [图—方法—代码证据表](evidence/traceability.tsv)
- [参数来源表](evidence/parameter_provenance.tsv)
- [固定仓库版本](evidence/repository_pins.tsv)
- [冲突与缺口登记](evidence/gaps.tsv)
- [来源与获取边界](evidence/source_index.md)
- [范围与执行状态](evidence/scope.json)
- [合成检查结果](evidence/sanity_result.json)
- [合成数学检查代码](scripts/evidence_sanity.py)
- [样本清单模板](templates/sample_manifest.tsv)
- [分析资格/缺失状态模板](templates/measurement_status.tsv)

## 最终应形成的研究判断

本文最值得迁移的是：**以独立定义的界面为坐标，在可比较的身份、细胞类型与几何条件下研究响应。**最不应直接照搬的是：将未测量、不可检验与不显著全部当作生物学上的零，再把汇总量当作平均效应。

本目录提供研究设计、方法解释、作者代码入口与局部检查，不伪装成一键复现工具。没有取得的样本级最终参数、完整补充文件、运行日志及输入对象，均保留为缺口。所有原图与完整上游源码均通过原始链接访问，不在本目录重新打包分发。
