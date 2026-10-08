import pathlib
import shutil
import subprocess
import unittest


class PrivateInstallationTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node is needed for browser integration checks')
    def test_matched_private_conversion_source_isolation_and_atomic_install(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        result = subprocess.run(['node', str(root/'tests/private_install_check.js'), str(root)],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
