"""Teaching implementation, NOT the authors' pipeline or a paper reproduction.

All coordinates must be micrometres. Cells must already be quality controlled.
No annotation, image registration, tissue masking or causal inference is hidden.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
import math
import warnings

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree


def _require(df: pd.DataFrame, columns: Sequence[str]) -> None:
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError("Expected a nonempty pandas DataFrame")
    missing = set(columns) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if df[list(columns)].isna().any().any():
        raise ValueError("Required columns contain missing values")


def _ids(df: pd.DataFrame, columns: Sequence[str]) -> None:
    for col in columns:
        if not df[col].map(lambda x: isinstance(x, str) and bool(x.strip())).all():
            raise ValueError(f"{col} must contain nonempty string identifiers")


def _finite(df: pd.DataFrame, columns: Sequence[str]) -> np.ndarray:
    a = df[list(columns)].to_numpy(dtype=float)
    if not np.isfinite(a).all():
        raise ValueError(f"Nonfinite values in {list(columns)}")
    return a


def summarize_serpin(cells: pd.DataFrame, *, representation: str) -> pd.DataFrame:
    """Patient-level prevalence and positive-only mean of two measured genes.

    representation is mandatory; numeric checks cannot prove matrix provenance.
    Positive means observed value > 0, not a validated biological on/off switch.
    Patients without malignant cells are not assigned an artificial zero row.
    """
    genes = ("SERPINE1", "SERPINB2")
    req = ["source", "patient_id", "cell_id", "is_malignant", *genes]
    _require(cells, req)
    _ids(cells, ["source", "patient_id", "cell_id"])
    if representation not in {"raw_counts", "log1p_nonnegative"}:
        raise ValueError("Use raw_counts or log1p_nonnegative; never scaled data")
    if not pd.api.types.is_bool_dtype(cells["is_malignant"]):
        raise ValueError("is_malignant must be boolean")
    if cells.duplicated(["source", "patient_id", "cell_id"]).any():
        raise ValueError("Duplicate cell identifiers within source/patient")
    x = _finite(cells, genes)
    if (x < 0).any():
        raise ValueError("Expression must be nonnegative")
    if representation == "raw_counts" and not np.allclose(x, np.rint(x), atol=1e-8, rtol=0):
        raise ValueError("raw_counts must be integer-valued")
    malignant = cells.loc[cells["is_malignant"]].copy()
    if malignant.empty:
        raise ValueError("No malignant cells: prevalence is undefined")
    rows = []
    for (source, patient), g in malignant.groupby(["source", "patient_id"], sort=True, observed=True):
        pos = g[list(genes)].to_numpy(float) > 0
        row = {"source": source, "patient_id": patient, "n_cancer": len(g),
               "representation": representation, "n_double_pos": int(pos.all(axis=1).sum()),
               "n_union_pos": int(pos.any(axis=1).sum())}
        row["fraction_double_pos"] = row["n_double_pos"] / len(g)
        row["fraction_union_pos"] = row["n_union_pos"] / len(g)
        for gene in genes:
            v = g[gene].to_numpy(float)
            positive = v > 0
            row[f"n_{gene}_pos"] = int(positive.sum())
            row[f"fraction_{gene}_pos"] = float(positive.mean())
            row[f"mean_{gene}_all"] = float(v.mean())
            row[f"mean_{gene}_positive"] = float(v[positive].mean()) if positive.any() else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


@dataclass
class ROIResult:
    table: pd.DataFrame
    exclusions: pd.DataFrame
    membership: pd.DataFrame


def build_roi_table(
    cells: pd.DataFrame,
    centers: pd.DataFrame,
    *,
    radius_um: float,
    control_label: str,
    ko_label: str,
    immune_labels: Sequence[str],
    min_total: int = 1,
    min_tumor: int = 1,
    mix_threshold: float = 0.20,
    assume_full_tissue: bool = False,
    record_membership: bool = False,
) -> ROIResult:
    """Build circular ROIs independently per image, with explicit denominators.

    centers: image_id, roi_id, x_um, y_um, optionally area_um2.
    cells: image_id, patient_id, cell_id, x_um, y_um, phenotype.
    An area_um2 column must describe the SAME mask used to include input cells.
    Without it, nominal circle area is allowed only by explicit opt-in.
    This function does NOT build alpha-shapes or reproduce authors' sampling.
    """
    _require(cells, ["image_id", "patient_id", "cell_id", "x_um", "y_um", "phenotype"])
    _require(centers, ["image_id", "roi_id", "x_um", "y_um"])
    _ids(cells, ["image_id", "patient_id", "cell_id", "phenotype"])
    _ids(centers, ["image_id", "roi_id"])
    _finite(cells, ["x_um", "y_um"])
    _finite(centers, ["x_um", "y_um"])
    if not np.isfinite(radius_um) or radius_um <= 0:
        raise ValueError("radius_um must be positive and finite")
    if any(not isinstance(v, (int, np.integer)) or v < 1 for v in (min_total, min_tumor)):
        raise ValueError("min_total and min_tumor must be positive integers")
    if not 0 <= mix_threshold < 0.5:
        raise ValueError("mix_threshold must be in [0, 0.5)")
    if not control_label or not ko_label or control_label == ko_label:
        raise ValueError("Two distinct tumor labels are required")
    immune = set(immune_labels)
    if not immune or immune.intersection({control_label, ko_label}):
        raise ValueError("Explicit nonempty immune labels must exclude tumor labels")
    if cells.duplicated(["image_id", "cell_id"]).any():
        raise ValueError("Duplicate cell_id within an image")
    if centers.duplicated(["image_id", "roi_id"]).any():
        raise ValueError("Duplicate roi_id within an image")
    if (cells.groupby("image_id")["patient_id"].nunique() != 1).any():
        raise ValueError("Each image_id must belong to exactly one biological unit")
    unknown = set(centers.image_id) - set(cells.image_id)
    if unknown:
        raise ValueError(f"Centers reference unknown images: {sorted(unknown)}")
    nominal_area = math.pi * radius_um**2
    supplied = "area_um2" in centers.columns
    if supplied:
        areas = _finite(centers, ["area_um2"]).ravel()
        if (areas <= 0).any() or (areas > nominal_area * (1 + 1e-8)).any():
            raise ValueError("Effective area must be >0 and <= nominal circle area")
    elif not assume_full_tissue:
        raise ValueError("Provide mask intersection area_um2, or explicitly allow nominal circle area")
    levels = sorted(cells.phenotype.unique())
    rows, excluded, members = [], [], []
    for image, c in centers.groupby("image_id", sort=True):
        g = cells.loc[cells.image_id == image].reset_index(drop=True)
        tree = cKDTree(g[["x_um", "y_um"]].to_numpy(float))
        hits = tree.query_ball_point(c[["x_um", "y_um"]].to_numpy(float), r=radius_um)
        for (_, center), indices in zip(c.iterrows(), hits):
            local = g.iloc[sorted(indices)]
            counts = local.phenotype.value_counts()
            n_control = int(counts.get(control_label, 0))
            n_ko = int(counts.get(ko_label, 0))
            n_tumor, n_all = n_control + n_ko, len(local)
            reason = "too_few_total_cells" if n_all < min_total else (
                "too_few_tumor_cells" if n_tumor < min_tumor else None)
            if reason:
                excluded.append({"image_id": image, "roi_id": center.roi_id,
                                 "reason": reason, "n_total": n_all, "n_tumor": n_tumor})
                continue
            fraction = n_control / n_tumor
            mixing = min(n_control, n_ko) / n_tumor
            majority = "control" if n_control >= n_ko else "ko"
            group = "high_mixing" if mixing > mix_threshold else f"low_{majority}"
            area = float(center.area_um2) if supplied else nominal_area
            row = {"image_id": image, "patient_id": g.patient_id.iloc[0],
                   "roi_id": center.roi_id, "x_um": float(center.x_um), "y_um": float(center.y_um),
                   "radius_um": float(radius_um), "area_um2": area,
                   "area_kind": "supplied_mask_intersection" if supplied else "nominal_circle",
                   "n_total": n_all, "n_tumor": n_tumor, "n_control": n_control, "n_ko": n_ko,
                   "p_control": fraction, "minority_fraction": mixing,
                   "majority": majority, "sample_group": group,
                   "n_immune": int(local.phenotype.isin(immune).sum())}
            row["immune_fraction_all"] = row["n_immune"] / n_all
            row["immune_density_per_mm2"] = row["n_immune"] / (area / 1e6)
            for label in levels:
                n = int(counts.get(label, 0))
                row[f"count__{label}"] = n
                row[f"fraction_all__{label}"] = n / n_all
                row[f"density_per_mm2__{label}"] = n / (area / 1e6)
            rows.append(row)
            if record_membership:
                members.extend({"image_id": image, "roi_id": center.roi_id, "cell_id": cell_id}
                               for cell_id in local.cell_id)
    table = pd.DataFrame(rows)
    if not table.empty:
        table["n_overlapping_nominal_circles"] = 0
        for _, indices in table.groupby("image_id", sort=True).groups.items():
            ix = np.asarray(list(indices))
            xy = table.loc[ix, ["x_um", "y_um"]].to_numpy(float)
            for a, b in cKDTree(xy).query_pairs(2 * radius_um):
                if np.linalg.norm(xy[a] - xy[b]) < 2 * radius_um:
                    table.loc[ix[[a, b]], "n_overlapping_nominal_circles"] += 1
    return ROIResult(table, pd.DataFrame(excluded, columns=["image_id", "roi_id", "reason", "n_total", "n_tumor"]),
                     pd.DataFrame(members, columns=["image_id", "roi_id", "cell_id"]))


def farthest_point_sample(rois: pd.DataFrame, *, n_per_group: int, seed: int = 42) -> pd.DataFrame:
    """Spatial coverage sampling per image/group; NOT a non-overlap guarantee."""
    _require(rois, ["image_id", "roi_id", "sample_group", "x_um", "y_um"])
    _finite(rois, ["x_um", "y_um"])
    if not isinstance(n_per_group, (int, np.integer)) or n_per_group < 1:
        raise ValueError("n_per_group must be a positive integer")
    if rois.duplicated(["image_id", "roi_id"]).any():
        raise ValueError("Duplicate ROI identifiers")
    rng = np.random.default_rng(seed)
    selected_frames = []
    for _, g in rois.groupby(["image_id", "sample_group"], sort=True, observed=True):
        g = g.sort_values("roi_id").reset_index(drop=True)
        xy = g[["x_um", "y_um"]].to_numpy(float)
        n = min(n_per_group, len(g))
        chosen = [int(rng.integers(len(g)))]
        nearest_sq = ((xy - xy[chosen[0]])**2).sum(axis=1)
        while len(chosen) < n:
            nearest_sq[chosen] = -np.inf
            j = int(np.argmax(nearest_sq))
            chosen.append(j)
            nearest_sq = np.minimum(nearest_sq, ((xy - xy[j])**2).sum(axis=1))
        selected_frames.append(g.iloc[chosen])
    return pd.concat(selected_frames, ignore_index=True)


def factorial_contrasts(data: pd.DataFrame) -> pd.DataFrame:
    """Average technical observations first, then calculate paired donor contrasts.

    Columns: donor_id, matrix (0/1), context (0/1), value.
    context can denote conditioned medium OR drug, but never silently both.
    """
    _require(data, ["donor_id", "matrix", "context", "value"])
    _ids(data, ["donor_id"])
    _finite(data, ["matrix", "context", "value"])
    if not data["matrix"].isin([0, 1]).all() or not data["context"].isin([0, 1]).all():
        raise ValueError("matrix/context must be encoded as 0 or 1")
    means = data.groupby(["donor_id", "matrix", "context"], observed=True)["value"].mean()
    rows = []
    for donor, g in means.groupby(level="donor_id", sort=True):
        v = g.droplevel("donor_id")
        if set(v.index) != {(0, 0), (0, 1), (1, 0), (1, 1)}:
            raise ValueError(f"Incomplete 2x2 factorial design for {donor}")
        a, b = float(v.loc[(1, 0)] - v.loc[(0, 0)]), float(v.loc[(1, 1)] - v.loc[(0, 1)])
        rows.append({"donor_id": donor, "matrix_effect_context0": a,
                     "matrix_effect_context1": b, "interaction": b - a})
    return pd.DataFrame(rows)


def bootstrap_mean(values: Sequence[float], *, n_boot: int = 2000, seed: int = 42) -> dict:
    """Descriptive percentile bootstrap of independent-unit contrasts, not cells."""
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or len(x) < 2 or not np.isfinite(x).all():
        raise ValueError("At least two finite independent-unit contrasts required")
    if not isinstance(n_boot, (int, np.integer)) or n_boot < 100:
        raise ValueError("n_boot must be an integer >=100")
    if len(x) < 10:
        warnings.warn("Few biological units: bootstrap interval is only descriptive", RuntimeWarning)
    rng = np.random.default_rng(seed)
    samples = np.array([rng.choice(x, size=len(x), replace=True).mean() for _ in range(n_boot)])
    lo, hi = np.quantile(samples, [0.025, 0.975])
    return {"n_biological_units": len(x), "mean": float(x.mean()), "ci_low": float(lo),
            "ci_high": float(hi), "n_boot": int(n_boot), "seed": int(seed),
            "method": "independent-unit percentile bootstrap; descriptive, not a causal test"}
