#!/usr/bin/env python3
"""Synthetic definition checks, NOT a reimplementation of author R analyses."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import platform
import sys
import tempfile
import unittest
from pathlib import Path
from audit_inputs import audit_cells


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered or not 0 <= probability <= 1 or not all(map(math.isfinite, ordered)):
        raise ValueError("finite nonempty values and probability in [0,1] required")
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    return ordered[lower] + (position - lower) * (ordered[upper] - ordered[lower])


def score_call(ref: list[float], score: float, lower: float) -> bool:
    a, b = quantile(ref, lower), quantile(ref, .995)
    if b <= a:
        raise ValueError("degenerate reference scaling interval")
    normalized = [(value - a) / (b - a) for value in ref]
    threshold = max(1., quantile(normalized, .99))
    return (score - a) / (b - a) > threshold


class DefinitionTests(unittest.TestCase):
    def test_score_floor_equals_raw_upper_quantile(self):
        ref = [float(i) for i in range(1, 1001)]
        for lower in (.005, .05):
            for score in (1., 980., 994., 997., 1200.):
                self.assertEqual(score_call(ref, score, lower), score > quantile(ref, .995))

    def test_lower_bound_changes_values_not_calls(self):
        ref = [float(i) for i in range(1, 1001)]
        score = 700.
        b = quantile(ref, .995)
        x = [(score - quantile(ref, a)) / (b - quantile(ref, a)) for a in (.005, .05)]
        self.assertNotEqual(x[0], x[1])
        self.assertEqual(score_call(ref, score, .005), score_call(ref, score, .05))

    def test_degenerate_reference_is_rejected(self):
        with self.assertRaises(ValueError):
            score_call([2., 2., 2.], 3., .005)

    def test_top_two_tie_counterexample(self):
        x = [.4, .4, .1, .1]
        correct = sorted(x, reverse=True)[0] / sorted(x, reverse=True)[1]
        next_distinct = max(x) / max(value for value in x if value != max(x))
        self.assertEqual(correct, 1.)
        self.assertEqual(next_distinct, 4.)

    def test_jaccard_excluding_value_loses_identical_other(self):
        # Row 0 compares self, an identical other set, and a disjoint set.
        row = [1., 1., 0.]
        self.assertEqual(max(row[1:]), 1.)
        self.assertEqual(max(value for value in row if value != 1.), 0.)

    def test_conditional_fraction_identity(self):
        n_state, n_lineage, n_all = 30, 60, 200
        self.assertAlmostEqual(n_state / n_all, (n_lineage / n_all) * (n_state / n_lineage))

    def test_constant_state_count_changing_denominator(self):
        self.assertEqual(100 / 200, .5)
        self.assertEqual(100 / 400, .25)

    def test_pooled_fraction_differs_from_individual_mean(self):
        pooled = (9 + 10) / (10 + 100)
        equal_weighted = (.9 + .1) / 2
        self.assertNotAlmostEqual(pooled, equal_weighted)

    def test_overlapping_program_rates_can_exceed_one(self):
        assignments = [(True, True), (True, False), (False, True)]
        rates = [sum(row[k] for row in assignments) / len(assignments) for k in (0, 1)]
        self.assertGreater(sum(rates), 1.)

    def test_rcop_positive_with_zero_within_group_covariance(self):
        a, b = [0., 0., 2., 2.], [0., 2., 0., 2.]
        ma, mb = sum(a) / 4, sum(b) / 4
        rcop = math.sqrt(ma * mb)
        covariance = sum((x - ma) * (y - mb) for x, y in zip(a, b)) / 4
        self.assertEqual(rcop, 1.)
        self.assertEqual(covariance, 0.)

    def test_identical_margins_do_not_identify_transition(self):
        p = [.5, .5]
        matrices = [[[1., 0.], [0., 1.]], [[0., 1.], [1., 0.]]]
        outputs = [[sum(p[i] * matrix[i][j] for i in (0, 1)) for j in (0, 1)] for matrix in matrices]
        self.assertNotEqual(matrices[0], matrices[1])
        self.assertEqual(outputs[0], outputs[1])


class InputTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.map = self.root / "states.csv"
        self.map.write_text("state,lineage\nA,Cancer\nB,Myeloid\nC,Myeloid\n", encoding="utf-8")
        self.fields = ["individual_id", "sample_id", "stage", "cell_id", "lineage", "state"]

    def tearDown(self):
        self.tmp.cleanup()

    def write_cells(self, rows):
        path = self.root / "cells.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(self.fields)
            writer.writerows(rows)
        return path

    def test_absent_parent_is_na_not_zero(self):
        path = self.write_cells([["synthetic1", "s1", "early", "c1", "Cancer", "A"]])
        result, _ = audit_cells(path, self.map)
        row = next(row for row in result if row["state"] == "B")
        self.assertIsNone(row["within_lineage_fraction"])
        self.assertEqual(row["whole_sample_fraction"], 0.)
        self.assertEqual(row["missing_reason"], "parent_lineage_not_observed")

    def test_present_parent_absent_state_is_zero(self):
        path = self.write_cells([["synthetic1", "s1", "early", "c1", "Myeloid", "B"]])
        result, _ = audit_cells(path, self.map)
        row = next(row for row in result if row["state"] == "C")
        self.assertEqual(row["within_lineage_fraction"], 0.)
        self.assertEqual(row["missing_reason"], "")

    def test_same_cell_id_across_samples_is_allowed(self):
        path = self.write_cells([["synthetic1", "s1", "early", "c1", "Cancer", "A"],
                                 ["synthetic2", "s2", "late", "c1", "Cancer", "A"]])
        _, summary = audit_cells(path, self.map)
        self.assertEqual(summary["n_individuals"], 2)

    def test_duplicate_within_sample_is_rejected(self):
        row = ["synthetic1", "s1", "early", "c1", "Cancer", "A"]
        path = self.write_cells([row, row])
        with self.assertRaisesRegex(ValueError, "duplicate sample/cell"):
            audit_cells(path, self.map)

    def test_sample_conflict_is_rejected(self):
        path = self.write_cells([["synthetic1", "s1", "early", "c1", "Cancer", "A"],
                                 ["synthetic2", "s1", "late", "c2", "Cancer", "A"]])
        with self.assertRaisesRegex(ValueError, "conflicting"):
            audit_cells(path, self.map)

    def test_lineage_mismatch_is_rejected(self):
        path = self.write_cells([["synthetic1", "s1", "early", "c1", "Cancer", "B"]])
        with self.assertRaisesRegex(ValueError, "lineage mismatch"):
            audit_cells(path, self.map)

    def test_repeated_individual_is_flagged_not_assumed_invalid(self):
        path = self.write_cells([["synthetic1", "s1", "early", "c1", "Cancer", "A"],
                                 ["synthetic1", "s2", "late", "c2", "Cancer", "A"]])
        _, summary = audit_cells(path, self.map)
        self.assertEqual(summary["individuals_observed_at_multiple_stages"], ["synthetic1"])
        self.assertTrue(summary["warnings"])

    def test_nonfinite_coordinates_are_rejected(self):
        self.fields += ["x_um", "y_um"]
        path = self.write_cells([["synthetic1", "s1", "early", "c1", "Cancer", "A", "nan", "0"]])
        with self.assertRaisesRegex(ValueError, "coordinates"):
            audit_cells(path, self.map)

    def test_empty_cells_are_rejected(self):
        path = self.write_cells([])
        with self.assertRaisesRegex(ValueError, "no observations"):
            audit_cells(path, self.map)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    receipt = {"synthetic_only": True, "patient_analysis_runs": 0,
               "animal_analysis_runs": 0, "python_version": platform.python_version(),
               "tests_run": result.testsRun, "failures": len(result.failures),
               "errors": len(result.errors), "skipped": len(result.skipped),
               "success": result.wasSuccessful(),
               "script_sha256": {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                                 for name in ("toy_checks.py", "audit_inputs.py")},
               "failed_test_ids": [test.id() for test, _ in result.failures + result.errors],
               "scope": "Synthetic identities, counterexamples and input contracts; no author model execution"}
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
