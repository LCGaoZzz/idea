# DeepAudit bundle mirror inventory

Source attachment used for this mirror: `KPSpatial_DeepAudit_2026-09-16(1).zip`.

- Source ZIP size: 984,496 bytes
- Source ZIP SHA256: `2bd711c66ed0e16d2ff9df438405b5b8bf7f80f370684fc7f9a41ced76371ba0`
- Original extracted bundle contained about 85 files, including 12 chapter documents, combined HTML/Markdown readers, audit receipts, evidence/code excerpts, tables, tools, workflow files, manifests, traceability files, four SVG figures and four PNG renderings.

## Committed into this GitHub mirror

The repository mirror contains the substantive, directly reusable materials rather than only the earlier distilled summary:

- all 12 full chapter documents under `docs/`;
- `review/FABLE_REVIEW_PROMPT.md`;
- `REPORT.md`, `DELIVERY.md`, `SOURCES.md`, `sources_catalog.json` and third-party notices;
- audit scope, 22-check deep-audit receipt, 10-check rerun receipt, delivery checks and browser checks;
- byte-audited CNV permutation script, sample metadata, public CNV result table and code excerpts used by the audit;
- editable SVG versions of all four explanatory figures;
- auditable fixed-neighbor permutation helper and delivery checker;
- thin Agent/knowledge index for selective retrieval.

## Binary-container limitation of this upload pass

The GitHub connector available in this chat writes repository content through text/Git-data operations. In this pass I therefore **do not claim that the original binary ZIP container or all four PNG byte streams were committed byte-for-byte**. The source ZIP hash above identifies the exact user attachment used as the source of truth. The repository contains editable SVG equivalents for all four figures and the substantive text/code/audit content.

Likewise, the original combined `KPSpatial_深度解析.html` and `KPSpatial_深度解析.md` are represented in the repository by the complete 12-chapter `docs/` tree plus the repository navigation files; do not treat this mirror as byte-identical to the original ZIP. Claims of byte identity are made only where a specific audit file explicitly records and verifies it.

This distinction is intentional: the repository should remain auditable and should not imply that recording a checksum is equivalent to uploading the corresponding binary object.
