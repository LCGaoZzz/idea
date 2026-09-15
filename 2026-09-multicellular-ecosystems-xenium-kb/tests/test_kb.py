import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('kb', ROOT / 'tools/kb.py')
kb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kb)


class KnowledgeBaseTests(unittest.TestCase):
    def test_structure(self):
        self.assertEqual(kb.validate()['errors'], [])
    def test_source_count(self):
        self.assertEqual(len(kb.load()[1]), 15)
    def test_claim_count(self):
        self.assertEqual(len(kb.load()[0]), 24)
    def test_figures(self):
        self.assertEqual(kb.validate()['figure_count'], 4)
    def test_chinese_lookup(self):
        self.assertEqual(kb.search('伪重复')[0]['id'], 'C011')
    def test_covarnet_lookup(self):
        self.assertEqual(kb.search('CoVarNet 上皮')[0]['id'], 'C010')
    def test_show_boundary(self):
        self.assertIn('Tlow', kb.show('C015')['boundary'])
    def test_source_detail(self):
        self.assertEqual(kb.show('C005')['source_details'][0]['id'], 'R15')
    def test_unknown(self):
        with self.assertRaises(KeyError):
            kb.show('C999')
    def test_empty(self):
        with self.assertRaises(ValueError):
            kb.search(' ')
    def test_invalid_limit(self):
        with self.assertRaises(ValueError):
            kb.search('CAF', 0)
    def test_cli(self):
        p = subprocess.run([sys.executable, str(ROOT / 'tools/kb.py'), 'show', 'C010'], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(p.stdout)['label'], 'EXTERNAL_FACT')


if __name__ == '__main__':
    unittest.main()
