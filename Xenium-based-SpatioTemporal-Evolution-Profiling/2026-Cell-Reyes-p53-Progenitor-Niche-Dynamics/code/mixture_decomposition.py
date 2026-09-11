#!/usr/bin/env python3
"""New descriptive tool; NOT author code, state matching, or causal inference.

Input: complete animal-by-state profiles in TSV, positive-count rows only.
Each animal receives equal group weight. Missing state rows mean zero counts
only after the caller explicitly confirms complete profiles.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class Row:
    animal_id: str
    group: str
    state: str
    n: int
    mean: float


def read_rows(path: Path) -> list[Row]:
    required = {"animal_id", "group", "state", "n", "mean"}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Input must contain animal_id, group, state, n, mean")
        rows = []
        for number, record in enumerate(reader, 2):
            try:
                rows.append(Row(record["animal_id"].strip(), record["group"].strip(),
                                record["state"].strip(), int(record["n"]),
                                float(record["mean"])))
            except (ValueError, TypeError, AttributeError) as exc:
                raise ValueError(f"Invalid TSV row {number}: {exc}") from exc
    return rows


def decompose(rows: Sequence[Row], group_a: str, group_b: str,
              *, profiles_complete: bool = False) -> dict:
    """Return symmetric mixture/within-state terms; no p-values are computed."""
    if not profiles_complete:
        raise ValueError("Confirm complete profiles; absent states cannot be guessed")
    if not group_a or not group_b or group_a == group_b:
        raise ValueError("Two distinct nonempty groups are required")
    if not rows:
        raise ValueError("Input is empty")
    animals: dict[str, list[Row]] = {}
    animal_groups: dict[str, str] = {}
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if not row.animal_id or not row.state or row.group not in {group_a, group_b}:
            raise ValueError("Empty identifier or unexpected group")
        if isinstance(row.n, bool) or not isinstance(row.n, int) or row.n <= 0:
            raise ValueError("n must be a positive integer; omit true zero-count rows")
        if not math.isfinite(row.mean):
            raise ValueError("mean must be finite")
        key = (row.animal_id, row.state)
        if key in seen:
            raise ValueError("Duplicate animal-state row; aggregate sections explicitly")
        seen.add(key)
        previous = animal_groups.setdefault(row.animal_id, row.group)
        if previous != row.group:
            raise ValueError("This tool requires disjoint animal IDs across groups")
        animals.setdefault(row.animal_id, []).append(row)
    summaries = {}
    for group in (group_a, group_b):
        selected = [profile for animal, profile in animals.items()
                    if animal_groups[animal] == group]
        if not selected:
            raise ValueError(f"No animals for group {group}")
        weights: dict[str, list[float]] = {}
        contributions: dict[str, list[float]] = {}
        for profile in selected:
            total = sum(row.n for row in profile)
            for row in profile:
                weight = (row.n / total) / len(selected)
                weights.setdefault(row.state, []).append(weight)
                contributions.setdefault(row.state, []).append(weight * row.mean)
        w = {state: math.fsum(values) for state, values in weights.items()}
        c = {state: math.fsum(values) for state, values in contributions.items()}
        summaries[group] = {"n_animals": len(selected), "weights": w,
                            "means": {state: c[state] / w[state] for state in w},
                            "mean": math.fsum(c.values())}
    a, b = summaries[group_a], summaries[group_b]
    if set(a["weights"]) != set(b["weights"]):
        different = sorted(set(a["weights"]) ^ set(b["weights"]))
        raise ValueError("NO_COMMON_SUPPORT: group-exclusive states " + repr(different))
    terms = []
    for state in sorted(a["weights"]):
        wa, wb = a["weights"][state], b["weights"][state]
        ma, mb = a["means"][state], b["means"][state]
        terms.append({"state": state, "weight_a": wa, "weight_b": wb,
                      "mean_a": ma, "mean_b": mb,
                      "mixture": (wb - wa) * (ma + mb) / 2,
                      "within": (mb - ma) * (wa + wb) / 2})
    delta = b["mean"] - a["mean"]
    mixture = math.fsum(term["mixture"] for term in terms)
    within = math.fsum(term["within"] for term in terms)
    return {"method": "new_descriptive_symmetric_decomposition",
            "weighting": "equal_animals; within-animal observed-state frequencies",
            "causal_effect": False, "paper_reproduction": False,
            "profiles_complete_confirmed": True, "group_a": group_a, "group_b": group_b,
            "groups": summaries, "delta_b_minus_a": delta, "mixture_term": mixture,
            "within_term": within, "identity_residual": delta - mixture - within,
            "state_terms": terms,
            "limitations": ["No hypothesis test or confidence interval",
                            "Group-level state support does not ensure covariate overlap",
                            "Selected-state and sampled-tissue denominator only",
                            "No individual-cell transition or mediation is identified"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--group-a", required=True)
    parser.add_argument("--group-b", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--profiles-complete", action="store_true")
    args = parser.parse_args()
    try:
        result = decompose(read_rows(args.input), args.group_a, args.group_b,
                           profiles_complete=args.profiles_complete)
        payload = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("x", encoding="utf-8") as handle:
            handle.write(payload)
    except (OSError, ValueError, OverflowError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
