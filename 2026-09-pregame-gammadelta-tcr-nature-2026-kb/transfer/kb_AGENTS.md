# Agent 入口：PreGame / γδ TCR 完整证据包

先读 [evidence_bundle/AGENT_KNOWLEDGE_CARD.json](evidence_bundle/AGENT_KNOWLEDGE_CARD.json) 的 routing 与 do_not_claim，再按问题进入 `evidence_bundle/reports/` 四篇报告。本目录是完整交付归档的导航层，不是作者代码复现，也不是新的工作流引擎。

原始 ZIP 字节保全于 [transfer/PreGame_Nature_2026_evidence_bundle.zip](transfer/PreGame_Nature_2026_evidence_bundle.zip)；完整解包树在 [evidence_bundle/](evidence_bundle/)，44 个成员的哈希核验以包内 `SHA256SUMS` 与 [integrity/import_verification.json](integrity/import_verification.json) 为准。需要重新校验时在仓库根目录运行 `python3 2026-09-pregame-gammadelta-tcr-nature-2026-kb/transfer/import_bundle.py`。不要一次无差别加载 `evidence_bundle/reconstruction_manifest.json`（约 167 KB）或 `evidence_bundle/traceability.tsv`（约 62 KB），按 routing 指向分文件读取。

严格区分四类内容：论文正文/图注/审稿材料中已读取的事实；本包原创的算术检查与 18 项单元测试（不是作者代码）；`figures/` 中的教学性理论图（参数为显式假设）；迁移建议。作者 Zenodo 代码（`10.5281/zenodo.20028241`）、模型权重、原始矩阵与 source-data 均未取得；A01–A19 全部受阻，qualifying successful executions 为 0。

不得声称：PreGame 仅用 CDR3 序列预测；27 个有序特征已恢复；作者源码已审读或执行；0.864 是供者留出 AUROC；10/10 极端候选证明普遍准确；HLA-C/Bw4/KIR3DL1 安全性已临床确立；无配对 VDJ/ADT 的 Xenium 数据可直接兼容。

恢复优先级：安全获取 Zenodo 归档并记录哈希；恢复最终特征顺序、模型权重、候选检测标签与患者/时间点纳入矩阵；刷新 source_inventory 并重过校验门后再考虑执行作者代码。任何新材料与真实执行必须另登记来源、版本、权限、哈希与运行记录；保留原归档，不覆盖历史证据。
