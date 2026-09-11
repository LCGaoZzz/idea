# 实际验证记录与未执行项

日期：2026-09-11。环境：Python3.13.5。

## 已实际执行

`python -m unittest discover -s code -p 'test_*.py' -v`：11项合成元数据测试通过，日志见[unit_tests.txt](unit_tests.txt)。两份Python代码通过`py_compile`。合成CLI运行退出码0；[输入](synthetic_manifest.tsv)和[报告](synthetic_cli_report.json)完整保留字段，JSON仅重新排版，没有改变值。

CLI报告包含ONE_ANIMAL警告，刻意展示“valid_metadata=true”不等于生物学重复充分。两行样本均为合成测试夹具，不来自原论文或用户。

本地测试的代码指纹：

| 文件 | Git blob SHA-1 | SHA-256 |
|---|---|---|
| check_project_manifest.py | cf007786422d516f699f17f6894a88ec9c35bdec | 56831a0529ff6bf97f627ea104a6a930c5e54416387ae624491e560c6e9d2c87 |
| test_check_project_manifest.py | 6e879729b3b6ab02d7daa49f41fd9fdf5df57e17 | ce1d1fc6f363134f87db9f49cf0417c793aae65e9c1a4459393bcf1322ec97f5 |

## 未执行

作者13份分析/制图脚本执行数0；用户数据分析数0；27个主图分析单元均未复算。受体删除等补充实验是论文报告，不是本项目实施的实验。未重新运行原重建skill的完整validator；没有将文档合规、元数据测试或Git提交成功写成科学复现成功。

测试未覆盖真实空间几何、表达矩阵、细胞注释、完整统计设计矩阵的秩、功效、多重检验或因果辨识。文档提出这些检查，不等于通过了这些检查。
