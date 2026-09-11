"""Mass-action analysis in a single consistent concentration unit.

Fits expect calibrated tracer bound fractions, not raw anisotropy.
No paper-specific baselines, bootstrap or wet-lab data are implied.
"""
from __future__ import annotations
import math
import numpy as np
from scipy.optimize import brentq, least_squares


def _nonnegative(value, name):
    x = np.asarray(value, dtype=float)
    if not np.isfinite(x).all() or np.any(x < 0):
        raise ValueError(f"{name} must be finite and nonnegative")
    return x


def bound_complex(protein_total, ligand_total, kd):
    p, l, k = np.broadcast_arrays(_nonnegative(protein_total, "protein"),
                                  _nonnegative(ligand_total, "ligand"), _nonnegative(kd, "kd"))
    if np.any(k <= 0):
        raise ValueError("kd must be positive")
    scale = np.maximum(np.maximum(p, l), k)
    ps, ls, ks = p / scale, l / scale, k / scale
    disc = (ps - ls) ** 2 + 2 * ks * (ps + ls) + ks ** 2
    return scale * (2 * ps * ls / (ps + ls + ks + np.sqrt(disc)))


def bound_fraction(protein_total, ligand_total, kd):
    l = _nonnegative(ligand_total, "ligand")
    if np.any(l <= 0):
        raise ValueError("A tracer fraction requires ligand_total > 0")
    return bound_complex(protein_total, l, kd) / l


def competition(protein_total, tracer_total, competitor_total, kd_tracer, kd_competitor):
    """Return free protein and both complexes, solving one shared binding site."""
    p, l, i, kl, ki = np.broadcast_arrays(*[_nonnegative(v, n) for v, n in zip(
        (protein_total, tracer_total, competitor_total, kd_tracer, kd_competitor),
        ("protein", "tracer", "competitor", "kd_tracer", "kd_competitor"))])
    if np.any(kl <= 0) or np.any(ki <= 0):
        raise ValueError("Dissociation constants must be positive")
    free = np.zeros_like(p)
    for index in np.ndindex(p.shape):
        pt, lt, it, klt, kit = (float(x[index]) for x in (p, l, i, kl, ki))
        if pt == 0:
            continue
        def balance(u):
            pf = pt * u
            return u + (lt / pt) * pf / (klt + pf) + (it / pt) * pf / (kit + pf) - 1
        free[index] = pt * brentq(balance, 0.0, 1.0, xtol=1e-14, rtol=1e-12)
    return {"protein_free": free, "tracer_complex": l * free / (kl + free),
            "competitor_complex": i * free / (ki + free)}


def _fit(predict, observed, initial, bounds):
    y = np.asarray(observed, dtype=float)
    initial = np.atleast_1d(np.asarray(initial, dtype=float))
    if y.ndim != 1 or len(y) <= len(initial) or not np.isfinite(y).all():
        raise ValueError("Need finite 1D observations exceeding parameter count")
    low, high = map(float, bounds)
    if not (0 < low < high < math.inf) or np.any(~np.isfinite(initial)) or np.any(initial <= low) or np.any(initial >= high):
        raise ValueError("Need positive finite bounds and interior initial values")
    def residual(log_k):
        predicted = np.asarray(predict(10 ** log_k), dtype=float)
        if predicted.shape != y.shape or not np.isfinite(predicted).all():
            raise ValueError("Prediction/observation shape or finiteness mismatch")
        return predicted - y
    result = least_squares(residual, np.log10(initial), bounds=(np.log10(low), np.log10(high)),
                           xtol=1e-12, ftol=1e-12, gtol=1e-12, max_nfev=3000)
    return {"kd": (10 ** result.x).tolist(), "success": bool(result.success),
            "residuals": result.fun.tolist(), "nfev": result.nfev,
            "local_jacobian_full_rank": bool(np.linalg.matrix_rank(result.jac) == len(initial)),
            "at_bound": bool(np.any(result.active_mask != 0)),
            "note": "No uncertainty estimate; local rank is not proof of identifiability"}


def fit_direct(protein_total, ligand_total, observed, *, initial_kd, bounds):
    return _fit(lambda kd: bound_fraction(protein_total, ligand_total, kd[0]),
                observed, [initial_kd], bounds)


def fit_competition(protein_total, tracer_total, competitor_total, observed, *, initial_kds, bounds):
    l = _nonnegative(tracer_total, "tracer")
    if np.any(l <= 0) or len(initial_kds) != 2:
        raise ValueError("Need positive tracer and two initial Kd values")
    return _fit(lambda kd: competition(protein_total, l, competitor_total, *kd)["tracer_complex"] / l,
                observed, initial_kds, bounds)


def proofreading_delta(holo_wt, holo_mut, apo_wt, apo_mut):
    values = [holo_wt, holo_mut, apo_wt, apo_mut]
    if any(not math.isfinite(v) or not 0 < v <= 1 for v in values):
        raise ValueError("Conditional probabilities must lie in (0, 1]")
    holo = math.log10(holo_mut) - math.log10(holo_wt)
    apo = math.log10(apo_mut) - math.log10(apo_wt)
    return {"delta_log10p_holo": holo, "delta_log10p_apo": apo,
            "holo_minus_apo_heuristic": holo - apo, "is_free_energy": False}


def mutant_cycle(kd_wt, kd_a, kd_b, kd_ab, *, temperature_K):
    values = [kd_wt, kd_a, kd_b, kd_ab, temperature_K]
    if any(not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError("Kd values and temperature must be finite and positive")
    rt = 0.00198720425864083 * temperature_K
    log_expected = math.log(kd_a) + math.log(kd_b) - math.log(kd_wt)
    return {"independent_expected_kd": math.exp(log_expected),
            "ddg_a_kcal_mol": rt * math.log(kd_a / kd_wt),
            "ddg_b_kcal_mol": rt * math.log(kd_b / kd_wt),
            "ddg_ab_kcal_mol": rt * math.log(kd_ab / kd_wt),
            "coupling_kcal_mol": rt * (math.log(kd_ab) - log_expected),
            "temperature_K_assumed": temperature_K, "uncertainty_assessed": False}


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054):
    if type(successes) is not int or type(total) is not int or not 0 <= successes <= total or total <= 0 or not math.isfinite(z) or z <= 0:
        raise ValueError("Invalid binomial counts or z")
    proportion, denominator = successes / total, 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    half = z * math.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total ** 2)) / denominator
    return [max(0.0, center - half), min(1.0, center + half)]
