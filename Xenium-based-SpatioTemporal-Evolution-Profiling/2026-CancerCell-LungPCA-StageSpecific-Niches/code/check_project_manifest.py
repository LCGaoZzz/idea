#!/usr/bin/env python3
"""Metadata-only design checks; no expression analysis or paper reproduction."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REQUIRED = ("animal_id", "sample_id", "section_id", "coordinate_frame_id",
            "stage", "batch_id", "panel_id")
DESIGNS = ("destructive", "longitudinal", "unknown")


def stage_components(rows: list[dict[str, str]], field: str) -> list[list[str]]:
    """Components of stages connected by shared batches/panels."""
    by_level: dict[str, set[str]] = defaultdict(set)
    stages = {r["stage"] for r in rows}
    for row in rows:
        by_level[row[field]].add(row["stage"])
    adjacency = {stage: {stage} for stage in stages}
    for linked in by_level.values():
        for stage in linked:
            adjacency[stage].update(linked)
    remaining, components = set(stages), []
    while remaining:
        stack, component = [min(remaining)], set()
        while stack:
            node = stack.pop()
            if node not in component:
                component.add(node)
                stack.extend(adjacency[node] - component)
        remaining -= component
        components.append(sorted(component))
    return sorted(components)


def audit(rows: list[dict[str, Any]], design: str, stages: list[str]) -> dict[str, Any]:
    if design not in DESIGNS or not stages or len(stages) != len(set(stages)):
        raise ValueError("Supply a supported design and distinct expected stage labels.")
    errors: list[str] = []
    warnings: list[str] = []
    valid: list[dict[str, str]] = []
    if not rows:
        errors.append("NO_DATA: manifest has no sample rows.")
    for number, row in enumerate(rows, start=2):
        if None in row:
            errors.append(f"EXTRA_FIELDS: line {number} has unlabelled values.")
        clean = {key: str(row.get(key) or "").strip() for key in REQUIRED}
        missing = [key for key, value in clean.items() if not value]
        if missing:
            errors.append(f"MISSING_FIELDS: line {number}: {','.join(missing)}")
            continue
        if clean["stage"] not in stages:
            errors.append(f"UNKNOWN_STAGE: line {number}: {clean['stage']}")
            continue
        valid.append(clean)
    sections: set[str] = set()
    sample_animals: dict[str, set[str]] = defaultdict(set)
    sample_stages: dict[str, set[str]] = defaultdict(set)
    animal_stages: dict[str, set[str]] = defaultdict(set)
    stage_animals: dict[str, set[str]] = defaultdict(set)
    for row in valid:
        if row["section_id"] in sections:
            errors.append(f"DUPLICATE_SECTION: {row['section_id']}")
        sections.add(row["section_id"])
        sample_animals[row["sample_id"]].add(row["animal_id"])
        sample_stages[row["sample_id"]].add(row["stage"])
        animal_stages[row["animal_id"]].add(row["stage"])
        stage_animals[row["stage"]].add(row["animal_id"])
    for sample, animals in sorted(sample_animals.items()):
        if len(animals) > 1:
            errors.append(f"SAMPLE_ANIMAL_CONFLICT: {sample}")
    for sample, values in sorted(sample_stages.items()):
        if len(values) > 1:
            errors.append(f"SAMPLE_STAGE_CONFLICT: {sample}")
    if design == "destructive":
        for animal, values in sorted(animal_stages.items()):
            if len(values) > 1:
                errors.append(f"DESTRUCTIVE_ANIMAL_REUSED: {animal}")
    elif design == "unknown":
        warnings.append("DESIGN_UNKNOWN: independence/repeated measures is unresolved.")
    for stage in stages:
        n = len(stage_animals[stage])
        if n == 0:
            warnings.append(f"MISSING_STAGE: {stage}")
        elif n == 1:
            warnings.append(f"ONE_ANIMAL: {stage}; within-stage animal variability is not estimable.")
    components = {field: stage_components(valid, field) for field in ("batch_id", "panel_id")}
    for field, groups in components.items():
        if len(groups) > 1:
            warnings.append(f"DISCONNECTED_STAGE_{field.upper()}: stage contrasts between "
                            "components are not separable from unrestricted fixed effects "
                            f"of {field}; inspect design, not just batch correction.")
    return {
        "scope": "metadata_only_not_biological_validation",
        "valid_metadata": not errors,
        "design": design,
        "expected_stages": stages,
        "rows_received": len(rows),
        "rows_with_required_fields": len(valid),
        "independent_animal_ids_by_stage": {s: sorted(stage_animals[s]) for s in stages},
        "animal_counts_by_stage": {s: len(stage_animals[s]) for s in stages},
        "stage_components": components,
        "errors": errors,
        "warnings": warnings,
        "not_checked": ["power", "expression", "cell_identity", "coordinates", "spatial_effects",
                        "tissue_area", "causal_effects", "author_pipeline", "joint_design_rank"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--design", choices=DESIGNS, required=True)
    parser.add_argument("--stages", nargs="+", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        raw = args.manifest.read_bytes()
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), delimiter="\t")
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)) or not set(REQUIRED).issubset(headers):
            raise ValueError("Manifest requires distinct headers including: " + ", ".join(REQUIRED))
        report = audit(list(reader), args.design, args.stages)
        report["manifest_sha256"] = hashlib.sha256(raw).hexdigest()
        report["python_version"] = sys.version.split()[0]
        output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8")
        else:
            print(output, end="")
        return 0 if report["valid_metadata"] else 2
    except (OSError, UnicodeError, ValueError, csv.Error) as exc:
        print(f"Manifest check failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
