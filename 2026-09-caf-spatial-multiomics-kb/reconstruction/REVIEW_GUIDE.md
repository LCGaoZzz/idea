# 阅读与复核入口

**目标**：Liu et al., Cancer Cell (2025), DOI 10.1016/j.ccell.2025.03.004。审阅日期2026-09-15。

## 先看什么

直接用浏览器打开 `READING_GUIDE.html`：它把主报告、研究逻辑、数学方法、统计审计、Xenium迁移、补全预处理和复核说明汇成单文件。文章事实、数学推导、迁移建议均按来源边界区分。网页不依赖网络脚本；公式以原始可复制LaTeX文本保存，不调用外部渲染器。

独立审核先看 `PROVENANCE.md` 和 `review/FABLE51_REVIEW_PROMPT.md`。逐条证据映射看 `traceability.tsv`，可计算状态看 `reconstruction_manifest.json`。不要把机器验收通过当成论文结论正确。

## 当前完成与未完成

形成27个分析目标记录与50条参数/结果事实索引；每个目标有8个审计维度的状态记录，共216条。**216条不是216项实证验证**，多数记录因缺原代码/输入处于受阻状态。26个目标受阻，1个存在IMC计数文字冲突；未执行论文生物学重分析。

自写数学诊断18项实际通过。它们只检验合成例子和辅助函数，不是复现了18张图或验证了18项论文结论。

## 解压后的复核

先验证交付文件原始哈希，再运行会产生新文件的命令。在Linux/macOS环境可执行：

```bash
sha256sum -c SHA256SUMS
python tools/restore_review_captures.py
python validation_tool/scripts/validate_reconstruction.py --project-dir . --write-report
python diagnostics/diagnostic_examples.py
```

验证器需要 `jsonschema`；诊断和事实副本恢复只需Python标准库。正式验证器已从用户上传包原样保留；其来源哈希记录在 `integrity/validation_tool_origin.json`。

打包器默认排除 `sources/` 的原始源材料，包括上传工作流副本。为可移交复核，`evidence/` 保留的是**本次手工整理的事实笔记**；恢复脚本仅把这四份已有笔记复制到清单要求的位置，并核对哈希。它不会凭空恢复论文PDF、补充表、作者代码或数据。验证成功也只认证这一来源受限的记录合同。

`REPORT.md` 是从manifest派生的严格机器报告；不要把任意段落插入它。自由文本解读放在ARTICLE_REVIEW_ZH.md和knowledge/methods目录。

## 文件导航

| 文件/目录 | 用途 |
|---|---|
| ARTICLE_REVIEW_ZH.md | 主判断、竞争解释、逐图逻辑与核心问题 |
| knowledge/01_research_logic.md | 研究设计及因果解释边界 |
| methods/01_mathematical_reconstruction.md | 邻域、NMF、图、Visium、距离与几何 |
| knowledge/02_statistics_audit.md | 伪重复、组成、循环验证、生存与多重检验 |
| methods/03_preprocessing_and_expression.md | 最终补全SCTransform/RPCA及Xenium表达链 |
| knowledge/03_xenium_transfer.md | 新项目的条件比较与阴性区域策略 |
| methods/02_reproduction_blueprint.md | 输入合同、待索取项目和停机边界 |
| evidence/ | 事实笔记、主来源索引、图注覆盖与极短原文 |
| diagnostics/ | 自写代码、真实输出与执行回执 |
| data/ | 数据入口与未取得的补充材料索引 |
| review/ | 给独立审核者的反驳式核查要求 |

## 关键限制

未取得原论文连续全文文件、全部原图及补充文件，也未取得原作者活动代码和生物学输入。已读的是公开作者接受稿的工具可见长文本片段及有针对性的补充检索。原始材料无法取得，不允许被“常规方法”补齐。本报告最重要的下一步是对照最终论文/补充和作者代码逐项裁定，而非相信本包的结论。
