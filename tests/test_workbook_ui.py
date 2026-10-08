"""Bounded DOM checks for staging and committing private browser imports."""
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).parents[1]


@unittest.skipUnless(shutil.which("node"), "Node is required for import-wizard checks")
class WorkbookWizardTests(unittest.TestCase):
    def test_two_phase_atomic_private_import_and_stale_read(self):
        result = subprocess.run(
            ["node", str(ROOT / "tests/browser_wizard_check.js")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS: two-phase CSV/XLSX", result.stdout)
