#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate a diagram's output manifest against references/output-manifest.md.

Shape, closed feature vocabulary, per-feature evidence, and -- the point of the
file -- every id in `sources` resolved against the real datasets, so a manifest
cannot name a component, state, motion or payload the skill does not have.

The on-screen half (a declared feature rendering empty) is the browser pass's job;
this is what runs without a browser.

  python3 diagram-director/scripts/validate_manifest.py diagram-director/examples/*.manifest.json
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from csv_cache import get_row                                   # noqa: E402
from csv_config import CSV_CONFIG                               # noqa: E402
from genre_registry import DEFAULT_GENRE, GENRES, row_in_genre  # noqa: E402
from validate_manifest_acts import validate_acts                # noqa: E402

FEATURES = {"beats", "acts", "recap", "staged-states", "spotlight", "captions",
            "act-titles", "payload-glyphs", "state-chips", "replica-stack",
            "legend", "multi-pane", "reduced-motion-mode",
            "node-identity", "act-delta", "role-lens"}
HOLD_KINDS = {"camera", "act", "state", "spotlight", "traffic"}
TARGET_KEYS = ("file", "title", "type", "layout", "style", "palette", "register",
               "viewbox", "master_ms", "beat_ms")
SOURCE_DOMAINS = ("types", "layouts", "styles", "components", "states", "motion", "payloads")
CAMERA_KEYS = ("id", "window", "k", "tx", "ty", "center", "bbox", "fs_min", "p_min")
CAMERA_GATES = {"read", "territory", "overview"}   # overview waives the k_read floor
WINDOW_KEYS = ("element", "keyframe", "windows")


def _windows(hold):
    return [hold["window"]] if hold.get("kind") == "camera" else hold.get("windows", [])


def validate(path):
    """Return a list of error strings; empty means the manifest stands."""
    errs = []
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"{path}: unreadable -- {exc}"]
    say = lambda msg: errs.append(f"{Path(path).name}: {msg}")

    if data.get("manifest") != 1:
        say("`manifest` must be 1 (the only schema version)")
    # ABSENT is not "unknown": a manifest written before the field existed is a
    # system-design cut by construction, so the default is the v1 reading and the
    # frozen goldens keep validating untouched.
    genre = data.get("genre", DEFAULT_GENRE)
    if genre not in GENRES:
        say(f"genre {genre!r} is not one of {list(GENRES)} (absent means {DEFAULT_GENRE!r})")
        genre = DEFAULT_GENRE
    target = data.get("target") or {}
    for key in TARGET_KEYS:
        if key not in target:
            say(f"target is missing {key!r}")
    if target.get("register") not in (None, "reference", "educational"):
        say(f"target.register {target['register']!r} is not reference|educational")
    if isinstance(target.get("viewbox"), list) and len(target["viewbox"]) != 4:
        say("target.viewbox must be [x, y, w, h]")
    master, beat = target.get("master_ms"), target.get("beat_ms")
    if master and beat and master % beat:
        say(f"beat_ms {beat} does not divide master_ms {master} (camera-beat.md divisor rule)")

    features = set(data.get("features") or [])
    for unknown in sorted(features - FEATURES):
        say(f"feature {unknown!r} is not in the closed vocabulary")

    holds = data.get("holds") or []
    kinds = {}
    for i, hold in enumerate(holds):
        kind = hold.get("kind")
        if kind not in HOLD_KINDS:
            say(f"holds[{i}].kind {kind!r} is not one of {sorted(HOLD_KINDS)}")
            continue
        kinds.setdefault(kind, []).append(hold)
        for key in (CAMERA_KEYS if kind == "camera" else WINDOW_KEYS):
            if key not in hold:
                say(f"holds[{i}] ({kind}) is missing {key!r}")
        if kind == "camera" and hold.get("gate", "read") not in CAMERA_GATES:
            say(f"holds[{i}].gate {hold['gate']!r} is not one of {sorted(CAMERA_GATES)}")
        for win in _windows(hold):
            if not (isinstance(win, list) and len(win) == 2
                    and 0 <= win[0] < win[1] <= 100):
                say(f"holds[{i}] window {win} must be [a, b] with 0 <= a < b <= 100")

    validate_acts(data, kinds, say)

    captions = data.get("captions") or []
    for i, cap in enumerate(captions):
        if not cap.get("text", "").strip():
            say(f"captions[{i}] has no text -- a caption with no string is not a caption")
        if not cap.get("element"):
            say(f"captions[{i}] is missing 'element'")

    # A lens hold with NO window is a declared feature with nothing to check: the render
    # side would report "0 lens window(s)" and pass. Evidence means a hold that plays.
    lensed = [h for h in kinds.get("spotlight", [])
              if h.get("lens") and (h.get("windows") or [])]
    evidence = {"beats": bool(kinds.get("camera")), "acts": bool(kinds.get("act")),
                # NOT `acts[]`: node identity is universal now (SKILL.md -> Output Rules),
                # so a single-act or act-less cut declares it too and the RENDER side is
                # what holds it -- stage A cannot see a DOM.
                "node-identity": True,
                "act-delta": bool(data.get("acts")), "role-lens": bool(lensed),
                "staged-states": bool(kinds.get("state")),
                "spotlight": bool(kinds.get("spotlight")), "captions": bool(captions),
                "payload-glyphs": bool(data.get("glyphs")),
                "state-chips": bool((data.get("sources") or {}).get("states")),
                "act-titles": "acts" in features}
    for feature, ok in evidence.items():
        if feature in features and not ok:
            say(f"feature {feature!r} is declared but the manifest carries no evidence for it")
    if "recap" in features:
        for hold in kinds.get("act", []):
            if len(hold.get("windows") or []) < 2:
                say(f"feature 'recap' is declared but act {hold.get('element')!r} has one window")
    if "multi-pane" in features and target.get("layout") not in ("split-compare", "progressive-tiers"):
        say(f"feature 'multi-pane' needs a multi-pane layout, not {target.get('layout')!r}")

    sources = data.get("sources") or {}
    for domain in sorted(set(sources) - set(SOURCE_DOMAINS)):
        say(f"sources.{domain} is not a dataset domain {SOURCE_DOMAINS}")
    # Every cited row must resolve AND belong to the cut's genre. A row from another
    # genre is not a typo -- it is a cut claiming a cast it does not draw, which no
    # id-resolution check can see (the id is perfectly real, in the wrong corpus).
    for domain in SOURCE_DOMAINS:
        for row_id in sources.get(domain, []):
            if domain not in CSV_CONFIG:
                continue
            row = get_row(domain, row_id)
            if row is None:
                say(f"sources.{domain}: {row_id!r} does not resolve in {CSV_CONFIG[domain]['file']}")
            elif not row_in_genre(row, genre):
                say(f"sources.{domain}: {row_id!r} is not a {genre} row")
    for glyph in data.get("glyphs") or []:
        if glyph not in sources.get("payloads", []):
            say(f"glyphs: {glyph!r} is not declared in sources.payloads")
    for hold in holds:
        ref = hold.get("source")
        if ref and (":" not in ref or get_row(ref.split(":", 1)[0], ref.split(":", 1)[1]) is None):
            say(f"holds source {ref!r} does not resolve (expected `<domain>:<row-id>`)")
    for key in ("type", "layout", "style"):
        domain = {"type": "types", "layout": "layouts", "style": "styles"}[key]
        row = get_row(domain, target[key]) if target.get(key) else None
        if target.get(key) and row is None:
            say(f"target.{key} {target[key]!r} does not resolve in {CSV_CONFIG[domain]['file']}")
        elif row is not None and not row_in_genre(row, genre):
            say(f"target.{key} {target[key]!r} is not a {genre} row")
    return errs


def main(argv=None):
    paths = (argv if argv is not None else sys.argv[1:])
    if not paths:
        print(__doc__.strip().splitlines()[-1].strip(), file=sys.stderr)
        return 2
    errors = []
    for path in paths:
        found = validate(path)
        errors += found
        print(f"{'FAIL' if found else 'ok  '}  {path}")
    for err in errors:
        print("  " + err)
    print(f"\n{len(paths)} manifest(s), {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
