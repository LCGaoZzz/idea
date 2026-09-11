"""Synthetic arithmetic/input tests only; no paper or biological data."""
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from mixture_decomposition import Row, decompose


class DecompositionTests(unittest.TestCase):
    def run_case(self, rows, a="A", b="B"):
        return decompose(rows, a, b, profiles_complete=True)

    def test_pure_mixture(self):
        rows = [Row("a", "A", "low", 9, 0), Row("a", "A", "high", 1, 10),
                Row("b", "B", "low", 1, 0), Row("b", "B", "high", 9, 10)]
        r = self.run_case(rows)
        self.assertAlmostEqual(r["delta_b_minus_a"], 8)
        self.assertAlmostEqual(r["mixture_term"], 8)
        self.assertAlmostEqual(r["within_term"], 0)

    def test_pure_within(self):
        rows = [Row("a", "A", "low", 1, 0), Row("a", "A", "high", 1, 10),
                Row("b", "B", "low", 1, 2), Row("b", "B", "high", 1, 12)]
        r = self.run_case(rows)
        self.assertAlmostEqual(r["mixture_term"], 0)
        self.assertAlmostEqual(r["within_term"], 2)

    def test_identity_and_reversal(self):
        rows = [Row("a", "A", "x", 3, -2), Row("a", "A", "y", 7, 5),
                Row("b", "B", "x", 8, 1), Row("b", "B", "y", 2, 9)]
        r, rev = self.run_case(rows), self.run_case(rows, "B", "A")
        self.assertAlmostEqual(r["identity_residual"], 0)
        self.assertAlmostEqual(r["delta_b_minus_a"], -rev["delta_b_minus_a"])
        self.assertAlmostEqual(r["mixture_term"], -rev["mixture_term"])
        self.assertAlmostEqual(r["within_term"], -rev["within_term"])

    def test_equal_animals_not_equal_cells(self):
        rows = [Row("a1", "A", "x", 100, 0), Row("a2", "A", "x", 1, 10),
                Row("b1", "B", "x", 1, 5)]
        r = self.run_case(rows)
        self.assertAlmostEqual(r["groups"]["A"]["mean"], 5)
        self.assertAlmostEqual(r["delta_b_minus_a"], 0)

    def test_group_exclusive_state_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "NO_COMMON_SUPPORT"):
            self.run_case([Row("a", "A", "x", 1, 0), Row("b", "B", "y", 1, 0)])

    def test_duplicate_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.run_case([Row("a", "A", "x", 1, 0), Row("a", "A", "x", 2, 1)])

    def test_nonfinite_and_zero_counts(self):
        for n, mean in [(0, 1), (-1, 1), (1, math.nan), (1, math.inf)]:
            with self.subTest(n=n, mean=mean), self.assertRaises(ValueError):
                self.run_case([Row("a", "A", "x", n, mean)])

    def test_incomplete_profiles_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "complete profiles"):
            decompose([], "A", "B")

    def test_same_animal_across_groups_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "disjoint"):
            self.run_case([Row("a", "A", "x", 1, 0), Row("a", "B", "y", 1, 1)])

    def test_cli_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src, out = root / "input.tsv", root / "out.json"
            src.write_text("animal_id\tgroup\tstate\tn\tmean\na\tA\tx\t1\t0\nb\tB\tx\t1\t2\n")
            command = [sys.executable, str(Path(__file__).with_name("mixture_decomposition.py")),
                       "--input", str(src), "--group-a", "A", "--group-b", "B",
                       "--out", str(out), "--profiles-complete"]
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(out.read_text())
            self.assertEqual(result["delta_b_minus_a"], 2)
            self.assertFalse(result["paper_reproduction"])
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(second.returncode, 2)
            self.assertEqual(json.loads(out.read_text()), result)


if __name__ == "__main__":
    unittest.main()
