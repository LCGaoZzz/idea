# 06｜代码、输入合同与可执行路线

[上一章](05_research_proposal.md) · [目录](../README.md) · [下一章](07_statistics.md)

## 1. 两类代码必须分开

**官方模型代码**负责训练、序列/侧链设计、联合结构预测、NISE 迭代及对应下游分析。这里给出固定版本与真实入口，但本次未运行模型。

**本目录原创分析代码**负责质量守恒、几何一致性、筛选审计、局部概率比较与测试。它们已经在 CPU 环境运行，使用合成数据和单独标记的论文中心值算术；不含训练权重，不输出新的设计序列，不冒充原作者全流程。

## 2. 官方代码到科学步骤的映射

| 步骤 | 固定来源与入口 | 应阅读的内容 | 不应误解为 |
|---|---|---|---|
| NISE 候选与队列 | [S2 `run_nise_boltz2x.py`](../evidence/SOURCES.md) | `DesignCampaign`、`sample_sequences`、`identify_backbone_candidates`、`main` | 仅按一张分数表做 top-k |
| 命令行参数 | [S5 `run_nise_boltz2x_cli.py`](../evidence/SOURCES.md) | `build_parser`、输入准备、参数传递 | 原论文全部历史配置 |
| 单次/批量序列设计 | [S3 LASErMPNN](../evidence/SOURCES.md) | `run_inference.py`、`run_batch_inference.py` | 完成模型训练重建 |
| 局部校对 | [S4 `run_proofreading.py`](../evidence/SOURCES.md) | `get_forward_pass_probabilities`、`compute_conditional_probs` | 直接计算实验 ΔΔG |
| apixaban 完整 campaign | [S6 example_design_campaign](../evidence/SOURCES.md) | docking → NISE → 最终筛选的索引脚本 | 所有脚本无需适配即可跨机器运行 |
| 初始刚体对接 | [S7 CARPdock](../evidence/SOURCES.md) | 对接、位阻、埋藏、聚类 | 已核实全部原始对接参数 |
| 原始设计与分析 | [S8 Zenodo 18308430](../evidence/SOURCES.md) | 设计 PDB、原始分析和面板映射 | 本次已取得完整档案 |

NISE 固定版本为 `61b7500e99ab37295ae9510b3db05aefe6a5fdfb`，其 LASErMPNN 子模块为 `d7b6d2878391f91865fde524c941f661e84050f3`。前者为发表后的公开版本，不是已证明的论文历史环境。[S2,S3]

## 3. 源码中必须知道的行为

`compute_objective_function` 支持 ligand_pLDDT、ipTM、P(bind) 及若干简单组合；支持组合不意味着论文所有分支都采用该组合或同一权重。

`sample_sequences` 的 NLL 使用 log10；结合位点 NLL 与全序列 NLL 是不同集合的均值。空结合位点、概率为零或模型输出非有限值应另行检查，不能把 NaN 当作好的排序值。

`identify_backbone_candidates` 在蛋白对齐与配体原子映射后计算一致性；pLDDT 从 PDB 的 B-factor 读取再除以 100。埋藏/暴露约束集合为空时，不等于已检查论文特定官能团的约束。

`debug` 在一致性与埋藏判断中可放行；不允许把 debug 输出作为科学筛选通过记录。`keep_best_generator_backbone` 可能保留最能产生高分后代的父状态，而不是简单保留当前最高分结构。本目录筛选代码不复制这种队列语义。

Boltz 子进程存在 `check=False`、按文件存在判断和重试逻辑；文件存在、解析成功、结构合理应分别校验。结果字段 `rosetta_paths` 在该路径保存 Boltz 输出，不能仅按名字判断运行了 Rosetta。pandas pickle 不应从不可信来源直接加载。[S2]

## 4. 官方环境与可选择的最小真实运行

以下是**执行指导，不是已执行记录**。需要能够访问上游依赖和权重的计算环境。

```bash
git clone --recurse-submodules https://github.com/polizzilab/NISE.git
cd NISE
git checkout 61b7500e99ab37295ae9510b3db05aefe6a5fdfb
git submodule update --init --recursive
# 不要加 --remote，否则会改变子模块版本。
# 先审阅 setup.py 及依赖来源；它会下载并创建环境。
python setup.py
.venv/bin/python run_nise_boltz2x_cli.py --help
```

该版本安装脚本选择 Python 3.11、Torch 2.8.0、Boltz 2.2.1，并对部分依赖设置约束；这仍不是完整 lockfile。应记录实际解析出的全部依赖、CUDA 与驱动、模型权重 SHA-256 和随机性配置，而不是把脚本中的几条版本号当作论文完整环境。[S2 setup.py]

准备好一个具有正确配体化学状态的起始 PDB、对应 SMILES、配体标识和权重后，可做**单轮、小规模、非 debug**兼容性检查：

```bash
: "${INPUT_PDB:?set a reviewed input pose}"
: "${LIGAND_SMILES:?set chemically matching SMILES}"
: "${LIGAND_CODE:?set ligand code}"
: "${WEIGHTS:?set verified checkpoint path}"
: "${NEW_RUN:?set a new output directory}"
.venv/bin/python run_nise_boltz2x_cli.py \
  --input-pdb "$INPUT_PDB" --smiles "$LIGAND_SMILES" \
  --ligand-3lc "$LIGAND_CODE" --model-checkpoint "$WEIGHTS" \
  --output-dir "$NEW_RUN" --num-iterations 1 \
  --num-top-backbones-per-round 1 \
  --sequences-sampled-per-backbone 2 --sequences-sampled-at-once 2 \
  --objective-function ligand_plddt \
  --self-consistency-protein-rmsd-threshold 2.5 \
  --self-consistency-ligand-rmsd-threshold 2.5
```

上面的 1 轮、2 条序列和阈值是**兼容性测试配置**，不是论文复现预算。默认输入准备会进行配体质子化与 CONECT 处理；它不能替代对质子化、互变异构、手性及原子命名的化学审核。失败时保存完整日志，不通过打开 debug 或放宽阈值把失败改成通过。[S3,S5]

exatecan 历史 RFAA 分支需要相应历史脚本与配置，不能用这段 Boltz 指导冒充。没有 GPU/权重也可以运行下一节的分析测试。

## 5. 本目录代码的功能与限制

| 文件 / 函数 | 输入 | 输出 | 实际边界 |
|---|---|---|---|
| `geometry.py::kabsch` | 已匹配蛋白坐标 | 旋转、平移、RMSD | 不做 PDB 链/残基自动匹配 |
| `geometry.py::complex_rmsd` | 蛋白和配体对应坐标、可选合法原子映射 | 两种 RMSD、映射索引 | 不独立重新对齐配体；化学等价性由上游证明 |
| `screen.py::evaluate_rows` | 候选记录、明确门槛 | 每条候选通过状态和失败原因 | 事后筛选审计，不实现 NISE 历史队列 |
| `binding.py::bound_complex` | 总浓度、Kd，统一单位 | 1:1 结合复合物浓度 | 单位必须由调用方统一 |
| `binding.py::competition` | 蛋白、示踪物、竞争物与两个 Kd | 游离蛋白与两类复合物 | 一个竞争位点、平衡模型 |
| `fit_direct` / `fit_competition` | 已校准结合比例，初值与边界 | Kd、残差、数值状态 | 等方差最小二乘；无原始各向异性基线拟合与置信区间 |
| `proofreading_delta` | 四个条件概率 | holo 改善与 holo–apo 启发式差值 | 不输出自由能 |
| `mutant_cycle` | 亲本、单点、双点 Kd 与指定温度 | 严格可加预期与耦合 | 中心值算术，不检验显著性 |
| `wilson_interval` | 成功数与总数 | 描述性比例区间 | 忽略谱系相关性，不能代替分层分析 |

## 6. 从零运行轻量示例

```bash
cd nise-lasermpnn-2026
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/run_demo.py --output results/my_demo
python scripts/screen.py \
  --input results/my_demo/candidates.synthetic.csv \
  --config results/my_demo/gate_policy.json \
  --output results/my_screen --data-origin synthetic_demo
```

程序拒绝覆盖已存在的输出目录。示例 seed 固定为 20260911，几何、候选表和结合曲线明确标记为 synthetic。`demo_results.json` 将 synthetic 结果与 `published_point_estimates_derived_math_not_refit` 分开，后者仅对作者公布的中心值做代数计算。

主要输出：`demo_results.json`、`candidates.synthetic.csv`、`direct.synthetic.csv`、`competition.synthetic.csv`、`gate_policy.json`；筛选脚本输出 `screening.json`。不需要登录、不调用收费 API、不下载权重。

本次实际运行环境是 Python 3.13.5、NumPy 2.3.5、SciPy 1.17.0。它只证明轻量分析代码在这一环境通过测试，不代表上游生成模型兼容该环境。测试记录见 [checks](../checks/verification.md)。

## 7. 接入真实候选 CSV

必需字段：

```text
candidate_id,protein_rmsd_A,ligand_rmsd_A,ligand_plddt,plddt_scale,mapping_valid,burial_pass,debug
```

`candidate_id` 必须非空且唯一；布尔值使用 `true/false`；`plddt_scale` 只能为 `0-1` 或 `0-100`。若配置 `min_pbind`，还必须提供有效 `pbind`。缺失、非有限值、错误单位、debug 或映射失败都会被拒绝。RMSD 使用严格小于门槛；pLDDT 使用大于等于门槛。

`mapping_valid` 和 `burial_pass` 是上游校验结果，不得为了让程序运行而手工全填 true。本程序验证字段和筛选规则，不会神奇地从布尔值恢复原子或埋藏证据。完整真实流程应另附坐标、原子映射、计算方法和哈希。

```bash
python scripts/screen.py --input your_candidates.csv \
  --config your_reviewed_policy.json --output results/real_audit \
  --data-origin user_provided
```

本目录的 `configs/demo_gate_policy.json` 仅用于演示，**不应直接套作论文某一分支的历史门槛**。未知论文参数见 `configs/paper_profiles.json`。

## 8. 不应省略的真实数据适配

结构分析需要显式处理链编号、残基插入码、缺失残基、alternate location、氢、互变异构、手性与对称原子。该目录不提供一个表面通用却会猜测映射的 PDB 读取器。

拟合实验数据前，先恢复原始信号与基线、结合后的亮度变化、浓度校准、重复层级及全局共享参数。简单拟合函数不能复现所有原作者的 global fit；少量点收敛也不证明 pM Kd 被可靠辨识。统计限制见下一章。

随机性要分层记录：Python / NumPy / Torch、CUDA、dropout、解码顺序、结构预测采样与版本。上游未提供或未核实的 seed 不得编造；本目录只为自己的演示固定 seed。

[上一章](05_research_proposal.md) · [目录](../README.md) · [下一章：统计与定量解析](07_statistics.md)
