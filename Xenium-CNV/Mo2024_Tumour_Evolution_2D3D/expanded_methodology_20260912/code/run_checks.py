"""Independent mathematical checks; NOT the authors' pipeline or patient data.

Inputs are synthetic, aligned, non-overlapping genomic windows. CNV states are
-1/0/+1, NOT the source R script's ratio coding (neutral=1). The legacy function
below reproduces only its numerator/denominator logic under this restricted grid.
Requires Python >=3.10 and NumPy. No network, R, Torch, or biological data needed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import unittest
from datetime import datetime, timezone
import numpy as np


def _vectors(a, b, lengths):
    a, b, w = (np.asarray(v, dtype=float) for v in (a, b, lengths))
    if a.ndim != 1 or a.size == 0 or a.shape != b.shape or a.shape != w.shape:
        raise ValueError('Expected equally sized, nonempty one-dimensional arrays')
    if not all(np.isfinite(v).all() for v in (a, b, w)):
        raise ValueError('Nonfinite input')
    if not np.isin(a, [-1, 0, 1]).all() or not np.isin(b, [-1, 0, 1]).all():
        raise ValueError('States must be -1, 0, or +1')
    if np.any(w <= 0):
        raise ValueError('Window lengths must be positive')
    return a, b, w


def signed_similarity(a, b, lengths):
    """Algebraic implementation of the paper formula on an aligned grid.

    Undefined all-neutral comparisons return NaN; do not silently impute them.
    Interval harmonization and CNV inference are deliberately not implemented.
    """
    a, b, w = _vectors(a, b, lengths)
    union = (a != 0) | (b != 0)
    if not union.any():
        return math.nan
    return float(np.sum(w[union] * a[union] * b[union]) / w[union].sum())


def legacy_no_probability_grid(a, b, lengths):
    """Restricted-grid translation of CNV_profile_jaccard; NOT a correction.

    Source: ST_subclone_publication@7067cd16, Figure2/3_CNV_jaccard_similarity.R.
    Intentionally retains A non-neutral OR B deletion denominator and absence
    of negative contributions. This tests logic, not R/GenomicRanges execution.
    """
    a, b, w = _vectors(a, b, lengths)
    if not np.any(a != 0):
        return 0.0
    union = (a != 0) | (b < 0)
    intersection = (a == b) & (a != 0)
    return float(w[intersection].sum() / w[union].sum())


def probability_pred_grid(a, b, lengths, p_a, p_b):
    """Restricted-grid translation of mode='pred', including state-wise union.

    Opposing events are counted in both state-specific denominator tracks;
    their numerator is zero, not the negative term of the paper formula.
    """
    a, b, w = _vectors(a, b, lengths)
    pa, pb = np.asarray(p_a, float), np.asarray(p_b, float)
    if pa.shape != a.shape or pb.shape != b.shape:
        raise ValueError('Probability shape mismatch')
    if any(not np.isfinite(p).all() or np.any((p < 0) | (p > 1)) for p in (pa, pb)):
        raise ValueError('Probabilities must be finite and between zero and one')
    denominator = numerator = 0.0
    for state in (-1, 1):
        union = (a == state) | (b == state)
        same = (a == state) & (b == state)
        denominator += float(w[union].sum())
        numerator += float((w[same] * pa[same] * pb[same]).sum())
    return numerator / denominator if denominator else 0.0


def distance_audit(distance):
    d = np.asarray(distance, float)
    if d.ndim != 2 or d.shape[0] != d.shape[1] or len(d) == 0:
        raise ValueError('Expected nonempty square distance matrix')
    if not np.isfinite(d).all() or np.any(d < 0):
        raise ValueError('Distances must be finite and nonnegative')
    if not np.allclose(d, d.T, atol=1e-10, rtol=0):
        raise ValueError('Asymmetric distance: do not silently take one triangle')
    if not np.allclose(np.diag(d), 0, atol=1e-10, rtol=0):
        raise ValueError('Distance diagonal is not zero')
    n = len(d)
    h = np.eye(n) - np.ones((n, n)) / n
    gram = -0.5 * h @ (d * d) @ h
    eig = np.linalg.eigvalsh((gram + gram.T) / 2)
    tolerance = 1e-10 * max(1.0, float(np.max(np.abs(eig))))
    return {'min_gram_eigenvalue': float(eig.min()),
            'is_euclidean_within_tolerance': bool(eig.min() >= -tolerance),
            'tolerance': tolerance}


def annulus_fraction(radius, depth):
    if not math.isfinite(radius) or not math.isfinite(depth) or radius <= 0 or not 0 <= depth <= radius:
        raise ValueError('Require finite radius>0 and 0<=depth<=radius')
    q = depth / radius
    return 2 * q - q * q


def allocate_expression(total, fractions, reference, floor_fraction=0.05):
    p, r = np.asarray(fractions, float), np.asarray(reference, float)
    if p.ndim != 1 or p.size == 0 or p.shape != r.shape:
        raise ValueError('Expected matching nonempty vectors')
    if not np.isfinite(p).all() or not np.isfinite(r).all() or np.any(p < 0) or np.any(r < 0):
        raise ValueError('Fractions/reference must be finite and nonnegative')
    if not np.isclose(p.sum(), 1) or not math.isfinite(total) or total < 0:
        raise ValueError('Require fractions summing to one and total>=0')
    if not math.isfinite(floor_fraction) or not 0 <= floor_fraction <= 1:
        raise ValueError('Invalid reference floor')
    r = np.where(r >= floor_fraction * r.max(), r, 0)
    contribution = p * r
    denominator = float(contribution.sum())
    if denominator <= 0:
        raise ValueError('No attributable signal: denominator is zero')
    return total * contribution / denominator


def cycle_rank(n_nodes, edges):
    """Simple undirected graph only. Includes isolated vertices.

    Duplicate edges and self-loops are rejected rather than silently changing
    the intended graph. Spatial topology is not a lineage history.
    """
    if not isinstance(n_nodes, int) or isinstance(n_nodes, bool) or n_nodes < 0:
        raise ValueError('n_nodes must be a nonnegative integer')
    parent = list(range(n_nodes))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    seen = set()
    for u, v in edges:
        if not all(isinstance(x, int) and not isinstance(x, bool) and 0 <= x < n_nodes for x in (u, v)):
            raise ValueError('Invalid vertex')
        edge = tuple(sorted((u, v)))
        if u == v or edge in seen:
            raise ValueError('Self-loop or duplicate edge')
        seen.add(edge)
        parent[find(u)] = find(v)
    components = len({find(i) for i in range(n_nodes)})
    return {'vertices': n_nodes, 'edges': len(seen), 'components': components,
            'cycle_rank': len(seen) - n_nodes + components}


def ce_on_logits(values, target):
    z = np.asarray(values, float)
    if z.ndim != 1 or len(z) < 2 or not np.isfinite(z).all():
        raise ValueError('Expected finite logits for at least two classes')
    if not isinstance(target, int) or not 0 <= target < len(z):
        raise ValueError('Invalid target')
    m = float(z.max())
    return float(m + np.log(np.exp(z - m).sum()) - z[target])


def partial_association(x, y, covariate):
    x, y, c = (np.asarray(v, float) for v in (x, y, covariate))
    if x.ndim != 1 or x.shape != y.shape or x.shape != c.shape or len(x) < 4:
        raise ValueError('Expected matching vectors with at least four entries')
    if not all(np.isfinite(v).all() for v in (x, y, c)):
        raise ValueError('Nonfinite values')
    design = np.column_stack((np.ones(len(x)), c))
    if np.linalg.matrix_rank(design) < 2:
        raise ValueError('Covariate/intercept not identifiable')
    rx = x - design @ np.linalg.lstsq(design, x, rcond=None)[0]
    ry = y - design @ np.linalg.lstsq(design, y, rcond=None)[0]
    if np.linalg.norm(rx) < 1e-12 or np.linalg.norm(ry) < 1e-12:
        raise ValueError('No residual variation')
    return {'partial_r': float(rx @ ry / (np.linalg.norm(rx) * np.linalg.norm(ry))),
            'slope': float(rx @ ry / (rx @ rx))}


class Checks(unittest.TestCase):
    def test_signed_identity(self):
        self.assertAlmostEqual(signed_similarity([1, -1], [1, -1], [2, 3]), 1)
    def test_signed_opposite(self):
        self.assertEqual(signed_similarity([1], [-1], [1]), -1)
    def test_signed_partial(self):
        self.assertEqual(signed_similarity([1, 0], [1, 1], [1, 1]), 0.5)
    def test_all_neutral_undefined(self):
        self.assertTrue(math.isnan(signed_similarity([0], [0], [1])))
    def test_invalid_states(self):
        with self.assertRaises(ValueError): signed_similarity([2], [1], [1])
    def test_invalid_lengths(self):
        with self.assertRaises(ValueError): signed_similarity([1], [1], [0])
    def test_legacy_asymmetry(self):
        self.assertEqual(legacy_no_probability_grid([1, 0], [1, 1], [1, 1]), 1)
        self.assertEqual(legacy_no_probability_grid([1, 1], [1, 0], [1, 1]), 0.5)
    def test_legacy_opposite_no_penalty(self):
        self.assertEqual(legacy_no_probability_grid([1], [-1], [1]), 0)
    def test_probability_self_confidence(self):
        self.assertAlmostEqual(probability_pred_grid([1], [1], [1], [.8], [.8]), .64)
    def test_probability_opposite(self):
        self.assertEqual(probability_pred_grid([1], [-1], [1], [1], [1]), 0)
    def test_non_euclidean_counterexample(self):
        p = [[-1, -1], [-1, 0], [-1, 1], [1, 0]]
        s = np.array([[signed_similarity(a, b, [1, 1]) for b in p] for a in p])
        result = distance_audit(1 - s)
        self.assertAlmostEqual(result['min_gram_eigenvalue'], -0.224744871391589)
        self.assertFalse(result['is_euclidean_within_tolerance'])
    def test_asymmetric_distance_rejected(self):
        with self.assertRaises(ValueError): distance_audit([[0, 1], [.5, 0]])
    def test_euclidean_distance(self):
        self.assertTrue(distance_audit([[0, 1, 2], [1, 0, 1], [2, 1, 0]])['is_euclidean_within_tolerance'])
    def test_geometry_dilution(self):
        self.assertAlmostEqual(annulus_fraction(100, 10), .19)
        self.assertAlmostEqual(annulus_fraction(200, 10), .0975)
    def test_invalid_geometry(self):
        with self.assertRaises(ValueError): annulus_fraction(1, 2)
    def test_allocation_conservation(self):
        values = allocate_expression(20, [.5, .5, 0], [.4, .3, .3])
        self.assertAlmostEqual(float(values.sum()), 20)
        self.assertAlmostEqual(float(values[0]), 80 / 7)
    def test_zero_allocation_denominator(self):
        with self.assertRaises(ValueError): allocate_expression(20, [.5, .5], [0, 0])
    def test_invalid_fractions(self):
        with self.assertRaises(ValueError): allocate_expression(20, [1, 1], [1, 1])
    def test_tree_has_no_cycle(self):
        self.assertEqual(cycle_rank(3, [(0, 1), (1, 2)])['cycle_rank'], 0)
    def test_triangle_cycle(self):
        self.assertEqual(cycle_rank(3, [(0, 1), (1, 2), (2, 0)])['cycle_rank'], 1)
    def test_disconnected_cycle(self):
        self.assertEqual(cycle_rank(4, [(0, 1), (1, 2), (2, 0)])['components'], 2)
        self.assertEqual(cycle_rank(4, [(0, 1), (1, 2), (2, 0)])['cycle_rank'], 1)
    def test_duplicate_edge_rejected(self):
        with self.assertRaises(ValueError): cycle_rank(2, [(0, 1), (1, 0)])
    def test_cross_entropy_input_semantics(self):
        p = np.array([.9, .1])
        self.assertAlmostEqual(ce_on_logits(np.log(p), 0), -math.log(.9))
        self.assertGreater(ce_on_logits(p, 0), -math.log(.9))
    def test_partial_r_not_slope(self):
        x, c = [1, 2, 3, 4, 5], [0, 1, 0, 1, 0]
        y = np.array([3.2, 7.8, 9, 14.2, 14.8])
        a, b = partial_association(x, y, c), partial_association(x, y * 10, c)
        self.assertAlmostEqual(a['partial_r'], b['partial_r'])
        self.assertAlmostEqual(a['slope'] * 10, b['slope'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output exists; use a new path to preserve the previous run')
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    record = {'scope': 'independent_synthetic_mathematical_checks',
              'paper_data_analyzed': False, 'author_code_executed': False,
              'utc_time': datetime.now(timezone.utc).isoformat(),
              'python': platform.python_version(), 'numpy': np.__version__,
              'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'tests_run': result.testsRun, 'failures': len(result.failures),
              'errors': len(result.errors), 'skipped': len(result.skipped),
              'passed': result.wasSuccessful(),
              'seed': 'not_applicable_deterministic_inputs',
              'examples': {'legacy_A_B': legacy_no_probability_grid([1, 0], [1, 1], [1, 1]),
                           'legacy_B_A': legacy_no_probability_grid([1, 1], [1, 0], [1, 1]),
                           'signed_opposite': signed_similarity([1], [-1], [1]),
                           'ce_probability_as_logits': ce_on_logits([.9, .1], 0),
                           'categorical_nll': -math.log(.9)}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
