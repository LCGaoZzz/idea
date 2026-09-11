"""Small synthetic unit tests; these do not validate the paper's biology."""
import unittest
import warnings
import numpy as np
import pandas as pd
from niche_idea import summarize_serpin, build_roi_table, farthest_point_sample, factorial_contrasts, bootstrap_mean


class NicheTests(unittest.TestCase):
    def setUp(self):
        self.expr = pd.DataFrame({"source": ["s"]*4, "patient_id": ["p"]*4,
                                  "cell_id": list("abcd"), "is_malignant": [True]*4,
                                  "SERPINE1": [0, 0, 0, 8], "SERPINB2": [0, 0, 2, 0]})
        self.cells = pd.DataFrame({"image_id": ["A"]*3+["B"]*2,
                                  "patient_id": ["p1"]*3+["p2"]*2,
                                  "cell_id": ["a", "b", "c", "a", "b"],
                                  "x_um": [0, 1, 2, 0, 1], "y_um": [0]*5,
                                  "phenotype": ["CTRL", "KO", "CD8", "CTRL", "CTRL"]})
        self.centers = pd.DataFrame({"image_id": ["A", "B"], "roi_id": ["r", "r"],
                                    "x_um": [0., 0.], "y_um": [0., 0.]})
        self.kw = dict(radius_um=3, control_label="CTRL", ko_label="KO", immune_labels=["CD8"], assume_full_tissue=True)

    def test_mean_decomposition(self):
        r = summarize_serpin(self.expr, representation="raw_counts").iloc[0]
        self.assertEqual(r.fraction_SERPINE1_pos, .25)
        self.assertEqual(r.mean_SERPINE1_positive, 8)
        self.assertEqual(r.mean_SERPINE1_all, r.fraction_SERPINE1_pos*r.mean_SERPINE1_positive)
        self.assertEqual(r.n_union_pos, 2)

    def test_positive_mean_is_undefined_without_positive_cells(self):
        x = self.expr.copy(); x["SERPINE1"] = 0
        r = summarize_serpin(x, representation="raw_counts").iloc[0]
        self.assertTrue(np.isnan(r.mean_SERPINE1_positive))

    def test_scaled_representation_is_rejected(self):
        with self.assertRaises(ValueError): summarize_serpin(self.expr, representation="scaled")

    def test_negative_expression_is_rejected(self):
        x = self.expr.copy(); x.loc[0,"SERPINE1"] = -1
        with self.assertRaises(ValueError): summarize_serpin(x, representation="raw_counts")

    def test_fractional_raw_counts_are_rejected(self):
        x = self.expr.astype({"SERPINE1": float}); x.loc[0,"SERPINE1"] = .5
        with self.assertRaises(ValueError): summarize_serpin(x, representation="raw_counts")

    def test_no_malignant_is_not_zero_prevalence(self):
        x = self.expr.copy(); x["is_malignant"] = False
        with self.assertRaises(ValueError): summarize_serpin(x, representation="raw_counts")

    def test_duplicate_cells_are_rejected(self):
        with self.assertRaises(ValueError): summarize_serpin(pd.concat([self.expr,self.expr]), representation="raw_counts")

    def test_images_do_not_mix_despite_identical_coordinates(self):
        r = build_roi_table(self.cells,self.centers,**self.kw).table
        self.assertEqual(list(r.n_total),[3,2]); self.assertEqual(list(r.p_control),[.5,1.])
        self.assertEqual(list(r.n_immune),[1,0])

    def test_area_opt_in_is_required(self):
        kw = dict(self.kw); kw["assume_full_tissue"] = False
        with self.assertRaises(ValueError): build_roi_table(self.cells,self.centers,**kw)

    def test_effective_area_and_density(self):
        c = self.centers.copy(); c["area_um2"] = 10.
        r = build_roi_table(self.cells,c,**self.kw).table.iloc[0]
        self.assertAlmostEqual(r.immune_density_per_mm2,100000.)
        self.assertEqual(r.area_kind,"supplied_mask_intersection")

    def test_invalid_area_rejected(self):
        c = self.centers.copy(); c["area_um2"] = 100.
        with self.assertRaises(ValueError): build_roi_table(self.cells,c,**self.kw)

    def test_unknown_image_rejected(self):
        c = self.centers.copy(); c.loc[0,"image_id"] = "missing"
        with self.assertRaises(ValueError): build_roi_table(self.cells,c,**self.kw)

    def test_empty_immune_definition_rejected(self):
        kw = dict(self.kw); kw["immune_labels"] = []
        with self.assertRaises(ValueError): build_roi_table(self.cells,self.centers,**kw)

    def test_tumor_denominator_zero_is_excluded(self):
        c = self.cells.copy(); c["phenotype"] = "CD8"
        r = build_roi_table(c,self.centers,**self.kw)
        self.assertTrue(r.table.empty); self.assertEqual(len(r.exclusions),2)

    def test_minor_fraction_is_not_directional_exposure(self):
        for n_control in [1,19]:
            c = pd.DataFrame({"image_id":["X"]*20,"patient_id":["P"]*20,
                              "cell_id":[str(i) for i in range(20)],"x_um":[0.]*20,"y_um":[0.]*20,
                              "phenotype":["CTRL"]*n_control+["KO"]*(20-n_control)})
            center = pd.DataFrame({"image_id":["X"],"roi_id":["r"],"x_um":[0.],"y_um":[0.]})
            r=build_roi_table(c,center,**self.kw).table.iloc[0]
            self.assertAlmostEqual(r.minority_fraction,.05)
            self.assertAlmostEqual(r.p_control,n_control/20)

    def test_overlap_and_membership_are_visible(self):
        c = self.centers.iloc[[0,0]].copy(); c["roi_id"]=["r1","r2"]
        r=build_roi_table(self.cells,c,record_membership=True,**self.kw)
        self.assertEqual(list(r.table.n_overlapping_nominal_circles),[1,1])
        self.assertEqual(len(r.membership),6)

    def test_one_image_cannot_have_two_patients(self):
        c = self.cells.copy(); c.loc[0,"patient_id"]="other"
        with self.assertRaises(ValueError): build_roi_table(c,self.centers,**self.kw)

    def test_nonfinite_coordinates_rejected(self):
        c = self.cells.astype({"x_um": float}); c.loc[0,"x_um"]=np.inf
        with self.assertRaises(ValueError): build_roi_table(c,self.centers,**self.kw)

    def test_fps_is_deterministic_without_duplicate_selection(self):
        r=pd.DataFrame({"image_id":["A"]*5,"roi_id":list("abcde"),"sample_group":["g"]*5,
                        "x_um":[0.,1.,2.,3.,4.],"y_um":[0.]*5})
        a=farthest_point_sample(r,n_per_group=3,seed=8)
        b=farthest_point_sample(r,n_per_group=3,seed=8)
        pd.testing.assert_frame_equal(a,b); self.assertEqual(a.roi_id.nunique(),3)

    def factorial(self):
        return pd.DataFrame([{"donor_id":d,"matrix":m,"context":c,"value":10+m+2*c+3*m*c}
                             for d in ["d1","d2"] for m in [0,1] for c in [0,1] for _ in range(3)])

    def test_factorial_averages_technical_replicates(self):
        r=factorial_contrasts(self.factorial())
        self.assertEqual(len(r),2); self.assertEqual(list(r.interaction),[3.,3.])

    def test_incomplete_factorial_rejected(self):
        x=self.factorial(); x=x.loc[~((x.donor_id=="d1")&(x.matrix==1)&(x.context==1))]
        with self.assertRaises(ValueError): factorial_contrasts(x)

    def test_bootstrap_units_and_reproducibility(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            a=bootstrap_mean([1,2,3],n_boot=100,seed=3)
            b=bootstrap_mean([1,2,3],n_boot=100,seed=3)
        self.assertEqual(a,b); self.assertEqual(a["n_biological_units"],3)

    def test_original_visium_syntax_excerpt_fails(self):
        # Upstream cell cc1b0050, SHA 29de6f90..., reproduced only as a parser test.
        original='for cand in "gene_symbol","gene_name", "features"]:\n    pass\n'
        with self.assertRaises(SyntaxError): compile(original,"upstream_excerpt","exec")
        corrected='for cand in ["gene_symbol", "gene_name", "features"]:\n    pass\n'
        compile(corrected,"proposed_fix","exec")


if __name__ == "__main__": unittest.main()
