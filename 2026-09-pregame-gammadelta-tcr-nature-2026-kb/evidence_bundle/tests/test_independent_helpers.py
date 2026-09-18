"""Synthetic tests only. No cells or model parameters from the paper are used."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_candidate_table import audit_rows
from arithmetic_audit import clopper_pearson,max_exceedance

def row(i=1,**kwargs):
    r=dict(cell_id=f's{i}:BC',donor_id=f'd{i}',batch_id=f'b{i}',clone_id=f'c{i}',delta_key=f'delta{i}',label='TR',split='train' if i==1 else 'test',score='.9')
    r.update(kwargs);return r
class AuditTests(unittest.TestCase):
    def test_valid(self):self.assertTrue(audit_rows([row(),row(2)])['passed'])
    def test_duplicate(self):self.assertFalse(audit_rows([row(),row()])['passed'])
    def test_donor_overlap(self):self.assertFalse(audit_rows([row(),row(2,donor_id='d1')])['passed'])
    def test_batch_overlap(self):self.assertFalse(audit_rows([row(),row(2,batch_id='b1')])['passed'])
    def test_relaxed_batch(self):self.assertTrue(audit_rows([row(),row(2,batch_id='b1')],require_batch_disjoint=False)['passed'])
    def test_clone_overlap(self):self.assertFalse(audit_rows([row(),row(2,clone_id='c1')])['passed'])
    def test_unknown_not_negative(self):self.assertFalse(audit_rows([row(label='unknown')])['passed'])
    def test_invalid_score(self):self.assertFalse(audit_rows([row(score='NaN')])['passed'])
    def test_out_of_range(self):self.assertFalse(audit_rows([row(score='1.1')])['passed'])
    def test_missing(self):r=row();del r['donor_id'];self.assertFalse(audit_rows([r])['passed'])
    def test_label_conflict(self):self.assertFalse(audit_rows([row(),row(2,split='train',clone_id='c1',label='NTR')])['passed'])
    def test_delta_pair_ambiguity(self):r=audit_rows([row(),row(2,split='train',donor_id='d1',delta_key='delta1')]);self.assertTrue(r['passed']);self.assertEqual(r['warnings'][0]['code'],'delta_one_to_many')
    def test_empty(self):self.assertFalse(audit_rows([])['passed'])
    def test_cp_all_successes(self):lo,hi=clopper_pearson(10,10);self.assertAlmostEqual(lo,.025**.1,places=10);self.assertEqual(hi,1)
    def test_cp_symmetry(self):a,b=clopper_pearson(21,25);c,d=clopper_pearson(4,25);self.assertAlmostEqual(a,1-d,places=10);self.assertAlmostEqual(b,1-c,places=10)
    def test_max_monotone(self):self.assertGreater(max_exceedance(30,.01),max_exceedance(10,.01))
    def test_max_single(self):self.assertAlmostEqual(max_exceedance(1,.01),.01)
    def test_invalid_binomial(self):self.assertRaises(ValueError,clopper_pearson,3,2)
if __name__=='__main__':unittest.main(verbosity=2)
