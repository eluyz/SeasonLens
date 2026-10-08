"""Scientific browser UI lifecycle and privacy, using real statistical modules."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).parents[1]

@unittest.skipUnless(shutil.which("node"), "Node required for scientific browser UI checks")
class ScientificUITests(unittest.TestCase):
    def test_real_math_panels_private_lifecycle_and_contained_errors(self):
        result = subprocess.run(["node", str(ROOT / "tests/scientific_ui_check.js")], cwd=ROOT, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS: lazy idempotent scientific panels", result.stdout)

    def test_self_contained_ui_and_unique_fragment_controls(self):
        import re
        source = (ROOT / "src/seasonlens/scientific_ui.js").read_text()
        for prohibited in ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage", "indexedDB", "sendBeacon", "WebSocket"):
            self.assertNotIn(prohibited, source)
        fragment = (ROOT / "src/seasonlens/scientific_panel.html").read_text()
        ids = re.findall(r'id="([^"]+)"', fragment)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(fragment.count('class="science-section"'), 5)
        self.assertIn('not a prediction interval', fragment)
        self.assertIn('not official data', fragment)

if __name__ == "__main__":
    unittest.main()
