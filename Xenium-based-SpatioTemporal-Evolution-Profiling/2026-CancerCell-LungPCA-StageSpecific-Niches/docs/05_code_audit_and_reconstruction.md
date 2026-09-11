# 05｜固定版本代码审计与三条复现路线

[返回入口](../README.md) · [上一章](04_figure_to_code_map.md) · [下一章：五条启发](06_transferable_insights.md)

## 1. 实际核对范围

【C】作者固定提交为`fba87dbee8dbae497b15b81a4b0fa79edccd17b2`，提交时间2025-09-18；递归树含7个R脚本、6个Python脚本和README，无Data目录或完整依赖锁。源码在本次系列整理中通过GitHub连接器读取；本次重新取得固定树。没有下载完整原始矩阵、没有运行作者脚本、没有复算科学结果。[固定树](https://github.com/FuduanPeng/LungPCA_Code/tree/fba87dbee8dbae497b15b81a4b0fa79edccd17b2)

README仍使用in revision表述，指向Zenodo17148540；论文指向17172149。二者关系未确认。固定旧提交便于审计，不意味着这是最终发表版唯一正确版本。完整文件指纹见[code_inventory.tsv](../references/code_inventory.tsv)。

## 2. 公开代码做到了哪一层

| 层次 | 公开片段中的实际情况 | 判定 |
|---|---|---|
| 原始计数、图像分割与配准 | 方法文字与GUI路径，未见完整上游入口 | 不可据现有脚本重建 |
| QC、整合、聚类 | 多为已处理Seurat/AnnData对象 | 未复算 |
| CNA、NMF、拟时序、邻域构造 | 多为已存在标签和表 | 未复算 |
| 差异/富集/相关 | 部分为预计算表，部分制图时调用检验 | 应逐图区分 |
| 图层处理 | min–max、argmax、分位数分类 | 源码可直接审计 |
| COMMOT方向 | 已有对象上计算方向摘要 | 有活动计算，但不是完整求解 |
| 输出图 | ggplot/pheatmap/hexbin等 | 需匹配输入、环境才能重绘 |

【I】“全部都是截图”和“作者已公开端到端全部分析”都不准确。

## 3. 具体审计问题：证据、触发条件、影响和修复边界

### A01｜对象命名不一致：条件性运行障碍

【C】[Figure 1.R，Fig.1C段](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%201.R)读入`seurat_obj`，首个DimPlot引用`dseurat_obj`。

【I】若前面的RDA没有注入该名字，独立执行会受阻；但本次未检查RDA内部，不能声称已经看到报错。最小修复先列出加载对象，再核对是否应统一名字。不能盲目替换后把成功叫作原版直接可跑。

### A02｜变量与纵轴语义冲突

【C】[Figure 3.R，Fig.3M段](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%203.R)把`percentage`对应图标为KAC score，把`KAC_Score`对应图标为克隆比例。

【I】记录为标签语义冲突；是否影响正式发表图仍需正式图/制图记录。修标签不等于重算数据，更不能据此否定其他证据。

### A03｜时间标签冲突

【C】[Figure 7.R，Fig.7F段](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%207.R)的`mat_7mo`仍使用`ggtitle('3 months')`。

【I】应先核对对象时间字段，再改标题；不能用文件名字单独认证样本身份。

### A04｜未被当前调用触发的subset分支风险

【C】多份`plot_category`函数在`subset is not None`分支引用`score`，但类别函数使用的是`color_vector`，且类别向量未随坐标同步筛选。[例：Figure 2C.py::plot_category](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%202C.py)

【I】现有面板调用没有传subset，不能声称影响原论文。迁移复用时应先写包含subset的最小测试，再修正同一mask下的坐标和类别。

### A05｜离散类别进入hexbin的聚合风险

【C】`plot_category`把类别编号作为hexbin的C输入。Matplotlib官方文档说明默认reducer为mean。[官方文档](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.hexbin.html)

【I】若一个hex汇入多个不同类别，平均编号可能制造不存在的中间类别。若几何恰好一spot一hex则未必触发。不能把潜在风险写成已确认图像错误。应验证每hex映射，必要时使用离散聚合/直接几何绘制，并报告改动。

### A06｜独立颜色缩放不保留跨样本强度

【C】[Figure 1E 4F.py::plot_super](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%201E%204F.py)按每幅输入独立min–max。

【I】适于显示位置，不适于直接比较绝对强度。共享尺度只在原分数可比时有意义；不能靠统一色条补救本来不一致的输入。

### A07｜counts名字不认证counts语义

【C】[Figure 6G.py](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%206G.py)执行`input.layers['counts']=input.X`。

【I】赋值不能证明X是原始计数。需要对象来源与数据字典；即使这个赋值未影响当前绘图，也可能误导后续模块。

### A08｜双高叠加是相对阈值规则

【C】[Figure 6E 6F 7D.py，L55–77](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%206E%206F%207D.py#L55-L77)逐样本计算70/90分位；两个分数都严格高于各自90分位时特殊着色，都低于70分位时标黑，其他情况按最大原分数显示。

【I】这不是简单的“70–90分位区域”。需保留实际阈值、等于阈值的规则、缺失和并列最大处理。更多叠加不自动代表绝对信号更强，也不是随机重叠检验。

### A09｜输出目录与图状态依赖

【C】部分Python文件不自行创建Results；Fig.5E `ggsave`未明确传入plot=p。

【I】前者可能要求先运行其他脚本；后者依赖last_plot状态。尚未在目标环境观察实际错误。外层runner创建目录、显式传图属于工程修复，不能宣称改变了科学模型。

### A10｜显示参数容易被错抄为生物参数

【C】Fig.5E `adjust=15`是小提琴平滑；Fig.6G `k=5`是方向摘要；`normalize_v_quantile=0.995`是方向图相关归一化；`dpi/figsize`仅控制输出。[Figure 5.R](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%205.R)、[Figure 6G.py](https://github.com/FuduanPeng/LungPCA_Code/blob/fba87dbee8dbae497b15b81a4b0fa79edccd17b2/Figure%206G.py)

【I】不能把这些值混成邻域半径、通信求解距离或最终模型超参数。函数默认值只证明默认行为，除非活动调用和对象版本能定位才可谈论文设置。

### A11｜统计调用不是完整统计设计

【C】Fig.6J/K和Fig.7若干图调用两两t检验；Fig.4读取已有调整p值；Fig.5图注检验未在对应制图段完整出现。

【I】不能据局部代码断言整篇未校正，也不能据总体BH描述断言每项都正确校正。需要完整比较家族、原始p、调整p、配对/嵌套结构和生物单位。

### A12｜输入缺失、序列化与环境不可恢复

【C】仓库无Data、锁文件或统一上游入口；RDA还可能含预构建图与隐式对象。

【H】未知pickle或R序列化对象不应在主环境随意加载。先确认来源/指纹、隔离环境、列对象结构，再执行。不要先安装最新所有包，再将差异归咎于论文。

## 4. 三条复现路线要分别命名

**A：图重绘。** 取得固定脚本对应Data、依赖版本、对象字典后运行制图；验证的是图的产生，不是上游正确性。

**B：处理矩阵重建。** 从已公开counts、坐标、注释和病理区域恢复QC、NMF、CNA、邻域等；需要人工选择、基因集和完整参数。可以进行改进分析，但原版/改进版必须分支。

**C：原始测量重跑。** 还需读段/成像、分割、配准及计数配置；人类原始序列公开访问受隐私限制，不能默认所有GEO附件都是FASTQ。

## 5. 本项目没有做的事

未执行作者13个脚本；未读取作者Data；未计算任何论文p值；未运行任何用户Xenium；未改作者仓库；未声称修复了论文；未将旧档案的结构验证“通过”升级成生物学验证。

本目录的新工具只做设计检查/文档检查，并与原分析分开。未来取得输入时应记录原版运行结果、补丁、种子和输出hash，再决定能否把某个分析状态升级。
