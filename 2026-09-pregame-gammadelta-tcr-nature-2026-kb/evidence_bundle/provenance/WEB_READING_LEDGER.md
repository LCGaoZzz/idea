# 在线阅读凭证与本地捕获边界

本文件是本次阅读定位清单，而不是出版方原始字节归档。下载失败没有用生成的内容伪装成原文。

|来源|实际读取范围/定位|状态|
|---|---|---|
|PAPER https://www.nature.com/articles/s41586-026-11055-9 |正文 Results；Methods 全部相关生信与实验模块；Fig.1–6；ED Fig.1–9 captions；Data/Code availability|浏览工具全文文本可读；原始 HTML/PDF 未保存|
|REVIEW https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-026-11055-9/MediaObjects/41586_2026_11055_MOESM3_ESM.pdf|88页；重点PDF第68–71页；Revisions Fig.3.7–3.10；第69页已目视核验|PDF文本可读；部分截图可读；原始文件未保存|
|TABLES https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-026-11055-9/MediaObjects/41586_2026_11055_MOESM1_ESM.pdf|S1患者；S2 sgRNA；S3 CDR3；S4序列/细胞数量，PDF第5页|解析文本可读；表页截图失败；人工转录需二次对照|
|REPORTING https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-026-11055-9/MediaObjects/41586_2026_11055_MOESM2_ESM.pdf|PDF第1–3页截图；软件、设计、缺失、排除、盲法|截图可读；原始文件未保存|
|FIG3 https://www.nature.com/articles/s41586-026-11055-9/figures/3|模型、验证、max-per-clonotype图注|图注可读；图像下载失败|
|ED6 https://www.nature.com/articles/s41586-026-11055-9/figures/12|特征、失败构建的替补、跨癌种图注|图注可读；完整特征标签像素未取得|
|EGA-ALQ https://ega-archive.org/studies/EGAS50000001889|EGAD50000002742：25 samples；EGAD50000002743：141 samples|官方元数据已读取；原始数据未取得|
|EGA-PG https://ega-archive.org/studies/EGAS50000001888|EGAD50000002744：20 samples；EGAD50000002745：11 samples|官方元数据已读取；不能把EGA sample字段直接等同患者|
|ZENODO https://doi.org/10.5281/zenodo.20028241|DOI、record与API多路径|本会话获取失败|
|LEGACY https://github.com/bigmaklab/TCRmodel|由审稿文件得到的旧仓库；GitHub连接器GET仓库|404；没有据此判断最终Zenodo记录状态|
|SEURAT https://satijalab.org/seurat/archive/v4.3/de_vignette|版本对应文档的p_val_adj含义|Bonferroni；不能代替作者调用核查|
|VEGAN https://vegandevs.github.io/vegan/reference/vegdist.html|horn输出是dissimilarity|只用于指出是否做1-d需要核查|
|SKLEARN https://scikit-learn.org/0.24/common_pitfalls.html|监督特征选择必须限制训练集|方法学解释，不当作作者实现|

## 关键精确定位

PAPER Methods: `Acquisition of patient samples`（ALQ-19-019缺失baseline）；`Alignment of raw γδ TCR sequencing data`（三套对齐与键定义）；`Quality control, normalization and single-cell clustering`；`PreGame development`（split前特征选择）；`Differential expression analysis of TR γδ T cells`（1000迭代）；Fig.4e caption（100迭代）。

REVIEW：PDF第69页，页脚60，Revisions Fig.3.7：group-held-out AUC 0.7229，CI 0.6588–0.7826，AUPR 0.4407，CI 0.3407–0.5540，F1 0.4722，threshold 0.5，2000 bootstrap。PDF第70页/页脚61：Revisions Fig.3.8、3.9；PDF第71页/页脚62：global feature selection和no-SMOTE回复。页码指PDF物理页；此处PDF69/70/71页分别对应回复页脚60/61/62，其他审稿轮次不能套用固定偏移。

本次浏览工具行号（帮助当前会话追溯，不是永久出版定位）：PAPER 110–236、238–396、850–917；REVIEW 1949–2035；TABLES 149–175；EGA-ALQ 83–97；EGA-PG 83–98。
