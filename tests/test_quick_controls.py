"""Mirrored selection and keyboard navigation remain local and synchronized."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).parents[1]


@unittest.skipUnless(shutil.which("node"), "Node required for browser checks")
class QuickControlsTests(unittest.TestCase):
    def test_selection_import_cutoff_navigation_and_idempotence(self):
        result = subprocess.run(["node", str(ROOT / "tests/quick_controls_check.js")],
                                cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS: synchronized local quick controls", result.stdout)

    def test_privacy_and_print_safe_mobile_layout(self):
        source = (ROOT / "src/seasonlens/quick_controls.js").read_text()
        for prohibited in ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage", "indexedDB", "sendBeacon", "WebSocket", "innerHTML"):
            self.assertNotIn(prohibited, source)
        css = (ROOT / "src/seasonlens/quick_controls.css").read_text()
        self.assertIn("position:sticky", css)
        self.assertNotIn("position:fixed", css)
        self.assertIn(".quick-controls-options[hidden]", css)
        self.assertIn("@media print", css)


if __name__ == "__main__":
    unittest.main()
