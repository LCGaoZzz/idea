# transfer/｜PreGame 证据包一次性导入暂存

本目录是一次性受控导入通道，配合仓库根 [.github/workflows/import-pregame-evidence-20260918.yml](../../.github/workflows/import-pregame-evidence-20260918.yml) 使用：

- `PreGame_Nature_2026_evidence_bundle.zip`：用户交付的原始证据包字节，未做任何改动。
- `import_bundle.py`：恢复与校验脚本（仅 Python 标准库）。验证 ZIP 哈希与包内 `SHA256SUMS`，把完整树解包到 `../evidence_bundle/`，落位导航 `../README.md` 与 `../AGENTS.md`，写 `../integrity/import_verification.json`，并注册根目录 `README.md`、`CATALOG.md`、`catalog.json`。任何不一致都会非零退出且不改动仓库文件。
- `READY.json`：导入标记与期望哈希；本文件被推送到 main 即触发工作流，由 CI 执行脚本并提交校验后的文件。
- `kb_README.md` / `kb_AGENTS.md`：脚本落位到上一级目录的导航文档母本。

导入完成后本目录整体保留，作为交付字节与校验逻辑的审计记录；再次运行脚本可重复校验。手动重校验：在仓库根目录运行 `python3 2026-09-pregame-gammadelta-tcr-nature-2026-kb/transfer/import_bundle.py`。
