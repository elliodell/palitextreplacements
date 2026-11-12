"""Invalid source terms must not erase a previous successful export."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from test_exports import ROOT, read_alfred, read_apple


class InputTests(unittest.TestCase):
    def run_generator(self, directory, terms):
        shutil.copyfile(ROOT / "gen.py", directory / "gen.py")
        (directory / "terms.txt").write_text(terms, encoding="utf-8")
        return subprocess.run(
            [sys.executable, "gen.py"],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_spaces_around_separator_are_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            result = self.run_generator(
                directory, "# spaced input\n\n doctrine | jhāna \n people | Ānanda \n"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            snippets, _ = read_alfred(directory / "dist/Pali.alfredsnippets")
            alfred = {entry["keyword"]: entry["snippet"] for entry in snippets}
            apple = {
                entry["shortcut"]: entry["phrase"]
                for entry in read_apple(directory / "dist/Pali Text Replacements.plist")
            }
            for mapping in (alfred, apple):
                self.assertEqual(mapping["jhana"], "jhāna")
                self.assertEqual(mapping["ananda"], "Ānanda")

    def test_collection_is_created_without_plain_keywords(self):
        fixtures = (
            ("doctrine|dāna\n", {"dana": "dāna"}),
            ("doctrine|metta\n", {}),
            ("# no source terms\n\n", {}),
        )
        extras = {
            "maha": "mahā", "cula": "cūḷa", "kaya": "kāya",
            "panca": "pañca", "ghana": "ghāna",
        }
        for terms, source_entries in fixtures:
            with self.subTest(terms=terms), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                result = self.run_generator(directory, terms)
                self.assertEqual(result.returncode, 0, result.stderr)
                snippets, metadata = read_alfred(directory / "dist/Pali.alfredsnippets")
                expected = {**extras, **source_entries}
                expected_alfred = {}
                for keyword, expansion in expected.items():
                    expected_alfred["!" + keyword] = expansion
                    expected_alfred["!" + keyword.capitalize()] = expansion.capitalize()
                self.assertEqual(len(snippets), len(expected_alfred))
                self.assertEqual(
                    {entry["keyword"]: entry["snippet"] for entry in snippets},
                    expected_alfred,
                )
                self.assertEqual(metadata["snippetkeywordprefix"], "")
                self.assertEqual(metadata["snippetkeywordsuffix"], "")
                apple = read_apple(directory / "dist/Pali Text Replacements.plist")
                self.assertEqual(len(apple), len(expected) - 1)
                self.assertEqual(
                    {entry["shortcut"]: entry["phrase"] for entry in apple},
                    {key: value for key, value in expected.items() if key != "ghana"},
                )
                self.assertTrue((directory / "pali-snippets-list.md").is_file())

    def test_invalid_terms_leave_previous_outputs_untouched(self):
        invalid_lines = (
            "unknown|mettā", "doctrine jhāna", "|mettā", "doctrine|",
            "doctrine|mettā|extra", "doctrine|mettā/karuṇā",
            "doctrine|mettā\\karuṇā",
        )
        for line in invalid_lines:
            with self.subTest(line=line), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                previous_outputs = (
                    directory / "build/Pali/previous.json",
                    directory / "dist/Pali.alfredsnippets",
                    directory / "dist/Pali Text Replacements.plist",
                    directory / "pali-snippets-list.md",
                )
                for path in previous_outputs:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(b"previous export\n")
                result = self.run_generator(
                    directory, "# invalid fixture\ndoctrine|jhāna\n" + line + "\n"
                )
                self.assertNotEqual(result.returncode, 0)
                for path in previous_outputs:
                    self.assertTrue(path.exists(), f"Removed existing output: {path.name}")
                    self.assertEqual(path.read_bytes(), b"previous export\n")
                self.assertIn("terms.txt:3:", result.stderr)


if __name__ == "__main__":
    unittest.main()
