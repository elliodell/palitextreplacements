"""Regression tests for the generated Alfred and Apple exports.

The generator runs in a temporary directory because it replaces build/ and dist/.
Only the standard library is needed; no snippets are installed into either app.
"""

import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import unittest
import uuid
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def read_alfred(path):
    with zipfile.ZipFile(path) as archive:
        snippets = [
            json.loads(archive.read(name))["alfredsnippet"]
            for name in archive.namelist()
            if name.endswith(".json")
        ]
        metadata = plistlib.loads(archive.read("info.plist"))
    return snippets, metadata


def read_apple(path):
    with path.open("rb") as source:
        return plistlib.load(source)


class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(directory.cleanup)
        cls.output = Path(directory.name)
        for name in ("gen.py", "terms.txt"):
            shutil.copyfile(ROOT / name, cls.output / name)
        result = subprocess.run(
            [sys.executable, "gen.py"],
            cwd=cls.output,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        cls.generator_stdout = result.stdout
        cls.alfred, cls.metadata = read_alfred(cls.output / "dist/Pali.alfredsnippets")
        cls.apple = read_apple(cls.output / "dist/Pali Text Replacements.plist")
        cls.alfred_map = {entry["keyword"]: entry["snippet"] for entry in cls.alfred}
        cls.apple_map = {entry["shortcut"]: entry["phrase"] for entry in cls.apple}

    def test_exports_have_unique_keywords_and_snippet_ids(self):
        self.assertTrue(self.alfred)
        self.assertTrue(self.apple)
        self.assertEqual(len(self.alfred), len(self.alfred_map))
        self.assertEqual(len(self.apple), len(self.apple_map))
        self.assertEqual(len(self.apple), len({key.casefold() for key in self.apple_map}))
        ids = [entry["uid"] for entry in self.alfred]
        self.assertEqual(len(ids), len(set(ids)))
        for identifier in ids:
            with self.subTest(uid=identifier):
                self.assertEqual(str(uuid.UUID(identifier)).upper(), identifier)

    def test_export_text_is_normalized_and_keywords_are_ascii(self):
        for mapping in (self.alfred_map, self.apple_map):
            for keyword, expansion in mapping.items():
                with self.subTest(keyword=keyword):
                    self.assertTrue(keyword)
                    self.assertTrue(keyword.isascii())
                    self.assertTrue(expansion)
                    self.assertEqual(expansion, unicodedata.normalize("NFC", expansion))

    def test_case_variants_preserve_nouns_and_proper_names(self):
        expected = {
            "jhana": "jhāna", "Jhana": "Jhāna",
            "satipatthana": "satipaṭṭhāna", "Satipatthana": "Satipaṭṭhāna",
            "ananda": "Ānanda", "Ananda": "Ānanda",
            "anguttara": "Aṅguttara", "Anguttara": "Aṅguttara",
        }
        for keyword, expansion in expected.items():
            with self.subTest(keyword=keyword):
                self.assertEqual(self.alfred_map[keyword], expansion)
        for keyword in ("jhana", "satipatthana", "ananda", "anguttara"):
            self.assertEqual(self.apple_map[keyword], expected[keyword])

    def test_english_clashes_require_bang_only_in_alfred(self):
        for keyword, expansion in {"pali": "Pāli", "sila": "sīla", "dana": "dāna"}.items():
            with self.subTest(keyword=keyword):
                self.assertNotIn(keyword, self.alfred_map)
                self.assertNotIn(keyword.capitalize(), self.alfred_map)
                self.assertEqual(self.alfred_map["!" + keyword], expansion)
                self.assertEqual(self.apple_map[keyword], expansion)
                self.assertNotIn("!" + keyword, self.apple_map)
        self.assertEqual(self.alfred_map["!ghana"], "ghāna")
        self.assertNotIn("ghana", self.apple_map)  # Do not rewrite the country name.

    def test_ambiguous_and_unreachable_terms_stay_excluded(self):
        for keyword in ("majjhima", "satta", "sammaditthi", "anattata"):
            with self.subTest(keyword=keyword):
                self.assertNotIn(keyword, self.alfred_map)
                self.assertNotIn(keyword.capitalize(), self.alfred_map)
                self.assertNotIn(keyword, self.apple_map)
        self.assertEqual(self.alfred_map["punna"], "puñña")
        self.assertEqual(self.apple_map["punna"], "puñña")
        self.assertNotIn("STILL BAD", self.generator_stdout)

    def test_collection_has_no_implicit_prefix_or_suffix(self):
        self.assertEqual(self.metadata["snippetkeywordprefix"], "")
        self.assertEqual(self.metadata["snippetkeywordsuffix"], "")

    def test_checked_in_alfred_matches_generated_keywords_and_text(self):
        committed, metadata = read_alfred(ROOT / "dist/Pali.alfredsnippets")
        self.assertEqual(len(committed), len(self.alfred))
        self.assertEqual(
            {entry["keyword"]: entry["snippet"] for entry in committed}, self.alfred_map
        )
        self.assertEqual(metadata, self.metadata)

    def test_checked_in_apple_matches_generated_replacements(self):
        committed = read_apple(ROOT / "dist/Pali Text Replacements.plist")
        self.assertEqual(committed, self.apple)

    def test_checked_in_list_matches_generated_documentation(self):
        self.assertEqual(
            (ROOT / "pali-snippets-list.md").read_text(encoding="utf-8"),
            (self.output / "pali-snippets-list.md").read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
