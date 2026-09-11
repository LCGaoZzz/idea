# 代码说明｜从方法理解到可检查的数据表

[返回研究 idea](../README.md) · [原始代码审读](../docs/06_code_walkthrough_and_audit.md) · [统计与因果方案](../docs/05_statistics_and_causal_inference.md)

## 1. 两条代码路径，必须区分

**作者路径：**按照 `provenance/upstream_manifest.json` 获取固定版本的真实原始代码，逐文件校验 Git blob SHA，结合第 6 章阅读。它包含原始 notebook/脚本，需要作者的数据、注释和实验配置；不保证直接从头运行。

**本目录教学路径：**使用 `niche_idea.py` 和 `demo.py` 学习来源汇总、方向性局部暴露、ROI 组成与分母、空间覆盖采样、供体级材料交互。它是独立编写并测试的简化实现，**不是作者完整算法的重新实现，更不是论文生物学复现**。

| 文件 | 用途 |
|---|---|
| [niche_idea.py](niche_idea.py) | 可复用的表格分析函数及输入验证 |
| [demo.py](demo.py) | 构造明确标记的合成数据，完整走通输入输出 |
| [test_niche_idea.py](test_niche_idea.py) | 23 项分析逻辑、边界与原始语法片段测试 |
| [fetch_original_code.py](fetch_original_code.py) | 获取固定版本作者文件与源码阅读副本，不执行 notebook |
| [test_fetch_original_code.py](test_fetch_original_code.py) | 5 项本地 SHA、路径与文件保护测试，不联网 |
| [requirements.txt](requirements.txt) | 教学代码依赖范围，不是作者环境锁文件 |

## 2. 安装与最小运行

需要 Python 3.10 或以上。以下命令均在 `2026-09-serpin-myeloid-spatial-niches` 目录执行：

```bash
python -m pip install -r code/requirements.txt
python -m unittest discover -s code -p 'test_*.py' -v
python code/demo.py --out demo_output
```

本次本地实际运行了 **28 项测试，全部通过**，并完成合成演示。版本与被测试代码的哈希见 [validation.json](../provenance/validation.json)。依赖文件允许合理版本范围，不代表该范围内所有组合均已测试；复用时应记录自己的实际环境。

演示会生成 200 行表达示例、3,000 个空间细胞、8 个 ROI，以及 12 名合成供体的 2×2 因子示例。所有数据均由程序构造，报告保留 `SYNTHETIC_NOT_PAPER_DATA`。演示里的交互项也是生成规则的一部分，不能拿其区间“证明”材料机制。

演示输出目录可能被再次运行更新，不要将真实研究结果保存在同名演示目录。

## 3. 输入合同 A：患者内的来源状态

`summarize_serpin(cells, representation=...)` 接收一个 DataFrame。

| 字段 | 类型/要求 | 含义 |
|---|---|---|
| source | 非空字符串 | 数据来源，避免跨研究患者编号碰撞 |
| patient_id | 非空字符串 | 生物学个体 |
| cell_id | 非空字符串 | 同一 source+patient 下唯一 |
| is_malignant | 真正的布尔列 | 已经完成的恶性细胞判定，不由该函数推断 |
| SERPINE1、SERPINB2 | 有限、非负数值 | 明确表示下的测量值 |

`representation` 必须显式为 `raw_counts` 或 `log1p_nonnegative`。前者还检查整数性；后者只说明调用者声明了该表示，数值检查无法证明数据确实经过正确归一化。不能把插补、缩放或批次校正后的任意矩阵随意标成此类型。

以下例子读取刚生成的合成数据：

```python
from pathlib import Path
import sys
import pandas as pd

sys.path.insert(0, str(Path('code').resolve()))
from niche_idea import summarize_serpin

cells = pd.read_csv('demo_output/synthetic_expression.csv')
summary = summarize_serpin(cells, representation='raw_counts')
print(summary[['source', 'patient_id', 'n_cancer',
               'fraction_SERPINE1_pos', 'mean_SERPINE1_positive']])
```

输出同时包含每基因阳性计数、阳性比例、全部恶性细胞均值、阳性细胞内均值，以及双阳性/任一阳性的计数和比例。只有恶性细胞进入这些分母。

**特意保留的边界：**无阳性细胞时，条件均值为 NaN，不是 0；整个输入没有恶性细胞时直接报错，不生成虚假的零比例。若某位患者没有恶性细胞，其患者行不出现在结果中，应与原始样本表对照记录，而不是把未出现解释为阴性。

## 4. 输入合同 B：ROI 细胞表与中心表

`build_roi_table` 接收两个 DataFrame。细胞表字段为：

```text
image_id, patient_id, cell_id, x_um, y_um, phenotype
```

中心表字段为：

```text
image_id, roi_id, x_um, y_um, [area_um2]
```

所有坐标都是 **μm**，`area_um2` 是 **μm²**。函数不会猜测像素大小，不读取图像，也不做 alpha-shape、组织分割、细胞注释或多模态配准。真实研究需要在调用前完成这些步骤。

`image_id` 表示独立空间坐标域，并且只能属于一个患者/小鼠。组织芯片中一张物理扫描图包含多个患者时，应按 core 等方式创建患者特异的空间域 ID，并保留原扫描 ID 为额外 metadata；不要把多个患者同放在一个分析域。

同一 `cell_id` 可以在不同 image 中复用，但 image+cell_id 必须唯一。中心引用不存在的图像、非有限坐标、缺失字段或重复 ROI ID 都会报错。

### 4.1 面积分母不是一个可忽略的默认值

推荐提供窗口与有效组织掩膜的交集面积 `area_um2`，并确保输入细胞也按**同一掩膜**纳入。函数仅检查面积有限、正且不大于圆面积；它无法自行证明面积来自哪个掩膜。

没有有效面积时，必须显式设置 `assume_full_tissue=True` 才能用 πr²，输出标记为 `area_kind='nominal_circle'`。这只是允许名义圆面积，不是程序自动证明整圆都处于组织内。对真实边缘区域应避免轻率启用。

### 4.2 两类肿瘤标签与免疫标签必须显式传入

`control_label` 与 `ko_label` 表示两种肿瘤类别；`immune_labels` 必须是非空标签列表，且不包含这两类肿瘤标签。细胞标签需事先映射一致，函数不会替用户判断哪些是免疫细胞。

这里的 `n_tumor` 专指两种指定标签的计数之和。若数据还有其他恶性类别，不能假设其自动进入该分母。迁移到多个来源状态时，应先定义新的暴露合同，再扩展函数。

### 4.3 示例调用

```python
from niche_idea import build_roi_table

cells = pd.read_csv('demo_output/synthetic_cells.csv')
centers = pd.read_csv('demo_output/synthetic_centers.csv')

result = build_roi_table(
    cells, centers,
    radius_um=180,                 # 合成例子参数，不是论文的 200 像素
    control_label='CTRL', ko_label='KO',
    immune_labels=['CD8', 'Macrophage'],
    min_total=20, min_tumor=10,     # 例子门槛，不是论文的 400/200
    mix_threshold=0.20,
    assume_full_tissue=True,       # 演示中的窗口在合成完整区域内
    record_membership=True,
)
if result.table.empty:
    raise RuntimeError('No retained ROIs; inspect result.exclusions')
```

函数默认 `min_total=1, min_tumor=1` 是最小数学可定义性，不是实际研究推荐门槛。正式研究需事前设定稳定性门槛并报告排除情况。

## 5. ROI 输出的公式解释

| 字段 | 公式/含义 |
|---|---|
| n_control、n_ko、n_tumor | 对照、KO 及二者之和 |
| p_control | n_control / n_tumor；有方向的来源暴露 |
| minority_fraction | min(n_control,n_ko) / n_tumor；对称混合度 |
| sample_group | low_control、low_ko 或 high_mixing |
| immune_fraction_all | 指定免疫标签细胞数 / ROI 全部细胞数 |
| immune_density_per_mm2 | 免疫细胞数 / (area_um2 / 10⁶) |
| count__标签 | 指定表型的真实计数 |
| fraction_all__标签 | 表型计数 / 全部细胞数 |
| density_per_mm2__标签 | 表型计数 / 面积 |
| n_overlapping_nominal_circles | 同图像中与该名义圆严格相交的其他保留圆数 |

1/20 对照和 19/20 对照都产生混合度 0.05，但方向性暴露分别是 0.05 和 0.95；测试专门验证二者没有混淆。

返回 `ROIResult`，其中 `table` 是保留 ROI，`exclusions` 是计数不足的窗口及原因，`membership` 是可选的 image/ROI/cell 对应表。没有肿瘤细胞的窗口被排除，不能通过填零伪装成“没有来源的有效 KO 窗口”。

名义圆重叠计数不是裁剪后真实多边形重叠，也不是独立性证明。保留 membership 可以检查共享细胞；正式空间相关分析仍需第 5 章的设计。

## 6. 最远点采样：覆盖优先，不保证独立

```python
from niche_idea import farthest_point_sample
selected = farthest_point_sample(result.table, n_per_group=20, seed=42)
```

函数分别在 image×sample_group 内采样，先随机选一个中心，再迭代挑选距离当前已选集合最远的候选。它不会重复选同一 ROI，但可能选中重叠圆，也不能消除大尺度组织相关性。

本函数对已经给定的候选表操作；不复制作者所有中心过滤、alpha-shape 或真实样本纳入流程。按组平衡抽样也不能用于直接推算整个组织各类生态位的实际覆盖比例。

## 7. 材料×背景或材料×药物：先形成供体级对比

`factorial_contrasts(data)` 需要：

```text
donor_id, matrix, context, value
```

`matrix/context` 用 0/1 编码；`value` 是事先规定尺度上的一个结局。技术重复可占多行，函数先在供体×条件内取平均。每位供体必须有完整 2×2 条件；缺失配对则报错。

```python
from niche_idea import factorial_contrasts, bootstrap_mean
assay = pd.read_csv('demo_output/synthetic_factorial.csv')
contrasts = factorial_contrasts(assay)
interval = bootstrap_mean(contrasts['interaction'].to_numpy(), n_boot=2000, seed=42)
```

每个供体的交互为：

```text
(材料=1、背景=1 - 材料=0、背景=1)
  - (材料=1、背景=0 - 材料=0、背景=0)
```

context 可以表示条件培养背景，也可以在另一个设计中表示 drug/vehicle，但不能把两种变量偷偷混为同一列。需在 metadata 中保存 0/1 的真实含义。

`bootstrap_mean` 只对独立生物学单位的对比重抽样，给出描述性百分位区间；不识别单位是否真的独立，不自动控制批次，也不提供机制因果 P 值。少于 10 个单位会警告。它不是第 5 章负二项混合模型或空间检验的实现。

## 8. 获取作者原始代码

```bash
python code/fetch_original_code.py --out original_code
```

脚本读取 [upstream_manifest.json](../provenance/upstream_manifest.json)，按固定 commit 获取 14 个源码/许可/说明文件，并对每个文件校验 Git blob SHA。原始 notebook 不被修改，另生成 `*.ipynb.source.txt` 方便阅读 code/markdown cells；该副本不包含保存输出和图片。

原文件若与本地已有文件不同，默认拒绝覆盖；需要有意替换时使用 `--overwrite`。阅读副本及 `fetch_report.json` 会更新，应避免在这些生成文件内保存手工注释。全部成功与部分失败在报告中区分，任何失败导致非零退出；没有 notebook 被自动执行。

本次受容器网络限制，**没有完成该脚本对远程全部文件的端到端下载测试**。其本地 SHA、路径保护、冲突行为与 notebook 源码提取已测试；源码事实通过 GitHub 连接器读取。两种验证不应混为一谈。

## 9. 测试覆盖与没有覆盖的内容

测试覆盖：非负表达/整数 counts、无阳性条件均值、无恶性输入、重复 ID、同坐标不同图像不混算、有效面积与密度、显式免疫定义、零分母、方向性暴露与对称混合度、重叠/membership、采样可复现、供体配对、bootstrap、Git 哈希与路径、错误源码片段解析。

没有覆盖：真实恶性注释质量、原始图像配准/分割、抗体门控真实性、特定材料机制、完整作者 notebook 执行、Fig. 5l 原始拟合、患者数据重分析、所有 Python/依赖版本组合，以及整套统计模型的性能。

本次 28 项测试通过的准确含义是：**这些已列明的程序行为在记录环境下符合测试定义。**不意味着生物学结论经过计算“认证”。

## 10. 交接时最低限度保留什么？

保留真实输入表示、患者/图像映射、物理单位、标签字典、面积掩膜与细胞纳入一致性、完整排除表、样本级结果、真实运行版本及随机种子。将新的统计模型写成独立可审阅步骤，不要把拟合结果和曲线硬编码进演示。

作者方法、我们的修正建议、教学简化与未来扩展分别存放并明确命名，才能让下一位读者知道自己正在复现什么、改变什么，以及尚未验证什么。
