"""Adversarial rendered-report serialization and browser lifecycle checks."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).parents[1]

@unittest.skipUnless(shutil.which("node"), "Node required for report browser checks")
class ReportExportTests(unittest.TestCase):
    def test_selected_snapshot_sanitization_and_lifecycle(self):
        result = subprocess.run(["node", str(ROOT / "tests/report_export_check.js")], cwd=ROOT, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS: report sanitizer", result.stdout)

    def test_standalone_assets_privacy_print_scope_and_unique_ids(self):
        import re
        source = (ROOT / "src/seasonlens/report_export.js").read_text()
        for prohibited in ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage", "indexedDB", "sendBeacon", "WebSocket", "dataset.textContent"):
            self.assertNotIn(prohibited, source)
        fragment = (ROOT / "src/seasonlens/report_panel.html").read_text()
        ids = re.findall(r'id="([^"]+)"', fragment)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn('Print / Save PDF', fragment)
        self.assertIn('original observation dataset is not embedded', fragment)
        self.assertIn('fixed snapshot', source)
        css = (ROOT / "src/seasonlens/report.css").read_text()
        self.assertIn('@media print', css)
        self.assertIn('body.seasonlens-report-open .report-preview-toolbar{display:none!important}', css)
        self.assertIn('min-width:0!important', css)

if __name__ == "__main__":
    unittest.main()
