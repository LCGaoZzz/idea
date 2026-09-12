# 来源索引与获取边界

[返回目录](../README.md)

## 一、原始论文

P：[Mo et al., Nature 2024](https://www.nature.com/articles/s41586-024-08087-4)，DOI 10.1038/s41586-024-08087-4。在线发表2024-10-30。正文、Methods、主图及Extended Data图注可通过网页核对。本轮图相关叙述主要按正文/图注，不声明对每张原始高分辨率图像做了独立量化。

固定图入口：[Fig.1](https://www.nature.com/articles/s41586-024-08087-4/figures/1)｜[Fig.2](https://www.nature.com/articles/s41586-024-08087-4/figures/2)｜[Fig.3](https://www.nature.com/articles/s41586-024-08087-4/figures/3)｜[Fig.4](https://www.nature.com/articles/s41586-024-08087-4/figures/4)｜[Fig.5](https://www.nature.com/articles/s41586-024-08087-4/figures/5)。

Methods小节名是本文主要方法定位，尤其包括：

| 方法组 | 原文小节 |
|---|---|
| 测量与处理 | Specimens and sample processing; ST preparation and sequencing; ST data processing |
| DNA遗传 | WES data processing; Mutation calling using WES; CNV calling using WES |
| RNA遗传 | InferCNV and CalicoST for CNV calling on Visium ST data; Mutation mapping to snRNA-seq and ST data; Spatial mutation VAF statistical test |
| 克隆识别 | Copy number profile similarity score calculation; Spatial subclone identification based on CNV profile similarity |
| 区域/深度 | Tumour microregion annotation and layer determination; Average spot area and microregion size calculation; Spot-depth correlation analysis |
| 表达来源 | Organ-specific gene blacklist for non-malignant cell types; Tumour intrinsic and non-tumour gene categorization; Spatial expression deconvolution |
| 状态 | Microregion transcriptional profile analysis; Module score calculation; Spot-depth GSEA pathway enrichment analysis |
| TME与药物 | ST cell-type decomposition; Spatial cell–cell interaction at tumour boundary; Spatial subclone-specific treatment response analysis |
| 三维 | Serial section alignment and branching factor calculation; Registration of Visium, CODEX and H&E serial sections |
| Mushroom | Neighbourhood identification input preprocessing; Neighbourhood identification model architecture; Model loss function; Model training and inference; 3D neighbourhood construction and integration; Analysis and quantification of 3D neighbourhoods |
| 成像与原位 | Cell-type annotation of CODEX imaging data; Distance to tumour boundary quantification on CODEX; 3D tumour volume reconstruction and location quantification; Xenium probe design |

补充入口在[原文Supplementary information](https://www.nature.com/articles/s41586-024-08087-4#MOESM1)：Supplementary Figures 1–11、Reporting Summary及Tables 1–6。本轮点击获取PDF、Table 4和主PDF失败；不声称已完整读取补充内容。正文引用补充图时，本文只转述正文明确写出的结果并注明此范围。

## 二、公开代码：固定提交而非漂移分支

C1：[ST_subclone_publication](https://github.com/ding-lab/ST_subclone_publication/tree/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa)。主要审读文件：Figure2/1_inferCNV_run.R、Figure2/2_CalicoST_run.md、Figure2/3_CNV_jaccard_similarity.R、Figure3/4_Layer/2_layer_DEG_correlation.R、Figure3/4_Layer/3_layer_DEG_pathway_analysis.R、Figure4/1_RCTD_devolution.R、Figure4/4_border_DEG.R、Figure4/5_CCI_COMMOT.py；其余在正文标为路径或README定位。

C2：[Mushroom subclone-resubmission固定快照](https://github.com/ding-lab/mushroom/tree/fde4dd8c91636629b1acab4473e1773468dcc1d8)。已读：README、[mushroom.py配置段](https://github.com/ding-lab/mushroom/blob/fde4dd8c91636629b1acab4473e1773468dcc1d8/mushroom/mushroom.py#L29-L74)、[训练notebook](https://github.com/ding-lab/mushroom/blob/fde4dd8c91636629b1acab4473e1773468dcc1d8/notebooks/manuscript/submission_v1/step3_train_mushroom_cancer_v2.ipynb)。[step7邻域分析notebook](https://github.com/ding-lab/mushroom/blob/fde4dd8c91636629b1acab4473e1773468dcc1d8/notebooks/projects/subclone_paper/step7_figure6_revisions_v2.ipynb)由README定位，未声称本轮通读。正文Methods和主仓库旧README还提及subclone_submission；本目录优先保留Code availability指定的resubmission快照，但未验证两分支是否等同。

C3：[multiplex-imaging-pipeline](https://github.com/estorrs/multiplex-imaging-pipeline/tree/c351da1d41e284eef2f732b3553e5602438ed978)。已读README及[segmentation.py](https://github.com/estorrs/multiplex-imaging-pipeline/blob/c351da1d41e284eef2f732b3553e5602438ed978/multiplex_imaging_pipeline/segmentation.py)。该快照晚于原论文，不用当前默认替代原实验通道。

C4：[Morph已审README快照](https://github.com/ding-lab/morph/tree/ba1db03976a72f0da0558e87207054ef9404309b)。另查到的发表日期前默认历史候选：[c284634](https://github.com/ding-lab/morph/tree/c284634abdeebc567c39a6367515d8decbf13af3)，其中operators.py为薄包装。它不代表所有历史分支，不是确认过的原论文运行版。

## 三、文档与运行证据

本次使用同一会话中此前生成的Mo2024报告作为待核对草稿，不把该草稿作为原论文事实的独立来源；重要结论重新对照论文和上述代码。用户指定的reconstruct-bioinfo-protocol-pr630-4bdc4d0.zip提供证据分层与审读组织参考，不代表该工具已对原研究完成执行复现。

本目录只附9项独立合成检查及其执行结果，不声称通过原技能的全流程患者数据复现验证。输入/输出、原文事实、代码事实、解释和建议在文档及表格中分开保存。

## 四、获取失败与未获取

2026-09-12通过网页工具获取正文/Methods，通过GitHub连接器获取指定文本与目录。容器直接HTTP获取Nature页面、主仓库压缩包及Mushroom完整tree时DNS失败；额外下载尝试也未成功。没有完整本地源码快照、全部原图、补充表格或患者输入。不将文本获取、文件哈希或GitHub提交当作科学算法运行。

## 五、引用与源码分发边界

正文为独立研究分析，不复制原文全文或整套图。作者代码通过固定permalink访问；本目录独立脚本不冒充作者实现。未取得完整源文件许可上下文时，不重新打包作者全部代码。用户项目仅记录本次明确提供的设计背景，不添加个体、样本或实验结果。
