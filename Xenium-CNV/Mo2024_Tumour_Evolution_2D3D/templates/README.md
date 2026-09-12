# 迁移模板使用说明

[返回总目录](../README.md)

本目录为研究设计建议，不是作者原始输入或已经取得的用户数据。两个TSV只有表头，没有虚构样本。

## sample_manifest.tsv

每行表示一份测量/切片记录。`biological_id`是真正独立的动物或患者；`block_id`与`section_id`记录嵌套。`timepoint`是生物学时期，`z_um`是同一组织内空间位置，不能互换。`batch_id`不能由时期名称代替。不同模态的配对可重复同一组织ID，但每个模态的原始路径、panel和参考要分别记录。

`coordinate_unit`应写明μm、pixel等单位；涉及变换时另附原始坐标、尺度因子和变换记录。未知字段保持为空并在工作日志说明，不填0或虚构默认值。

## measurement_status.tsv

建议`measurement_status`使用：`not_measured`、`measured_not_testable`、`tested_inconclusive`、`tested_directional_evidence`。这四种状态不能直接映射为0/1表达。若事先设计了等效性检验并有足够精度，可以单独增加`tested_equivalent_within_prespecified_margin`，同时记录效应界值；不能用不显著替代。

`response_type`区分gene、program、cell_density、proportion等。比例的`unit_or_denominator`写清分子/分母，密度写清有效组织面积。不确定性可能是置信区间或其他合理量，必须在`uncertainty_method`说明。模板不预设所有结果适用同一种统计模型。

只有原始数据和资格规则明确后才填写效应，不把模板作为对尚未分析样本的结果表。
