"""Geometry on already matched coordinates; not a PDB/chemistry mapper."""
from __future__ import annotations
import numpy as np


def _xyz(value, name: str) -> np.ndarray:
    a = np.asarray(value, dtype=float)
    if a.ndim != 2 or a.shape[1] != 3 or len(a) == 0:
        raise ValueError(f"{name}: expected a nonempty (n, 3) array")
    if not np.isfinite(a).all():
        raise ValueError(f"{name}: nonfinite coordinates")
    return a


def kabsch(mobile, reference):
    """Return rotation, translation and RMSD; row vectors: mobile @ R + t."""
    x, y = _xyz(mobile, "mobile"), _xyz(reference, "reference")
    if x.shape != y.shape or len(x) < 3:
        raise ValueError("Need at least three matched protein atoms")
    xc, yc = x - x.mean(0), y - y.mean(0)
    if np.linalg.matrix_rank(xc) < 2 or np.linalg.matrix_rank(yc) < 2:
        raise ValueError("Collinear/coincident alignment is ambiguous")
    u, _, vt = np.linalg.svd(xc.T @ yc)
    correction = np.diag([1.0, 1.0, np.sign(np.linalg.det(u @ vt))])
    rotation = u @ correction @ vt
    translation = y.mean(0) - x.mean(0) @ rotation
    rmsd = float(np.sqrt(np.mean(np.sum((x @ rotation + translation - y) ** 2, 1))))
    return rotation, translation, rmsd


def complex_rmsd(protein_mobile, protein_reference, ligand_mobile,
                 ligand_reference, *, allowed_permutations=None) -> dict:
    """Apply PROTEIN transform to ligand; no independent ligand superposition.

    Each supplied permutation maps reference order to mobile atom indices.
    Caller must establish chemical equivalence and stereochemical validity.
    This function only validates that each supplied mapping is a bijection.
    """
    lm, lr = _xyz(ligand_mobile, "ligand_mobile"), _xyz(ligand_reference, "ligand_reference")
    if lm.shape != lr.shape:
        raise ValueError("Ligand atom counts must match")
    rotation, translation, protein_rmsd = kabsch(protein_mobile, protein_reference)
    mappings = [list(range(len(lm)))] if allowed_permutations is None else list(allowed_permutations)
    if not mappings:
        raise ValueError("No allowed atom mapping")
    aligned, scores = lm @ rotation + translation, []
    for mapping in mappings:
        p = np.asarray(mapping)
        if p.dtype.kind not in "iu" or p.ndim != 1 or sorted(p.tolist()) != list(range(len(lm))):
            raise ValueError("Each mapping must be an integer bijection")
        scores.append(float(np.sqrt(np.mean(np.sum((aligned[p] - lr) ** 2, 1)))))
    best = int(np.argmin(scores))
    return {"protein_rmsd_A": protein_rmsd, "ligand_rmsd_A": scores[best],
            "mapping_index": best, "rotation_determinant": float(np.linalg.det(rotation)),
            "alignment_scope": "supplied_protein_atoms", "chemical_mapping_checked_here": False}
