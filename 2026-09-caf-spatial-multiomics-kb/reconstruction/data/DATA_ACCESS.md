# 数据来源状态与取数计划

目标研究使用公开平台数据及作者生成数据。以下只记录已在论文中找到的来源线索，不声称已经下载。

| 路线 | 已知入口 | 需要核对 | 本次状态 |
|---|---|---|---|
| CosMx | 论文关联公开数据，参考 TableS1 | 具体样本ID、980面板文件、细胞表、FOV全局坐标 | 索引级；未取得原始数据 |
| MERSCOPE | 论文关联公开数据，参考 TableS1 | 具体样本ID、500面板、cell_by_gene / metadata /边界 | 索引级；未取得原始数据 |
| Xenium | 原文5K验证数据及TableS1 | 五张切片ID、panel精确版本、细胞及转录本文件 | 索引级；不猜 vendor 样本URL |
| LUAD Visium | GSE246011 | 对应本论文切片、矩阵、图像、scRNA参考 | accession 在原文可见；GEO直接访问受阻 |
| PDAC Visium | GSE274103 | 纳入切片、图像、探针清单、counts | accession 在原文可见；GEO直接访问受阻 |
| COMET | 本研究作者数据 | 原始/处理后蛋白图像、细胞/ROI表、抗体验证 | 未取得；TableS7仅索引 |
| CODEX | 原始研究公共资料，TableS1 | 70核心与35患者映射、标签、临床终点 | 未取得对象 |
| IMC | 原始研究公共资料，TableS1 | 两种样本计数的关系、临床子集、cell表/分型 | 存文字计数差异，未取得筛选表 |

GEO accession 不是文件级 manifest。不能因为论文写了公开数据，就把文件大小、下载路径、hash、样本单位或可直接复现状态补齐。

建议按 `sample_manifest_template.tsv` 建立一行一个最小物理观测单元的表，并保留父级患者/标本/切片。入库前校验压缩包与单文件 SHA256；逐样本记录测量、面板、分割、QC及排除规则。

`cell_feature_matrix.h5`、`cells.parquet`、`cell_boundaries.parquet`、`transcripts.parquet` 是论文描述的 Xenium 文件类型线索；本包没有这些文件。未根据文件名推断其行序或细胞标识一致性。
