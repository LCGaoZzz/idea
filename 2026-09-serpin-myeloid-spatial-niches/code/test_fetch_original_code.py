"""Local fixtures only; no network request is performed by these tests."""
import json
from pathlib import Path
import tempfile
import unittest
from fetch_original_code import git_blob_sha, safe_target, write_verified, readable_notebook


class SourceTests(unittest.TestCase):
    def test_known_git_empty_blob(self):
        self.assertEqual(git_blob_sha(b""),"e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")

    def test_path_traversal_rejected(self):
        for p in ["../bad", "/absolute", "a/../../bad", "a\\bad", "."]:
            with self.assertRaises(ValueError): safe_target(Path("/tmp/idea_test"),p)

    def test_bad_hash_never_writes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"source.txt"
            with self.assertRaises(ValueError): write_verified(p,b"wrong","0"*40)
            self.assertFalse(p.exists())

    def test_verified_existing_and_conflict(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"source.txt"
            self.assertEqual(write_verified(p,b"ok",git_blob_sha(b"ok")),"downloaded_verified")
            self.assertEqual(write_verified(p,b"ok",git_blob_sha(b"ok")),"already_verified")
            with self.assertRaises(FileExistsError): write_verified(p,b"new",git_blob_sha(b"new"))
            self.assertEqual(p.read_bytes(),b"ok")

    def test_extracts_source_not_outputs(self):
        raw=json.dumps({"cells":[{"cell_type":"code","id":"abc","source":["x = 1\n"],
                                    "outputs":[{"text":"NOT_A_REPRODUCTION"}]}]}).encode()
        s=readable_notebook(raw)
        self.assertIn("CELL 0",s); self.assertIn("id=abc",s); self.assertIn("x = 1",s)
        self.assertNotIn("NOT_A_REPRODUCTION",s)


if __name__ == "__main__": unittest.main()
