# 新项目元数据检查工具：不是作者分析流水线

[返回入口](../README.md) · [项目设计](../docs/07_three_stage_xenium_project.md)

`check_project_manifest.py`为本整理新增的【H】辅助代码，只读取TSV元数据，不读取表达、空间坐标、图像、RDS或pickle，不运行作者任何算法。只用Python标准库，类型注解使用Python3.9+语法；本次实际测试环境Python3.13.5。

## 输入

每行代表一个全局唯一`section_id`。最低字段：`animal_id, sample_id, section_id, coordinate_frame_id, stage, batch_id, panel_id`。允许一个sample多section；sample必须对应一个animal和一个stage。`coordinate_frame_id`必须由研究者定义为物理坐标域；工具仅要求字段非空，**不验证真实几何，也不把共享玻片视为自动可连边**。

[模板](../templates/sample_manifest.tsv)只有表头，运行会报告NO_DATA，不含伪造研究样本。用户应复制并填入自己的实际设计，stage标签在命令行显式给出。

```bash
python code/check_project_manifest.py path/to/actual_manifest.tsv \
  --design destructive --stages early middle late \
  --output results/design_audit.json
```

`destructive`表示每只动物只对应一个取材阶段；`longitudinal`允许同动物多阶段，但每次采样应有独立sample ID；`unknown`不替用户假定设计，并输出警告。上述early/middle/late是示例标签，不是论文固定天数。

## 检查与解释

拒绝空表、缺关键字段、未知stage、重复section、sample到animal或stage的矛盾映射，以及destructive下动物跨期复用。分别按阶段统计唯一animal ID，不把多切片当多动物。

工具对stage–batch及stage–panel分别建连接图。不同阶段可以经共享batch间接连接；如果图分成多个组件，则组件间stage对比不能与不受约束的相应batch/panel固定效应分离。警告提示检查设计，不代表任何生物差异一定不存在，也不是批次校正已完成。

**两个单独图都连通，仍不保证含其他协变量或同时含batch和panel的完整模型可辨识。** 工具不检查联合设计矩阵秩、功效、平衡性或实际因果效应。只有一只动物的stage会警告无法估计其阶段内动物变异，没有设定跨项目通用的最小样本量。

退出码0表示没有格式/映射错误，仍可能有重要警告；2表示错误。`valid_metadata=true`绝不等于充分功效、无混杂或生物学验证。无效输入中的计数也只能作为错误诊断，不应用于正式分析。

## 实际测试

```bash
python -m unittest discover -s code -p 'test_*.py' -v
```

11项合成测试在本次执行通过，另实际运行了合成TSV的CLI检查。测试覆盖切片不膨胀动物数、阶段批次断连、重复动物、重复section、映射冲突、空输入、缺字段和预期stage标签等。测试数据不是论文数据或用户样本。原始测试日志和CLI输入/输出见[validation目录](../validation/README.md)。

## 作者代码如何对应

本目录**没有复制作者源码或改写成伪端到端runner**。原文件路径、blob指纹和固定提交见[代码清单](../references/code_inventory.tsv)；每图预期Data、实际函数和缺失上游见[逐图映射](../docs/04_figure_to_code_map.md)。要执行原文分析，先解决匹配Data、环境、上游参数与人工选择，不能用这个元数据检查脚本替代。
