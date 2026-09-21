#!/usr/bin/env python3
"""Unit tests for the pure legacy-CLAUDE.md fold used by the project-pack migration.

Run: python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sync_rules import fold_legacy, strip_marker_block  # noqa: E402

MARKER = "agent-harness-kit:index"
BLOCK = f"<!-- {MARKER}:start -->\nkit pack\n<!-- {MARKER}:end -->"


class StripMarkerBlockTests(unittest.TestCase):
    def test_removes_the_kit_block_and_keeps_surrounding_text(self):
        text = f"# Mine\n\n{BLOCK}\n\ntrailing\n"
        stripped = strip_marker_block(text, MARKER)
        self.assertNotIn("kit pack", stripped)
        self.assertIn("# Mine", stripped)
        self.assertIn("trailing", stripped)

    def test_text_without_a_block_is_unchanged(self):
        self.assertEqual(strip_marker_block("# Mine\n", MARKER), "# Mine\n")

    def test_incomplete_block_raises(self):
        with self.assertRaises(ValueError):
            strip_marker_block(f"# Mine\n<!-- {MARKER}:start -->\nno end\n", MARKER)

    def test_other_marker_prefixes_are_kept_as_text(self):
        text = "<!-- agent-harness-kit:start -->\nglobal\n<!-- agent-harness-kit:end -->\n"
        self.assertIn("global", strip_marker_block(text, MARKER))


class FoldLegacyTests(unittest.TestCase):
    def test_appends_operator_text_under_a_migrated_heading(self):
        result = fold_legacy("# Agents\n", "# Claude Only\n", MARKER, "CLAUDE.md")
        self.assertIn("## Migrated from CLAUDE.md", result)
        self.assertIn("# Claude Only", result)
        self.assertTrue(result.startswith("# Agents\n"))

    def test_the_kit_block_in_the_legacy_text_is_not_carried_over(self):
        legacy = f"# Claude Only\n\n{BLOCK}\n"
        self.assertNotIn("kit pack", fold_legacy("# Agents\n", legacy, MARKER, "CLAUDE.md"))

    def test_a_paragraph_already_present_is_not_folded_twice(self):
        agents = "# Agents\n\nShared paragraph.\n"
        legacy = "# Claude Only\n\nShared paragraph.\n"
        result = fold_legacy(agents, legacy, MARKER, "CLAUDE.md")
        self.assertEqual(result.count("Shared paragraph."), 1)
        self.assertEqual(result.count("# Claude Only"), 1)

    def test_dedupe_ignores_whitespace_and_line_wrapping(self):
        agents = "# Agents\n\nOne long   sentence\nwrapped twice.\n"
        legacy = "One long sentence wrapped twice.\n"
        self.assertEqual(fold_legacy(agents, legacy, MARKER, "CLAUDE.md"), agents)

    def test_nothing_left_to_fold_returns_the_input_unchanged(self):
        agents = "# Agents\n"
        self.assertEqual(fold_legacy(agents, f"{BLOCK}\n", MARKER, "CLAUDE.md"), agents)
        self.assertEqual(fold_legacy(agents, "   \n\n", MARKER, "CLAUDE.md"), agents)

    def test_folding_into_an_empty_agents_file(self):
        result = fold_legacy("", "# Claude Only\n", MARKER, ".claude/CLAUDE.md")
        self.assertTrue(result.startswith("## Migrated from .claude/CLAUDE.md"))
        self.assertIn("# Claude Only", result)

    def test_folding_is_idempotent(self):
        once = fold_legacy("# Agents\n", "# Claude Only\n\nSecond.\n", MARKER, "CLAUDE.md")
        twice = fold_legacy(once, "# Claude Only\n\nSecond.\n", MARKER, "CLAUDE.md")
        self.assertEqual(once, twice)

    def test_an_incomplete_marker_block_raises_so_the_caller_can_leave_the_file(self):
        with self.assertRaises(ValueError):
            fold_legacy("# Agents\n", f"<!-- {MARKER}:end -->\n", MARKER, "CLAUDE.md")


if __name__ == "__main__":
    unittest.main()
