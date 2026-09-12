# 验证记录及其边界

本次在Python3.13.5实际执行新增辅助脚本，20项合成单元测试通过，0失败、0错误、0跳过。回执为[toy_results.json](toy_results.json)，包含实际脚本SHA-256。另执行两个脚本的`py_compile`、人工CSV的CLI成功路径，以及重复写同一输出目录的拒绝路径；后者实际返回exit code2。

测试输入只有合成数值和人工ID，不含患者／真实动物。通过不代表作者R代码、标签、NMF、CellChat、Xenium niche或临床预测器已复现。patient_analysis_runs与animal_analysis_runs均为0。

## 实际命令

```bash
python -m py_compile code/toy_checks.py code/audit_inputs.py
python code/toy_checks.py --out validation/toy_results.json
python code/audit_inputs.py --cells examples/synthetic_cells.csv \
  --state-map examples/synthetic_state_map.csv --out /tmp/tnbc_input_audit_example
# 对同一非空输出路径再次运行，应拒绝覆盖并返回2。
```

测试覆盖的是可构造反例、定义恒等式与关键输入边界，并非穷尽测试，也未做百万级内存／性能测试。仍需检查真实数据中的矩阵尺度、panel、临床标签、组织边界及所有作者依赖。

文献与源码检查也有独立边界：正式版HTML与图注已核对；没有逐张审计原始图像、没有全部补充表／最终模型／历史运行对象。源码证据来源和冲突分别见[sources](../sources/README.md)与[audits](../audits/ISSUES.md)。

本目录不使用以前那轮11项测试替代本次20项测试；测试数量和脚本哈希只对应这里的新代码。
