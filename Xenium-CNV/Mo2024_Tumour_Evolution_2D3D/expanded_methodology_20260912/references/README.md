# 来源、固定代码版本与读取范围

[总目录](../README.md)

## P｜原始论文

Mo, C.-K., Liu, J., Chen, S. et al. **Tumour evolution and microenvironment interactions in 2D and 3D space.** *Nature* 634, 1178–1186 (2024). 在线发表：2024-10-30。DOI [10.1038/s41586-024-08087-4](https://doi.org/10.1038/s41586-024-08087-4)。[期刊全文与Methods](https://www.nature.com/articles/s41586-024-08087-4)；[PubMed PMID 39478210](https://pubmed.ncbi.nlm.nih.gov/39478210/)。

本轮阅读：论文HTML、Methods与图注；未重新完成所有图的高清视觉审计。此前对话曾检查主图预览，但不据此宣称逐像素或逐数值复核。扩展图的证据主要来自原文与图注。Supplementary Information PDF与关键xlsx本轮访问失败，不能视为已读。

### 按论证用途定位

| 主题 | 原文定位 |
|---|---|
| 队列与空间单元 | Fig.1；Spatial microregions across cancers；Tumour microregion annotation and layer determination |
| 区域面积 | Average spot area and microregion size calculation |
| 遗传证据 | Fig.2；InferCNV and CalicoST for CNV calling on Visium ST data |
| 克隆公式/分组 | Copy number profile similarity score calculation；Spatial subclone identification based on CNV profile similarity |
| 变异定位 | Fig.2h–j；Mutation mapping to snRNA-seq and ST data；Spatial mutation VAF statistical test；Xenium probe design |
| 转录状态与来源 | Extended Data Fig.6–8；Microregion transcriptional profile analysis；Organ-specific gene blacklist for non-malignant cell types；Tumour intrinsic and non-tumour gene categorization |
| 深度与通路 | Spot-depth correlation analysis；Spot-depth GSEA pathway enrichment analysis |
| 界面与通信 | Fig.3；Cellular composition deconvolution；Gene expression at the tumour boundary；Spatial cell–cell interaction at tumour boundary |
| 三维连接 | Fig.4；Serial section alignment and branching factor calculation |
| Mushroom | Fig.5；Registration；Neighbourhood identification；Model architecture；Model loss function；3D neighbourhood construction and integration |
| 成像与表达分配 | Cell-type annotation of CODEX imaging data；Spatial expression deconvolution |
| 药物候选边界 | Spatial subclone-specific treatment response analysis |

补充材料入口来自期刊页面：Supplementary Information包含补充图；Table1为样本/临床信息，Table4为模型超参数，Table5与非恶性黑名单相关，Table6为Xenium面板。这里只记录索引与缺口，不补写未取得的表内容。

## C｜固定代码索引

每个链接冻结到commit；发表后快照不是已证明的论文运行版本。行号只在该文件快照内有效；notebook优先使用cell ID，避免把JSON行号理解为代码执行行。

| ID | 文件与固定链接 | 读取深度/定位 | 能支持什么 |
|---|---|---|---|
| C01 | [ST Figure2/1_inferCNV_run.R](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure2/1_inferCNV_run.R) | 完整文本；option_list、parse_args、infercnv::run | 默认覆盖与活动接线；不是实际argv |
| C02 | [ST Figure2/2_CalicoST_run.md](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure2/2_CalicoST_run.md) | 完整短文 | 工具指针，无本研究配置 |
| C03 | [ST Figure4/1_RCTD_devolution.R](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure4/1_RCTD_devolution.R) | 完整文本；Reference/create.RCTD/run.RCTD | multi模式、参考标签与过滤 |
| C04 | [ST Figure4/5_CCI_COMMOT.py](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure4/5_CCI_COMMOT.py) | 完整文本；OptionParser/spatial_communication/cache | 全基因对象、距离接口与缓存风险 |
| C05 | [ST Figure4/4_border_DEG.R](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure4/4_border_DEG.R#L64-L180) | 前225行及重点64–111行复读 | 多宽度、FindMarkers、输出覆盖/删除 |
| C06 | [ST Figure2/3_CNV_jaccard_similarity.R](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure2/3_CNV_jaccard_similarity.R#L68-L155) | 本轮扩展：辅助函数68–155、过滤/调用段、300行至EOF；完整请求曾截断，关键区间单独读取 | 三种相似度、WES过滤、末端jac_pred选择；未复原最终人工标签 |
| C07 | [ST Figure3/4_Layer/2_layer_DEG_correlation.R](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure3/4_Layer/2_layer_DEG_correlation.R#L79-L110) | 全文已读，79–110重点复核 | 端点归一化与预计算TSV；不证明上游偏相关实现 |
| C08 | [Mushroom README](https://github.com/ding-lab/mushroom/blob/fde4dd8c91636629b1acab4473e1773468dcc1d8/README.md) | 完整README | 两个论文notebook入口 |
| C09 | [Mushroom训练notebook](https://github.com/ding-lab/mushroom/blob/fde4dd8c91636629b1acab4473e1773468dcc1d8/notebooks/manuscript/submission_v1/step3_train_mushroom_cancer_v2.ipynb) | JSON1–530；cells f7768f25/462c6638/c98c5f6e | 空cases、外部配置、训练及体积流程定义 |
| C10 | [Mushroom mushroom.py](https://github.com/ding-lab/mushroom/blob/fde4dd8c91636629b1acab4473e1773468dcc1d8/mushroom/mushroom.py#L29-L150) | 前150行；DEFAULT_CONFIG、from_config | 库默认与配置覆盖结构 |
| C11a | [Morph历史operators.py](https://github.com/ding-lab/morph/blob/c284634abdeebc567c39a6367515d8decbf13af3/Morph/operators.py) | 全文及候选树 | 此默认分支历史候选仅有限封装 |
| C11b | [Morph新README](https://github.com/ding-lab/morph/blob/ba1db03976a72f0da0558e87207054ef9404309b/README.md) | README，不是全实现 | 后续Xenium示例，不倒推2024 |
| C12 | [multiplex segmentation.py](https://github.com/estorrs/multiplex-imaging-pipeline/blob/c351da1d41e284eef2f732b3553e5602438ed978/multiplex_imaging_pipeline/segmentation.py) | 完整文本；segment_cells/remove_labeled_edges/keep_first | Mesmer分块与标签合并；未执行 |
| C13 | [multiplex README](https://github.com/estorrs/multiplex-imaging-pipeline/blob/c351da1d41e284eef2f732b3553e5602438ed978/README.md) | 完整README | 当前安装与feature模式警告 |
| C14 | [ST README](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/README.md) | 完整README | 仓库旧图号结构与数据入口 |
| C15 | [ST Figure5/README.md](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure5/README.md) | README/目录，不是全部脚本 | 最终Fig.4的连接拓扑路线 |
| C16 | [ST Figure6/README.md](https://github.com/ding-lab/ST_subclone_publication/blob/7067cd16f06ec4aa2500aa1e5c9a6eb1e6e42cfa/Figure6/README.md) | 完整短文 | 旧分支指针，优先论文resubmission分支 |
| C17 | [Mushroom邻域notebook](https://github.com/ding-lab/mushroom/blob/fde4dd8c91636629b1acab4473e1773468dcc1d8/notebooks/projects/subclone_paper/step7_figure6_revisions_v2.ipynb) | 仅README定位，未完整读取 | 不能据路径补写所有最终面板实现 |
| C18 | [Mushroom model/sae.py](https://github.com/ding-lab/mushroom/blob/fde4dd8c91636629b1acab4473e1773468dcc1d8/mushroom/model/sae.py) | 本轮分段读1–245及240至EOF；_to_quantized/quantize/forward | 层级组合、softmax概率传入cross_entropy |

## D｜接口语义的官方参考

[R hclust](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/hclust.html)：Ward.D2对输入差异的处理及聚类语义。

[R dist/as.dist](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/dist.html)：矩阵转换使用下三角。

[PyTorch functional.cross_entropy](https://docs.pytorch.org/docs/2.14/generated/torch.nn.functional.cross_entropy.html) 与 [CrossEntropyLoss](https://docs.pytorch.org/docs/2.14/generated/torch.nn.CrossEntropyLoss.html)：输入logits与目标类别的接口含义。

这些是本次检索的官方文档，用于检查数学/接口语义。它们不是作者的版本锁文件或运行环境证据。

## 检索失败与范围限制

期刊页面部分干净链接曾进入授权跳转；带原用户查询参数的页面可读取HTML。Supplementary PDF、Table1和Table4下载请求失败；容器直接联网下载亦失败。使用GitHub连接器读取源码，而不是声称已经克隆四个完整仓库。

因未取得PDF，本轮没有PDF图像审阅；没有OCR补写正文；没有运行作者脚本。对失败入口保留“未取得”，不借其他文章或常规流程补全。

## 内容与版权

原文以出版社许可条款为准，页面标注CC BY-NC-ND 4.0。本目录只提供原创分析、必要的事实定位、代码链接和原创数学检查，不再分发或改绘原图，不复制论文全文。作者源码仍以各上游仓库许可和来源为准。
