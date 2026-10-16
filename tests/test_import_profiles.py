"""Versioned private XLSX settings, exercised independently of the UI."""
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).parents[1]


@unittest.skipUnless(shutil.which("node"), "Node is required for import-profile checks")
class ImportProfileTests(unittest.TestCase):
    def test_strict_configuration_and_exact_layout_guards(self):
        result = subprocess.run(
            ["node", str(ROOT / "tests/import_profiles_check.js")],
            cwd=ROOT, text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS: bounded strict configuration profiles", result.stdout)
