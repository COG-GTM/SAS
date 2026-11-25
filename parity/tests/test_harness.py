"""Unit tests for the parity harness (no SAS engine or Spark needed): python3 -m unittest discover parity/tests"""
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from cases import CASES, label  # noqa: E402
from compare import norm, same  # noqa: E402
from sas_runner import extract, mock_datalines  # noqa: E402


def _digest(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(root)).encode() + p.read_bytes())
    return h.hexdigest()


class MockGen(unittest.TestCase):
    def test_deterministic(self):
        digests = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as d:
                subprocess.run([sys.executable, str(HERE / "mockgen.py"), "--out", d], check=True,
                               capture_output=True)
                digests.append(_digest(Path(d)))
        self.assertEqual(digests[0], digests[1])


class Compare(unittest.TestCase):
    def test_numeric_tolerance(self):
        self.assertTrue(same(1.0, 1.0 + 1e-12, "num"))
        self.assertFalse(same(1.0, 1.001, "num"))
        self.assertTrue(same(None, None, "num"))
        self.assertFalse(same(None, 0.0, "num"))

    def test_char_trailing_blanks(self):
        self.assertTrue(same(norm("ab  ", "char"), norm("ab", "char"), "char"))
        self.assertTrue(same(norm(None, "char"), norm("", "char"), "char"))
        self.assertFalse(same(norm(" ab", "char"), norm("ab", "char"), "char"))


class Registry(unittest.TestCase):
    def test_every_step_extracts(self):
        for c in CASES:
            for step, _ in c.steps:
                self.assertTrue(extract(step).strip(), step)

    def test_labels_unique(self):
        labels = [label(s, d) for c in CASES for s, ds in c.steps for d in ds]
        self.assertEqual(len(labels), len(set(labels)))

    def test_datalines_replaced(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run([sys.executable, str(HERE / "mockgen.py"), "--out", d], check=True, capture_output=True)
            mock = (Path(d) / "datalines" / "book_7-3__1.dat").read_text().strip()
            txt = mock_datalines(extract("book:7-3"), "book:7-3", Path(d))
            self.assertIn(mock, txt)
            self.assertNotIn("21 M 80 B- 82", txt)


if __name__ == "__main__":
    unittest.main()
