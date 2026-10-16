"""Hand-calculated local workbook comparison and strict shared preparation."""
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).parents[1]


@unittest.skipUnless(shutil.which("node"), "Node is required for workbook comparison checks")
class ImportComparisonTests(unittest.TestCase):
    def test_exact_changes_and_same_validation_before_omissions(self):
        result = subprocess.run(
            ["node", str(ROOT / "tests/import_comparison_check.js")],
            cwd=ROOT, text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS: hand-calculated old/new corrections", result.stdout)
