# 独立审核工具，不是作者代码

源文件在 `../scripts/`。仅使用Python标准库；当前测试环境见audit/arithmetic_checks.json。

```bash
python -m unittest discover -s tests -v
python scripts/arithmetic_audit.py --input tables/S4_manual_transcription.tsv --output audit/arithmetic_checks.json
python scripts/audit_candidate_table.py --input YOUR_CELL_TABLE.tsv --output audit/your_table_audit.json
python tools/reconstruction_protocol/scripts/validate_reconstruction.py --project-dir . --write-report
```

表审计器要求单个CV split、一行一个细胞。clone_id必须是稳定配对受体身份，不能使用在每个样本中重置的整数。label严格区分TR/NTR/borderline/unknown/expression_failure；训练/测试仅允许前两者。未测克隆不能自动当NTR。工具只检验你提供的标识是否自洽，不从测序中恢复生物学真相，也不实现随机森林。

辅助代码无随机过程，不需要随机种子；原作者模型种子未知，不能用本工具的确定性掩盖该缺口。18项合成测试通过仅说明这些检查器对列明场景工作。
