# 环境与执行范围

## 本次独立辅助检查的真实环境

Python: 3.13.5

算术与表格检查器仅使用标准库；18项unittest实际通过。理论图使用matplotlib（3.10.8）；图中参数为明确的教学假设，不来自作者训练。HTML由本地pandoc生成。

## 原论文环境

论文报告的R/Seurat/CellRanger/Python等版本在tables/parameter_registry.tsv。该环境没有在本次容器中重建；不能把上述辅助环境当作论文环境。原作者RF参数、模型权重、随机种子及输入feature schema未知。没有安装作者依赖、运行作者notebook或重训练PreGame。

## 原用户protocol

tools/reconstruction_protocol中的validator及schema来自用户上传ZIP，未改写校验逻辑。它验证正式manifest的交接一致性，不对附带长篇文献评论做生物学事实证明。正式stage1因原始来源字节缺失保持partial；作者执行账本为空。
