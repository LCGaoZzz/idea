#!/usr/bin/env python3
"""Offline audit helpers, not an implementation or reproduction of KPSpatial."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

PINNED_PUCK_BLOB = "75b5f677202c1655fba4a7281df9cdd82261d403"
REQUIRED_SAMPLE_FIELDS = ("sample_id", "animal_id", "tumor_id", "section_id", "stage", "assay_batch")


def read_tsv(path: Path, required: tuple[str, ...]) -> list[dict[str, str]]:
    """Reject ambiguous tables rather than inferring delimiters or missing identities."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None or not set(required).issubset(reader.fieldnames):
            raise ValueError(f"Missing columns or wrong delimiter; required: {required}")
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError("Duplicate column names")
        rows = []
        for line, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Malformed row at line {line}")
            clean = {key: value.strip() for key, value in row.items()}
            if any(not clean[key] for key in required):
                raise ValueError(f"Required value is empty at line {line}")
            rows.append(clean)
    if not rows:
        raise ValueError("Header-only template is not study data")
    return rows


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def audit_puck(path: Path) -> dict:
    """Count this public file only; it is not a census of all paper experiments."""
    data = path.read_bytes()
    actual = git_blob_sha1(data)
    if actual != PINNED_PUCK_BLOB:
        raise ValueError(f"Public metadata bytes differ from pinned blob: {actual}")
    rows = read_tsv(path, ("Puck", "ID", "Mouse"))
    if len({row["Puck"] for row in rows}) != len(rows):
        raise ValueError("Duplicate array identifiers")
    platforms = Counter()
    tags_mice = set()
    for row in rows:
        if row["ID"].startswith("S-seq "):
            platforms["Slide-seq"] += 1
        elif row["ID"].startswith("S-tags "):
            platforms["Slide-tags"] += 1
            tags_mice.add(row["Mouse"])
        else:
            raise ValueError(f"Unexpected platform label: {row['ID']}")
    return {
        "scope": "puck_meta.txt only; not the complete paper cohort",
        "bytes": len(data), "git_blob_sha1": actual,
        "sha256": hashlib.sha256(data).hexdigest(),
        "arrays": len(rows), "platform_counts": dict(platforms),
        "unique_mouse_ids": len({row["Mouse"] for row in rows}),
        "slide_tags_mouse_ids": sorted(tags_mice),
        "arrays_per_mouse": dict(sorted(Counter(row["Mouse"] for row in rows).items())),
    }


def leaves_to_remove(all_leaves: list[str], keep: list[str]) -> list[str]:
    """Set-contract example; no Cassiopeia tree is loaded or pruned here."""
    if len(set(all_leaves)) != len(all_leaves) or len(set(keep)) != len(keep):
        raise ValueError("Duplicate leaf identifiers")
    if not keep:
        raise ValueError("Empty group")
    unknown = set(keep) - set(all_leaves)
    if unknown:
        raise ValueError(f"Unknown leaves: {sorted(unknown)}")
    return sorted(set(all_leaves) - set(keep))


def audit_samples(path: Path) -> dict:
    """Screen design metadata; passing is not proof of statistical identifiability."""
    rows = read_tsv(path, REQUIRED_SAMPLE_FIELDS)
    if len({row["sample_id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate sample_id; define one row per profiled section/sample")
    tumor_animals: dict[str, set[str]] = defaultdict(set)
    section_tumors: dict[str, set[str]] = defaultdict(set)
    stage_animals: dict[str, set[str]] = defaultdict(set)
    batch_stages: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        tumor_animals[row["tumor_id"]].add(row["animal_id"])
        section_tumors[row["section_id"]].add(row["tumor_id"])
        stage_animals[row["stage"]].add(row["animal_id"])
        batch_stages[row["assay_batch"]].add(row["stage"])
    errors = []
    if any(len(values) != 1 for values in tumor_animals.values()):
        errors.append("tumor_id maps to multiple animals; use globally unique tumor IDs")
    # Sections can legitimately contain multiple tumors; expose this, do not reject it.
    multi_tumor_sections = sorted(key for key, value in section_tumors.items() if len(value) > 1)
    warnings = []
    if len(stage_animals) < 2:
        warnings.append("Only one stage; no stage contrast available")
    if any(len(values) < 2 for values in stage_animals.values()):
        warnings.append("At least one stage has fewer than two animal IDs; this is not a power calculation")
    nested = len(stage_animals) > 1 and all(len(values) == 1 for values in batch_stages.values())
    if nested:
        warnings.append("Every assay batch belongs to one stage: stage cannot be separated from unrestricted fixed batch effects")
    return {
        "scope": "design screening only; no expression analysis or causal estimate",
        "sample_rows": len(rows), "animal_ids": len({row["animal_id"] for row in rows}),
        "animals_per_stage": {key: len(value) for key, value in sorted(stage_animals.items())},
        "stage_determined_by_batch": nested, "multi_tumor_sections": multi_tumor_sections,
        "errors": errors, "warnings": warnings,
        "limitations": "Does not resolve pairing, longitudinal attrition, power, spatial dependence or unmeasured confounding",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--puck-meta", type=Path)
    parser.add_argument("--samples", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.puck_meta is None and args.samples is None:
        parser.error("Provide --puck-meta and/or --samples")
    result: dict = {"scientific_reproduction": False, "checks": {}, "errors": []}
    for key, path, function in (("public_metadata", args.puck_meta, audit_puck), ("sample_design", args.samples, audit_samples)):
        if path is None:
            continue
        try:
            result["checks"][key] = function(path)
            result["errors"].extend(result["checks"][key].get("errors", []))
        except (OSError, UnicodeError, ValueError, csv.Error) as exc:
            result["errors"].append(f"{key}: {exc}")
    result["ok"] = not result["errors"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
