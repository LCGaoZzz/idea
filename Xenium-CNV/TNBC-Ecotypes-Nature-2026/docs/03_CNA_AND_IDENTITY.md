# 03｜CNA、恶性身份与遗传克隆：一个必须守住的上游关卡

[返回](../README.md) · [P：Methods](https://www.nature.com/articles/s41586-026-10469-9) 中 Identification of aneuploid cells、Filtering of scRNA-seq data、CNA inference in Visium data。[C1：判定函数](https://github.com/navinlabcode/tnbc-chemo/blob/fbe1dd3b1db05dd5e9f02485a45fdd438d6af9fb/analysis/scripts/copykat_mix.R#L160-L235)。

## 1. 任务定义：筛选身份，不是恢复完整克隆树

【P】本文用 scRNA 表达推断 CNA，与来自正常乳腺参考的细胞混合分析，再结合 Leiden-based 与 modified Tirosh-like 判定。两个判定同时支持 aneuploid，且具有上皮身份，才进入癌细胞集合。论文随后分析患者 CNA 概貌和表达背景。

【I】应分开四个对象：表达推断的拷贝数异常；对恶性身份的支持；遗传亚克隆划分；有方向的谱系树。前一对象不能自动识别后一对象。广域异常有助于身份判断，但没有 DNA、可信等位信息或独立谱系证据时，不应把表达状态标签改名为 clone。

## 2. 作者报告的身份链

【P】CopyKAT v1.0.8 每样本推断 CNA；参考约 800 个 HBCA 正常细胞。Leiden 分支对 CNA profile 做 PCA／UMAP，再建图并递增分辨率；与正常参考混合较少的簇被视作候选。Modified Tirosh 分支同时要求异常幅度与共同异常模式的相关高于参照阈值。Methods 给出最终两分支 AND；上皮谱系是后续独立条件。

【C】`copykat_mix.R` 同时产生默认、Tirosh、Leiden 和 Livnat 等中间列。L394–475 的 Livnat 路径还涉及肿瘤／正常组织表达相似性；不能仅因为存在该列就宣称它是最终论文标签。必须追踪后续读入了哪一列及最终 cell ID 列表。

【T】恢复时导出一个决策表：`sample_id, cell_id, score, ACC, score_threshold, acc_threshold, prediction_tirosh, prediction_leiden, prediction_livnat, epithelial_label, final_malignant, decision_source`。保存分支比只交付一个 `malignant=True` 更重要。

## 3. Score 与 ACC 的数学意义

【C／I】设 $X_{bc}$ 是 bin $b$、细胞 $c$ 的 log2 相对拷贝数矩阵。函数 `decide_aneuploid` 首先计算：

$$S_c=\sqrt{\sum_bX_{bc}^2}.$$

这衡量偏离零基线的整体幅度，不区分增益还是缺失，也不表示绝对 ploidy。若 bin 数量、权重或缺失分布不同，score 的可比性需要重新判断。原函数有 `na.rm=TRUE`；缺失 bin 多时 score 可能较小，不能只看数值有界就认定质控合格。

函数再以正常参照分位数缩放：

$$a=Q_{0.005}(S_{ref}),\ b=Q_{0.995}(S_{ref}),\quad S'_c=(S_c-a)/(b-a).$$

查询细胞 score 最高约 1% 的平均 CNA profile 构成候选异常模式，细胞与该模式的 Pearson 相关用于 ACC。高幅度但不同于主导模式的细胞可能较难通过；这适合身份过滤的一种目标，不是为充分恢复稀有分支设计的无偏克隆发现器。

## 4. 真正改变决策边界的是阈值下限

【P】Methods 写缩放下界 5%、上界 99.5%，再用正常 score 的 99% 分位与 ACC 的 99% 分位作为判定阈值。

【C】L173 使用 `c(0.5/100,99.5/100)`；L217 附近计算标准化 score 的 99% 分位后把阈值限制为至少 1。两个差异不能只合并成“参数写错”。

【I】假设参照值有限、分位数定义一致、$b>a$，且正仿射变换保持分位数，则：

$$Q_{.99}(S'_{ref})\le Q_{.995}(S'_{ref})=1,$$

$$S'_c>\max\{Q_{.99}(S'_{ref}),1\}\iff S_c>Q_{.995}(S_{ref}).$$

因此当前 score 子条件等价于超过原始参照 99.5% 分位，而非仅按 99% 分位。改变缩放下界 $a$ 而保留上界与 floor，标准化数值会改变，但二分类可以不变。这个区别能防止把任何参数文字差异都夸大成分类错误。

不能忽略的边界包括：$a=b$、常数 profile、NaN、严格大于与大于等于、分位插值类型及浮点邻界。ACC 仍是另一个 AND 条件，本推导不等于推导了完整最终恶性判定。

本项目合成测试验证这个等价关系；没有原始患者矩阵，不能报告有多少真实细胞标签改变。

## 5. “更严格”不等于“更真实”

【I】要求多条件一致可能提高某类特异性，同时系统性减少弱异常、不同模式或低覆盖细胞。论文把 non-aneuploid epithelial 归入不保留的组，意味着后续癌细胞图谱主要描述通过该筛选器的癌细胞，而非已证明覆盖所有恶性细胞。

近二倍体恶性细胞、低质量癌细胞与正常上皮细胞不容易仅凭同一规则完全区分。这里是可观察范围和误分类风险，不是已经证实本文漏检了哪一位患者的具体细胞。

【T】新项目不要把“CNA 弱”直接改成“正常”。可以保留 `malignant_supported / nonmalignant_supported / unresolved`，在独立证据允许时评估不同阈值下的结果。上下游共同使用 CNA 相关表达特征时，还应警惕筛选后关联和循环定义。

## 6. Visium、VisiumHD 与 Xenium 不能混成一个 CNV 方法

【P】Visium Methods 用 spot CNA 幅度、与样本平均 profile 的相关和 Copykit 聚类支持癌细胞富集 spot；VisiumHD 使用 32 μm bin、aneuploid 与 RCTD 细胞身份组合。Xenium 的主细胞状态路径是从 scRNA 转移标签及空间程序评分。来源：对应三个 Methods 小节。

【I】混合 spot 的异常幅度同时受肿瘤纯度与异常幅度影响；从混合 spot 直接解释单细胞克隆比例会混淆两者。32 μm bin 也不能因为产品名含 HD 就当作一个实测单细胞。

【T】迁移到靶向 Xenium 面板前，先生成按染色体／区段的基因覆盖、检测率、表达方差和稳定参考表。组织位置上的表达程序可以形成成片图案，但“成片”不证明 DNA 拷贝数变化。缺少等位／DNA／独立 marker 支持时，输出候选 CNA 模式及不确定性，不输出未经支持的确定克隆树。

## 7. 如何评价可能的改进

【T】使用固定患者和参考，把 `source_exact`、`methods_declared`、`adapted` 分开保存。比较细胞保留／剔除交叉表、CNA 模式一致性、独立身份 marker、下游程序与共现的稳定性。先判定上游差异是否传导，再决定是否重新跑全部分析。若只改变画图阈值就得到更漂亮的边界，不构成方法改进。

优先级应按结论影响，而不是按代码行看起来有多可疑排序：验证结局进入筛选的风险通常比关闭分支中的拼写更值得先处理；CNA floor 对实际边界的影响比单看缩放下界更直接。
