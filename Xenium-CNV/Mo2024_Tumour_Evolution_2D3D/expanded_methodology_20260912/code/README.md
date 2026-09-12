# 原创合成数学检查：可运行，但不是论文复现入口

[目录](../README.md)｜[数学解释](../docs/06_math_statistics.md)

`run_checks.py` 是本档案自编的诊断示例。它不调用网络、R、GenomicRanges、PyTorch或患者数据，不实现真实区间统一、CNV推断、Xenium分割或Mushroom训练。

## 运行

```bash
python -m venv .venv
# 根据操作系统激活该环境后执行：
python -m pip install -r code/requirements.txt
python code/run_checks.py --output validation/my_checks.json 2> validation/my_checks.log
```

从本目录根运行。输出路径已经存在时脚本拒绝覆盖，使用新文件名以保留历史日志。依赖锁仅服务于本档案诊断程序，不是作者环境锁定。本次实际测试Python3.13.5、NumPy2.3.5；代码声明Python>=3.10，但没有测试所有版本组合。

## 输入与数学范围

CNV示例使用已对齐、非重叠、有限且正长度的小区间，符号−1/0/+1；原R脚本的中性比值为1，二者不可直接混用。`legacy_no_probability_grid` 故意保留被审读分母逻辑，用来展示反例，不是推荐修复或完整R移植。

`probability_pred_grid` 限于状态轨道并集与置信度乘积的网格版本。`signed_similarity`是论文描述的代数重述，全中性时NaN表示没有有效非中性比较，不能自动当作完全一致。

## 覆盖的检查

24项测试包括有符号相似度性质、全中性与非法输入、不对称辅助公式、概率自相似、非欧氏距离反例、几何稀释、表达分配守恒与零分母、连通/不连通图循环秩、交叉熵输入语义以及偏相关和斜率的区别。

CE数值使用NumPy的稳定log-sum-exp计算，不是Torch实际运行。距离诊断用双中心Gram的特征值检查，不会自动修正输入。

## 如何理解通过

测试通过意味着代码重现了明确写下的性质、数值或反例。证明一个反例存在，不等于证明作者患者结果发生错误。测试没有检查原始数据、原作者训练权重、区间处理、真实空间统计或生物学假说。

真实执行记录：[synthetic_checks.json](../validation/synthetic_checks.json)，[test_log.txt](../validation/test_log.txt)。其中`source_sha256`绑定该次运行的源码；任何修改后应重新生成独立日志。
