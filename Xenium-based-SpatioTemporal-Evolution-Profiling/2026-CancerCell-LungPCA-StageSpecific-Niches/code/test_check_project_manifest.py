"""Synthetic tests only; fixtures are not study or user data."""
import unittest
from check_project_manifest import audit


def fixture(animal, stage, batch="shared", section=None, sample=None):
    return dict(animal_id=animal, sample_id=sample or animal + "_" + stage,
                section_id=section or animal + "_" + stage + "_s1",
                coordinate_frame_id=animal + "_frame", stage=stage,
                batch_id=batch, panel_id="common_panel")


class ManifestTests(unittest.TestCase):
    def test_clean_crossed_design(self):
        rows = [fixture(f"a{i}", stage) for i, stage in enumerate(["early", "early", "late", "late"])]
        result = audit(rows, "destructive", ["early", "late"])
        self.assertTrue(result["valid_metadata"])
        self.assertEqual(result["warnings"], [])

    def test_sections_do_not_inflate_animals(self):
        rows = [fixture("a", "early", section="s1"), fixture("a", "early", section="s2")]
        self.assertEqual(audit(rows, "destructive", ["early"])["animal_counts_by_stage"], {"early": 1})

    def test_batch_confounding_warning(self):
        rows = [fixture("a", "early", "b1"), fixture("b", "late", "b2")]
        result = audit(rows, "destructive", ["early", "late"])
        self.assertTrue(any("DISCONNECTED_STAGE_BATCH_ID" in w for w in result["warnings"]))
        self.assertTrue(result["valid_metadata"])

    def test_reused_animal_destructive(self):
        result = audit([fixture("a", "early"), fixture("a", "late")], "destructive", ["early", "late"])
        self.assertTrue(any("DESTRUCTIVE_ANIMAL_REUSED" in e for e in result["errors"]))

    def test_reused_animal_longitudinal(self):
        result = audit([fixture("a", "early"), fixture("a", "late")], "longitudinal", ["early", "late"])
        self.assertTrue(result["valid_metadata"])

    def test_duplicate_section(self):
        row = fixture("a", "early")
        result = audit([row, row.copy()], "destructive", ["early"])
        self.assertTrue(any("DUPLICATE_SECTION" in e for e in result["errors"]))

    def test_sample_animal_conflict(self):
        result = audit([fixture("a", "early", sample="x"), fixture("b", "early", sample="x")],
                       "destructive", ["early"])
        self.assertTrue(any("SAMPLE_ANIMAL_CONFLICT" in e for e in result["errors"]))

    def test_empty_data(self):
        self.assertFalse(audit([], "unknown", ["early"])["valid_metadata"])

    def test_missing_fields_and_unknown_stage(self):
        result = audit([{}, fixture("a", "other")], "unknown", ["early"])
        self.assertTrue(any("MISSING_FIELDS" in e for e in result["errors"]))
        self.assertTrue(any("UNKNOWN_STAGE" in e for e in result["errors"]))

    def test_duplicate_expected_stages_rejected(self):
        with self.assertRaises(ValueError):
            audit([], "unknown", ["early", "early"])

    def test_indirect_batch_overlap_connects_stages(self):
        rows = [fixture("a", "early", "b1"), fixture("b", "middle", "b1"),
                fixture("c", "middle", "b2"), fixture("d", "late", "b2")]
        result = audit(rows, "destructive", ["early", "middle", "late"])
        self.assertEqual(len(result["stage_components"]["batch_id"]), 1)
        self.assertFalse(any("DISCONNECTED_STAGE_BATCH_ID" in w for w in result["warnings"]))


if __name__ == "__main__":
    unittest.main()
