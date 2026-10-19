#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stages C and E of diagram-director/scripts/verify_all.py: the render-side gates, manifest-gated.

Every entry below names the FEATURE that makes its check mandatory. That mapping is the
zero-means-fail contract from references/output-manifest.md:

  declared + the check finds nothing  -> the .mjs exits 1 on an empty element set
                                         (browser-checks/README.md house rule) -> FAIL
  not declared                        -> the check never runs -> N-A, printed as such

`always` entries have no feature: a diagram with no text and no console is not a diagram.

Exit codes from the .mjs scripts: 0 pass, 1 violation (or empty element set), 2 could not
run. Code 2 is disambiguated by the UNVERIFIED banner on stderr -- a code 2 WITH the banner
is "puppeteer absent", anything else at code 2 is a usage error and fails.
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import act_dom_scan as scan                                           # noqa: E402
from genre_registry import DEFAULT_GENRE                              # noqa: E402
from verify_all_json import fold_diag_lines                           # noqa: E402
from verify_all_report import bad, na, ok, unverified                 # noqa: E402

CHECKS_DIR = Path(__file__).resolve().parent / "browser-checks"
BANNER_MARK = "UNVERIFIED -- puppeteer not available"

# (stage, feature-that-makes-it-mandatory or None, label, script, extra argv)
SPEC = [
    ("C browser", None, "text-containment", "verify-text-containment.mjs", []),
    ("C browser", None, "console-clean", "verify-console-clean.mjs", []),
    ("C browser", "captions", "caption-boxes", "verify-caption-boxes.mjs", []),
    ("C browser", "payload-glyphs", "glyph-label-gap", "verify-glyph-label-gap.mjs", []),
    ("C browser", "staged-states", "staged-windows", "verify-staged-windows.mjs", []),
    ("C browser", "acts", "staged-windows --acts", "verify-staged-windows.mjs", ["--acts"]),
    ("C browser", "acts", "staged-windows --reduced-motion", "verify-staged-windows.mjs",
     ["--reduced-motion"]),
]

# --- gates whose evidence is the DOM, not a declared feature ------------------------
# `node-identity` is declarable by ANY cut because its evidence is the file itself
# (references/output-manifest.md), and the glyph/label rule is the same shape: a node that
# draws a badge owes its own label clearance whether or not the cut also declares
# `payload-glyphs`. Gating it on that feature alone meant a cut with seven node glyphs and
# no packets -- a correct, undeclared cut -- never ran the only check of that class, and
# shipped a glyph at the clearance floor of its own label. The FEATURE gate stays beside it
# untouched: `payload-glyphs` declared and zero pairs on screen is still a hard fail, which
# is the declared-but-empty contract and not something DOM evidence can replace.
#
# Read with the same stdlib scanner the act-identity gates use, so this costs no browser.
def has_node_glyph(html_text):
    """True when at least one `.node__icon` is drawn inside a `<g class="node">`."""
    text = scan.COMMENT.sub("", html_text or "")
    return any("node__icon" in scan.group_body(text, match)
               for match in scan.NODE_OPEN.finditer(text))


# label -> (predicate over the HTML text, the evidence phrase printed on the row)
DOM_GATES = {
    "glyph-label-gap": (has_node_glyph, ".node__icon inside a g.node"),
}

# Stage E is one script over every declared camera hold; curves are its explicit N-A.
GEOMETRY = ("E geometry", "beats", "hold-geometry", "verify-hold-geometry.mjs")

# Stage E, gated on TWO features, and the only gate in the runner that is.
#
# A caption card is measured against the scene UNDER it -- the edge labels it could destroy
# and the edges of its own beat's subjects -- so the check needs BOTH halves of the cut:
# `captions` to have a card at all, and `beats` because "its own window" and "the camera
# pose there" are only defined at a declared hold. Either one absent and there is nothing
# to be right about, which is an N-A with that reason and never a quiet pass.
CAPTION_OCCLUSION = ("E geometry", ("captions", "beats"), "caption-occlusion",
                     "verify-caption-occlusion.mjs")

# Stage E, EVERY genre. Same gating as GEOMETRY (a hold-aware check needs declared
# holds and the `beats` feature) and the same argv.
#
# CAMERA-LIVE is the only gate in the whole runner that asks the PAGE what the camera
# is doing. Stage D re-solves the manifest without opening a browser, stage E PINS the
# hold's transform before it measures, and the regression reads the HTML with a regex --
# so a cut whose `@keyframes beats` had been killed by a stray comment once printed 20
# PASS with no camera motion at all (builder-260827-1408, unresolved 1). Reading the
# computed transform BEFORE pinning closes that whole class, and it is genre-neutral:
# every cut this skill ships drives one `.camera` off the manifest's own k/tx/ty.
GEOMETRY_COMMON = [("camera-live", "verify-camera-live.mjs", [])]

# Stage E, per-genre additions.
#
# FRAME-MARGIN is here rather than in SPEC because it is a HOLD-aware check: it can
# only be asked at a frame, and a frame only exists at a declared hold. The RULE is
# engine-general (references/camera-beat.md -- "keep the teaching line off the frame
# edge"); only the INSTRUMENT is per-genre, because the two construction modes hide
# their stations in different places. A `process` cut's stations are `[data-station]`
# DIVs inside a `.frame`; a `system-design` cut's are `g.node > .node__shape` inside
# the root `<svg>` (plus the two other things an edge may honestly terminate on --
# `.lane-line` lifelines and `.group__box` cluster boundaries -- exactly as
# diagram-director/scripts/verify_edge_anchors.py enumerates them). Same rule, same M, one reader each.
GEOMETRY_EXTRA = {
    "process": [("frame-edge-margin", "verify-frame-edge-margin.mjs", [])],
    "system-design": [("frame-edge-margin",
                       "verify-svg-frame-edge-margin.mjs", [])],
}

# --- genre substitutions (additive; `system-design` never reaches this table) ---
# A `process` cut is built HTML-FIRST: its stations are divs and only the connectors
# live in an <svg class="edges"> overlay (references/genres/process.md -> Construction
# mode). `verify-text-containment.mjs` reasons entirely about SVG `g.node` +
# `.node__shape`, so on such a file it finds zero nodes and FAILS by the house rule --
# a gate that fails 100% of correct files measures nothing. The HTML-mode instrument
# for the SAME two defect classes (plus DEAD GEOMETRY, the cost of contract clause 4)
# is verify-html-edge-anchors.mjs, so the process corpus runs that one INSTEAD.
# Everything else in SPEC is genre-neutral and keeps running unchanged.
#
# That one script also carries the WEBAPP TEMPLATE CONTRACT v2 (three semantic
# [data-anchor] per webapp station, none gated by data-lod="close", no self-set
# opacity inside an LOD subtree). It rides there rather than in a fourth entry
# on purpose: the contract is scoped to stations that declare `.win` or hold a
# [data-anchor], so a process cut with no webapp station would give a new SPEC
# row nothing to measure -- and by the house rule an empty check FAILS. Folding
# it in keeps the process line count identical and keeps `system-design` byte
# for byte unchanged.
GENRE_SWAP = {
    "process": {
        "text-containment": ("html-edge-anchors", "verify-html-edge-anchors.mjs", []),
    },
}


def run_node(script, argv, timeout=180):
    """(status, first_meaningful_line, [##DIAG payload, ...]). status is pass/fail/unverified.

    The `##DIAG {json}` lines a check emits are STRUCTURED evidence for the JSON envelope
    (diagram-director/scripts/browser-checks/README.md -> "The ##DIAG line"). They are folded out of both
    streams BEFORE the prose tail is built, so the human stage table reads exactly as it
    did before any check learned to emit them.
    """
    path = CHECKS_DIR / script
    if not path.exists():
        return "fail", f"{script} is missing from {CHECKS_DIR}", []
    proc = subprocess.run(["node", str(path)] + argv,
                          capture_output=True, text=True, timeout=timeout)
    out, out_diags = fold_diag_lines(proc.stdout or "")
    err, err_diags = fold_diag_lines(proc.stderr or "")
    out, err, diags = out.strip(), err.strip(), out_diags + err_diags
    if proc.returncode == 2 and BANNER_MARK in err:
        return "unverified", BANNER_MARK, diags
    tail = (out.splitlines() or err.splitlines() or [""])
    if proc.returncode == 0:
        return "pass", tail[0][:200], diags
    detail = " | ".join(line.strip() for line in (out.splitlines() + err.splitlines())
                        if line.strip())[:400]
    return "fail", detail or f"exit {proc.returncode}", diags


def _result(stage, label, status, reason, diags=()):
    """The folded payloads ride in `evidence['diagnostics']`; verify_all_json expands them
    into one diagnostic each, because a browser sweep reports several defects per run."""
    make = {"pass": ok, "fail": bad, "unverified": unverified}[status]
    evidence = {"reason": reason, "diagnostics": list(diags)} if diags else None
    return make(stage, label, reason, evidence=evidence)


def run_stage_c(url, features, genre=DEFAULT_GENRE, html_text=""):
    """`html_text` is the cut's own source, read once by the caller: a DOM-gated check
    decides from the FILE whether it is mandatory, which costs no extra browser trip."""
    results = []
    swaps = GENRE_SWAP.get(genre, {})
    for stage, feature, label, script, extra in SPEC:
        if label in swaps:
            label, script, extra = swaps[label]
        declared = not feature or feature in features
        dom_gate = DOM_GATES.get(label)
        dom_evidence = bool(dom_gate and dom_gate[0](html_text))
        if not declared and not dom_evidence:
            why_not = f"feature {feature!r} not declared"
            if dom_gate:
                why_not += f", and the file draws no {dom_gate[1]}"
            results.append(na(stage, label, why_not))
            continue
        status, reason, diags = run_node(script, [url] + extra)
        if declared and feature:
            why = f"[{feature}] {reason}"
        elif dom_evidence:
            why = f"[dom: {dom_gate[1]}] {reason}"
        else:
            why = reason
        results.append(_result(stage, label, status, why, diags))
    return results


def _caption_occlusion_row(url, manifest_path, features, holds):
    """The caption card vs the scene under it. Two features and a hold, or N-A."""
    stage, needed, label, script = CAPTION_OCCLUSION
    missing = [f for f in needed if f not in features]
    if missing:
        return na(stage, label,
                  f"feature(s) {missing} not declared -- a caption card is measured "
                  f"against the scene at a declared hold, inside its own window")
    if not holds:
        return na(stage, label, "no camera holds declared -- nothing to evaluate at")
    status, reason, diags = run_node(script, [url, "--manifest", str(manifest_path)])
    return _result(stage, label, status, f"[captions+beats] {reason}", diags)


def run_stage_e(url, manifest_path, features, holds, genre=DEFAULT_GENRE):
    """Ink-vertical containment, straight-segment intersections, the caption-vs-scene
    sweep and (per genre) the frame-margin sweep, all at every declared hold."""
    stage, feature, label, script = GEOMETRY
    extras = GEOMETRY_COMMON + GEOMETRY_EXTRA.get(genre, [])
    caption_row = _caption_occlusion_row(url, manifest_path, features, holds)
    if not holds:
        return [na(stage, label, "no camera holds declared -- nothing to evaluate at"),
                na(stage, "curves", "curved edges are never geometry-checked; "
                                    "they are contact-sheet territory (visual review)")] \
            + [na(stage, lbl, "no camera holds declared -- nothing to evaluate at")
               for lbl, _, _ in extras] + [caption_row]
    if feature not in features:
        return [na(stage, lbl, f"feature {feature!r} not declared")
                for lbl in [label] + [e[0] for e in extras]] + [caption_row]
    argv = [url, "--manifest", str(manifest_path)]
    status, reason, diags = run_node(script, argv)
    results = [_result(stage, label, status, reason, diags),
               na(stage, "curves", "curved edges skipped by design -- straight segments only; "
                                   "curves are reviewed on the contact sheet (G17)")]
    for lbl, extra_script, extra_argv in extras:
        extra_status, extra_reason, extra_diags = run_node(extra_script, argv + extra_argv)
        results.append(_result(stage, lbl, extra_status, extra_reason, extra_diags))
    results.append(caption_row)
    return results
