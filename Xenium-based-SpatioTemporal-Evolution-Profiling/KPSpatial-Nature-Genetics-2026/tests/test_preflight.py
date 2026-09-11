"""Synthetic contract tests and one public-file test, not paper result tests."""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from preflight import REQUIRED_SAMPLE_FIELDS, audit_puck, audit_samples, leaves_to_remove, read_tsv


class PreflightTests(unittest.TestCase):
    def table(self, rows):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / "samples.tsv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=REQUIRED_SAMPLE_FIELDS, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
        return path

    def row(self, sample="s1", animal="a1", tumor="t1", section="sec1", stage="early", batch="b1"):
        return dict(zip(REQUIRED_SAMPLE_FIELDS, (sample, animal, tumor, section, stage, batch)))

    def test_keep_complement(self):
        self.assertEqual(leaves_to_remove(["a", "b", "c"], ["a", "b"]), ["c"])

    def test_reverse_difference_is_empty(self):
        self.assertEqual({"a", "b"} - {"a", "b", "c"}, set())

    def test_empty_group_rejected(self):
        with self.assertRaises(ValueError):
            leaves_to_remove(["a"], [])

    def test_unknown_leaf_rejected(self):
        with self.assertRaises(ValueError):
            leaves_to_remove(["a"], ["b"])

    def test_duplicate_leaf_rejected(self):
        with self.assertRaises(ValueError):
            leaves_to_remove(["a", "a"], ["a"])

    def test_three_values_do_not_unpack_into_two(self):
        with self.assertRaises(ValueError):
            state, concordance = (1, 0.8, 5)

    def test_header_only_rejected(self):
        with self.assertRaises(ValueError):
            read_tsv(self.table([]), REQUIRED_SAMPLE_FIELDS)

    def test_empty_identity_rejected(self):
        with self.assertRaises(ValueError):
            audit_samples(self.table([self.row(animal="")]))

    def test_duplicate_sample_rejected(self):
        with self.assertRaises(ValueError):
            audit_samples(self.table([self.row(), self.row()]))

    def test_batch_nesting_warning(self):
        rows = [self.row(), self.row("s2", "a2", "t2", "sec2", "late", "b2")]
        self.assertTrue(audit_samples(self.table(rows))["stage_determined_by_batch"])

    def test_shared_batch_not_complete_nesting(self):
        rows = [self.row(), self.row("s2", "a2", "t2", "sec2", "late", "b1")]
        self.assertFalse(audit_samples(self.table(rows))["stage_determined_by_batch"])

    def test_tumor_parent_conflict(self):
        rows = [self.row(), self.row("s2", "a2", "t1", "sec2", "late", "b1")]
        self.assertTrue(audit_samples(self.table(rows))["errors"])

    def test_public_metadata(self):
        result = audit_puck(ROOT / "evidence" / "puck_meta.txt")
        self.assertEqual(result["arrays"], 49)
        self.assertEqual(result["platform_counts"], {"Slide-seq": 44, "Slide-tags": 5})
        self.assertEqual(result["unique_mouse_ids"], 24)
        self.assertEqual(result["slide_tags_mouse_ids"], ["SPC-11"])


if __name__ == "__main__":
    unittest.main()
