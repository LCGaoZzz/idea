# 导入范围与版本区别

本目录将已有论文重建包整理为可直接在GitHub阅读、检索和交给Agent使用的知识库。**这次是知识库核心内容导入，不是原ZIP的完整备份。**

## 原始交付物身份

- 文件名：`CAF_spatial_2025_audit_v1.zip`
- 大小：214770字节；含46个文件。
- SHA256：`d6ffc84218db17dabc90c25f06b781e1b3f6dd3d99f48d3bef3177c6821ef53b`
- 来源：本次对话前一轮交付的论文重建/审计包。原ZIP仍是独立的对话附件，本目录没有上传该ZIP。

## 已原字节导入

24个文件覆盖：中文主报告、来源边界、3份知识章节、3份方法章节、作者报告参数、论文身份与参考文献、50条参数事实、短原文片段、部分图注事实、候选空仓库记录、数据与补充材料索引、样本模板、诊断代码/结果/回执/说明，以及原独立审核提示词。完整文件名和SHA256见 [IMPORTED_SHA256SUMS](integrity/IMPORTED_SHA256SUMS)。

24份文件均逐字节保留，没有为简化知识库而改写其历史证据或原诊断记录。新增的导航、AGENTS、分析简表和导入验证记录属于本次知识库整理，不冒充原始作者或前次审计输出。

## 没有原字节导入的22个原包文件

```text
AGENTS.md
DELIVERY.md
READING_GUIDE.html
REPORT.md
REVIEW_GUIDE.md
SHA256SUMS
acquisition_log.json
diagnostics/stderr.log
integrity/html_render_check.json
integrity/user_bundle_inspection.json
integrity/validation_tool_origin.json
package_manifest.json
reconstruction_manifest.json
source_inventory.json
tools/restore_review_captures.py
traceability.tsv
validation_report.json
validation_tool/schemas/reconstruction_manifest.schema.json
validation_tool/scripts/execution_contract.py
validation_tool/scripts/package_reconstruction.py
validation_tool/scripts/validate_reconstruction.py
working_state.json
```

其中原`AGENTS.md`被本次专用知识库入口替代；原`READING_GUIDE.html`的合并阅读用途由README和分章节Markdown承担，但HTML文件本身未上传。完整清单的27个分析目标和原状态另行抽取为`evidence/analysis_index.json`，仅是便于检索的派生简表，不与原`reconstruction_manifest.json`等价。

原通用验证器、完整运行状态/追踪账本未在此版本中导入。不能在本目录直接执行原审核提示词中的`tools/restore_review_captures.py`或`validation_tool/...`命令。它们需要完整原ZIP，详见 [知识库版审核说明](review/README.md)。

## 如何理解保留文档中的原路径

为了保持原字节与历史审计可核对，`ARTICLE_REVIEW_ZH.md`、`PROVENANCE.md`、`review/FABLE51_REVIEW_PROMPT.md`等保留了对原包文件的说明。这些地方的“本包”、`SHA256SUMS`、`traceability.tsv`、完整manifest和通用验证器，指的是原ZIP，不表示相应文件已存在于本知识库。

本知识库的有效导航以README、AGENTS和knowledge_index为准。不得把找不到的原包文件当成已读、已执行，或根据文件名自行补写内容。

## 两类验证严格分开

前次交付的18项诊断结果和运行回执是历史记录。本次另外对24个导入文件做了远端Git blob与原ZIP字节一致性核对，并重新运行同一诊断代码，18/18通过；本次记录见`integrity/import_verification.json`。

本次没有重跑原包通用验证器、没有重新检索全文与补充材料、没有执行论文生物学复现。原包的“26个受阻、1个材料冲突”按原记录保留，并不因为上传GitHub而升级证据等级。

## 权利与传播

本目录不包含论文完整PDF、补充表原件、患者原始数据或作者受限代码；引用和方法材料保持其原权利。原工作流的通用验证器也未在这里重新分发。来源哈希只绑定具体文件版本，不赋予任何额外版权许可。
