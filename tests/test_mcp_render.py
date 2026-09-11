#!/usr/bin/env python3
"""Unit tests for the pure MCP profile parser, renderers and mergers.

Run: python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sync_rules import (  # noqa: E402
    load_mcp_profile,
    merge_mcp_config,
    merge_tool_allowlist,
    parse_profile_mcp,
    render_mcp_config,
    render_tool_allowlist,
    unsupported_target,
)
from verify import literal_secret_errors, profile_mcp_errors  # noqa: E402

PROFILE = """# Sample profile

Prose that must be ignored.

```toml
mcp_tools = [
  "mcp__postgres__query",
  "mcp__framefit__get_layout_spec",
]

[mcp.postgres]
type = "http"
url = "http://localhost:33000/pg"

[mcp.framefit]
command = "npx"
args = ["-y", "framefit"]
env = { FIGMA_TOKEN = "${FIGMA_API_KEY}" }
```
"""


class ParseProfileMcp(unittest.TestCase):
    def test_parses_servers_and_tools(self) -> None:
        profile = parse_profile_mcp(PROFILE)
        self.assertEqual(sorted(profile["mcp"]), ["framefit", "postgres"])
        self.assertEqual(profile["mcp"]["postgres"]["url"], "http://localhost:33000/pg")
        self.assertEqual(profile["mcp"]["framefit"]["env"], {"FIGMA_TOKEN": "${FIGMA_API_KEY}"})
        self.assertEqual(
            profile["mcp_tools"],
            ["mcp__postgres__query", "mcp__framefit__get_layout_spec"],
        )

    def test_profile_without_a_toml_block_is_empty(self) -> None:
        self.assertEqual(parse_profile_mcp("# Just prose\n"), {"mcp": {}, "mcp_tools": []})

    def test_empty_mcp_section_is_empty(self) -> None:
        self.assertEqual(
            parse_profile_mcp("```toml\nmcp_tools = []\n```\n"),
            {"mcp": {}, "mcp_tools": []},
        )

    def test_malformed_block_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            parse_profile_mcp("```toml\n[mcp.postgres\nurl =\n```\n")
        self.assertIn("malformed toml block", str(ctx.exception))

    def test_mcp_must_be_a_table(self) -> None:
        with self.assertRaises(ValueError):
            parse_profile_mcp('```toml\nmcp = "postgres"\n```\n')

    def test_mcp_tools_nested_under_a_server_is_rejected(self) -> None:
        # The trap: toml binds a bare key after a table header to that table.
        with self.assertRaises(ValueError) as ctx:
            parse_profile_mcp('```toml\n[mcp.framefit]\ncommand = "npx"\nmcp_tools = ["a"]\n```\n')
        self.assertIn("mcp_tools", str(ctx.exception))

    def test_mcp_tools_must_be_strings(self) -> None:
        with self.assertRaises(ValueError):
            parse_profile_mcp("```toml\nmcp_tools = [1, 2]\n```\n")


class RenderMcpConfig(unittest.TestCase):
    def test_claude_renders_mcp_servers_mapping(self) -> None:
        rendered = render_mcp_config(parse_profile_mcp(PROFILE), "claude")
        self.assertEqual(sorted(rendered["mcpServers"]), ["framefit", "postgres"])
        self.assertIsNone(unsupported_target(rendered))

    def test_empty_profile_renders_empty_mapping(self) -> None:
        self.assertEqual(render_mcp_config({"mcp": {}}, "claude"), {"mcpServers": {}})
        self.assertEqual(render_mcp_config({}, "claude"), {"mcpServers": {}})

    def test_unverified_targets_return_an_explicit_marker(self) -> None:
        profile = parse_profile_mcp(PROFILE)
        for target in ("codex", "gemini"):
            rendered = render_mcp_config(profile, target)
            self.assertEqual(unsupported_target(rendered), target)
            self.assertNotIn("mcpServers", rendered)

    def test_renderer_does_not_alias_the_profile(self) -> None:
        profile = parse_profile_mcp(PROFILE)
        rendered = render_mcp_config(profile, "claude")
        rendered["mcpServers"]["postgres"]["url"] = "mutated"
        self.assertEqual(profile["mcp"]["postgres"]["url"], "http://localhost:33000/pg")


class RenderToolAllowlist(unittest.TestCase):
    def test_returns_declared_tools_in_order(self) -> None:
        self.assertEqual(
            render_tool_allowlist(parse_profile_mcp(PROFILE), "claude"),
            ["mcp__postgres__query", "mcp__framefit__get_layout_spec"],
        )

    def test_unlisted_tools_of_a_listed_server_are_absent(self) -> None:
        allowlist = render_tool_allowlist(parse_profile_mcp(PROFILE), "claude")
        framefit = [tool for tool in allowlist if tool.startswith("mcp__framefit__")]
        self.assertEqual(framefit, ["mcp__framefit__get_layout_spec"])

    def test_duplicates_are_dropped(self) -> None:
        profile = {"mcp_tools": ["mcp__a__b", "mcp__a__b", "mcp__c__d"]}
        self.assertEqual(render_tool_allowlist(profile, "claude"), ["mcp__a__b", "mcp__c__d"])

    def test_empty_and_unsupported(self) -> None:
        self.assertEqual(render_tool_allowlist({}, "claude"), [])
        self.assertEqual(render_tool_allowlist(parse_profile_mcp(PROFILE), "codex"), [])


class MergeMcpConfig(unittest.TestCase):
    def test_existing_servers_survive(self) -> None:
        original = {"mcpServers": {"local-thing": {"command": "node"}}}
        merged = merge_mcp_config(original, {"mcpServers": {"postgres": {"type": "http"}}})
        self.assertEqual(sorted(merged["mcpServers"]), ["local-thing", "postgres"])
        self.assertEqual(original["mcpServers"], {"local-thing": {"command": "node"}})

    def test_merge_is_idempotent(self) -> None:
        rendered = {"mcpServers": {"postgres": {"type": "http"}}}
        once = merge_mcp_config({}, rendered)
        self.assertEqual(merge_mcp_config(once, rendered), once)

    def test_non_object_mcp_servers_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            merge_mcp_config({"mcpServers": []}, {"mcpServers": {}})


class MergeToolAllowlist(unittest.TestCase):
    def test_unrelated_permission_survives_a_reinstall(self) -> None:
        settings = {
            "permissions": {"allow": ["Bash(git status)"], "deny": ["Bash(rm -rf *)"]},
            "model": "opus",
        }
        merged = merge_tool_allowlist(settings, ["mcp__postgres__query"])
        self.assertEqual(
            merged["permissions"]["allow"], ["Bash(git status)", "mcp__postgres__query"]
        )
        self.assertEqual(merged["permissions"]["deny"], ["Bash(rm -rf *)"])
        self.assertEqual(merged["model"], "opus")
        self.assertEqual(settings["permissions"]["allow"], ["Bash(git status)"])

    def test_reinstall_produces_no_duplicates(self) -> None:
        entries = ["mcp__postgres__query", "mcp__redis__get"]
        once = merge_tool_allowlist({}, entries)
        twice = merge_tool_allowlist(once, entries)
        self.assertEqual(twice, once)
        self.assertEqual(twice["permissions"]["allow"], entries)

    def test_non_array_allow_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            merge_tool_allowlist({"permissions": {"allow": "everything"}}, ["mcp__a__b"])


class LiteralSecretCheck(unittest.TestCase):
    def test_var_references_pass(self) -> None:
        self.assertEqual(literal_secret_errors(parse_profile_mcp(PROFILE)), [])

    def test_non_secret_env_values_pass(self) -> None:
        profile = {"mcp": {"framefit": {"env": {"MCP_TRANSPORT": "stdio"}}}}
        self.assertEqual(literal_secret_errors(profile), [])

    def test_literal_token_is_reported_with_its_key(self) -> None:
        profile = {"mcp": {"framefit": {"env": {"FIGMA_TOKEN": "figd_live_abc"}}}}
        findings = literal_secret_errors(profile)
        self.assertEqual(len(findings), 1)
        self.assertIn("mcp.framefit.env.FIGMA_TOKEN", findings[0])

    def test_credentials_embedded_in_a_url_are_reported(self) -> None:
        profile = {"mcp": {"pg": {"url": "postgres://admin:hunter2@db/idx"}}}
        findings = literal_secret_errors(profile)
        self.assertEqual(len(findings), 1)
        self.assertIn("mcp.pg.url", findings[0])

    def test_var_reference_inside_a_url_passes(self) -> None:
        profile = {"mcp": {"pg": {"url": "postgres://admin:${PG_PASSWORD}@db/idx"}}}
        self.assertEqual(literal_secret_errors(profile), [])

    def test_secret_inside_a_list_is_reported(self) -> None:
        profile = {"mcp": {"x": {"args": ["--token", "live-secret"], "env": {"TOKEN": "nope"}}}}
        findings = literal_secret_errors(profile)
        self.assertEqual(len(findings), 1)
        self.assertIn("mcp.x.env.TOKEN", findings[0])


class VerifyProfileScan(unittest.TestCase):
    """verify.py's profile scan is what makes `scripts/verify.sh` fail."""

    def scan(self, body: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "offender.md").write_text(body, encoding="utf-8")
            return profile_mcp_errors(Path(tmp))

    def test_literal_secret_names_the_profile_and_the_key(self) -> None:
        errors = self.scan('```toml\n[mcp.pg]\nenv = { PG_PASSWORD = "hunter2" }\n```\n')
        self.assertEqual(len(errors), 1)
        self.assertIn("offender.md", errors[0])
        self.assertIn("mcp.pg.env.PG_PASSWORD", errors[0])

    def test_malformed_block_names_the_profile(self) -> None:
        errors = self.scan("```toml\n[mcp.pg\n```\n")
        self.assertEqual(len(errors), 1)
        self.assertIn("offender.md", errors[0])
        self.assertIn("malformed toml block", errors[0])

    def test_clean_profile_reports_nothing(self) -> None:
        self.assertEqual(self.scan(PROFILE), [])

    def test_shipped_profiles_are_clean(self) -> None:
        self.assertEqual(profile_mcp_errors(ROOT / "profiles"), [])


class ShippedIndexProfiles(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = load_mcp_profile(
            [ROOT / "profiles" / "index" / "api.md", ROOT / "profiles" / "index" / "cms.md"]
        )

    def test_index_profiles_declare_the_verified_servers(self) -> None:
        servers = render_mcp_config(self.profile, "claude")["mcpServers"]
        self.assertEqual(
            sorted(servers), ["figma-developer-mcp", "framefit", "postgres", "redis"]
        )
        self.assertEqual(servers["postgres"], {"type": "http", "url": "http://localhost:33000/pg"})

    def test_index_allowlist_excludes_the_403_framefit_tools(self) -> None:
        allowlist = render_tool_allowlist(self.profile, "claude")
        self.assertIn("mcp__framefit__get_layout_spec", allowlist)
        self.assertNotIn("mcp__framefit__get_variables", allowlist)
        self.assertNotIn("mcp__framefit__get_libraries", allowlist)

    def test_index_profiles_hold_no_literal_secrets(self) -> None:
        self.assertEqual(literal_secret_errors(self.profile), [])


if __name__ == "__main__":
    unittest.main()
