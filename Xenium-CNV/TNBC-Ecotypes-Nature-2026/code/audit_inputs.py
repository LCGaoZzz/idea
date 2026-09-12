#!/usr/bin/env python3
"""T-class input audit, not the paper's pipeline. Standard library only.

Required cells columns: individual_id,sample_id,stage,cell_id,lineage,state.
Required state-map columns: state,lineage. Optional x_um,y_um must occur together.
Outputs sample-level counts and explicit conditional denominators, never density.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path


def read_rows(path: Path, required: set[str]):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        if len(fields) != len(set(fields)):
            raise ValueError(f"{path.name}: duplicate column names")
        missing = required - set(fields)
        if missing:
            raise ValueError(f"{path.name}: missing columns {sorted(missing)}")
        for number, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{path.name}:{number}: inconsistent CSV width")
            yield number, {key: value.strip() for key, value in row.items()}


def audit_cells(cells: Path, state_map: Path) -> tuple[list[dict], dict]:
    mapping: dict[str, str] = {}
    for number, row in read_rows(state_map, {"state", "lineage"}):
        state, lineage = row["state"], row["lineage"]
        if not state or not lineage or state in mapping:
            raise ValueError(f"state-map:{number}: blank or duplicate state")
        mapping[state] = lineage
    if not mapping:
        raise ValueError("state-map has no states")
    required = {"individual_id", "sample_id", "stage", "cell_id", "lineage", "state"}
    sample_meta: dict[str, tuple[str, str]] = {}
    stages: dict[str, set[str]] = defaultdict(set)
    total: Counter = Counter()
    parents: Counter = Counter()
    numerators: Counter = Counter()
    seen: set[tuple[str, str]] = set()
    n_rows = 0
    for number, row in read_rows(cells, required):
        if any(not row[key] for key in required):
            raise ValueError(f"cells:{number}: blank required field; encode unresolved explicitly")
        individual, sample, stage = row["individual_id"], row["sample_id"], row["stage"]
        state, lineage = row["state"], row["lineage"]
        if mapping.get(state) != lineage:
            raise ValueError(f"cells:{number}: state absent from map or lineage mismatch")
        if sample in sample_meta and sample_meta[sample] != (individual, stage):
            raise ValueError(f"cells:{number}: sample maps to conflicting individual/stage")
        key = (sample, row["cell_id"])
        if key in seen:
            raise ValueError(f"cells:{number}: duplicate sample/cell key")
        has_x, has_y = "x_um" in row, "y_um" in row
        if has_x != has_y:
            raise ValueError("x_um and y_um must both be provided or both omitted")
        if has_x:
            try:
                valid_xy = all(math.isfinite(float(row[c])) for c in ("x_um", "y_um"))
            except ValueError:
                valid_xy = False
            if not valid_xy:
                raise ValueError(f"cells:{number}: non-finite or invalid coordinates")
        seen.add(key)
        sample_meta[sample] = (individual, stage)
        stages[individual].add(stage)
        total[sample] += 1
        parents[(sample, lineage)] += 1
        numerators[(sample, state)] += 1
        n_rows += 1
    if not n_rows:
        raise ValueError("cells file has no observations")
    records = []
    for sample in sorted(sample_meta):
        individual, stage = sample_meta[sample]
        for state, lineage in sorted(mapping.items()):
            n = numerators[(sample, state)]
            d = parents[(sample, lineage)]
            records.append(dict(individual_id=individual, sample_id=sample,
                                stage=stage, state=state, lineage=lineage,
                                numerator=n, lineage_denominator=d,
                                all_cells_denominator=total[sample],
                                within_lineage_fraction=n / d if d else None,
                                whole_sample_fraction=n / total[sample],
                                missing_reason="" if d else "parent_lineage_not_observed"))
    repeated = sorted(key for key, value in stages.items() if len(value) > 1)
    summary = dict(n_cells=n_rows, n_samples=len(sample_meta),
                   n_individuals=len(stages), n_defined_states=len(mapping),
                   individuals_observed_at_multiple_stages=repeated,
                   warnings=["Multiple stages in one individual: confirm repeated-measures design."] if repeated else [],
                   empirical_reproduction=False,
                   scope="ID, annotation-map and sample-level denominator audit only",
                   limitations=["No label truth check", "No tissue area or density calculation",
                                "No cross-section pooling", "No spatial or clinical inference",
                                "In-memory uniqueness set uses O(number of cells) memory"])
    return records, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cells", type=Path, required=True)
    parser.add_argument("--state-map", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        targets = [args.out / "sample_state_counts.csv", args.out / "input_audit.json"]
        if any(path.exists() for path in targets):
            raise ValueError("output files already exist; use a new output directory")
        records, summary = audit_cells(args.cells, args.state_map)
        args.out.mkdir(parents=True, exist_ok=True)
        with targets[0].open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)  # None becomes empty CSV field, not zero.
        targets[1].write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"INPUT_AUDIT_FAILED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
