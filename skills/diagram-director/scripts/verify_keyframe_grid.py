#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The KEYFRAME half of stage B's master-divisor rule: `keyframe-grid`.

Its own module for the same reason verify_all split into four: the other stage-B
checks are provable from the FILE ALONE, and this one needs the MANIFEST -- a
different input, a different failure mode, and the only stage-B check that can go
N-A. Everything it shares with its sibling (the CSS regexes, `var()` resolution,
the `<time>` reader, the brace-matching @keyframes walker) is IMPORTED from
verify_all_structural rather than re-spelt, so those patterns keep one home.

Read the block comment below before changing the grid or the tolerance: both were
chosen by measuring all four frozen goldens, not by taste.
"""

import re

from verify_all_structural import (_CUSTOM_PROP, _DECL, _TIME, _keyframe_blocks,
                                   _ms, _resolve_vars)

_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_KF_OPEN = re.compile(r"@keyframes\s+([-\w]+)\s*\{")
_RULE = re.compile(r"([^{}@]+)\{([^{}]*)\}")
# animation shorthand words that are never the @keyframes name
_ANIM_KEYWORDS = {"infinite", "both", "forwards", "backwards", "none", "normal",
                  "alternate", "alternate-reverse", "reverse", "paused", "running",
                  "linear", "ease", "ease-in", "ease-out", "ease-in-out",
                  "step-start", "step-end", "important"}

GRID_TOL_PP = 0.01      # percentage points a stop may sit off a declared instant

# HAND-AUTHORED master-length keyframes whose stops are legitimately NOT on the
# cut's declared grid. Named here the way tests/run_golden_regression.py names its
# emitter exemptions (PROCESS_OWN_IDIOM) -- never inferred, always with a reason:
#
#   chrome-fade / heading-fade   the PAGE CHROME fade (title, legend, banner):
#       one block per cut, six stops, no camera pose and no teaching content on it.
#       Its two shoulders are hand-eased scenery -- 240ms past b7 in the process
#       golden, 720ms past b1 in compare-chat-pubsub -- so they sit between grid
#       instants by construction, and all four frozen goldens ship them that way.
#       The contact sheet is what reviews this block; a retimed cut moves the
#       chrome fade cosmetically, never the beat it is read against.
#   lod-        the two-tier LOD fade rides an animated `--lodc` whose ramp sits
#       INSIDE the window instead of leading it (process sheet deviation 17) --
#       the same family run_golden_regression already exempts by name, and it is
#       owed the same engine pass in diagram-director/scripts/timeline_css_idiom.py.
#
# NOT stale-checked the way the regression's list is: that list is per-cut, this
# one is repo-wide, so `heading-fade` matching nothing in a process cut is normal.
OFF_GRID_EXEMPT = ("chrome-fade", "heading-fade", "lod-")


# The DIVISOR check in verify_all_structural proves every animation's DURATION divides the master.
# It says nothing about WHERE inside that duration the stops sit, and that is a
# real hole: when the process golden's master went 33.6s -> 38.4s the emitter
# re-derived every window it owns from ms, but `br-back`, `br-ok` and
# `pull-park` are HAND-AUTHORED -- their literal percentages stayed on the old
# scale, still divided the master perfectly, and only a pixel diff caught them.
#
# THE RULE (references/camera-beat.md -> "Every stop is an instant the manifest
# names"). For a keyframe driven by an animation whose duration IS the master,
# one turn of the block is one turn of the story, so a stop IS an instant of the
# cut. Every such stop must land within GRID_TOL_PP of an instant the manifest
# already declares:
#
#     {0, 100} u {n * beat}                the beat grid, from target.beat_ms
#              u {every window edge}       holds[].window / windows / captions[]
#
# SCOPE, and why it stops where it does. A keyframe the MANIFEST PINS -- one
# named by a `holds[].keyframe`, or carried by a `holds[].element` /
# `captions[].element` -- is already diffed stop-for-stop against the cut's own
# event table by tests/run_golden_regression.py, and its fade shoulders are
# legitimately off-grid (a 600ms lead off a window edge declared at 4435.2ms is
# not a beat instant and never was). Re-checking those here would duplicate a
# stronger gate and import its fractional-ms windows as false failures. What is
# LEFT is exactly the hand-authored set -- the blocks no fixture re-derives, the
# ones the retiming rotted -- so that is what this measures.
#
# TOLERANCE. GRID_TOL_PP = 0.01 pp is a ROUNDING allowance, not slack: the
# emitter rounds each stop once, to 4dp (timeline_css_idiom.pct), which at a
# 38.4s master is at most 0.00005 pp = 0.02ms of error. Measured on the four
# frozen goldens the worst in-scope stop sits 0.00005 pp off; a stop left on a
# 33.6s scale lands 0.1-0.8 pp off, i.e. 10x to 80x outside the allowance.


def _strip_comments(css):
    return _COMMENT.sub(" ", css)


def _rules_outside_keyframes(css):
    """(selector-token, declaration-text) for every rule that is NOT a keyframe stop.

    @keyframes bodies are cut out first, by brace matching, so a `0%,12.5%{...}`
    stop can never be read as a selector. Comments go first of all: a `/* ... */`
    that ends just before a rule is otherwise glued onto its first selector token
    (`... */\\n.br-back` reads as one selector) and that rule is silently dropped
    -- which is exactly how `br-back`, the keyframe this check exists for, went
    missing from the first draft's index.
    """
    css = _strip_comments(css)
    kept, prev = [], 0
    for match in _KF_OPEN.finditer(css):
        depth, i = 1, match.end()
        while i < len(css) and depth:
            depth += (css[i] == "{") - (css[i] == "}")
            i += 1
        kept.append(css[prev:match.start()])
        prev = i
    kept.append(css[prev:])
    out = []
    for match in _RULE.finditer("".join(kept)):
        for token in match.group(1).split(","):
            token = token.strip()
            if token:
                out.append((token, match.group(2)))
    return out


def animation_index(css):
    """({selector: {keyframe-name}}, {selector: {duration_ms}}).

    Keyed on the selector token AS WRITTEN, which is what lets the two halves of
    the house idiom meet: `.br-back,.br-ok{animation-duration:var(--master)}`
    carries the time and `.br-back{animation-name:br-back}` carries the name.
    """
    table = {name: value.strip() for name, value in _CUSTOM_PROP.findall(css)}
    names, durations = {}, {}
    for selector, decls in _rules_outside_keyframes(css):
        for prop, value in _DECL.findall(decls):
            low = prop.lower()
            if low not in ("animation", "animation-name", "animation-duration"):
                continue
            resolved = _resolve_vars(value, table)
            for part in resolved.split(","):
                if low != "animation-duration":
                    for word in re.split(r"\s+", part.strip()):
                        word = word.strip(";").lower()
                        if (not word or word in _ANIM_KEYWORDS or word.startswith("!")
                                or _TIME.fullmatch(word)
                                or word.startswith(("cubic-bezier", "steps"))):
                            continue
                        names.setdefault(selector, set()).add(
                            word.split("!")[0])
                        break
                if low != "animation-name":
                    times = _TIME.findall(part)
                    if times:
                        durations.setdefault(selector, set()).add(
                            _ms(f"{times[0][0]}{times[0][1]}"))
    return names, durations


def declared_instants(manifest):
    """Sorted percents the manifest itself names: beat grid + every window edge."""
    spec = manifest.get("target") or {}
    master = float(spec.get("master_ms") or 0)
    beat = float(spec.get("beat_ms") or 0)
    instants = {0.0, 100.0}
    if master and beat:
        step, n = beat / master * 100.0, 0
        while n * step <= 100.0 + 1e-9:
            instants.add(n * step)
            n += 1
    for hold in manifest.get("holds") or []:
        windows = hold.get("windows") or ([hold["window"]] if hold.get("window") else [])
        for window in windows:
            instants.update(float(v) for v in window)
    for caption in manifest.get("captions") or []:
        instants.update(float(v) for v in (caption.get("window") or []))
    return sorted(instants)


def _stops(body):
    """([percent], [unreadable]) for every stop in a keyframe body."""
    out, unreadable = [], []
    for match in re.finditer(r"([^{}]+)\{[^{}]*\}", body):
        for token in match.group(1).split(","):
            token = token.strip().lower()
            if not token:
                continue
            if token in ("from", "to"):
                out.append(0.0 if token == "from" else 100.0)
            elif token.endswith("%"):
                try:
                    out.append(float(token[:-1]))
                except ValueError:
                    unreadable.append(token)
            else:
                unreadable.append(token)
    return out, unreadable


def check_keyframe_stops(css, manifest, exempt=OFF_GRID_EXEMPT):
    """(violations, notes, checked, exempted) -- see the block comment above.

    The caller must have both a `master_ms` and a `beat_ms`; without them the cut
    declares no grid and this check is N-A, never a pass.
    """
    master = float((manifest.get("target") or {}).get("master_ms") or 0)
    names, durations = animation_index(css)
    driven = set()
    for selector, keyframes in names.items():
        if any(d and abs(d - master) < 1e-6 for d in durations.get(selector, ())):
            driven |= keyframes
    pinned = set()
    for hold in manifest.get("holds") or []:
        if hold.get("keyframe"):
            pinned.add(str(hold["keyframe"]).lower())
        if hold.get("element"):
            pinned |= names.get(hold["element"], set())
    for caption in manifest.get("captions") or []:
        pinned |= names.get(caption.get("element", ""), set())

    grid = declared_instants(manifest)
    errs, notes, checked, exempted = [], [], [], []
    for name, body in _keyframe_blocks(_strip_comments(css)):
        low = name.lower()
        if low not in driven or low in pinned:
            continue
        if low.startswith(tuple(exempt)):
            exempted.append(name)
            continue
        checked.append(name)
        stops, unreadable = _stops(body)
        for token in unreadable:
            notes.append(f"@keyframes {name}: stop {token!r} is not a percentage")
        for stop in sorted(set(stops)):
            off = min(abs(stop - instant) for instant in grid)
            if off > GRID_TOL_PP:
                near = min(grid, key=lambda i: abs(stop - i))
                errs.append(
                    f"@keyframes {name} stop {stop:g}% ({stop / 100 * master:.1f}ms) sits "
                    f"{off:.4f} pp off the nearest instant the manifest declares "
                    f"({near:g}%) -- a hand-authored stop on another master's scale")
    if not checked and not exempted:
        notes.append("this cut has no hand-authored master-length @keyframes")
    return errs, notes, checked, exempted
