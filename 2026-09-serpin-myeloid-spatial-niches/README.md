# 稀有肿瘤状态如何组织局部免疫抑制

**文章标题：** A serpin–myeloid axis in pancreatic cancer heterogeneity and immune evasion

**文章链接：** [期刊原文](https://www.nature.com/articles/s41586-026-11002-8) · [DOI](https://doi.org/10.1038/s41586-026-11002-8)

**第一张主图（Figure 1）：**

[![论文 Figure 1](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41586-026-11002-8/MediaObjects/41586_2026_11002_Fig1_HTML.png)](https://www.nature.com/articles/s41586-026-11002-8/figures/1)

*来源：[Nature · Figure 1](https://www.nature.com/articles/s41586-026-11002-8/figures/1)。图片由出版社网站外链展示，版权归原作者及出版方。*

---

## 从 serpin–myeloid 研究到可检验、可编码、可迁移的空间肿瘤学 idea

**核心问题：少数恶性细胞能否通过改变局部胞外材料环境，重塑周围髓系细胞与 T 细胞，进而获得不成比例的生态位优势？**

本目录围绕 Falcomatà、Schaefer、Singh 等发表于 **Nature，2026 年 9 月 9 日**的研究 *A serpin–myeloid axis in pancreatic cancer heterogeneity and immune evasion*，将论文逻辑、三条见解、实际代码及新的研究设计组织成一套独立可读的研究档案。[原文与 DOI](https://doi.org/10.1038/s41586-026-11002-8)

这不是论文全文翻译，也不是“已复现论文”的声明。原文的实验发现、作者公开代码的实际实现、我们的解释与拟议扩展始终分开。**未获得并重跑完整原始图像、测序数据和全部 Source Data；教学代码中的数据明确为合成数据。**

## 1. 三个见解，最终合成一个 idea

| 见解 | 从什么问题转向什么问题 | 需要增加的测量 |
|---|---|---|
| 不只看平均表达 | 从“整个肿瘤表达多高”转向“谁在何处表达、谁受到局部影响” | 来源比例、阳性细胞内强度、空间暴露与邻域响应 |
| ECM 是有生物学作用的材料环境 | 从“ECM 通路上调”转向“哪一种材料状态改变了细胞定位与状态” | 特定基质蛋白/沉积、结构、接触关系与功能对照 |
| 原位功能基因组学 | 从“敲除后自己长不长”转向“敲除后周围环境如何改变，邻居能否补偿” | 扰动身份、组织坐标、免疫状态、时间与群体适应度 |

统一链条：

```text
恶性细胞状态 / 基因扰动
          ↓
局部胞外材料环境
          ↓
髓系细胞的数量、位置与内部程序
          ↓
T 细胞进入、停留与功能
          ↓
肿瘤群体在特定免疫背景下的适应度
```

这些箭头不是全部由同一种实验直接证明；每个箭头的证据等级和替代解释见第 1、5、8 章。

## 2. 阅读目录

建议首次按顺序阅读。面向组会，可先读 1、2、3、4、7 章；面向分析人员，再完整阅读 5、6、8 章。

| 章节 | 内容 |
|---|---|
| [01 论文故事与研究设计](docs/01_paper_story_and_design.md) | 研究矛盾、筛选逻辑、时空证据、机制与功能闭环、术语 |
| [02 稀有状态与局部显性](docs/02_rare_states_local_dominance.md) | 均值分解、患者级统计、混合实验、ROI 真实实现、可证伪假说 |
| [03 ECM 作为信号性材料环境](docs/03_ecm_as_signal_surface.md) | fibrin 实验到底证明什么、测量层级、基底控制、因子设计 |
| [04 原位功能基因组学](docs/04_in_situ_functional_genomics.md) | 候选富集、Pro-Code、跨模态对齐、空间图、邻居补偿 |
| [05 统计与因果推断](docs/05_statistics_and_causal_inference.md) | 估计目标、分母、伪重复、重叠、空间零模型、非线性、中介 |
| [06 原始代码逐层解析与审读](docs/06_code_walkthrough_and_audit.md) | 文件—函数—参数—输入输出映射，以及真实复现风险 |
| [07 完整 idea 与执行方案](docs/07_integrated_idea_and_execution_plan.md) | 假说、工作包、证据升级、结果图、失败分支与交付物 |
| [08 来源、数据与复现边界](docs/08_sources_data_and_reproducibility.md) | 证据台账、数据可及性、固定版本、尚未完成事项 |
| [代码使用说明](code/README.md) | 可执行的来源汇总、ROI、空间采样、供体级因子对比、测试与原始代码获取 |

## 3. 阅读前必须记住的五个限定

1. 混合实验是**起始 5% 对照细胞**，终点约 17%；不能写成“终点只有 5% 即解释全部效应”。
2. 原 BMDM 比较包含 **PDAC 条件培养基**；ARG1/PD-L1 的关键读数为流式 MFI，不能改写成“无条件培养背景下 fibrin 单独引起转录上调”。
3. Fig. 5l 是 ROI 组成—CD8 关系；公开 `ROI_TME_mixing.ipynb` 提供 ROI 表构建，但未提供该关系的完整拟合步骤。不能把我们提出的模型当成作者模型。
4. 该 notebook 的 `Serpine1` 是 **KO 标签**；`F8` 是本实验中 serpin 功能完整的对照。不是 SERPINE1 高低表达分组。
5. 局部相关、非细胞自主作用、非线性响应、严格的机制中介，是四个不同命题。

前两项与混合实验及 BMDM 证据见[原文 Fig. 4–5 与 Methods](https://www.nature.com/articles/s41586-026-11002-8)；代码限定见[固定版本 ROI notebook](https://github.com/BDBrownLab/Falcomata_PDAC_2026/blob/da2fcf70b89c911728cdcd519e72a153f17e743b/Perturb-map/CyCIF_mixing/ROI_TME_mixing.ipynb)。

## 4. 如何快速开始运行

在本目录内：

```bash
python -m pip install -r code/requirements.txt
python -m unittest discover -s code -p 'test_*.py' -v
python code/demo.py --out demo_output
```

`demo_output` 只用于理解输入、输出和程序行为，**不能作为论文结果或机制验证**。本次实际测试记录见 [validation.json](provenance/validation.json)。

获取作者固定版本代码，而不是无记录地下载最新主分支：

```bash
python code/fetch_original_code.py --out original_code
```

该脚本校验 Git blob SHA，保存原始 notebook，并生成带 cell 编号的源码阅读副本；它不自动运行作者 notebook，也不下载患者数据。

## 5. 来源和贡献边界

本次专属仓库审读固定在：

```text
BDBrownLab/Falcomata_PDAC_2026
commit: da2fcf70b89c911728cdcd519e72a153f17e743b
```

旧版基础方法仓库 `srose89/Perturb-map` 只作为方法来源，不能替代本篇 PDAC 的实验配置。作者代码为 MIT，保留 [Brown Lab 版权与许可](provenance/LICENSE_BrownLab.txt)。本目录的示意结构、方法评论、研究方案与教学实现不是作者原始产物；未转载论文原图、未重新许可整篇论文或整个 idea 仓库。

**一句话结论：用局部暴露替代全局均值，用材料实测补充转录标签，用邻居响应扩展细胞自身的筛选终点。**
