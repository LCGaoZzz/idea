"""Synthetic tests only. No paper inputs, external services, or random data."""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from sensitivity_checks import (classify_clone, zero_detection_upper, roe_counts,
                                bh_adjust, radius_counts, equal_host_contrast)


class RuleTests(unittest.TestCase):
    def test_pre_and_inverse(self):
        self.assertEqual(classify_clone(495, 5), 'pre_specific')
        self.assertEqual(classify_clone(5, 495), 'inv_specific')

    def test_scale_dependence(self):
        self.assertEqual(classify_clone(4950, 50), 'shared')

    def test_strict_fraction_boundary(self):
        self.assertEqual(classify_clone(95, 5), 'shared')

    def test_strict_count_boundary(self):
        self.assertEqual(classify_clone(1000, 25), 'shared')
        self.assertEqual(classify_clone(1000, 24), 'pre_specific')

    def test_zero_is_unobserved(self):
        self.assertEqual(classify_clone(0, 0), 'not_observed')

    def test_invalid_counts(self):
        for x in [-1, 1.5, True]:
            with self.subTest(x=x), self.assertRaises(ValueError):
                classify_clone(x, 1)

    def test_invalid_fraction(self):
        with self.assertRaises(ValueError):
            classify_clone(10, 1, min_fraction=0.4)

    def test_zero_detection_equation(self):
        u = zero_detection_upper(100)
        self.assertAlmostEqual((1 - u) ** 100, 0.05)

    def test_detection_and_monotonicity(self):
        self.assertLess(zero_detection_upper(200), zero_detection_upper(100))
        self.assertAlmostEqual(zero_detection_upper(100, detection_probability=0.5),
                               2 * zero_detection_upper(100))
        self.assertEqual(zero_detection_upper(1, detection_probability=0.1), 1)

    def test_invalid_detection_inputs(self):
        with self.assertRaises(ValueError):
            zero_detection_upper(0)
        with self.assertRaises(ValueError):
            zero_detection_upper(100, detection_probability=0)


class TableTests(unittest.TestCase):
    def test_roe_independence(self):
        expected, ratio = roe_counts([[10, 20], [20, 40]])
        np.testing.assert_allclose(expected, [[10, 20], [20, 40]])
        np.testing.assert_allclose(ratio, 1)

    def test_roe_zero_column(self):
        expected, ratio = roe_counts([[1, 0], [2, 0]])
        self.assertTrue(np.isnan(ratio[:, 1]).all())
        self.assertTrue((expected[:, 1] == 0).all())

    def test_invalid_roe(self):
        for data in [[[0, 0]], [[1, -1]], [[1, np.nan]]]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                roe_counts(data)

    def test_bh_hand_example(self):
        np.testing.assert_allclose(bh_adjust([0.01, 0.04, 0.03]), [0.03, 0.04, 0.04])

    def test_bh_empty_and_invalid(self):
        self.assertEqual(len(bh_adjust([])), 0)
        for p in [[-0.1], [1.1], [np.nan]]:
            with self.subTest(p=p), self.assertRaises(ValueError):
                bh_adjust(p)

    def test_bh_permutation(self):
        p = np.array([0.3, 0.01, 0.9, 0.03, 0.04])
        order = np.array([4, 2, 0, 1, 3])
        np.testing.assert_allclose(bh_adjust(p)[order], bh_adjust(p[order]))

    def test_denominator_example(self):
        self.assertEqual((20 / 200) / (20 / 100), 0.5)


class SpatialTests(unittest.TestCase):
    def calculate(self, include_self=False, keys=None, ids=None, chunk_size=1):
        return radius_counts([[0, 0], [1, 0], [0, 0]], ['T', 'O', 'T'],
            keys or [('a', 's', 'd'), ('a', 's', 'd'), ('b', 's', 'd')],
            ids or ['1', '2', '1'], radius_um=1, include_self=include_self,
            target_label='T', chunk_size=chunk_size)

    def test_domain_isolation_and_boundary(self):
        out = self.calculate()
        np.testing.assert_array_equal(out.total, [1, 1, 0])
        np.testing.assert_array_equal(out.target, [0, 1, 0])
        self.assertTrue(np.isnan(out.proportion[2]))
        self.assertEqual(out.edge_policy, 'not_corrected')

    def test_explicit_self_policy(self):
        out = self.calculate(include_self=True)
        np.testing.assert_array_equal(out.total, [2, 2, 1])
        np.testing.assert_array_equal(out.target, [1, 1, 1])

    def test_chunk_invariance(self):
        np.testing.assert_array_equal(self.calculate().target, self.calculate(chunk_size=100).target)

    def test_duplicate_identity_rejected(self):
        with self.assertRaises(ValueError):
            self.calculate(keys=[('a', 's', 'd')] * 3, ids=['1', '2', '1'])

    def test_empty_target(self):
        out = radius_counts([[0, 0], [0.5, 0]], ['O', 'O'], [('a', 's', 'd')] * 2,
                            ['1', '2'], radius_um=1, include_self=False, target_label='T')
        np.testing.assert_array_equal(out.target, [0, 0])
        np.testing.assert_allclose(out.proportion, 0)

    def test_nonfinite_coordinates_rejected(self):
        with self.assertRaises(ValueError):
            radius_counts([[np.nan, 0]], ['T'], [('a', 's', 'd')], ['1'],
                          radius_um=1, include_self=False, target_label='T')

    def test_missing_domain_rejected(self):
        with self.assertRaises(ValueError):
            radius_counts([[0, 0]], ['T'], [('a', 's', '')], ['1'],
                          radius_um=1, include_self=False, target_label='T')

    def test_nonboolean_self_policy_rejected(self):
        with self.assertRaises(ValueError):
            self.calculate(include_self='false')

    def test_empty_spatial_input(self):
        out = radius_counts(np.empty((0, 2)), [], [], [], radius_um=1,
                            include_self=False, target_label='T')
        self.assertEqual(out.total.size, 0)


class HostTests(unittest.TestCase):
    def test_equal_hosts_not_equal_cells(self):
        values = [10] * 100 + [0] + [2, 0]
        hosts = ['a'] * 101 + ['b', 'b']
        groups = ['E'] * 100 + ['C', 'E', 'C']
        out = equal_host_contrast(values, hosts, groups, exposed='E', control='C')
        self.assertEqual(out['equal_host_mean'], 6)
        self.assertEqual(out['n_included_hosts'], 2)

    def test_missing_arm_reported(self):
        out = equal_host_contrast([2, 0, 10], ['a', 'a', 'b'], ['E', 'C', 'E'],
                                  exposed='E', control='C')
        self.assertEqual(out['excluded_hosts'], {'b': 'missing comparison arm'})

    def test_no_comparable_host_rejected(self):
        with self.assertRaises(ValueError):
            equal_host_contrast([1], ['a'], ['E'], exposed='E', control='C')

    def test_nonfinite_values_rejected(self):
        with self.assertRaises(ValueError):
            equal_host_contrast([np.nan, 0], ['a', 'a'], ['E', 'C'], exposed='E', control='C')


if __name__ == '__main__':
    unittest.main(verbosity=2)
