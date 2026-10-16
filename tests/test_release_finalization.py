"""Pinned-draft recovery verifies immutable browser contents across known versions."""
from contextlib import redirect_stdout
import ast
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile


ROOT = Path(__file__).parents[1]


@unittest.skipUnless(sys.version_info >= (3, 11), "Finalization uses the Python 3.12 workflow's tomllib")
class ReleaseFinalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("release_finalization", ROOT / "scripts/finalize_release.py")
        cls.helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.helper)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        previous = Path.cwd()
        os.chdir(self.temporary.name)
        self.addCleanup(os.chdir, previous)
        Path("dist").mkdir()
        self.version = "0.1.3"
        self.target = "a" * 40
        self.mapping = self.helper.browser_mapping(self.version)
        self.frozen = {source: (source + "\nfrozen tagged bytes\n").encode() for source in self.mapping.values()}
        self.template_source = b"raise AssertionError('Tagged code must never execute')\nbundle.writestr('README-browser.txt', f'SeasonLens {version}\\nFrozen instructions.\\n')\n"
        self.readme = f"SeasonLens {self.version}\nFrozen instructions.\n".encode()
        self.entries = [(name, self.frozen[source]) for name, source in self.mapping.items()]
        self.entries.append(("README-browser.txt", self.readme))
        self.data = {"version": self.version, "tag_commit": self.target, "release_id": 42, "assets": []}
        self.remote = {"id": 42, "tag_name": "v" + self.version, "draft": True, "assets": []}
        self.write_bundle()
        self.pin_assets()

    def write_bundle(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(Path("dist") / f"seasonlens-browser-v{self.version}.zip", "w") as bundle:
                for name, content in self.entries:
                    bundle.writestr(name, content)

    def pin_assets(self):
        wheel = f"seasonlens-{self.version}-py3-none-any.whl"
        source = f"seasonlens-{self.version}.tar.gz"
        (Path("dist") / wheel).write_bytes(b"unchanged wheel bytes")
        (Path("dist") / source).write_bytes(b"unchanged source distribution bytes")
        names = [wheel, source, f"seasonlens-browser-v{self.version}.zip"]
        checksum = "".join(hashlib.sha256((Path("dist") / name).read_bytes()).hexdigest() + "  " + name + "\n" for name in names)
        (Path("dist") / "SHA256SUMS").write_text(checksum)
        self.data["assets"] = []
        for asset_id, name in enumerate(names + ["SHA256SUMS"], 101):
            content = (Path("dist") / name).read_bytes()
            self.data["assets"].append({"name": name, "id": asset_id, "size": len(content), "digest": "sha256:" + hashlib.sha256(content).hexdigest()})
        self.remote["assets"] = [{**asset, "state": "uploaded"} for asset in self.data["assets"]]
        Path("draft.json").write_text(json.dumps(self.remote))

    def git(self, *args):
        self.assertEqual(args[0], "show")
        prefix = self.target + ":"
        self.assertTrue(args[1].startswith(prefix))
        source = args[1][len(prefix):]
        if source == "scripts/prepare_release.py":
            return self.template_source
        return self.frozen[source]

    def verify(self, downloaded=True):
        with patch.object(self.helper, "git", side_effect=self.git), redirect_stdout(io.StringIO()):
            self.helper.verify(self.data, "draft.json", downloaded)

    def test_current_inventory_matches_public_packager_sources(self):
        tree = ast.parse((ROOT / "scripts/prepare_release.py").read_text())
        assignments = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Name) and target.id == "files" for target in node.targets)]
        self.assertEqual(len(assignments), 1)
        packaged = ast.literal_eval(assignments[0].value)
        expected = {target: source for source, target in packaged.items()}
        for version in ("0.1.1", "0.1.2", "0.1.3"):
            self.assertEqual(self.helper.browser_mapping(version), expected)
        self.assertEqual(set(self.helper.browser_mapping("0.1.0")),
                         {"index.html", "walkthrough.html", "seasonlens-import-template.xlsx",
                          "sample_prices.csv", "layout-check.html", "LICENSE", "SHEETJS-LICENSE.txt"})

    def test_known_inventories_and_exact_tagged_bytes(self):
        for version, count in [("0.1.0", 8), ("0.1.1", 15), ("0.1.2", 15), ("0.1.3", 15)]:
            with self.subTest(version=version):
                self.version = self.data["version"] = version
                self.remote["tag_name"] = "v" + version
                mapping = self.helper.browser_mapping(version)
                self.assertEqual(len(mapping) + 1, count)
                self.entries = [(name, self.frozen[source]) for name, source in mapping.items()]
                self.entries.append(("README-browser.txt", f"SeasonLens {version}\nFrozen instructions.\n".encode()))
                self.write_bundle()
                self.pin_assets()
                self.verify(False)
                self.verify()

    def test_extra_missing_and_duplicate_archive_members_reject_even_when_repinned(self):
        original = self.entries[:]
        cases = [original + [("extra.txt", b"extra")], original[:-1], original + [original[0]]]
        for entries in cases:
            with self.subTest(names=[name for name, _ in entries]):
                self.entries = entries
                self.write_bundle()
                self.pin_assets()
                with self.assertRaisesRegex(ValueError, "unexpected files"):
                    self.verify()

    def test_mutated_frozen_file_rejects_even_when_repinned(self):
        self.entries[0] = (self.entries[0][0], b"modified public page")
        self.write_bundle()
        self.pin_assets()
        with self.assertRaisesRegex(ValueError, "Frozen browser bytes"):
            self.verify()

    def test_mutated_readme_rejects_even_when_repinned(self):
        self.entries[-1] = ("README-browser.txt", b"modified instructions")
        self.write_bundle()
        self.pin_assets()
        with self.assertRaisesRegex(ValueError, "Frozen browser README"):
            self.verify()

    def test_wrong_draft_identity_or_published_state_reject(self):
        for field, value in [("id", 99), ("tag_name", "v0.1.2"), ("draft", False)]:
            with self.subTest(field=field):
                remote = deepcopy(self.remote)
                remote[field] = value
                Path("draft.json").write_text(json.dumps(remote))
                with self.assertRaisesRegex(ValueError, "pinned unpublished draft"):
                    self.verify(False)

    def test_remote_asset_identity_size_digest_and_state_reject(self):
        for field, value in [("id", 999), ("size", 1), ("digest", "sha256:" + "0" * 64), ("state", "new")]:
            with self.subTest(field=field):
                remote = deepcopy(self.remote)
                remote["assets"][0][field] = value
                Path("draft.json").write_text(json.dumps(remote))
                with self.assertRaisesRegex(ValueError, "assets changed"):
                    self.verify(False)

    def test_downloaded_byte_mutation_rejects(self):
        path = Path("dist") / self.data["assets"][0]["name"]
        path.write_bytes(b"changed wheel")
        with self.assertRaisesRegex(ValueError, "Downloaded bytes differ"):
            self.verify()

    def test_checksum_manifest_must_match_even_when_manifest_is_repinned(self):
        path = Path("dist/SHA256SUMS")
        path.write_text("incorrect manifest\n")
        content = path.read_bytes()
        asset = self.data["assets"][-1]
        asset.update(size=len(content), digest="sha256:" + hashlib.sha256(content).hexdigest())
        self.remote["assets"][-1].update(asset)
        Path("draft.json").write_text(json.dumps(self.remote))
        with self.assertRaisesRegex(ValueError, "Checksum manifest differs"):
            self.verify()

    def test_unknown_versions_reject_before_remote_or_file_access(self):
        for version in ["0.1.4", "0.2.0", "1.0.0"]:
            with self.subTest(version=version):
                with self.assertRaisesRegex(ValueError, "Unsupported frozen browser inventory"):
                    self.helper.verify({"version": version}, "does-not-exist.json", False)

    def test_readme_ast_rejects_computation_and_ambiguous_templates(self):
        for source in [b"bundle.writestr('README-browser.txt', f'{danger()}')", self.template_source + self.template_source]:
            with self.subTest(source=source):
                self.template_source = source
                with self.assertRaisesRegex(ValueError, "Unsupported frozen browser README"):
                    self.verify()
