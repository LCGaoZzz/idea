"""New teaching helpers; NOT the authors' pipeline or a biological replication.

No network, object deserialization, plotting, fitting, or automatic installation.
Coordinates must already be in micrometres in independent spatial domains.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from numbers import Integral
from typing import Sequence

import numpy as np
from scipy.spatial import cKDTree


def _integer(value: int, name: str, minimum: int = 0) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an integer, not a boolean")
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return int(value)


def _probability(value: float, name: str, allow_one: bool = False) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{name} cannot be boolean")
    value = float(value)
    if not math.isfinite(value) or value <= 0 or value > 1 or (value == 1 and not allow_one):
        raise ValueError(f"{name} is outside the permitted probability range")
    return value


def classify_clone(n_pre: int, n_inv: int, *, other_limit: int = 25,
                   min_fraction: float = 0.95) -> str:
    """Formalize the reported strict rule; zero handling is OUR added safeguard.

    This classifies observed spot counts, not true genetic ancestry.
    """
    a = _integer(n_pre, "n_pre")
    b = _integer(n_inv, "n_inv")
    limit = _integer(other_limit, "other_limit", 1)
    fraction = _probability(min_fraction, "min_fraction")
    if fraction < 0.5:
        raise ValueError("min_fraction must be >= 0.5 to avoid ambiguous classes")
    if a + b == 0:
        return "not_observed"
    if b < limit and a / (a + b) > fraction:
        return "pre_specific"
    if a < limit and b / (a + b) > fraction:
        return "inv_specific"
    return "shared"


def zero_detection_upper(n: int, *, alpha: float = 0.05,
                         detection_probability: float = 1.0) -> float:
    """Ideal iid-binomial bound, NOT valid for raw spatial cell counts by default."""
    n = _integer(n, "n", 1)
    alpha = _probability(alpha, "alpha")
    q = _probability(detection_probability, "detection_probability", True)
    return min(1.0, -math.expm1(math.log(alpha) / n) / q)


def roe_counts(counts: Sequence[Sequence[float]]) -> tuple[np.ndarray, np.ndarray]:
    """Return marginal-independence expected counts and observed/expected.

    Zero expected cells return NaN; no significance or spatial null is inferred.
    """
    observed = np.asarray(counts, dtype=float)
    if observed.ndim != 2 or observed.size == 0:
        raise ValueError("counts must be a nonempty two-dimensional table")
    if not np.isfinite(observed).all() or (observed < 0).any():
        raise ValueError("counts must be finite and nonnegative")
    total = observed.sum()
    if total <= 0:
        raise ValueError("the table must have a positive grand total")
    expected = np.outer(observed.sum(axis=1), observed.sum(axis=0)) / total
    ratio = np.full_like(observed, np.nan)
    np.divide(observed, expected, out=ratio, where=expected > 0)
    return expected, ratio


def bh_adjust(p_values: Sequence[float]) -> np.ndarray:
    """BH arithmetic for an explicitly chosen family; no dependence guarantee."""
    p = np.asarray(p_values, dtype=float)
    if p.ndim != 1 or not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("p_values must be a finite one-dimensional vector in [0,1]")
    if p.size == 0:
        return p.copy()
    order = np.argsort(p, kind="stable")
    raw = p[order] * p.size / np.arange(1, p.size + 1)
    adjusted = np.minimum(1.0, np.minimum.accumulate(raw[::-1])[::-1])
    result = np.empty_like(p)
    result[order] = adjusted
    return result


@dataclass(frozen=True)
class NeighborhoodCounts:
    total: np.ndarray
    target: np.ndarray
    proportion: np.ndarray
    edge_policy: str = "not_corrected"


def radius_counts(coordinates: Sequence[Sequence[float]], labels: Sequence[str],
                  spatial_keys: Sequence[tuple[str, str, str]], cell_ids: Sequence[str],
                  *, radius_um: float, include_self: bool, target_label: str,
                  chunk_size: int = 4096) -> NeighborhoodCounts:
    """Count neighbours within each (animal, sample, spatial-domain) tuple.

    Uses exact Euclidean radius queries (eps=0), <= radius including boundary.
    Returned vectors preserve input order. No edge correction, density, tests,
    segmentation correction, matching, or spatial permutations are performed.
    The explicit self policy is a new analysis choice, not a recovered paper rule.
    """
    xy = np.asarray(coordinates, dtype=float)
    if xy.ndim != 2 or xy.shape[1] != 2 or not np.isfinite(xy).all():
        raise ValueError("coordinates must be finite N-by-2 micrometre coordinates")
    n = len(xy)
    if len(labels) != n or len(spatial_keys) != n or len(cell_ids) != n:
        raise ValueError("all inputs must have equal length")
    if not isinstance(include_self, (bool, np.bool_)):
        raise ValueError("include_self must be explicitly boolean")
    if isinstance(radius_um, (bool, np.bool_)):
        raise ValueError("radius_um cannot be boolean")
    r = float(radius_um)
    if not math.isfinite(r) or r <= 0:
        raise ValueError("radius_um must be finite and positive")
    chunk = _integer(chunk_size, "chunk_size", 1)
    if not isinstance(target_label, str) or not target_label.strip():
        raise ValueError("target_label must be a nonempty string")
    groups: dict[tuple[str, str, str], list[int]] = {}
    seen: set[tuple[str, str, str, str]] = set()
    for i, (key, cell_id, label) in enumerate(zip(spatial_keys, cell_ids, labels)):
        if not isinstance(key, tuple) or len(key) != 3:
            raise ValueError("each spatial key must be an (animal, sample, domain) tuple")
        if any(not isinstance(v, str) or not v.strip() for v in (*key, cell_id, label)):
            raise ValueError("keys, cell IDs, and labels must contain nonempty strings")
        identity = (*key, cell_id)
        if identity in seen:
            raise ValueError(f"duplicate cell identity: {identity}")
        seen.add(identity)
        groups.setdefault(key, []).append(i)
    total = np.zeros(n, dtype=np.int64)
    target = np.zeros(n, dtype=np.int64)
    is_target = np.asarray([s == target_label for s in labels], dtype=bool)
    for index_list in groups.values():
        index = np.asarray(index_list, dtype=np.int64)
        points = xy[index]
        all_tree = cKDTree(points)
        target_points = points[is_target[index]]
        target_tree = cKDTree(target_points) if len(target_points) else None
        for start in range(0, len(index), chunk):
            ids = index[start:start + chunk]
            query = xy[ids]
            total[ids] = all_tree.query_ball_point(query, r, p=2, eps=0, return_length=True)
            if target_tree is not None:
                target[ids] = target_tree.query_ball_point(query, r, p=2, eps=0, return_length=True)
        if not include_self:
            total[index] -= 1
            target[index] -= is_target[index].astype(np.int64)
    proportion = np.full(n, np.nan)
    np.divide(target, total, out=proportion, where=total > 0)
    return NeighborhoodCounts(total=total, target=target, proportion=proportion)


def equal_host_contrast(values: Sequence[float], hosts: Sequence[str], groups: Sequence[str],
                        *, exposed: str, control: str) -> dict:
    """Equal-host mean of within-host mean contrasts; no confidence interval.

    Missing comparison arms exclude a host and are explicitly reported.
    Rows must already represent the intended comparable regions/centres.
    """
    y = np.asarray(values, dtype=float)
    if y.ndim != 1 or len(y) != len(hosts) or len(y) != len(groups):
        raise ValueError("values, hosts and groups must be equal-length vectors")
    if not np.isfinite(y).all():
        raise ValueError("values must be finite; choose/report missingness policy first")
    if not all(isinstance(x, str) and x.strip() for x in [*hosts, *groups, exposed, control]):
        raise ValueError("all group and host identifiers must be nonempty strings")
    if exposed == control:
        raise ValueError("exposed and control must differ")
    h, g = np.asarray(hosts), np.asarray(groups)
    effects: dict[str, float] = {}
    excluded: dict[str, str] = {}
    for host in sorted(set(hosts)):
        a, b = y[(h == host) & (g == exposed)], y[(h == host) & (g == control)]
        if len(a) == 0 or len(b) == 0:
            excluded[host] = "missing comparison arm"
        else:
            effects[host] = float(a.mean() - b.mean())
    if not effects:
        raise ValueError("no host has both comparison arms")
    return {"host_effects": effects, "equal_host_mean": float(np.mean(list(effects.values()))),
            "n_included_hosts": len(effects), "excluded_hosts": excluded,
            "inference": "descriptive_only"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="run deterministic synthetic illustrations")
    args = parser.parse_args()
    if not args.demo:
        parser.error("choose --demo; this script does not load real study data")
    print(json.dumps({"scope": "synthetic teaching examples; no paper reanalysis",
                      "clone_495_5": classify_clone(495, 5),
                      "clone_4950_50": classify_clone(4950, 50),
                      "zero_of_100_iid_upper": zero_detection_upper(100),
                      "bh": bh_adjust([0.01, 0.04, 0.03]).tolist(),
                      "fixed_numerator_proportions": [20 / 100, 20 / 200]}, indent=2))


if __name__ == "__main__":
    main()
