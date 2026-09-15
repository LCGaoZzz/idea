# M02｜按问题选方法，不用工具投票代替证据

下面的工具定位来自原始研究/官方文档；“先后顺序”和“项目边界”是本知识库迁移建议。本版未安装、运行或逐行审计这些算法。

| 问题 | 可选方法及来源 | 项目中必须另外检查 |
|---|---|---|
| 特定细胞对是否空间富集 | 显式图统计；[Squidpy R08](https://squidpy.readthedocs.io/en/stable/api/squidpy.gr.nhood_enrichment.html) | 空间图、交换性和零模型 |
| 可重复出现的空间 niche | [CellCharter R04](https://www.nature.com/articles/s41588-023-01588-4) | 表示和聚类稳定性、样本可重复性 |
| 带程序解释的 niche | [NicheCompass R05](https://nichecompass.readthedocs.io/en/latest/) | 先验与面板覆盖、先验依赖 |
| 不同细胞类型的协调表达程序 | [DIALOGUE R03](https://www.nature.com/articles/s41587-022-01288-0) | 区分细胞内状态与组成效应 |
| 跨样本共同变化的细胞模块 | [CoVarNet R02](https://www.nature.com/articles/s41586-025-09053-4) | 生物学样本量与组织混杂 |
| 邻域信息的额外预测贡献 | [MISTy R06](https://pubmed.ncbi.nlm.nih.gov/35422018/) | 验证划分、空间泄漏、非因果解释 |
| 候选通讯与接收端程序 | [LIANA+ R09](https://pubmed.ncbi.nlm.nih.gov/39223377/)；[NicheNet R10](https://pubmed.ncbi.nlm.nih.gov/31819264/) | 实测证据、空间位置和下游响应 |

## EXTERNAL_FACT：DIALOGUE 与 CoVarNet 回答不同问题

DIALOGUE 的 MCP 是不同细胞类型中协调变化的程序组合，不要求每种细胞使用完全相同的一组基因。CoVarNet 利用跨样本细胞亚群频率协变构建细胞模块；两者不宜分别运行后直接拿显著性作优劣排名。[R03](https://www.nature.com/articles/s41587-022-01288-0)；[R02](https://www.nature.com/articles/s41586-025-09053-4)

CoVarNet 原论文在跨组织 CM 识别中因上皮细胞高度组织特异而排除了上皮细胞，定位 “Identification of cross-tissue CMs”。**这不是所有 Xenium 肿瘤研究必须排除肿瘤细胞的通则。** 若做肿瘤–CAF–髓系关系，应将原方法复现和扩展分析分别命名。[R02](https://www.nature.com/articles/s41586-025-09053-4)

## TRANSFER：推荐的最小方法组合

先建立可解释的邻域组成、距离、边界指标，再选择一个 niche 发现框架；若问题确实涉及状态协调，再加入相应模型；通讯留到候选结构定位之后。跨工具一致可能来自共享数据、先验或错误，不是天然独立验证。

固定半径保留物理尺度但邻居数随密度变化；固定 k 保留邻居数量但物理距离变化。组织空洞可能被连边穿过。应预先指定主尺度，检查有限的合理尺度、图构建、分割与注释敏感性。30/50/100 μm 仅是可讨论的示例，不是作者参数或默认推荐。

每个 niche 至少输出：逐样本出现情况、组成、各细胞类型的程序、病理区室、质量分布和稳定性。跨样本注释稳定比单张切片分成更多类别更重要。
