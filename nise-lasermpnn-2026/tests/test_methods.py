from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from geometry import complex_rmsd, kabsch
from screen import GatePolicy, evaluate_rows, normalized_plddt
from binding import (bound_complex, bound_fraction, competition, fit_direct,
                     fit_competition, proofreading_delta, mutant_cycle, wilson_interval)


class GeometryTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(1)
        self.p, self.l = rng.normal(size=(10, 3)), rng.normal(size=(5, 3))

    def test_joint_rigid_transform(self):
        r = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
        out = complex_rmsd(self.p @ r + 2, self.p, self.l @ r + 2, self.l)
        self.assertLess(out["protein_rmsd_A"], 1e-12)
        self.assertLess(out["ligand_rmsd_A"], 1e-12)

    def test_ligand_translation_is_not_erased(self):
        out = complex_rmsd(self.p, self.p, self.l + [3, 0, 0], self.l)
        self.assertAlmostEqual(out["ligand_rmsd_A"], 3)

    def test_reflection_excluded(self):
        r, _, error = kabsch(self.p * [-1, 1, 1], self.p)
        self.assertAlmostEqual(np.linalg.det(r), 1)
        self.assertGreater(error, .1)

    def test_allowed_atom_permutation(self):
        permutation = [1, 0, 2, 3, 4]
        out = complex_rmsd(self.p, self.p, self.l[permutation], self.l,
                           allowed_permutations=[permutation])
        self.assertLess(out["ligand_rmsd_A"], 1e-12)

    def test_invalid_mapping(self):
        with self.assertRaises(ValueError):
            complex_rmsd(self.p, self.p, self.l, self.l, allowed_permutations=[[0] * 5])

    def test_nonfinite_coordinates(self):
        self.p[0, 0] = np.nan
        with self.assertRaises(ValueError):
            kabsch(self.p, self.p)

    def test_collinear_alignment(self):
        with self.assertRaises(ValueError):
            kabsch([[0, 0, 0], [1, 0, 0], [2, 0, 0]], [[0, 0, 0], [1, 0, 0], [2, 0, 0]])


class ScreeningTests(unittest.TestCase):
    def setUp(self):
        self.policy = GatePolicy(2.5, 2.5, .8)
        self.row = dict(candidate_id="a", protein_rmsd_A=1, ligand_rmsd_A=1,
                        ligand_plddt=90, plddt_scale="0-100", mapping_valid=True,
                        burial_pass=True, debug=False)

    def test_valid(self):
        self.assertTrue(evaluate_rows([self.row], self.policy)[0]["passed"])

    def test_scales(self):
        self.assertAlmostEqual(normalized_plddt(90, "0-100"), normalized_plddt(.9, "0-1"))

    def test_wrong_scale(self):
        self.row["plddt_scale"] = "0-1"
        self.assertFalse(evaluate_rows([self.row], self.policy)[0]["passed"])

    def test_nan(self):
        self.row["ligand_rmsd_A"] = np.nan
        self.assertFalse(evaluate_rows([self.row], self.policy)[0]["passed"])

    def test_threshold_is_strict(self):
        self.row["ligand_rmsd_A"] = 2.5
        self.assertFalse(evaluate_rows([self.row], self.policy)[0]["passed"])

    def test_debug_rejected(self):
        self.row["debug"] = True
        self.assertFalse(evaluate_rows([self.row], self.policy)[0]["passed"])

    def test_boolean_string_rejected_in_api(self):
        self.row["mapping_valid"] = "false"
        self.assertFalse(evaluate_rows([self.row], self.policy)[0]["passed"])

    def test_missing_field(self):
        del self.row["mapping_valid"]
        self.assertFalse(evaluate_rows([self.row], self.policy)[0]["passed"])

    def test_duplicate_id(self):
        with self.assertRaises(ValueError):
            evaluate_rows([self.row, self.row], self.policy)

    def test_pbind_missing_when_required(self):
        self.assertFalse(evaluate_rows([self.row], GatePolicy(2.5, 2.5, .8, .5))[0]["passed"])

    def test_bad_policy(self):
        with self.assertRaises(ValueError):
            GatePolicy(-1, 2.5, .8)


class BindingTests(unittest.TestCase):
    def test_mass_conservation(self):
        p = np.logspace(-4, 5, 100)
        l, k = 50., 1.2
        x = bound_complex(p, l, k)
        np.testing.assert_allclose((p - x) * (l - x), k * x, rtol=1e-9, atol=1e-9)
        self.assertTrue(np.all(x <= np.minimum(p, l)))

    def test_tight_binding_depletion(self):
        fraction = float(bound_fraction(25., 50., .001))
        self.assertLess(fraction, .5)
        self.assertGreater(fraction, .49)

    def test_zero_protein(self):
        self.assertEqual(float(bound_fraction(0., 10., 1.)), 0)

    def test_invalid_ligand(self):
        with self.assertRaises(ValueError):
            bound_fraction(1., 0., 1.)

    def test_competitive_conservation(self):
        out = competition(2., 1., 3., .7, .2)
        total = out["protein_free"] + out["tracer_complex"] + out["competitor_complex"]
        self.assertAlmostEqual(float(total), 2., places=10)

    def test_no_competitor_matches_quadratic(self):
        p = np.logspace(-2, 3, 50)
        out = competition(p, 2., 0., .5, 1.)["tracer_complex"]
        np.testing.assert_allclose(out, bound_complex(p, 2., .5), rtol=1e-10, atol=1e-10)

    def test_competitor_reduces_occupancy(self):
        out = competition(2., 1., np.array([0., 1., 10.]), .7, .2)["tracer_complex"]
        self.assertTrue(np.all(np.diff(out) < 0))

    def test_direct_fit_recovers_synthetic_kd(self):
        p = np.logspace(-2, 3, 80)
        y = bound_fraction(p, 3., 2.3)
        result = fit_direct(p, 3., y, initial_kd=1., bounds=(1e-5, 1e4))
        self.assertAlmostEqual(result["kd"][0], 2.3, places=6)

    def test_competition_global_fit(self):
        p = np.r_[np.logspace(-2, 2, 30), np.repeat([1., 3.], 30)]
        l = np.full(len(p), .5)
        i = np.r_[np.zeros(30), np.tile(np.logspace(-3, 3, 30), 2)]
        y = competition(p, l, i, 1.4, .23)["tracer_complex"] / l
        result = fit_competition(p, l, i, y, initial_kds=[1., .5], bounds=(1e-5, 1e4))
        np.testing.assert_allclose(result["kd"], [1.4, .23], rtol=1e-5)
        self.assertTrue(result["local_jacobian_full_rank"])

    def test_shape_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            fit_direct([1., 2.], 1., [0., .1, .2], initial_kd=1., bounds=(1e-5, 1e4))

    def test_probability_delta(self):
        out = proofreading_delta(.1, .4, .1, .2)
        self.assertAlmostEqual(out["holo_minus_apo_heuristic"], np.log10(2))
        self.assertFalse(out["is_free_energy"])

    def test_zero_probability_rejected(self):
        with self.assertRaises(ValueError):
            proofreading_delta(0., .4, .1, .2)

    def test_mutant_cycle_additive_case(self):
        out = mutant_cycle(100., 10., 20., 2., temperature_K=298.15)
        self.assertAlmostEqual(out["coupling_kcal_mol"], 0., places=12)

    def test_wilson_not_certainty(self):
        low, high = wilson_interval(4, 4)
        self.assertLess(low, .6)
        self.assertAlmostEqual(high, 1.)


if __name__ == "__main__":
    unittest.main()
