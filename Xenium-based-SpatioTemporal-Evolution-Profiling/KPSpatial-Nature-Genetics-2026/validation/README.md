# 本次实际执行记录

[返回入口](../README.md) · [复现边界](../reproducibility/README.md)

本目录记录新写离线审计脚本在本次会话中的实际测试，不是作者论文的运行日志。`receipt.json`列出命令、退出码、Python版本、源文件SHA256以及公共元数据计数；`unittest.stderr.txt`是13项测试的实际输出。

测试内容包括人工集合反例、返回值解包、空模板／空身份／重复样本／肿瘤跨动物身份冲突、阶段—批次嵌套提示，以及一个字节核验后的真实公开metadata文件。人工例子明确标记为synthetic，不能当作论文原始生物数据。

这些结果没有证明：完整文章科学复现、真实Cassiopeia树运行、全部notebook正确、原论文效应或P值可复现、用户Xenium数据可分析、原reconstruct工作流验证器已在新文档树上通过。

源文件在提交时应与receipt的哈希一致；公共metadata保留原换行，可用Git blob SHA复核来源。后续用户自行重跑会产生不同耗时，建议写新日志，保留本次记录不覆盖。

命令与使用见[reproducibility/README](../reproducibility/README.md)。文档中较宽的“数据合同检查”只指脚本实际覆盖的字段与规则，不代表所有输入格式、样本功效或空间独立性均已检验。
