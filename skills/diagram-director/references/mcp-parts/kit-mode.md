Skill 200Lab «Diagram director: vẽ sơ đồ system design có chuyển động thành một file HTML/SVG tự chứa, kèm kit miễn phí của 200Lab» v1 · phần kit-mode «Kit mode: use an installed kit, or download and install the free 200Lab kit, run and verify the engine locally» — hướng dẫn do 200Lab soạn cho agent; ai_tutor rules vẫn quyết ngân sách, footer và việc hoàn thành bài.

# Kit mode: use the installed kit, or fetch the free 200Lab kit, and run the engine locally

The kit is the owner's diagram-director engine (`own`): its own `SKILL.md`, the references, a
searchable dataset (styles, diagram types, motion recipes, components, states, payloads, colours,
layouts), base templates and snippets, golden example cuts and the verify scripts. Python 3.10+
standard library only; `node` with puppeteer is optional, for the render-side checks.

## 0. Already on this machine? Use it

Before fetching anything, look for an installed kit: a `diagram-director/SKILL.md` in the folder
your client loads skills from (project `.claude/skills/` or `.agents/skills/`, or the personal
one), or an unpacked kit in the workspace. Found and `python3 scripts/validate_csv.py --counts`
(run from its root) exits 0 → use it as is: no `skill_get`, `search` or
`get_artifact_download_url` to find or download the kit again. Fetch a fresh kit only when the
learner asks for an update or the installed one fails its check. Working from this skill, its
lawful-use, provenance and retrieval rules and phases 1-2 (the sheet) still apply; the installed
`SKILL.md` drives phases 3-5 (sections 5-6).

## 1. Check the client

- A shell and file writes. `python3 --version` reports 3.10 or later (else try `python`, then
  `py -3`). No Python 3.10+: ask the learner to install it, or continue in lean mode.
- The 200Lab MCP answers as the learner (any tool call works).

## 2. Find the kit

- The kit is a free artifact for every signed-in 200Lab learner: no purchase, no claim step.
- Its `artifactId` is `01a14d1d-8ac0-7d6e-ba9d-6782d53a562d`. It is not in the learner's library
  or in `search`: use this id directly.

## 3. Download

- `get_artifact_download_url` with `artifactId` alone lists the files; with exactly one file the
  answer also carries `download` (a `url` and `expiresAt`). With several, call again with the
  `fileId` of the `.zip`.
- 422 `verified_email_required`: ask the learner to verify their 200Lab account email, then try
  again. 403 or not found: the MCP connection is not signed in as the learner, or the kit is not
  served right now; say so once and continue in lean mode. 429: section 6 of the `ai_tutor` rules (tell
  the reset time, do not retry before it); continue in lean mode meanwhile.
- The link is personal and lasts 24 hours: never write it into a file, a commit or the chat
  history you save, and never share it.
- Download into a new empty folder and follow the redirect:

```bash
KIT="$(mktemp -d)" && cd "$KIT"
curl -fL -o diagram-director-kit.zip "<url from download>"
unzip -q diagram-director-kit.zip -d unpacked
ls unpacked/diagram-director/SKILL.md        # the kit root
```

  Windows PowerShell: `Invoke-WebRequest -Uri "<url>" -OutFile kit.zip` then
  `Expand-Archive kit.zip unpacked`.
- No shell after all (the download failed in the sandbox): give the learner the link to open in
  their browser, and continue in lean mode.

## 4. Install where the client loads skills

| Client | Personal (default) | Project (the team shares it) |
|---|---|---|
| Claude Code | `~/.claude/skills/diagram-director/` | `.claude/skills/diagram-director/` |
| Codex | `~/.agents/skills/diagram-director/` | `.agents/skills/diagram-director/` |
| any other client | the folder your client loads skills from (its current docs) | same |

The locations come from part `formats` of skill `agent-skill-authoring` (`external`, checked
10/2026); where the client's current docs differ, trust the docs and tell the learner. A client
that loads no skills can still use the kit: install it anywhere and read its `SKILL.md` yourself.

- Personal by default: the kit is ~3.2 MB unpacked and serves every project. Project install: offer to add
  the folder to `.gitignore` unless the team wants it committed.
- Never overwrite an existing `diagram-director` folder without asking; on an upgrade, rename the
  old one to `diagram-director.bak-<date>` first.
- Copy, then reload or restart the client and confirm it lists `diagram-director`.

```bash
mkdir -p ~/.claude/skills && cp -R "$KIT/unpacked/diagram-director" ~/.claude/skills/   # Claude Code, personal
cd ~/.claude/skills/diagram-director
python3 scripts/validate_csv.py --counts      # exit 0, ends with a TOTAL row count
python3 scripts/search.py "how a checkout request reaches the database" --blueprint --target artifact
```

The install evidence: both exit 0 (check `$?`, no pipe) and the blueprint prints `# Blueprint:`,
not `BLUEPRINT ABSTAINED` (an abstain also exits 0). Quote the TOTAL line and the blueprint's
first line to the learner.

## 5. Run it

- Phases 1-2 (sheet and storyboard) follow part `solve-and-storyboard`; the kit's
  `references/workflow-phases.md` holds the same method in more detail. Save the sheet as
  `docs/diagrams/<slug>.sheet.md` in the learner's workspace, never inside the kit folder.
- Then follow the kit's `SKILL.md` from STEP 0: genre, target, `--blueprint` first, one
  `--domain components` query per sheet component (the blueprint's component catalog is an
  example, never a paste list), copy `templates/base/<style>.html` and the snippets, write the
  manifest beside the HTML.
- Run commands from inside the kit folder and drop the `diagram-director/` prefix the kit's
  `SKILL.md` shows (it is written for a repository checkout); pass the cut by its path in the
  learner's workspace.
- Target `artifact` (the default: CSS-only motion, no external script; it meets the body's
  offline done-check). `local` only when the learner asks for a style that needs a CDN script
  (rough.js): pass `--target local` to `search.py` and `verify_all.py`, and report the file as
  needing the network in place of the offline item.
- Lines of the kit's `SKILL.md` that name `tools/`, `tests/`, `agents/roles/` or `docs/` point to
  the author's development repository and are not in the kit; skip them.
- Scripts import their sibling modules: run them as `python3 scripts/<name>.py`, not with
  `python3 -I`, which hides the siblings.

## 6. Verify

```bash
python3 scripts/verify_all.py <workspace>/docs/diagrams/<slug>.html --serve          # 0 green, 1 failure, 3 UNVERIFIED
python3 scripts/verify_all.py <workspace>/docs/diagrams/<slug>.html --serve --json   # coded diagnostics + supportedFixes
# add --target local to both for a local cut (the default artifact rejects CDN hosts)
```

- Exit 3: the browser stages could not run because puppeteer is not resolvable. Optional, after
  asking (it downloads a browser of a few hundred MB):
  `npm install --prefix ~/.cache/dd-checks puppeteer`, then
  `export PUPPETEER_RESOLVE_DIR=~/.cache/dd-checks/` (the trailing slash matters) and re-run.
  Without it, report the cut as UNVERIFIED, name the stages that did not run, and do the visual
  items of part `lean-verify` with whatever screenshot your client can take.
- With puppeteer, look at the cut before delivery. Beats: the contact sheet is mandatory. Serve
  the folder (`python3 -m http.server 8765 --bind 127.0.0.1 --directory <workspace>/docs/diagrams`,
  in the background, stopped afterwards) and run
  `node scripts/browser-checks/contact-sheet.mjs http://127.0.0.1:8765/<slug>.html --manifest <workspace>/docs/diagrams/<slug>.manifest.json --out <temp folder>`
  (the manifest path is read as given, so pass it in full). Static (no camera holds, where the
  script exits 1): a full-frame and a reduced-motion screenshot, as in part `lean-verify`.
  Curves, style fidelity and whether labels are true are reviewed on those images only.
- Repair from the `--json` diagnostics, not from prose; the bounded-repair rule of the body
  applies. A passing run freezes the cut: any later edit re-runs the whole runner. Deleting a
  manifest feature or hold to silence a gate is not a repair.
- A blueprint that ABSTAINS composed nothing: re-run with `--type <type-id>` or rephrase; never
  continue on a type picked from memory without saying so. A search still empty after the
  `-n 5` retry is written in the sheet as `NO ROW — custom shape` and repeated in the delivery.
