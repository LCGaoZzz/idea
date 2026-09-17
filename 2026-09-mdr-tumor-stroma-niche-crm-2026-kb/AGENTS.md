# Agent 入口：MDR 肿瘤—基质界面生态位

先读 `IMPORT_SCOPE.md`、`evidence/scope_boundary.json` 和 `knowledge_index.json`，再按问题阅读 `knowledge/DEEP_REVIEW_ZH.md`。这是完整交付归档的导航层，不是新的工作流引擎。

完整日志、A01–A12 重建清单、traceability、工作状态与原创测试在 `archives/MDR_CellReportsMedicine_complete_evidence_20260917.tar.xz`；内部路径列于 `integrity/complete_bundle_manifest.json`。需要这些内容时先运行 `python integrity/verify_archive.py`，再解包到单独的 `complete_evidence/` 目录，读取其中 `agent/README.md` 和 `working_state.json`。不要一次无差别加载大型 manifest。

固定作者版本为 `KangjieShen/MDR_Code@f0fd6fc17654541fa97e49dbaf93cde583ee55a7`。原包不附作者源码字节；恢复源码时核对 `evidence/repository_file_manifest.json`，不要默认换成最新版本。

严格区分论文报告、公开代码实现、逻辑解释、迁移建议。正文/Methods/原图图注/补充材料与受控矩阵未取得；论文重建全部受阻；没有执行作者 R 脚本。9 个原创合成检查和结构验证不能升级为生物学复现。

后续优先补齐原文与图注，核对 Xenium 展示/统计分组、S12H 距离表来源、坐标与样本边界、临床 Cox 设计及跨模态状态映射。任何新材料和执行必须另登记来源、版本、权限、哈希与真实运行记录，保留原归档，不覆盖历史证据。
