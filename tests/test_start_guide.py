"""Onboarding paths stay optional, accessible and browser local."""
from html.parser import HTMLParser
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).parents[1]


class FragmentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.attributes = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
            self.attributes[attrs["id"]] = attrs
        if tag in ("script", "iframe", "img"):
            raise AssertionError("Guide fragment should not load executable or external assets")


class StartGuideTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node required for browser checks")
    def test_navigation_download_failure_recovery_and_no_data_access(self):
        result = subprocess.run(["node", str(ROOT / "tests/start_guide_check.js")],
                                cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS: optional local start guide", result.stdout)

    def test_honest_template_privacy_and_mobile_contract(self):
        panel = (ROOT / "src/seasonlens/start_panel.html").read_text()
        parser = FragmentParser()
        parser.feed(panel)
        self.assertEqual(len(parser.ids), len(set(parser.ids)))
        self.assertNotIn("open", parser.attributes["start-guide-details"])
        for name, destination in (("explore", "fiveyear"), ("monthly", "prices-seasonality"),
                                  ("import", "browser-import-panel"), ("report", "report-export-panel")):
            self.assertEqual(parser.attributes[f"start-{name}"]["href"], "#" + destination)
        self.assertIn("disabled", parser.attributes["start-template"])
        for copy in ("SYNTHETIC, invented data", "Reloading clears private imports",
                     "first data row <strong>4</strong>", "2026-10-06", "Read me",
                     "Sharing a downloaded report shares its visible results"):
            self.assertIn(copy, panel)
        source = (ROOT / "src/seasonlens/start_ui.js").read_text()
        for prohibited in ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage",
                           "indexedDB", "sendBeacon", "WebSocket", "innerHTML"):
            self.assertNotIn(prohibited, source)
        css = (ROOT / "src/seasonlens/start.css").read_text()
        self.assertIn("@media(max-width:800px)", css)
        self.assertIn("min-height:44px", css)
        self.assertIn("minmax(0,1fr)", css)
        self.assertIn("@media print", css)


if __name__ == "__main__":
    unittest.main()
