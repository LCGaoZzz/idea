#!/usr/bin/env python3
"""One-off verified import of the PreGame / Nature 2026 evidence bundle.

Restores and verifies the delivered ZIP, extracts the complete tree into
``../evidence_bundle/``, stages the navigation README/AGENTS, writes the
integrity record, and registers the knowledge base in the repository root
README.md, CATALOG.md and catalog.json.

Runs in GitHub Actions from the repository root (see
.github/workflows/import-pregame-evidence-20260918.yml) and is safe to
re-run manually from the repository root. Uses only the Python standard
library. Any inconsistency exits non-zero before touching repository files.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

KB_DIR_NAME = "2026-09-pregame-gammadelta-tcr-nature-2026-kb"
BUNDLE_NAME = "PreGame_Nature_2026_evidence_bundle.zip"
EXPECTED_SHA256 = "4700b548e0d245598366e80f0f527ea9e46862a40e587abdd75587533b5d207f"
EXPECTED_SIZE = 447_834
EXPECTED_MEMBERS = 44
EXPECTED_SHA256SUMS_ENTRIES = 43

ROOT_README_BULLET = (
    "- [PreGame：多发性骨髓瘤的广谱肿瘤反应性 γδ TCR]"
    "(2026-09-pregame-gammadelta-tcr-nature-2026-kb/README.md)："
    "基于 Nature 2026 论文的完整 44 文件证据分层重建包，含中文深度解读、图集、"
    "数学审计、复现路线图、参数与冲突清单及独立算术检查；作者代码与受控数据未取得，"
    "非生物学复现。"
)

ROOT_CATALOG_SECTION = """## 免疫学 → γδ TCR 与肿瘤反应性受体挖掘

| 资源 | 主用途 | 交叉标签 |
|---|---|---|
| [PreGame γδ TCR：Nature 2026 完整证据包](2026-09-pregame-gammadelta-tcr-nature-2026-kb/README.md) | γδ TCR 挖掘、PreGame 模型边界、统计审计与复现路线的完整 44 文件归档；作者 Zenodo 代码与受控数据未取得，非生物学复现 | multiple-myeloma、γδ T 细胞、PreGame、随机森林、TCR 挖掘、methodology-audit、evidence-bundle、agent-kb |

"""

CATALOG_JSON_ENTRY = {
    "path": KB_DIR_NAME,
    "title": "PreGame γδ TCR：骨髓瘤广谱肿瘤反应性受体完整证据包",
    "primary_classification": [
        "immunology",
        "gd-tcr"
    ],
    "tags": [
        "gamma-delta-TCR",
        "multiple-myeloma",
        "PreGame",
        "random-forest",
        "TCR-mining",
        "methodology-audit",
        "evidence-bundle",
        "agent-kb"
    ],
    "doi": "10.1038/s41586-026-11055-9",
    "edition": "complete_evidence_bundle_archive",
    "evidence_status": "source-limited literature reconstruction; author code/data not obtained; no biological reproduction",
    "entrypoint": "README.md",
    "delivered_member_count": 44
}


def fail(message: str) -> None:
    print(f"import_bundle: FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main() -> None:
    transfer_dir = Path(__file__).resolve().parent
    kb_dir = transfer_dir.parent
    repo_root = kb_dir.parent

    for name, path in (
        ("repository root", repo_root),
        ("knowledge base directory", kb_dir),
    ):
        if not path.is_dir():
            fail(f"expected {name} at {path}")

    bundle_path = transfer_dir / BUNDLE_NAME
    ready_path = transfer_dir / "READY.json"
    for required in (bundle_path, ready_path,
                     transfer_dir / "kb_README.md",
                     transfer_dir / "kb_AGENTS.md"):
        if not required.is_file():
            fail(f"missing transfer file: {required.name}")

    # ---- 1. Verify the delivered bundle bytes against READY.json ----------
    ready = json.loads(ready_path.read_text(encoding="utf-8"))
    bundle_bytes = bundle_path.read_bytes()
    actual_sha256 = sha256_bytes(bundle_bytes)
    if actual_sha256 != EXPECTED_SHA256:
        fail(f"bundle sha256 mismatch: expected {EXPECTED_SHA256}, got {actual_sha256}")
    if len(bundle_bytes) != EXPECTED_SIZE:
        fail(f"bundle size mismatch: expected {EXPECTED_SIZE}, got {len(bundle_bytes)}")
    if ready.get("bundle_sha256") != EXPECTED_SHA256:
        fail("READY.json bundle_sha256 does not match the pinned digest")
    print(f"bundle sha256 ok: {actual_sha256}")

    # ---- 2. Verify the internal SHA256SUMS against the zip members --------
    try:
        archive = zipfile.ZipFile(bundle_path)
    except zipfile.BadZipFile as error:
        fail(f"bundle is not a valid zip archive: {error}")

    with archive:
        members = archive.namelist()
        if len(members) != EXPECTED_MEMBERS:
            fail(f"expected {EXPECTED_MEMBERS} zip members, got {len(members)}")
        if len(set(members)) != len(members):
            fail("duplicate zip member names")
        for name in members:
            if name.startswith("/") or ".." in Path(name).parts or "\\" in name or not name:
                fail(f"unsafe zip member path: {name!r}")

        if "SHA256SUMS" not in members:
            fail("bundle does not contain SHA256SUMS")
        sums_text = archive.read("SHA256SUMS").decode("utf-8")
        declared: dict[str, str] = {}
        self_digest_declared: str | None = None
        for line in sums_text.splitlines():
            line = line.strip()
            if not line:
                continue
            digest, _, name = line.partition("  ")
            name = name.lstrip("*")
            if name == "SHA256SUMS":
                self_digest_declared = digest
                continue
            declared[name] = digest
        if len(declared) != EXPECTED_SHA256SUMS_ENTRIES:
            fail(f"expected {EXPECTED_SHA256SUMS_ENTRIES} SHA256SUMS entries, got {len(declared)}")
        member_set = set(members)
        if member_set != set(declared) | {"SHA256SUMS"}:
            fail("SHA256SUMS entries do not match the zip member list")
        mismatches = [
            name for name, digest in declared.items()
            if sha256_bytes(archive.read(name)) != digest
        ]
        if mismatches:
            fail(f"sha256 mismatch inside bundle: {mismatches}")
        self_note = (f"self entry declared as {self_digest_declared}, not recomputable"
                     if self_digest_declared else "no self entry present")
        print(f"internal SHA256SUMS verified: {len(declared)}/{len(declared)} entries ({self_note})")

        # ---- 3. Restore the complete tree into ../evidence_bundle/ ---------
        evidence_dir = kb_dir / "evidence_bundle"
        if evidence_dir.exists():
            shutil.rmtree(evidence_dir)
        evidence_dir.mkdir(parents=True)
        archive.extractall(evidence_dir)
        restored = sorted(p.relative_to(evidence_dir).as_posix() for p in evidence_dir.rglob("*") if p.is_file())
        if restored != sorted(members):
            fail("restored file tree does not match the zip member list")
        print(f"restored {len(restored)} files into {evidence_dir.relative_to(repo_root)}")

    # ---- 4. Stage navigation documents ------------------------------------
    write_text(kb_dir / "README.md",
               (transfer_dir / "kb_README.md").read_text(encoding="utf-8"))
    write_text(kb_dir / "AGENTS.md",
               (transfer_dir / "kb_AGENTS.md").read_text(encoding="utf-8"))

    # ---- 5. Write the integrity record ------------------------------------
    verification = {
        "schema_version": "1.0",
        "tool": f"{KB_DIR_NAME}/transfer/import_bundle.py",
        "run_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bundle_file": BUNDLE_NAME,
        "bundle_sha256": EXPECTED_SHA256,
        "bundle_size_bytes": EXPECTED_SIZE,
        "zip_member_count": EXPECTED_MEMBERS,
        "internal_sha256sums_entries_verified": EXPECTED_SHA256SUMS_ENTRIES,
        "internal_sha256sums_self_entry_declared": self_digest_declared,
        "internal_sha256sums_self_entry_note":
            ("self-referential entry cannot be recomputed from the file itself; recorded as declared"
             if self_digest_declared
             else "SHA256SUMS lists the 43 non-self members only; coverage is complete"),
        "restored_tree": "evidence_bundle/",
        "staged_documents": ["README.md", "AGENTS.md"],
        "root_files_registered": ["README.md", "CATALOG.md", "catalog.json"],
        "verified_by": "github-actions one-off import workflow (import-pregame-evidence-20260918)"
    }
    write_text(kb_dir / "integrity" / "import_verification.json",
               json.dumps(verification, ensure_ascii=False, indent=2) + "\n")

    # ---- 6. Register the knowledge base in the root navigation files ------
    root_readme = repo_root / "README.md"
    text = root_readme.read_text(encoding="utf-8")
    if KB_DIR_NAME not in text:
        anchor = "\n## 分类导航"
        if text.count(anchor) != 1:
            fail("root README.md anchor '\\n## 分类导航' not found exactly once")
        text = text.replace(anchor, ROOT_README_BULLET + "\n" + anchor, 1)
        write_text(root_readme, text)
        print("root README.md: added PreGame bullet under 研究 ideas")
    else:
        print("root README.md: entry already present, skipped")

    root_catalog = repo_root / "CATALOG.md"
    text = root_catalog.read_text(encoding="utf-8")
    if KB_DIR_NAME not in text:
        anchor = "## 按方法学问题进入新知识库"
        if text.count(anchor) != 1:
            fail("root CATALOG.md anchor '## 按方法学问题进入新知识库' not found exactly once")
        text = text.replace(anchor, ROOT_CATALOG_SECTION + anchor, 1)
        text = re.sub(r"更新：\d{4}-\d{2}-\d{2}",
                      f"更新：{datetime.now(timezone.utc):%Y-%m-%d}",
                      text, count=1)
        write_text(root_catalog, text)
        print("root CATALOG.md: added 免疫学 section and refreshed the update date")
    else:
        print("root CATALOG.md: entry already present, skipped")

    catalog_path = repo_root / "catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    entries = catalog.setdefault("entries", [])
    if any(entry.get("path") == KB_DIR_NAME for entry in entries):
        print("catalog.json: entry already present, skipped")
    else:
        entries.append(CATALOG_JSON_ENTRY)
        catalog["updated_on"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        write_text(catalog_path, json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
        print("catalog.json: registered the knowledge base entry")

    print("import_bundle: OK — bundle verified, tree restored, knowledge base registered")


if __name__ == "__main__":
    main()
