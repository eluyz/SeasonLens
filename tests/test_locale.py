"""Bilingual presentation changes must preserve private values and update safely."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).parents[1]


@unittest.skipUnless(shutil.which("node"), "Node required for locale checks")
class LocaleTests(unittest.TestCase):
    def test_roundtrip_mutations_private_titles_and_storage_denial(self):
        result = subprocess.run(["node", str(ROOT / "tests/locale_check.js")],
                                cwd=ROOT, capture_output=True, text=True, timeout=25)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS: reversible locale", result.stdout)

    def test_language_only_storage_without_provider_or_data_access(self):
        source = (ROOT / "src/seasonlens/locale.js").read_text()
        for forbidden in ("fetch(", "XMLHttpRequest", "sessionStorage", "indexedDB", "sendBeacon", "WebSocket"):
            self.assertNotIn(forbidden, source)
        self.assertEqual(source.count("localStorage?.setItem"), 1)
        self.assertIn("localStorage?.setItem(KEY,lang)", source)


if __name__ == "__main__":
    unittest.main()
