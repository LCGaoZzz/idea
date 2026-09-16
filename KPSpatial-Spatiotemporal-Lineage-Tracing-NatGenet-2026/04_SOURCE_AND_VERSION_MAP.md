# 04｜Source & Version Map

## 论文

- Jones, Sun et al. **Spatiotemporal lineage tracing reveals the dynamic spatial architecture of tumour growth and metastasis.** Nature Genetics, 2026.
- DOI: `10.1038/s41588-026-02739-z`

## 公开代码

- KPSpatial-release: `https://github.com/mattjones315/KPSpatial-release`
- 本次固定提交：`c2fa7568ee48a9e35bbc6ecd88378c6768b23e00`
- Cassiopeia: `https://github.com/YosefLab/Cassiopeia`
- 本次审读固定提交：`1ee5959eb9d3f8d4d26e2af5678234493bf54d6d`

## 论文提供的归档信息

- Reproducibility code Zenodo：论文 Code availability 指向 `10.5281/zenodo.21263890`。
- 公开 README 还引用 processed datasets：`10.5281/zenodo.19771805`。

## 核心代码定位

KPSpatial-release：

- `utilities/reconstruct.py`：character matrix、tree solver 入口、空间插补调用；
- `utilities/target_site_utilities.py`：缺失字符空间投票插补；
- `utilities/phylodynamics.py`：tree fitness 包装；
- `reproducibility/Figure1/scripts/bootstrap_phylo_infercnv_slidetags.py`：CNV/谱系最近邻纯度和 permutation；
- `reproducibility/Figure1/scripts/evaluate_imputation_accuracy_semisynthetic.py`：半合成缺失值插补评估；
- `reproducibility/Figure2/scripts/score_consensus_hotspot.py`：共识 Hotspot 模块打分；
- `reproducibility/Figure3/scripts/score_neighborhood_abundances.py`：空间 neighborhood composition；
- `reproducibility/Figure3/scripts/slidetags_fitness.py`：Slide-tags fitness 调用；
- `reproducibility/Figure4/ligand_receptor_analysis.ipynb`：局部 ligand-receptor 分析；
- `reproducibility/Figure5/map_metastasis.ipynb`：转移相关原发区域映射。

## 数据/元数据中已核对的局部事实

公开 `data/puck_meta.txt` 包含 44 个 Slide-seq 阵列和 5 个 Slide-tags 阵列；5 个 Slide-tags 阵列均标记为 Mouse `SPC-11`。

## 证据等级约定

- **P**：论文/补充材料明确报告；
- **C**：固定提交代码直接可见；
- **E**：本次实际执行得到；
- **I**：基于 P/C/E 的解释；
- **H**：迁移建议或新假说。

在后续 Agent 使用本知识库时，严禁把 H/I 自动改写为论文事实。
