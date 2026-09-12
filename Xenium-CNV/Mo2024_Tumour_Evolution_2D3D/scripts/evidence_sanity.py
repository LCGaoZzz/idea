"""Small mathematical checks; NOT execution of the authors' R pipeline.

Python standard library only. Synthetic aligned windows are used to distinguish
paper definitions from simplified code logic. No patient data or R is loaded.
Run: python scripts/evidence_sanity.py
"""
from __future__ import annotations
import json
import math
import platform
import unittest
from typing import Sequence


def paper_signed_similarity(a: Sequence[int], b: Sequence[int], widths: Sequence[float]) -> float | None:
    """Methods' signed length-weighted score on already aligned windows."""
    if not a or not (len(a) == len(b) == len(widths)):
        raise ValueError('Nonempty aligned vectors of identical length are required.')
    if any(x not in (-1, 0, 1) for x in (*a, *b)):
        raise ValueError('States must be -1, 0 or 1.')
    if any(not math.isfinite(w) or w <= 0 for w in widths):
        raise ValueError('Widths must be finite and positive.')
    active = [i for i in range(len(a)) if a[i] != 0 or b[i] != 0]
    denominator = sum(widths[i] for i in active)
    if denominator == 0:
        return None
    return sum(widths[i] * a[i] * b[i] for i in active) / denominator


def simplified_public_hard_score(a: Sequence[int], b: Sequence[int]) -> float:
    """Unit-grid analogue of CNV_profile_jaccard, not a general interval port.

    Public code uses CNV>1 for gain, CNV<1 for loss; these arrays instead use
    +1/-1/0. Its union includes A non-neutral and B loss (not all B events).
    This hard-score path is NOT the selected jac_pred_mat clustering path.
    """
    if not a or len(a) != len(b):
        raise ValueError('Aligned nonempty vectors required.')
    if any(x not in (-1, 0, 1) for x in (*a, *b)):
        raise ValueError('Invalid state.')
    if not any(x != 0 for x in a):
        return 0.0
    denominator = sum(x != 0 or y < 0 for x, y in zip(a, b))
    numerator = sum(x == y and x != 0 for x, y in zip(a, b))
    return numerator / denominator if denominator and numerator else 0.0


def single_window_pred_score(a: int, b: int, pa: float = 1.0, pb: float = 1.0) -> float:
    """Restricted one-window analogue of CNV_profile_jaccard_prob(mode='pred')."""
    if a not in (-1, 0, 1) or b not in (-1, 0, 1):
        raise ValueError('Invalid state.')
    if not (0 <= pa <= 1 and 0 <= pb <= 1):
        raise ValueError('Probabilities must lie in [0,1].')
    denominator = sum(a == state or b == state for state in (-1, 1))
    numerator = sum(pa * pb for state in (-1, 1) if a == b == state)
    return numerator / denominator if denominator else 0.0


def inner_band_fraction(radius: float, depth: float) -> float:
    """Area fraction of an inner band in a circular 2D toy region."""
    if not (math.isfinite(radius) and math.isfinite(depth) and 0 <= depth <= radius and radius > 0):
        raise ValueError('Require finite radius>0 and 0<=depth<=radius.')
    return 2 * depth / radius - (depth / radius) ** 2


class SanityTests(unittest.TestCase):
    def test_paper_same(self):
        self.assertEqual(paper_signed_similarity([1, -1], [1, -1], [10, 20]), 1.0)
    def test_paper_opposite(self):
        self.assertEqual(paper_signed_similarity([1], [-1], [10]), -1.0)
    def test_all_neutral(self):
        self.assertIsNone(paper_signed_similarity([0], [0], [10]))
    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            paper_signed_similarity([2], [1], [10])
        with self.assertRaises(ValueError):
            paper_signed_similarity([1], [1], [0])
    def test_hard_asymmetry(self):
        self.assertEqual(simplified_public_hard_score([1, 0], [1, 1]), 1.0)
        self.assertEqual(simplified_public_hard_score([1, 1], [1, 0]), 0.5)
        self.assertEqual(paper_signed_similarity([1, 0], [1, 1], [10, 10]), 0.5)
    def test_selected_pred_vs_paper(self):
        self.assertEqual(single_window_pred_score(1, -1), 0.0)
        self.assertEqual(paper_signed_similarity([1], [-1], [1]), -1.0)
    def test_uncertain_self_score(self):
        self.assertAlmostEqual(single_window_pred_score(1, 1, .8, .8), .64)
    def test_geometry_dilution(self):
        self.assertAlmostEqual(inner_band_fraction(100, 10), .19)
        self.assertAlmostEqual(inner_band_fraction(200, 10), .0975)
        self.assertGreater(inner_band_fraction(100, 10), inner_band_fraction(200, 10))
    def test_geometry_limits(self):
        self.assertEqual(inner_band_fraction(100, 0), 0)
        self.assertEqual(inner_band_fraction(100, 100), 1)
        with self.assertRaises(ValueError):
            inner_band_fraction(0, 0)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SanityTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {'scope': 'synthetic_mathematical_checks_only', 'python': platform.python_version(),
              'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'success': result.wasSuccessful(), 'author_pipeline_executed': False,
              'patient_data_used': False}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
