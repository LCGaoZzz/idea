# 辅助代码：只检查定义与输入，不冒充作者复现

[返回](../README.md)。两个脚本均为本项目新增T类辅助实现，使用Python标准库。语法目标Python≥3.10；本次实际测试Python3.13.5，不声称其他环境已经测试。没有调用R、Seurat、CopyKAT、CellChat或原作者模型。

## 1. 运行合成测试

在本idea目录内执行：

```bash
python code/toy_checks.py --out /tmp/tnbc_toy_results.json
```

测试CNA score floor等价、缩放下界、退化输入、负载并列、Jaccard相同程序、条件比例、汇总权重、多标签率、RCOP与协变区别、阶段比例的转移不可识别性，以及输入合同。输出带脚本SHA、解释器版本、测试数量、失败和错误。**全部例子是合成，不含患者或真实动物数据。**

## 2. 输入审计的运行方式

```bash
python code/audit_inputs.py \
  --cells examples/synthetic_cells.csv \
  --state-map examples/synthetic_state_map.csv \
  --out /tmp/tnbc_input_audit_example
```

输出目标已有结果时返回exit code2，不默默覆盖。命令中的示例是3行人工数据；换真实CSV时保留输入合同，不把示例标签当论文细胞状态。

### 必需字段

`cells.csv`：`individual_id,sample_id,stage,cell_id,lineage,state`。可选`x_um,y_um`必须同时给出并为有限数。字段值去除前后空白；ID应预先标准化，不能依赖空白区分个体。每行一个已给定单标签的细胞，不接受同一细胞多MP重复行。

`state_map.csv`：`state,lineage`，每状态唯一父谱系。所有细胞state必须存在于字典。unresolved应显式定义状态及父类，不能用空值自动当正常或癌细胞。程序分数和多标签MP应另存，不用此单标签工具聚合。

### 检查与输出

检查重复列、CSV宽度、必需字段、sample→individual/stage一致性、样本内cell键重复、state→lineage映射和可选坐标。不同样本可以具有相同cell_id；同一动物出现多个阶段仅标记需确认重复测量，不自动拒绝。

输出`sample_state_counts.csv`：状态计数、父谱系分母、全样本分母、两种比例、缺失原因。父谱系未观察到时，内部比例为空而非0；父谱系存在但目标状态没有时为0。全样本分母含全部输入细胞，包括显式保留的unknown。

输出`input_audit.json`：样本／个体／状态数和设计提示。统计是每样本，不自动合并同一动物多切片，避免未确认重叠面积就聚合。

## 3. 不覆盖的能力

不验证细胞标签的生物学真值，不算组织面积密度，不判断癌细胞，不推断CNV／clone，不建立邻域，不做DEG、临床或空间统计，不检查全部panel覆盖与批次可识别性。程序使用O(细胞数)的去重集合，大样本需评估内存，未进行百万级benchmark。

这些工具帮助尽早暴露输入错误；返回成功只表示这部分合同通过。作者真实代码的对应路径与缺口见[方法卡](../protocol/25_ANALYSIS_CARDS.md)，不得用这两个辅助脚本替代原论文流程。
