#!/usr/bin/env python3
"""Seven synthetic decision examples. Not a reproduction of patient analyses.

Run from the idea directory: python code/decision_examples.py
Uses only the Python standard library and writes JSON to standard output.
A failed mathematical check exits nonzero; no files are overwritten.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import platform
from typing import Sequence


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-10)


def quantile(values: Sequence[float], p: float) -> float:
    """Finite linear interpolation, matching R type 7 for this finite example."""
    if not values or not 0 <= p <= 1 or not all(math.isfinite(x) for x in values):
        raise ValueError("Require nonempty finite values and p in [0, 1].")
    xs = sorted(values)
    h = (len(xs) - 1) * p
    lo = math.floor(h)
    hi = math.ceil(h)
    return xs[lo] + (h - lo) * (xs[hi] - xs[lo])


def run() -> dict:
    checks = []
    w0, w1 = [0.2, 0.8], [0.4, 0.6]
    mu0, mu1 = [10.0, 1.0], [12.0, 1.0]
    x0 = sum(w * m for w, m in zip(w0, mu0))
    x1 = sum(w * m for w, m in zip(w1, mu1))
    composition = sum((b - a) * (d + c) / 2 for a, b, c, d in zip(w0, w1, mu0, mu1))
    within = sum((d - c) * (b + a) / 2 for a, b, c, d in zip(w0, w1, mu0, mu1))
    require(close(x1 - x0, composition + within), "Symmetric decomposition failed")
    require(close(composition, 2.0) and close(within, 0.6), "Unexpected contributions")
    checks.append({"id": "D01", "passed": True, "baseline": x0, "followup": x1,
                   "composition_symmetric": composition, "within_symmetric": within})

    base_composition = sum((b - a) * c for a, b, c in zip(w0, w1, mu0))
    endpoint_within = sum(b * (d - c) for b, c, d in zip(w1, mu0, mu1))
    require(close(base_composition + endpoint_within, x1 - x0), "Reference decomposition failed")
    require(not close(base_composition, composition), "Attribution should depend on convention")
    checks.append({"id": "D02", "passed": True, "composition_reference": base_composition,
                   "within_reference": endpoint_within, "same_total_not_unique_attribution": True})

    target_count, parent0, parent1, area = 100, 200, 400, 2.0
    require(close(target_count / parent0, 0.5) and close(target_count / parent1, 0.25), "Wrong fractions")
    checks.append({"id": "D03", "passed": True, "within_parent_fractions": [0.5, 0.25],
                   "target_density_both_per_mm2": target_count / area,
                   "assumption": "equal fully observed areas and equal target counts"})

    radius_mm = 0.03
    densities = [100.0, 400.0]
    probabilities = [1 - math.exp(-lam * math.pi * radius_mm ** 2) for lam in densities]
    require(probabilities[1] > probabilities[0], "Density should increase contact opportunity")
    checks.append({"id": "D04", "passed": True, "radius_mm": radius_mm,
                   "target_density_per_mm2": densities, "at_least_one_neighbor_probability": probabilities,
                   "assumption": "homogeneous Poisson process on an unbounded plane; not a tissue null"})

    p = [0.5, 0.5]
    c0 = [[0.9, 0.1], [0.1, 0.9]]
    c1 = [[0.6, 0.1], [0.4, 0.9]]
    obs0 = [sum(row[j] * p[j] for j in range(2)) for row in c0]
    obs1 = [sum(row[j] * p[j] for j in range(2)) for row in c1]
    require(all(close(v, 1.0) for v in [sum(row[j] for row in c) for c in [c0, c1] for j in range(2)]),
            "Confusion matrices must be column stochastic")
    require(close(obs0[0], 0.5) and close(obs1[0], 0.35), "Misclassification example failed")
    checks.append({"id": "D05", "passed": True, "true_proportions_both": p,
                   "observed_baseline": obs0, "observed_followup": obs1})

    identity, swap = [[1.0, 0.0], [0.0, 1.0]], [[0.0, 1.0], [1.0, 0.0]]
    finals = [[sum(p[i] * t[i][j] for i in range(2)) for j in range(2)] for t in [identity, swap]]
    require(finals[0] == finals[1] == p, "Different transitions should have equal marginals here")
    checks.append({"id": "D06", "passed": True, "final_proportions": finals,
                   "fraction_switching": [0.0, 1.0], "marginals_do_not_identify_transitions": True})

    reference = [float(i) for i in range(1, 101)]
    queries = [50.0, 99.0, 99.505, 100.0, 101.0]
    upper = quantile(reference, 0.995)
    direct = [q > upper for q in queries]
    result = []
    for lower_p in [0.005, 0.05]:
        lower = quantile(reference, lower_p)
        scaled = [(r - lower) / (upper - lower) for r in reference]
        threshold = max(quantile(scaled, 0.99), 1.0)
        classified = [(q - lower) / (upper - lower) > threshold for q in queries]
        require(classified == direct, "CNA score-floor equivalence failed")
        result.append({"lower_quantile": lower_p, "scaled_threshold": threshold, "labels": classified})
    checks.append({"id": "D07", "passed": True, "upper_raw_quantile": upper, "queries": queries,
                   "raw_threshold_labels": direct, "scaled_results": result,
                   "scope": "score gate only; no ACC, malignant labels, or real CNA data"})

    require(len(checks) == 7 and all(x["passed"] for x in checks), "Incomplete checks")
    return {"status": "passed", "checks_run": len(checks), "patient_analysis_runs": 0,
            "animal_analysis_runs": 0, "input_kind": "hand_constructed_synthetic_examples",
            "python_version": platform.python_version(),
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "checks": checks}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2, allow_nan=False))
