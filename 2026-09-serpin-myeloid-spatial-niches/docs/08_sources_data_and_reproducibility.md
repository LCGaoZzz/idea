# 08｜来源、数据可及性与复现边界

[返回总目录](../README.md) · [上一章](07_integrated_idea_and_execution_plan.md) · [代码说明](../code/README.md)

## 1. 来源登记

### S1：研究原文

Falcomatà, C., Schaefer, M. M., Singh, B. et al. *A serpin–myeloid axis in pancreatic cancer heterogeneity and immune evasion*. **Nature**，2026 年 9 月 9 日。DOI：[10.1038/s41586-026-11002-8](https://doi.org/10.1038/s41586-026-11002-8)。

本目录使用原文公开可检索文本、相关 Methods 和图注进行事实核对，不是全文译文。部分直接页面/PDF 访问出现登录重定向；未完整下载和逐项重算所有 Source Data/补充表，未逐图像复核全套主图与扩展图。方法分析中的“不确定/未核实”不能被抹去。

### S2：本篇专属代码

[固定版本仓库](https://github.com/BDBrownLab/Falcomata_PDAC_2026/tree/da2fcf70b89c911728cdcd519e72a153f17e743b)

```text
repository: BDBrownLab/Falcomata_PDAC_2026
commit: da2fcf70b89c911728cdcd519e72a153f17e743b
```

其 README 说明仓库包含单细胞、Visium、Xenium 和相应图的代码。这个说明不意味着所有实际输入、门控配置、图像和下游拟合均已包含。第 6 章以文件为单位说明实际看到的实现与缺口。

### S3：基础 Perturb-map 代码

[srose89/Perturb-map](https://github.com/srose89/Perturb-map) 的 README 将其标明为早期 Perturb-map 分析代码，包括小鼠肺 Visium、MICSSS 去条码/病灶定义等。[README](https://github.com/srose89/Perturb-map/blob/main/README.md)

本目录仅使用它说明基础方法来源，没有把它当成本篇 PDAC 的固定实验配置；也没有将这个未冻结的链接纳入“本次已下载并重现”的声明。

### S4–S6：软件语义的第一方说明

- [Scanpy score_genes 官方说明](https://scanpy.readthedocs.io/en/stable/generated/scanpy.tl.score_genes.html)：分数是目标与参考基因表达之差，输入表示和随机设置需要明确。
- [cell2location 官方教程](https://cell2location.readthedocs.io/en/latest/notebooks/cell2location_tutorial.html)：`q05_cell_abundance_w_sf` 是后验 5% 分位摘要，不是均值或真实计数。
- [Squidpy nhood_enrichment 官方实现](https://squidpy.readthedocs.io/en/stable/_modules/squidpy/gr/_nhood.html)：邻接计数、置换、z-score 与图像限制的实际语义。

这些在线说明用于解释 API 含义，不能代替作者当年具体环境；正式复现应分别冻结原方法环境与新实现环境。

## 2. 核心证据台账

| ID | 可支持的主张 | 来源位置 | 证据类别 | 不能越过的边界 |
|---|---|---|---|---|
| E01 | 问题指向局部免疫组织，而非只有全局性质 | S1 Main；S2 README | 研究问题 | 不是已证明所有肿瘤都服从同一规律 |
| E02 | 候选经过来源/胞外定位与体外依赖性优先筛选 | S1 Fig. 1、ED1–3 | 设计事实 | 不是全基因组无偏筛选 |
| E03 | 分时点观察局部环境与群体空间变化 | S1 Fig. 1；S2 README | 时序组织证据 | 不是同一细胞连续追踪 |
| E04 | serpin 缺失效应依赖免疫背景 | S1 Fig. 1g–h、2j–k | 干预与环境比较 | 免疫缺失不等于单一 CD8 专一干预 |
| E05 | serpin、材料与髓系改变共同支持机制框架 | S1 Fig. 3–4；S2 README | 多层证据 | 未直接测得完整纤溶动力学 |
| E06 | BMDM 基底比较包含 PDAC 条件培养基，关键读数为 MFI | S1 Fig. 4i–j、ED8r | 条件性材料干预 | 不等于无条件充分或完整功能证明 |
| E07 | 起始 5% 对照在终点约 17% | S1 Fig. 5d–i | 组成操纵与选择结果 | 不能称终点仍为个位数 |
| E08 | ROI 半径、计数门槛、混合度与采样可追溯 | S1 ROI Methods；S2 ROI notebook | 方法＋源码 | 不等于独立 ROI 或完整拟合公开 |
| E09 | 患者级代码分开阳性比例与阳性内均值 | S2 per_patient notebook | 直接源码 | 检测零不等于确定的生物学阴性 |
| E10 | Visium 比较涉及解卷积与非癌组成归一化 | S2 Visium 02/03；S5 | 直接源码/模型语义 | 不是细胞级来源或绝对密度的直接实测 |
| E11 | 公布版本存在可确认语法错误与若干条件性风险 | S2 Visium 02；本地编译测试 | 源码行为 | 不能直接判定论文生物学错误 |
| E12 | 完整 idea 的层级/非线性/材料交互方案 | 本目录第 5、7 章 | 拟议扩展 | 不得归于作者已完成分析 |

每个章节中的原文/源码链接进一步定位该表；代码获取清单保存具体文件的 Git blob SHA。

## 3. 公开数据与“数据完全开放”不是一回事

原文列出的外部人类空间资料包括 `phs002371.v1.p1`、`GSE274557`、`GSE278694`；人类单细胞资料包括 `phs002371.v1.p1`、`GSE155698`、`GSE217847`、`GSE278694`、`GSE205013`。[原文 Data availability](https://www.nature.com/articles/s41586-026-11002-8)

本次没有下载这些患者数据，也未独立验证每个入口的当前可下载文件、权限状态或全部元数据。尤其不能因为论文引用了 accession，就假定原始文件都能无需授权获取。`phs...` 条目的访问条件应在对应数据库核实，不能与 GEO 条目混为同一种开放方式。

专属 Visium README 还列出 Zhou/HTAN、Pei、Chen 三个分析来源及 PMID，提供预处理、整合解卷积、论文分析三个入口。[Visium README](https://github.com/BDBrownLab/Falcomata_PDAC_2026/blob/da2fcf70b89c911728cdcd519e72a153f17e743b/Visium/README.md)

这些是作者使用来源的导航，不是本目录新建立的数据集。小鼠 Perturb-map Multi-modal 的 Xenium 代码也不能自动被称作“患者 Xenium 验证”；必须以样本物种和实验身份区分。

## 4. 实际完成与未完成

| 状态 | 内容 |
|---|---|
| 已完成 | 三条见解及其统一研究逻辑的详细组织 |
| 已完成 | 关键源文件、参数、变量与输入输出的静态审读 |
| 已完成 | 隔离确认 Visium 辅助函数的括号语法错误，提供最小修正示例 |
| 已完成 | 新写教学程序的本地单元测试与合成数据演示 |
| 已完成 | 固定代码来源清单、SHA 校验获取脚本与上游许可保留 |
| 未完成 | 原始图像全流程配准/分割与门控重跑 |
| 未完成 | 患者数据下载、完整 atlas/Visium/cell2location 重训练 |
| 未完成 | Fig. 5l 精确拟合、系数、P 值或 R² 的独立再计算 |
| 未完成 | 全套 Source Data、补充表与论文图的数值复现 |
| 未完成 | 新提出的研究假说与实验的生物学验证 |
| 未完成 | 获取脚本对远程全部文件的端到端网络下载验证；本次测试为本地校验/解析逻辑 |

未完成项不是用来否认已有证据，而是防止把方法理解、代码通过测试和论文结果复现当作同一件事。

## 5. 如何取回作者代码并保持可追溯？

在本目录运行：

```bash
python code/fetch_original_code.py --out original_code
```

脚本逐文件使用固定 commit 的 raw URL，计算 Git blob SHA（含 Git 的 blob header），与 manifest 中值比较。校验失败不写入该文件；与现有本地不同内容冲突时默认不覆盖。只有显式 `--overwrite` 才允许有意替换。

原 notebook 保留；另外生成 `*.ipynb.source.txt` 阅读副本，包含 cell 编号/id 和源码，不包含 notebook 保存的输出或图片。**读取副本不等于执行结果**，脚本不自动执行 notebook。失败记录进入 `fetch_report.json`，不得将部分下载显示为全部成功。

## 6. 环境与测试如何解释？

`code/requirements.txt` 是本目录教学代码的依赖范围，不是作者环境锁文件。实际本地版本、测试数量与演示输出摘要记录在 [validation.json](../provenance/validation.json)。

测试覆盖表达表示、阴性组条件均值、图像隔离、方向性暴露与对称混合度、面积、重叠、零分母、因子配对、Git SHA 与路径安全等。它们不能验证肿瘤来源身份是否真实，也不能证明材料中介或临床疗效。

演示中的效应项是程序构造的，输出必须保留 `SYNTHETIC_NOT_PAPER_DATA`。不要将演示置信区间拷贝到研究结果中。

## 7. 版权与引用

作者代码的 MIT 许可在 [LICENSE_BrownLab.txt](../provenance/LICENSE_BrownLab.txt) 中完整保留；原代码短摘录和固定版本链接均标明来源。论文网页显示 CC BY-NC-ND 4.0，不因此获得转载改编原图或全文译文的许可；本目录不分发论文 PDF、原图或全文翻译。

本目录是独立的方法评论、代码审读与拟议研究方案，不代表作者认可，也未给整个 `idea` 仓库添加新的统一许可证。

## 8. 更新原则

未来若作者补充 Fig. 5l 拟合、修复 notebook 或公开缺失配置，应新增审读日期与 commit，保留旧版发现的适用范围。不能仅因为主分支更新就让旧链接漂移；也不应将已经修复的问题继续写成最新版现状。

**可信的研究档案应同时保留：已知什么、由什么支持、代码实际做了什么，以及哪些连接仍需验证。**
