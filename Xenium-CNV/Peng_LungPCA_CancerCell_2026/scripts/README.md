# 新增统计检查代码：只做明确规则，不冒充原论文流水线

[返回项目入口](../README.md) · [数学解释](../docs/03_cnv_and_identifiability.md) · [统计解释](../docs/04_statistics_and_measurement.md)

本目录代码是本项目新增的教学性工具 **[T]**，不是 `FuduanPeng/LungPCA_Code` 的原始源码，也不产生作者科学分析结果。所有测试是合成数据；没有作者或用户真实数据加载。

## 可以运行什么

在项目目录下：

```bash
python scripts/sensitivity_checks.py --demo
python -m unittest discover -s tests -v
```

需要可用的 Python、NumPy、SciPy。实际测试环境是 Python3.13.5、NumPy2.3.5、SciPy1.17.0；这是本次运行记录，不是作者环境锁定。没有执行自动安装，也没有证明所有其他版本兼容。空间索引接口见 [SciPy query_ball_point](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.cKDTree.query_ball_point.html)。

`--demo`只输出固定教学例子：相同99%比例因spot数不同而得到不同操作性克隆类别；独立二项假设下的未检出上限；BH算术；固定分子的比例变化。不读取任何真实数据文件。

## 函数合同

| 函数 | 用途 | 关键边界 |
|---|---|---|
| `classify_clone` | 形式化论文文字中的严格25/95规则 | 不是从counts推断CNA；零总数`not_observed`是新增防护 |
| `zero_detection_upper` | 独立同分布抽样且检测模型明确时的单侧上限 | 空间依赖使原始细胞数不能直接当n |
| `roe_counts` | 根据边际计算期望与observed/expected | 无空间零模型，无显著性；零期望返回NaN |
| `bh_adjust` | 给定完整p值族的BH算术 | 不修复基础p值偏差、选择偏差或任意依赖 |
| `radius_counts` | 在各动物／样本／空间域内按半径计数 | 明确μm、自身策略；不做边缘校正、面积密度或显著性 |
| `equal_host_contrast` | 先宿主内E-C，再宿主等权平均 | 描述性；无匹配、置信区间、空间依赖校正或因果估计 |

## 空间使用例子

```python
import sys
sys.path.insert(0, 'scripts')
from sensitivity_checks import radius_counts

result = radius_counts(
    coordinates=[[0, 0], [20, 0], [0, 0]],  # 合成μm坐标
    labels=['target', 'other', 'target'],
    spatial_keys=[('animal1', 'sample1', 'core1'),
                  ('animal1', 'sample1', 'core1'),
                  ('animal2', 'sample2', 'core1')],
    cell_ids=['c1', 'c2', 'c1'],
    radius_um=30,       # 演示用显式值，不是作者最终参数
    include_self=False, # 新分析选择；作者self规则未恢复
    target_label='target',
)
print(result.total, result.target, result.proportion)
```

同坐标但不同物理空间域的细胞不会成为邻居。重复的联合身份被拒绝；同一条码在不同空间域允许出现。坐标必须已经转换成μm，程序不能从数值自动识别单位。

每个空间域分别建cKDTree，查询以chunk执行，使用`return_length=True`，避免构造全局N×N距离矩阵和全部邻居列表。没有做百万细胞性能基准，不能宣传具体速度或资源保证。

`total=0`时比例为NaN，不能填0后直接计算平均；缺失处理应先决定并报告。`edge_policy='not_corrected'`明确提示没有组织掩膜／边缘校正。程序不会把截断圆当完整圆计算密度。

## 接入现有数据前必须做什么

先核验动物／切片／core映射、坐标单位、唯一ID、分割质量、标签定义和目标／对照共同支持。宿主对比函数假定输入行已经代表科学上可比较的对象，不会自动进行病理区域匹配。缺少比较组的宿主会被排除并记录；这也会改变目标总体，不能隐藏。

没有包含混合模型、空间置换、置信区间、CNA发现、程序打分、真实数据FDR或因果中介。需要这些功能时应另立明确估计目标与验证，不将本示例当成生产流水线。

## 测试状态

30项单元测试实际通过，涵盖严格阈值、零输入、非法值、Ro/e、BH、坐标域隔离、自邻居、精确半径边界、chunk一致性、目标缺失、重复ID和宿主等权。源码与测试文件的SHA256及Git blob校验值记录于 [validation_report.json](../tests/validation_report.json)。

测试通过仅说明这些特定检查通过，不等于算法在所有输入上正确，不等于统计假设在真实组织成立，更不等于本文主结论复现。
