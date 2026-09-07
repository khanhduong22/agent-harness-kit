# Agent Harness Kit

One versioned source of truth for reusable Agent Skills and global rules across Codex, Claude Code, Gemini, and Google Antigravity.

The repository contains 67 portable common skills plus six Claude-specific SDLC adapters. The installer links each skill directory into the native user-level discovery path for every selected harness. Rules are merged into a clearly marked block, so existing personal instructions remain intact.

## Supported harnesses

| Target | Skills | Global rules |
| --- | --- | --- |
| Codex | `~/.agents/skills/` | `~/.codex/AGENTS.md` |
| Claude Code | `~/.claude/skills/` | `~/.claude/CLAUDE.md` |
| Gemini / Antigravity | `~/.gemini/config/skills/` | `~/.gemini/GEMINI.md` |

Antigravity uses the Gemini target because both products share the same global skill and rule locations.

## Install

Clone the repository into a stable path because symlink mode points back to the clone:

```bash
git clone git@github.com:khanhduong22/agent-harness-kit.git ~/.agent-harness-kit
cd ~/.agent-harness-kit
./scripts/install.sh --targets all --rules
```

The default mode is `symlink`. Existing files are skipped. Add `--force` to move conflicts into a timestamped backup under `~/.agent-harness-backups/` before replacing them.

Useful variants:

```bash
# Skills only, selected harnesses
./scripts/install.sh --targets codex,claude

# Copy instead of symlink (updates require reinstalling)
./scripts/install.sh --targets all --mode copy --rules

# Preview every change
./scripts/install.sh --targets all --rules --dry-run
```

## Update

```bash
cd ~/.agent-harness-kit
./scripts/update.sh --targets all --rules
```

`update.sh` performs a fast-forward-only pull and then reruns the idempotent installer.

## Safety model

- Existing skill directories are never overwritten silently.
- `--force` moves conflicts to a backup; it does not delete them.
- Rules live between `agent-harness-kit` markers and can be updated without replacing unrelated instructions.
- No credentials, tokens, MCP settings, hook settings, or machine-specific absolute paths are stored here.
- Run `./scripts/verify.sh` before publishing a change.

## Repository layout

```text
skills/                    Portable Agent Skills (`SKILL.md` plus resources)
overlays/claude/skills/    Claude-specific SDLC command adapters
rules/core.md              Shared always-on rules
rules/adapters/            Harness-specific rendered wrappers
scripts/install.sh         Idempotent multi-harness installer
scripts/update.sh          Pull and reinstall
scripts/verify.sh          Structural and portability checks
scripts/test.sh            Installer integration test in an isolated home
```

## Sources

See [SOURCES.md](SOURCES.md). Bundled third-party material remains subject to its upstream license. Keep the repository private unless those licenses have been reviewed for redistribution.

## Official conventions

- [Codex skills](https://developers.openai.com/codex/skills)
- [Codex `AGENTS.md`](https://developers.openai.com/codex/guides/agents-md)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Claude Code memory and `CLAUDE.md`](https://code.claude.com/docs/en/memory)
- [Google Antigravity skills](https://codelabs.developers.google.com/getting-started-with-antigravity-skills)
