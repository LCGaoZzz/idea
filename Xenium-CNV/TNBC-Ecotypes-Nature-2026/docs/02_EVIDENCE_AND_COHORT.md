# 02｜队列、图号、分母与证据路线

[返回](../README.md) · 【P】定位到[正式版正文及 Methods](https://www.nature.com/articles/s41586-026-10469-9)。以下规模来自原论文及此前重建材料，不是本项目重新计算的结果。

## 1. 一项研究并不存在一个贯穿所有分析的 N

| 层级 | 论文报告规模 | 正确用途与限制 |
|---|---:|---|
| 治疗前入组 | 108 位 | 临床设计范围，不能直接作为每个检验的 N |
| 已知应答 | pCR 50、RD 39 | 应答分支仍须排除缺少特定谱系／模态者 |
| 无对应 NAC 应答 | 19 位 | 中期反应不佳后治疗转轨；不是可自动填成 RD 的随机缺失 |
| QC 后 scRNA | 101 位、427,857 细胞 | 患者是临床重复，细胞是嵌套观察 |
| 癌细胞 | 97 位、49,275 细胞 | 癌细胞专属 pseudobulk 的起始范围 |
| Xenium | 44 位 | 靶向空间分析，不等于所有空间平台的合并集合 |

来源：Study design and TNBC cell types、Tumour archetypes and chemotherapy response、Fig. 1–2、Methods: Study participant details from the ARTEMIS Trial。

【I】病例中没有某谱系细胞，可能是未回收、低覆盖、取材不包含，也可能是确实缺少该谱系。在谱系内部计算状态比例时，这类病例的条件分母不存在。将其填为零，会把“不可估计”变成“测得阴性”，并改变所有相关和比较。

## 2. 分母待仲裁：39 与 46 不自行合并

【P】Study design 段写总体有 39 位拥有匹配的 scRNA 与空间数据；Tumour archetypes 段又写在 46 位具有匹配 scRNA 的患者中使用三种空间技术作验证。两段的对象是否经过不同 QC、是否平台并集或文稿版本不同，本次未取得患者级表来仲裁。

【I】这只能记为文本分母待核实，不能宣布其中一个必错，更不能改写成“46 位 Xenium 患者”。最低恢复材料是逐患者的 scRNA、Xenium、Visium、VisiumHD 可用性和分析纳入列。

## 3. 结局规则与目标总体

【P】入组定义包含 ER／PR 低表达范围，并非所有病例必然严格低于 1%。pCR 对应 RCB-0，RD 对应 RCB-I–III。19 位转向靶向治疗的病例可用于生物学分析，未进入应答组比较。来源：ARTEMIS Methods。

【I】需要区分三种目标：所有入组患者的基线生态；完成某治疗路径的患者中的应答关联；假如所有患者均接受固定处理时的潜在结局。现有观察不自动同时识别三者。无结局病例不能因为“中期不好”直接判定最终 RD，也不能用普通均值插补构造未经历治疗路径的结局。

## 4. pooled 比例不是平均患者比例

【I】两种常见汇总为：

$$p_{pool}=\frac{\sum_j n_{c,j}}{\sum_j n_{all,j}},\qquad p_{patient}=\frac1J\sum_j\frac{n_{c,j}}{n_{all,j}}.$$

前者按回收细胞数加权，后者等权患者。它们不同不构成数据错误；但检验与可视化必须说明使用哪一种。论文给出的平均癌细胞比例不能用总癌细胞数除总细胞数直接“核错”。对面积密度还需真实的有效组织面积，不能把细胞捕获量当绝对组织丰度。

## 5. 图组按证据职责定位

| 图／正式版位置 | 直接问题 | 对应分析和代码路径（均在固定提交） | 结论上限 |
|---|---|---|---|
| Fig. 1；ED1 | 数据来源、主要谱系、CNA 背景 | `analysis/identifying_aneuploid_cells.md`；`analysis/scripts/copykat_mix.R` | 支持身份与采样框架，不是克隆谱系 |
| Fig. 2；ED2 | 癌细胞患者表达背景与应答 | `psbulk.prepare.R`、`psbulk.fastNMF.R`；`archetype*.md` | 表达 archetype；正常谱系相似不证明起源 |
| Fig. 3a–c；ED3a | 跨患者重复的细胞程序 | `metamodule_fnmf.s1.R/s2a.R/s2c.R` | 程序可重复，不等于遗传亚克隆 |
| Fig. 3d | 癌细胞内 HLA／IFN 来源 | Xenium marker 与细胞归属 | 原位来源支持，不定位上游刺激 |
| Fig. 3e,f；ED3b–e | 阳性频率和平均评分 | `metamodule_cell_frequency.R` | 两个不同估计对象，非细胞转变证明 |
| Fig. 3g–l | 周期、免疫与应激相关表达；Ki-67 | `cell_cycle_scoring.md`；pseudobulk DEG | 多测量支持，非干预因果 |
| Fig. 4；ED4–7 | TME 细状态、正常参考和应答 | `TME.md`、`TME_freq_test.md` | 状态分布不同，不能按显著性给谱系排因果重要性 |
| Fig. 5a；ED8a–c | 患者频率共现社区 | `ecotype_0_create_feature_corr.R`、`ecotype_1_define.R` | 跨患者协变 |
| Fig. 5b,c；ED9 | 类别相对共存在量 | `ecotype_3_contexts.response.R` | RCOP 不等于组内相关或信号传递速率 |
| ED8d | 候选配体—受体关系 | `cellchat_ligand_receptor.md` | 表达与数据库兼容性 |
| Fig. 5d–k；ED8e–g | 组织内空间组成、niche | `xenium.spatial_niche.md` | 局部组织，不证明方向性作用 |
| ED10a–c | 细胞频率模型 | `scML/scML_classifier.v3.R` | 当前代码存在上游信息泄漏，性能须重评估 |
| ED10d–g | 基因模型与外部关联 | `ML13g/build_ML_model.R` | 外部信号支持，不等于冻结单样本部署 |
| ED10h,i | 综合研究模型 | 概念汇总 | 箭头是解释，不自动是机制证据 |

`ED` 表示 Extended Data。原仓库部分教程沿用旧稿 Fig. 6／Fig. S 命名；本项目按正式版定位，不把旧编号直接当算法错误。表中短脚本路径除特殊说明均在 `analysis/scripts/` 下。是否完整取得各文件见来源表。

## 6. 检验名称的材料差异

【P】Methods: Cell frequency of the metaprograms and TME cell states 写 Wilcoxon signed-rank；Fig. 3、Fig. 4 及多组扩展图图注写 Wilcoxon rank-sum。前者通常需要配对差值，后者比较独立组，不能互换。

【I】本项目不凭常识替作者把 Methods 改掉，也不直接断言作者真的对独立患者做了配对检验。最低仲裁材料是实际调用的 `paired`、`exact`、纳入患者 ID 与结果表。对迁移项目，应根据设计选择独立组或配对／重复测量方法，不能因为论文写了某名称就照搬。

## 7. 建议保存的最小元数据

【T】`individual_id, sample_id, biopsy_or_section_id, platform, time_or_stage, batch, response_original, response_used, treatment_switch, eligibility_reason, tissue_area, n_cells, lineage_counts`。

不要把不明的时间、面积或治疗信息补零。每一结果表另带实际患者 ID、分母定义、缺失规则、效应量、区间和检验家族。一个总流程图不能替代逐分析的纳入清单。

## 8. 统计学上“不显著”的正确含义

【I】正文以年龄在 archetype 间无显著差异来支持与年龄无关，这不足以证明独立性；频率不显著也不能证明完全不变。需要看区间是否足够窄、效能是否足够、是否有预先规定的等效界限。把“未拒绝零假设”当“已经排除混杂／已经证明无差异”，会使整个故事显得比证据更强。
