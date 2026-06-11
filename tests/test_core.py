from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from deepbrief.analyst import verify_code_deepdive
from deepbrief.llm import is_readonly_bash_command
from deepbrief.tuner import prompt_diff_bounds


class BashGateTests(unittest.TestCase):
    def test_allows_read_only_git(self) -> None:
        self.assertTrue(is_readonly_bash_command("git show HEAD"))

    def test_denies_shell_control_operator(self) -> None:
        self.assertFalse(is_readonly_bash_command("git show HEAD && touch nope"))


class PromptDiffTests(unittest.TestCase):
    def test_small_candidate_is_within_bounds(self) -> None:
        active = "\n".join([f"line {idx}" for idx in range(10)])
        candidate = active + "\nnew bounded line"
        self.assertTrue(prompt_diff_bounds(active, candidate)["ok"])


class CitationVerifierTests(unittest.TestCase):
    def test_verifies_existing_path_line_and_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("def run():\n    return 'ok'\n", encoding="utf-8")
            result = verify_code_deepdive("| step | file:line | symbol |\n| 1 | `app.py:1` | `run` |\n", root)
            self.assertEqual(result["path_pass_rate"], 1.0)
            self.assertEqual(result["symbol_pass_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
