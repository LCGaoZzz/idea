# 来源与定位索引

本表为阅读来源目录；严格原工作流的可执行证据状态另见 `source_inventory.json`。在线读到不等于取得本地完整原件。代码片段的本地行号不是原文件行号。

## P1｜终刊公开页面

摘要、主图标题、ED1–ED10图注、数据/代码可用性；非完整Results/Main Methods；无本地PDF

[打开固定来源](https://www.nature.com/articles/s41588-026-02739-z)

## P2｜Supplementary Information (23页)

在线方法/讨论阅读；PDF17与21页截图已核对；完整PDF未下载

[打开固定来源](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41588-026-02739-z/MediaObjects/41588_2026_2739_MOESM1_ESM.pdf)

定位：PDF pp.1–23; pp.17,21 image checked。

## P3｜Reporting Summary (7页)

在线文本；第3页Hotspot流程；第3页最新截图失败，未伪称全部页面图像可读

[打开固定来源](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41588-026-02739-z/MediaObjects/41588_2026_2739_MOESM2_ESM.pdf)

定位：PDF pp.1–7; p.3 community detection/scoring。

## R1｜KPSpatial-release 固定提交

读取目录及部分源代码/选定notebook；不是完整checkout或全部notebook审计

[打开固定来源](https://github.com/mattjones315/KPSpatial-release/tree/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00)

提交：`c2fa7568ee48a9e35bbc6ecd88378c6768b23e00`。

## R2｜Cassiopeia 固定提交

当前可见提交；重点追踪fitness输出；不等同于终刊依赖冻结

[打开固定来源](https://github.com/YosefLab/Cassiopeia/tree/1ee5959eb9d3f8d4d26e2af5678234493bf54d6d)

提交：`1ee5959eb9d3f8d4d26e2af5678234493bf54d6d`。

## R0｜用户Library中的既往同题准备包

2026-09-11同题包；用于继承来源/参数登记及十项检查，非本次独立科学结果

## W0｜用户指定protocol重建工作流

reconstruct-bioinfo-protocol-pr630-4bdc4d0.zip；读取技能与证据合同，并使用安全检查/验证/打包脚本

## C1｜Fitness工具

score_fitness / _fitness_wrapper；本地为非连续选段

[打开固定来源](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/utilities/phylodynamics.py)

本地：`evidence/phylodynamics_excerpt.txt`。
定位：score_fitness / _fitness_wrapper；本地为非连续选段。
提交：`c2fa7568ee48a9e35bbc6ecd88378c6768b23e00`。

## C2｜字符矩阵与树入口

create_character_matrix；原窗口L365–L560；本地为选段

[打开固定来源](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/utilities/reconstruct.py)

本地：`evidence/reconstruct_excerpt.txt`。
定位：create_character_matrix；原窗口L365–L560；本地为选段。
提交：`c2fa7568ee48a9e35bbc6ecd88378c6768b23e00`。

## C3｜插补辅助函数

impute_single_state；本地为选段

[打开固定来源](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/utilities/target_site_utilities.py)

本地：`evidence/target_site_excerpt.txt`。
定位：impute_single_state；本地为选段。
提交：`c2fa7568ee48a9e35bbc6ecd88378c6768b23e00`。

## C4｜Figure3 fitness活动调用

继承旧包的固定提交选段；无本次真实执行日志

[打开固定来源](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/reproducibility/Figure3/scripts/slidetags_fitness.py)

本地：`evidence/fitness_entrypoint_excerpt.txt`。
定位：继承旧包的固定提交选段；无本次真实执行日志。
提交：`c2fa7568ee48a9e35bbc6ecd88378c6768b23e00`。

## C5｜Figure3邻域脚本

继承旧包的固定提交选段；RADIUS/读表/图构造

[打开固定来源](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/reproducibility/Figure3/scripts/score_neighborhood_abundances.py)

本地：`evidence/neighborhood_excerpt.txt`。
定位：继承旧包的固定提交选段；RADIUS/读表/图构造。
提交：`c2fa7568ee48a9e35bbc6ecd88378c6768b23e00`。

## C6｜共识社区打分

当前重新读取全脚本；本地仅保存选段

[打开固定来源](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/reproducibility/Figure2/scripts/score_consensus_hotspot.py)

本地：`evidence/community_scoring_excerpt.txt`。
定位：当前重新读取全脚本；本地仅保存选段。
提交：`c2fa7568ee48a9e35bbc6ecd88378c6768b23e00`。

## C7｜通用DE入口

继承旧包选段；默认不等于活动调用

[打开固定来源](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/utilities/differential_expression.py)

本地：`evidence/de_excerpt.txt`。
定位：继承旧包选段；默认不等于活动调用。
提交：`c2fa7568ee48a9e35bbc6ecd88378c6768b23e00`。

## C8｜CNV近邻纯度置换脚本

完整4730字节；AST抽取5个函数执行合成测试

[打开固定来源](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/reproducibility/Figure1/scripts/bootstrap_phylo_infercnv_slidetags.py)

本地：`evidence/code/bootstrap_phylo_infercnv_slidetags.py`。
定位：完整4730字节；AST抽取5个函数执行合成测试。
提交：`c2fa7568ee48a9e35bbc6ecd88378c6768b23e00`。

## C9｜Cassiopeia LBIJungle 导出层

在线读取完整包装器；本地为L114–124选段，非完整Git blob

[打开固定来源](https://github.com/YosefLab/Cassiopeia/blob/1ee5959eb9d3f8d4d26e2af5678234493bf54d6d/cassiopeia/tools/fitness_estimator/_lbi_jungle.py)

本地：`evidence/code/cassiopeia_lbi_export_excerpt.py.txt`。
定位：estimate_fitness, upstream L114–124。
提交：`1ee5959eb9d3f8d4d26e2af5678234493bf54d6d`。

## C10｜Vendored Jungle中间调用层

在线读取Tree.infer_fitness；仅另存本次解释笔记，不冒充源码捕获

[打开固定来源](https://github.com/YosefLab/Cassiopeia/blob/1ee5959eb9d3f8d4d26e2af5678234493bf54d6d/cassiopeia/tools/fitness_estimator/_jungle/jungle/tree.py)

定位：Tree.infer_fitness。
提交：`1ee5959eb9d3f8d4d26e2af5678234493bf54d6d`。

## C11｜FitnessInference变量分派

在线读取L1–270；本地为compute_rankings选段

[打开固定来源](https://github.com/YosefLab/Cassiopeia/blob/1ee5959eb9d3f8d4d26e2af5678234493bf54d6d/cassiopeia/tools/fitness_estimator/_jungle/jungle/resources/FitnessInference/prediction_src/node_ranking.py)

本地：`evidence/code/cassiopeia_ranking_excerpt.py.txt`。
定位：node_ranking.compute_rankings。
提交：`1ee5959eb9d3f8d4d26e2af5678234493bf54d6d`。

## D1｜阵列元数据

完整文件；字节身份校验成功

[打开固定来源](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/data/puck_meta.txt)

本地：`evidence/puck_meta.txt`。
定位：header and all 49 rows。
提交：`c2fa7568ee48a9e35bbc6ecd88378c6768b23e00`。

## D2｜公开CNV近邻纯度结果表

完整文件；只重数，没有重做原始分析

[打开固定来源](https://github.com/mattjones315/KPSpatial-release/blob/c2fa7568ee48a9e35bbc6ecd88378c6768b23e00/reproducibility/Figure1/data/slidetags_infercnv_nn_score.tsv)

本地：`evidence/tables/slidetags_infercnv_nn_score.tsv`。
定位：header and all 15 rows。
提交：`c2fa7568ee48a9e35bbc6ecd88378c6768b23e00`。

## Z1｜处理后数据公开记录

读取记录/文件大小/声明MD5；6.1 GB数据文件未下载

[打开固定来源](https://zenodo.org/records/19771805)

## Z2｜代码公开记录

读取记录；152.6 MB ZIP未下载；与用户21263890概念/版本关系未确证

[打开固定来源](https://zenodo.org/records/21263891)

## Z0｜文章提供的代码DOI

访问未得到可用关系元数据；不自动等同Z2

[打开固定来源](https://doi.org/10.5281/zenodo.21263890)

## B1｜Hotspot原始方法

DeTomaso & Yosef; Cell Systems 2021; DOI10.1016/j.cels.2021.04.005；背景，不补写作者未见参数

[打开固定来源](https://pubmed.ncbi.nlm.nih.gov/33951459/)

## B2｜从谱系形状推断fitness的原始研究

Neher et al. 2014; DOI10.7554/eLife.03568；区分背景定义与本次实际导出

[打开固定来源](https://elifesciences.org/articles/03568)

## B3｜随机置换P值原始统计论文

Phipson & Smyth 2010; DOI10.2202/1544-6115.1585；Monte Carlo +1与完整枚举不同

[打开固定来源](https://pubmed.ncbi.nlm.nih.gov/21044043/)

## T1｜本次新增22项审计收据

合成函数执行、数据表重数、身份/回归；不是论文重现

本地：`audit/deep_audit_results.json`。

## T2｜继承10项检查的本次重跑

记录原检查重跑，不声称10个新发现

本地：`audit/inherited_checks_rerun.json`。

## L1｜Cassiopeia MIT License

源许可证完整保存；KPSpatial LICENSE路径返回404，论文声明其代码MIT

[打开固定来源](https://github.com/YosefLab/Cassiopeia/blob/1ee5959eb9d3f8d4d26e2af5678234493bf54d6d/LICENSE)

本地：`evidence/Cassiopeia_LICENSE.txt`。
定位：LICENSE。
提交：`1ee5959eb9d3f8d4d26e2af5678234493bf54d6d`。
