"""Engineering + analytic teaching tests, not author software validation."""
import json
import math
import subprocess
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from kb_core import KnowledgeBase,check_project,tokens
from demo import miss_probability,transition_two_state,stationary_two_state,moran_i,expected_vaf,run_demo

class RetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.kb=KnowledgeBase(ROOT)
    def test_integrity(self):self.assertTrue(self.kb.validate(checksums=False)['ok'])
    def test_claim_schema(self):
        for c in self.kb.claims.values():
            with self.subTest(c=c['claim_id']):
                self.assertIn(c['layer'],{'REVIEW','PRIMARY','CODE','ANALYSIS','TRANSFER'})
                if c['layer'] in {'REVIEW','PRIMARY','CODE'}:self.assertTrue(c['evidence'])
    def test_expected_sources(self):self.assertEqual(len(self.kb.sources),16)
    def test_expected_claims(self):self.assertEqual(len(self.kb.claims),62)
    def test_chinese_tokenization(self):self.assertIn('遗传',tokens('遗传性'))
    def test_alias_expansion(self):self.assertIn('遗传',tokens('heritability',True))
    def test_chinese_retrieval(self):
        self.assertIn('C025',[h['id'] for h in self.kb.search('没有突变 reads 就是野生型吗',10)])
    def test_english_retrieval(self):
        self.assertIn('C008',[h['id'] for h in self.kb.search('TreeAlign unpaired',10)])
    def test_code_retrieval(self):
        self.assertIn('C017',[h['id'] for h in self.kb.search('one.sided.pvalue',5)])
    def test_empty_query_rejected(self):
        with self.assertRaises(ValueError):self.kb.search(' ')
    def test_unknown_no_hits(self):self.assertEqual(self.kb.search('zxqv987654321'),[])
    def test_limit_validation(self):
        for v in [0,21,-1,True,2.5]:
            with self.subTest(v=v):
                with self.assertRaises(ValueError):self.kb.search('PATH',v)
    def test_read_claim(self):self.assertEqual(self.kb.read_claim('C032')['layer'],'ANALYSIS')
    def test_unknown_claim_rejected(self):
        with self.assertRaises(ValueError):self.kb.read_claim('C999')
    def test_read_document(self):self.assertIn('共同演化',self.kb.read_document('README.md')['text'])
    def test_path_traversal_rejected(self):
        for p in ['../../etc/passwd','/etc/passwd','tools/kb.py','../README.md']:
            with self.subTest(p=p):
                with self.assertRaises(ValueError):self.kb.read_document(p)
    def test_context_is_not_model_answer(self):
        c=self.kb.build_context('PATH 遗传性')
        self.assertFalse(c['model_called']);self.assertTrue(c['retrieval_only']);self.assertTrue(c['open_gaps'])
    def test_source_code_pinned(self):
        self.assertEqual(self.kb.sources['S13']['commit'],'caffc5105678224f108b3dd61fea545f96235ffc')

class PlanningTests(unittest.TestCase):
    def example(self,name):return json.loads((ROOT/'agent/examples'/name).read_text())
    def test_rna_only_blocked(self):
        p=check_project(self.example('project_rna_only.json'))
        self.assertTrue(all(x['status']=='blocked_for_claim' for x in p['decisions']))
    def test_uncalibrated_absolute_blocked(self):
        p=check_project(self.example('project_paired_tree.json'))
        self.assertEqual(p['decisions'][-1]['status'],'blocked_for_claim')
        self.assertEqual(p['decisions'][1]['status'],'conditional_expert_review')
    def test_spatial_does_not_imply_lineage(self):
        p=check_project(self.example('project_spatial_stages.json'))
        self.assertEqual(p['decisions'][0]['status'],'conditional_expert_review')
        self.assertEqual(p['decisions'][1]['status'],'blocked_for_claim')
    def test_missing_is_unknown(self):
        p=check_project({'project_id':'x','goals':['lineage_heritability']})
        self.assertEqual(p['decisions'][0]['missing_requirements'][0]['state'],'未提供/未知')
    def test_leaf_mismatch_blocks(self):
        x=self.example('project_paired_tree.json');x['tree_leaf_ids_matched']=False
        self.assertEqual(check_project(x)['decisions'][1]['status'],'blocked_for_claim')
    def test_no_claim_of_execution(self):
        self.assertFalse(check_project(self.example('project_paired_tree.json'))['execution_performed'])
    def test_absolute_units_and_calibration(self):
        x=self.example('project_paired_tree.json');x['time_calibrated']=True;x['branch_unit']='days'
        self.assertEqual(check_project(x)['decisions'][-1]['status'],'conditional_expert_review')
    def test_single_donor_warning(self):
        x=self.example('project_paired_tree.json');x['independent_units']=1
        self.assertTrue(any('一个独立' in w for w in check_project(x)['warnings']))
    def test_bad_types_rejected(self):
        x=self.example('project_paired_tree.json');x['has_tree']='true'
        with self.assertRaises(ValueError):check_project(x)
    def test_unsupported_fields_rejected(self):
        with self.assertRaises(ValueError):check_project({'project_id':'x','goals':['lineage_heritability'],'run_shell':'whoami'})
    def test_contradictory_inputs_rejected(self):
        x=self.example('project_paired_tree.json');x['genotype_origin']='none'
        with self.assertRaises(ValueError):check_project(x)

class MathTeachingTests(unittest.TestCase):
    def test_dropout(self):
        for m,p in [(0,1),(1,.5),(4,.0625),(10,.0009765625)]:self.assertEqual(miss_probability(m,.5),p)
    def test_dropout_invalid(self):
        for m,p in [(-1,.5),(True,.5),(1,math.nan),(1,1.1)]:
            with self.subTest(m=m,p=p):
                with self.assertRaises(ValueError):miss_probability(m,p)
    def test_transition_t_zero_identity(self):self.assertEqual(transition_two_state(.1,.2,0),[[1.,0.],[0.,1.]])
    def test_transition_rows(self):
        for a,b,t in [(.05,.05,1),(5,5,1),(.2,.3,4)]:
            for row in transition_two_state(a,b,t):
                self.assertAlmostEqual(sum(row),1);self.assertTrue(all(0<=v<=1 for v in row))
    def test_stationary_invariance(self):
        p=stationary_two_state(.2,.3);P=transition_two_state(.2,.3,4)
        for j in range(2):self.assertAlmostEqual(sum(p[i]*P[i][j] for i in range(2)),p[j])
    def test_same_marginals_distinct_dynamics(self):
        self.assertEqual(stationary_two_state(.05,.05),stationary_two_state(5,5))
        self.assertLess(transition_two_state(.05,.05,1)[0][1],transition_two_state(5,5,1)[0][1])
    def test_invalid_transition(self):
        for vals in [(0,0,1),(-1,1,1),(1,1,math.inf),(1,math.nan,1)]:
            with self.subTest(v=vals):
                with self.assertRaises(ValueError):transition_two_state(*vals)
    def test_moran_constant_rejected(self):
        with self.assertRaises(ValueError):moran_i([1,1],[[0,1],[1,0]])
    def test_moran_bad_weights(self):
        with self.assertRaises(ValueError):moran_i([0,1],[[1,0],[0,1]])
    def test_exact_moran_permutation(self):
        m=run_demo()['moran'];self.assertEqual(m['exact_permutations'],70)
        self.assertAlmostEqual(m['null_mean'],-1/7)
        self.assertAlmostEqual(m['exact_upper_tail_p'],2/70)
    def test_normal_tail_arithmetic(self):
        p=run_demo()['normal_tail_at_Z_2'];self.assertAlmostEqual(p['two_sided'],2*p['one_sided_upper'])
        self.assertAlmostEqual(p['two_sided'],.04550026389635844)
    def test_vaf_dependency(self):
        self.assertAlmostEqual(2*expected_vaf(.4,2,1),.4)
        self.assertNotAlmostEqual(2*expected_vaf(.4,4,1),.4)
    def test_composition_confounding(self):
        c=run_demo()['composition_confounding'];self.assertGreater(c['mutant_overall_mean'],c['WT_overall_mean'])
        self.assertEqual(c['within_background_difference'],0)

class InterfaceTests(unittest.TestCase):
    def command(self,*args,input=None):
        return subprocess.run([sys.executable,*args],cwd=ROOT,input=input,text=True,capture_output=True,timeout=20)
    def test_cli_json(self):
        r=self.command('tools/kb.py','get','C032');self.assertEqual(r.returncode,0);self.assertEqual(json.loads(r.stdout)['claim_id'],'C032')
    def test_cli_fail_exit_code(self):
        r=self.command('tools/kb.py','get','C999');self.assertEqual(r.returncode,2);self.assertFalse(json.loads(r.stdout)['ok'])
    def test_jsonl_multiple_requests_and_error_recovery(self):
        lines=[{'id':'1','tool':'read_claim','arguments':{'claim_id':'C017'}},
               {'id':'2','tool':'run_shell','arguments':{'cmd':'id'}},
               {'id':'3','tool':'read_claim','arguments':{'claim_id':'C032'}}]
        r=self.command('tools/tool_server.py',input='\n'.join(json.dumps(x) for x in lines)+'\n')
        out=[json.loads(x) for x in r.stdout.splitlines()]
        self.assertEqual(len(out),3);self.assertTrue(out[0]['ok']);self.assertFalse(out[1]['ok']);self.assertTrue(out[2]['ok'])
    def test_malformed_json(self):
        r=self.command('tools/tool_server.py',input='not JSON\n')
        self.assertFalse(json.loads(r.stdout)['ok'])
    def test_interactive_claim_read(self):
        r=self.command('tools/kb.py','interactive',input=':get C032\n退出\n')
        self.assertEqual(r.returncode,0);self.assertIn('C032',r.stdout)
    def test_tools_contract(self):
        specs=json.loads((ROOT/'agent/tools.json').read_text())
        self.assertIn('not-mcp',specs['protocol'])
        self.assertEqual(len(specs['tools']),6)

if __name__=='__main__':unittest.main(verbosity=2)
