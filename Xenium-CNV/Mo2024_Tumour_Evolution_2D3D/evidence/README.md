# 证据表与执行记录说明

[返回总目录](../README.md)

## 阅读和审计顺序

先读[source_index.md](source_index.md)，确认原文及代码获取范围；再按[traceability.tsv](traceability.tsv)查正文主张、最终图号、Methods、代码位置和缺口。参数细节在[parameter_provenance.tsv](parameter_provenance.tsv)，固定版本在[repository_pins.tsv](repository_pins.tsv)，未解决事项在[gaps.tsv](gaps.tsv)。

P代表原始论文；C1–C4及C4H在repository_pins.tsv映射到完整固定SHA。`C1:路径::函数`表示该固定快照下的函数定位，不是声称原作者曾用此快照生成最终结果。Methods标题用于稳定的人类可读定位，不依赖网页行号。

## 本目录记录数量

- 14项主张—分析记录：13项原研究模块和1项独立局部检查。
- 61条参数/处理规则来源，区分论文声明、活动代码、CLI默认、被覆盖示例、库默认及文字歧义。
- 5个版本条目：4个指定仓库及1个Morph历史候选；没有将历史候选当作已确认论文运行版。
- 29条尚需处理的材料缺口、冲突、统计或接口风险；并非29个已证实的论文错误。

这些数量用于导航，不是质量评分，也不代表完整覆盖所有上游依赖。

## 状态语义

`受阻`：未取得足够输入、配置、源码链或运行结果来完成实证复现。

`材料冲突`：论文定义与已读公开材料之间存在需要解释的差异；不能直接推断原结论错误。

`已执行验证`：只用于本目录T01的9项合成数学检查；原作者代码和患者数据均未运行。

[scope.json](scope.json)将这些执行范围机器化记录。没有通过结构/字段校验就推定科学正确性的逻辑；本目录也没有声称通过原workflow的全流程复现验证。

## 合成检查及哈希

执行文件：[scripts/evidence_sanity.py](../scripts/evidence_sanity.py)。结果：[sanity_result.json](sanity_result.json)，标准错误测试日志：[sanity_test_log.txt](sanity_test_log.txt)。测试运行环境Python 3.13.5，标准库，无随机输入。

被执行脚本SHA-256：

```text
c4545da44f825a4cfabc6e6edee8fcb3e2ea108ba23fb0d247ef84d489b92380
```

哈希只用于确认文件身份，不保证数学推理或生物学结论正确。合成例子展示定义间差异，不负责真实segment对齐、基因组转换、CNV调用或作者最终标签验证。
