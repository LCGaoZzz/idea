"""Fail-closed post-hoc screening. Not an implementation of the NISE queue."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class GatePolicy:
    protein_max_A: float
    ligand_max_A: float
    ligand_plddt_min: float
    min_pbind: float | None = None

    def __post_init__(self):
        for name in ("protein_max_A", "ligand_max_A"):
            value = getattr(self, name)
            if isinstance(value, bool) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"Invalid {name}")
        for name in ("ligand_plddt_min", "min_pbind"):
            value = getattr(self, name)
            if value is not None and (isinstance(value, bool) or not math.isfinite(value) or not 0 <= value <= 1):
                raise ValueError(f"Invalid {name}")
        if self.ligand_plddt_min is None:
            raise ValueError("ligand_plddt_min is required")


def _number(value, name):
    if isinstance(value, bool):
        raise ValueError(f"invalid:{name}")
    try:
        x = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"invalid:{name}") from None
    if not math.isfinite(x):
        raise ValueError(f"nonfinite:{name}")
    return x


def normalized_plddt(value, scale: str) -> float:
    if scale not in ("0-1", "0-100"):
        raise ValueError("invalid:plddt_scale")
    x = _number(value, "ligand_plddt") / (100 if scale == "0-100" else 1)
    if not 0 <= x <= 1:
        raise ValueError("invalid:ligand_plddt_range")
    return x


def evaluate_rows(rows, policy: GatePolicy):
    results, seen = [], set()
    required = ("protein_rmsd_A", "ligand_rmsd_A", "ligand_plddt", "plddt_scale",
                "mapping_valid", "burial_pass", "debug")
    for row in rows:
        cid = row.get("candidate_id")
        if not isinstance(cid, str) or not cid.strip() or cid in seen:
            raise ValueError("Each candidate_id must be a unique nonempty string")
        seen.add(cid)
        reasons = [f"missing:{key}" for key in required if key not in row]
        score = None
        for key, desired in (("mapping_valid", True), ("burial_pass", True), ("debug", False)):
            if key in row and (type(row[key]) is not bool or row[key] is not desired):
                reasons.append(f"failed:{key}")
        for key, threshold in (("protein_rmsd_A", policy.protein_max_A), ("ligand_rmsd_A", policy.ligand_max_A)):
            if key in row:
                try:
                    value = _number(row[key], key)
                    if value < 0 or value >= threshold:
                        reasons.append(f"failed:{key}")
                except ValueError as exc:
                    reasons.append(str(exc))
        if "ligand_plddt" in row and "plddt_scale" in row:
            try:
                score = normalized_plddt(row["ligand_plddt"], row["plddt_scale"])
                if score < policy.ligand_plddt_min:
                    reasons.append("failed:ligand_plddt_min")
            except ValueError as exc:
                reasons.append(str(exc))
        if policy.min_pbind is not None:
            try:
                p = _number(row.get("pbind"), "pbind")
                if not 0 <= p <= 1 or p < policy.min_pbind:
                    reasons.append("failed:pbind")
            except ValueError as exc:
                reasons.append(str(exc))
        results.append({"candidate_id": cid, "passed": not reasons,
                        "reasons": reasons, "ligand_plddt_01": score})
    return results


def _csv_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("Input CSV has no candidate rows")
    for row in rows:
        for key in ("mapping_valid", "burial_pass", "debug"):
            if key in row:
                token = row[key].strip().lower()
                if token not in ("true", "false"):
                    raise ValueError(f"{key} must be true or false, not {token!r}")
                row[key] = token == "true"
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--data-origin", choices=["synthetic_demo", "user_provided", "published_data"], required=True)
    args = parser.parse_args()
    policy = GatePolicy(**json.loads(args.config.read_text(encoding="utf-8")))
    results = evaluate_rows(_csv_rows(args.input), policy)
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"data_origin": args.data_origin, "analysis": "posthoc_gate_audit_not_model_inference",
              "policy": asdict(policy), "n_input": len(results), "n_passed": sum(r["passed"] for r in results),
              "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
              "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(), "rows": results}
    (args.output / "screening.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "n_input": report["n_input"], "n_passed": report["n_passed"]}))


if __name__ == "__main__":
    main()
