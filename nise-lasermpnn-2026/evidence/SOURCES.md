# 来源、版本与引用范围

[返回目录](../README.md)

整理日期：2026-09-11。以下只使用论文与作者/软件项目的原始来源。正文的章节、图与函数名称用于定位；未取得的附件不冒充已读。

## S1｜正式论文

Fry, B., Slaw, K. & Polizzi, N. F. *Zero-shot design of drug-binding proteins via neural iterative selection–expansion*. Nature 656, 237–249 (2026). 正式发表：2026-06-24。

- [DOI / 原文](https://doi.org/10.1038/s41586-026-10670-w)
- [Nature 页面](https://www.nature.com/articles/s41586-026-10670-w)
- [PubMed PMID 42343133](https://pubmed.ncbi.nlm.nih.gov/42343133/)
- [PMC13441969](https://pmc.ncbi.nlm.nih.gov/articles/PMC13441969/)
- [Supplementary Information 入口](https://www.nature.com/articles/s41586-026-10670-w#MOESM1)
- [Reporting Summary 入口](https://www.nature.com/articles/s41586-026-10670-w#MOESM2)

使用范围：公开索引中的正文、主图/扩展图注、Data/Code availability。直接页面访问遇到重定向/浏览器检查；完整 PDF、SI、原始图像及原始曲线未取得。正文主要定位为 NISE sampling algorithm、Exatecan design objective、Design/Characterization of exatecan binders、Neural proofreading、Fig. 5、apixaban 设计/表征与 Discussion。

原论文标注 CC BY 4.0。此目录为原创中文重述与分析，未复制全文或原图；引用和衍生数学均保留归属。论文许可不等于第三方软件、数据或模型权重均采用相同许可。

## S2｜NISE 固定公开实现

[仓库](https://github.com/polizzilab/NISE)；固定 commit：`61b7500e99ab37295ae9510b3db05aefe6a5fdfb`。

- [核心实现 run_nise_boltz2x.py](https://github.com/polizzilab/NISE/blob/61b7500e99ab37295ae9510b3db05aefe6a5fdfb/run_nise_boltz2x.py)
- [安装脚本 setup.py](https://github.com/polizzilab/NISE/blob/61b7500e99ab37295ae9510b3db05aefe6a5fdfb/setup.py)
- [对称性感知 RMSD 工具](https://github.com/polizzilab/NISE/blob/61b7500e99ab37295ae9510b3db05aefe6a5fdfb/utility_scripts/calc_symmetry_aware_rmsd.py)
- [NISE notebook](https://github.com/polizzilab/NISE/blob/61b7500e99ab37295ae9510b3db05aefe6a5fdfb/NISE_LASErMPNN.ipynb)

已读范围以主实现选段、安装脚本和 CLI 为主；工具和 notebook 链接提供继续定位，不表示本次逐行执行过。该 commit 晚于正式发表，因此仅作公开实现版本，不强称论文历史版本。

## S3｜LASErMPNN 子模块

NISE 所引用子模块 commit：`d7b6d2878391f91865fde524c941f661e84050f3`。

- [README 与质子化提醒](https://github.com/polizzilab/LASErMPNN/blob/d7b6d2878391f91865fde524c941f661e84050f3/README.md)
- [单次推理](https://github.com/polizzilab/LASErMPNN/blob/d7b6d2878391f91865fde524c941f661e84050f3/run_inference.py)
- [批量推理](https://github.com/polizzilab/LASErMPNN/blob/d7b6d2878391f91865fde524c941f661e84050f3/run_batch_inference.py)
- [官方 Colab 入口](https://colab.research.google.com/github/polizzilab/LASErMPNN/blob/main/run_lasermpnn.ipynb)

Colab 的 main 链接会变化，执行时另记录实际 commit 和权重哈希。此前仅解析到另一个 main commit `e70f2c6d765416f7e29d51bfd6d4e08496438878`，本 idea 不用它替换 NISE 子模块，也不宣称它永远是最新版本。

## S4｜proofreading

[run_proofreading.py，固定子模块版本](https://github.com/polizzilab/LASErMPNN/blob/d7b6d2878391f91865fde524c941f661e84050f3/run_proofreading.py)。重点函数：`get_forward_pass_probabilities`、`compute_unconditional_probs`、`compute_conditional_probs`。已读选段显示逐位点解除固定、解码顺序与 dropout 重复的概率汇总；不据此反推全部 Fig. 4 历史参数。

## S5｜CLI

[run_nise_boltz2x_cli.py，固定 NISE 版本](https://github.com/polizzilab/NISE/blob/61b7500e99ab37295ae9510b3db05aefe6a5fdfb/run_nise_boltz2x_cli.py)。本次重新读取参数构建前 230 行，核对输入、输出、采样、RMSD、模型权重等实际选项。文中命令只使用已核对参数，不声称执行成功。

## S6｜完整 apixaban campaign 的公开索引

[example_design_campaign/README.md](https://github.com/polizzilab/NISE/blob/61b7500e99ab37295ae9510b3db05aefe6a5fdfb/example_design_campaign/README.md)。索引指出 `all_apex_design_scripts.zip` 内包含 docking、NISE 与最终筛选，并明确部分脚本依赖实验室特定基础设施。本次未取得并执行该二进制 ZIP，不据 README 填造其全部参数。

## S7｜CARPdock

[仓库](https://github.com/benf549/CARPdock)；已解析 commit：`9e11474052a0934444acfb5392e56b67f1a12c58`。本次只沿用明确版本与用途定位，不声称逐行审计了 docking 核心。

## S8｜设计与分析档案

[Zenodo DOI 10.5281/zenodo.18308430](https://doi.org/10.5281/zenodo.18308430)。来自正式论文 Code availability；本次未获取完整文件清单与 payload。因此它是必要输入入口，而不是已取得的实验数据。

## S9｜训练数据

[SPICE 2.0.1，Zenodo 10975225](https://doi.org/10.5281/zenodo.10975225)；[LASErMPNN 处理数据入口，Zenodo 17990180](https://doi.org/10.5281/zenodo.17990180)。后者标题涉及 Chunk 1/2，不能将一个入口说成全部训练数据已齐备。未下载训练数据、未核对完整 split、未训练模型。

## S10｜结构与配体参考

[PDB 9NZE](https://doi.org/10.2210/pdb9NZE/pdb)、[9NZG](https://doi.org/10.2210/pdb9NZG/pdb)、[6W70](https://doi.org/10.2210/pdb6W70/pdb)。其他论文引用结构包括 4JNJ、4L9K、8TN6；exatecan 构象来源关联 CSD 1504071。当前只核对文中的结构身份和用途，不把结构编号当作已做比对/密度验证。

## 本项目推导与代码

Kabsch 坐标检验、质量守恒推导、局部概率对比、突变循环算术、Wilson 描述区间以及拟议研究设计属于此目录的解释/实现。它们不得写成作者新报告的实验结果。实际测试范围和版本见 [verification](../checks/verification.md)。
