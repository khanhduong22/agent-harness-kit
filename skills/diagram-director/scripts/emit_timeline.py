#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Table -> CSS EMITTER for camera-beat timelines (references/camera-beat.md).

An emitter, NOT a compiler. It turns a sheet's event table into exact `@keyframes`
percents, `animation-name` lines and `data-window` values, plus the matching
`holds`/`captions` fragment for the output manifest (references/output-manifest.md).
It never invents a row, an element, a caption or a beat: anything the table does
not state is a REFUSAL, not a default. The CSS shapes live in timeline_css_idiom.py.

Why it exists: hand-computed window percents drift -- a rounded 42.8571 fed back
into `+1.7857` lands 0.0001 off and every downstream stop inherits it. This does
the arithmetic in exact floats from ms/beat inputs and rounds once, at the end.

INPUT -- TSV or markdown table, header row required. Columns:
  element   selector the window rides on (`.stage-oload-a1`)             required
  kind      state | spotlight | traffic | act | caption                  required
  keyframe  @keyframes name                                              required
  windows   space-separated `START:END[:LEAD[:TAIL]]`                    required
  lead      row-default fade-in duration   (default 600ms)
  tail      row-default fade-out duration  (default = lead)
  park      the act's parked transform, e.g. `translate(0px,-2400px)`    act only, required
  seam      fade-out duration for the 0% loop-seam segment               act/traffic
  wipe      clip-path wipe duration (default 600ms)                      caption only
  eps       LEGACY, ignored: the opacity-snap epsilon of the old caption
            block. The caption is clip-only now (timeline_css_idiom.caption_window)
            so there is no opacity stop for it to sit before. Still accepted as a
            column so the frozen goldens' event tables keep parsing unchanged.
  text      the VERBATIM caption string from the sheet                   caption only, required
  source    dataset row id (`states:is-overloaded`) for the manifest     optional
Endpoints and durations carry a unit: `42.8571%`, `4000ms`, or `b2.5` (beats, needs --beat).

USAGE
  emit_timeline.py TABLE --master 33600ms [--beat 4800ms]
                   [--out CSS] [--manifest JSON] [--format css|json|both]
                   [--acts-table SHEET.md]

`--acts-table` merges the sheet's `## Phase 2 -- ACT DELTA` table into the JSON
fragment as `acts[]`, so the manifest's act deltas come out of the same emitter run
as its windows (diagram-director/scripts/emit_act_delta.py does the parsing).
"""

import argparse
import json
import re
import sys

from timeline_css_idiom import act_windows, caption_window, opacity_windows, pct  # noqa: F401

KINDS = ("state", "spotlight", "traffic", "act", "caption")
ANNOTATED = ("state", "traffic", "act")     # kinds that carry a data-window attribute
COLUMNS = ("element", "kind", "keyframe", "windows", "lead", "tail",
           "park", "seam", "wipe", "eps", "text", "source")


class Refuse(Exception):
    """The table asked for something the emitter must not invent."""


def _unit(tok, master_ms, beat_ms, where):
    tok = (tok or "").strip()
    if tok.endswith("%"):
        return float(tok[:-1])
    if tok.endswith("ms"):
        return float(tok[:-2]) / master_ms * 100.0
    if tok.startswith("b"):
        if not beat_ms:
            raise Refuse(f"{where}: beat endpoint {tok!r} needs --beat")
        return float(tok[1:]) * beat_ms / master_ms * 100.0
    raise Refuse(f"{where}: {tok!r} needs a unit -- %, ms or bN")


def read_table(path, columns=COLUMNS, required=("element", "kind", "keyframe", "windows")):
    """Rows of a TSV or markdown table as dicts. Blank and `#` lines are skipped."""
    lines = [ln.rstrip("\n") for ln in open(path, encoding="utf-8")
             if ln.strip() and not ln.lstrip().startswith("#")]
    return parse_table(lines, path, columns, required)


def parse_table(lines, where, columns=COLUMNS,
                required=("element", "kind", "keyframe", "windows")):
    """The row splitting itself, over lines already selected by the caller.

    Apart so a SECOND table with its own header can reuse exactly this splitting rather
    than growing a parser that drifts from it -- diagram-director/scripts/emit_act_delta.py reads the
    sheet's ACT DELTA table through here (`columns`/`required` are the only difference).
    """
    path = where
    if not lines:
        raise Refuse(f"{path}: no rows")
    md = lines[0].lstrip().startswith("|")
    cells = (lambda ln: [c.strip() for c in ln.strip().strip("|").split("|")]) if md \
        else (lambda ln: [c.strip() for c in ln.split("\t")])
    header = [h.lower() for h in cells(lines[0])]
    missing = [c for c in required if c not in header]
    unknown = [h for h in header if h not in columns]
    if missing or unknown:
        raise Refuse(f"{path}: header missing {missing} / unknown {unknown} "
                     f"-- the emitter defaults nothing")
    rows = []
    for line in lines[1:]:
        if md and re.fullmatch(r"[|\s:-]+", line):
            continue
        values = cells(line)
        if len(values) != len(header):
            # A row is SHORT far more often than it is long, and the reason is almost
            # always an optional trailing column (`text`, `note`) left empty: most
            # editors strip the trailing tab, so the row loses a cell it looks like it
            # has. The emitter defaults nothing, so it cannot guess -- but it can say
            # exactly what to type, instead of leaving the author counting tabs.
            hint = ""
            if len(values) < len(header):
                short = header[len(values):]
                sep = "`|` and an empty cell" if md else "TAB character"
                hint = (f" -- missing the trailing column(s) {short}; an optional cell "
                        f"left EMPTY still needs its separator, so end the line with "
                        f"{len(short)} more {sep}"
                        f"{'s' if len(short) > 1 else ''} (most editors strip it)")
            raise Refuse(f"{path}: row {values[:1]} has {len(values)} cells, "
                         f"header has {len(header)}{hint}")
        rows.append(dict(zip(header, values)))
    return rows


def _windows(row, where, master_ms, beat_ms, lead, tail):
    wins = []
    for tok in (row.get("windows") or "").split():
        parts = tok.split(":")
        if not 2 <= len(parts) <= 4:
            raise Refuse(f"{where}: window {tok!r} must be START:END[:LEAD[:TAIL]]")
        parts += [""] * (4 - len(parts))
        span = [_unit(parts[0], master_ms, beat_ms, where),
                _unit(parts[1], master_ms, beat_ms, where),
                _unit(parts[2], master_ms, beat_ms, where) if parts[2] else lead,
                _unit(parts[3], master_ms, beat_ms, where) if parts[3] else tail]
        if not 0 <= span[0] < span[1] <= 100:
            raise Refuse(f"{where}: window {tok!r} resolves to {span[0]}..{span[1]}, "
                         f"need 0 <= start < end <= 100")
        if wins and span[0] < wins[-1][1]:
            raise Refuse(f"{where}: window {tok!r} overlaps or precedes the previous one")
        wins.append(tuple(span))
    if not wins:
        raise Refuse(f"{where}: no windows -- the emitter does not generate them")
    return wins


def parse_row(row, master_ms, beat_ms):
    """Validated row with its windows resolved to percents. Refuses every gap."""
    element, kind = row.get("element", ""), row.get("kind", "")
    where = f"{element or '<no element>'} ({kind or 'no kind'})"
    if not element or not row.get("keyframe"):
        raise Refuse(f"{where}: element and keyframe are required, never defaulted")
    if kind not in KINDS:
        raise Refuse(f"{where}: kind must be one of {KINDS}")
    lead = _unit(row.get("lead") or "600ms", master_ms, beat_ms, where)
    tail = _unit(row["tail"], master_ms, beat_ms, where) if row.get("tail") else lead
    wins = _windows(row, where, master_ms, beat_ms, lead, tail)
    if kind == "act" and not row.get("park"):
        raise Refuse(f"{where}: kind=act needs a park transform (the act's off-canvas pose)")
    if kind == "caption" and not row.get("text"):
        raise Refuse(f"{where}: kind=caption needs the sheet's verbatim text "
                     f"-- captions are never generated")
    seam = _unit(row["seam"], master_ms, beat_ms, where) if row.get("seam") else None
    if seam is None and wins[-1][1] >= 100 and wins[0][0] > 0:
        print(f"WARNING {where}: last window reaches 100% but the element is hidden at 0% "
              f"and no seam duration is given -- the loop seam will not be byte-identical.",
              file=sys.stderr)
    return dict(row, kind=kind, wins=wins, seam=seam,
                wipe=_unit(row.get("wipe") or "600ms", master_ms, beat_ms, where))


def body(row):
    """The row's @keyframes body, from the idiom module."""
    if row["kind"] == "caption":
        start, end, _lead, tail = row["wins"][0]
        return caption_window(start, end, tail, row["wipe"])
    if row["kind"] == "act":
        return act_windows(row["wins"], row["park"], row["seam"])
    return opacity_windows(row["wins"])


def emit(rows):
    """(css_text, manifest_fragment) for parsed rows."""
    css, seen, holds, captions = [], {}, [], []
    for row in rows:
        name, block = row["keyframe"], body(row)
        if name in seen and seen[name] != block:
            raise Refuse(f"{name}: two rows define the same @keyframes differently")
        windows = [[float(pct(s)), float(pct(e))] for s, e, _l, _t in row["wins"]]
        if row["kind"] == "caption":
            captions.append({"element": row["element"], "text": row["text"],
                             "window": windows[0]})
        else:
            entry = {"element": row["element"], "kind": row["kind"], "keyframe": name,
                     "windows": windows}
            if row.get("source"):
                entry["source"] = row["source"]
            holds.append(entry)
        if row["kind"] in ANNOTATED:
            attr = " ".join(f"{pct(s)},{pct(e)}" for s, e, _l, _t in row["wins"])
            css.append(f'/* {row["element"]} -> data-window="{attr}" */')
        css.append(f'{row["element"]}{{animation-name:{name}}}')
        if name not in seen:
            css.append(f"@keyframes {name}{{{block}}}")
        seen[name] = block
    return "\n".join(css) + "\n", {"holds": holds, "captions": captions}


def _ms(text):
    return float(text[:-1]) * 1000 if text.endswith("s") and not text.endswith("ms") \
        else float(text.rstrip("ms"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("table")
    ap.add_argument("--master", required=True, help="master duration, e.g. 33600ms or 33.6s")
    ap.add_argument("--beat", help="beat length, e.g. 4800ms (needed for bN endpoints)")
    ap.add_argument("--format", choices=("css", "json", "both"), default="css")
    ap.add_argument("--acts-table", help="a sheet carrying a `## Phase 2 -- ACT DELTA` "
                                         "table; its acts[] fragment is merged into the "
                                         "JSON output (diagram-director/scripts/emit_act_delta.py)")
    ap.add_argument("--out"), ap.add_argument("--manifest")
    args = ap.parse_args(argv)
    try:
        master, beat = _ms(args.master), (_ms(args.beat) if args.beat else None)
        if beat and master % beat:
            raise Refuse(f"beat {beat}ms does not divide master {master}ms "
                         f"(camera-beat.md: every loop divides the master)")
        css, frag = emit([parse_row(r, master, beat) for r in read_table(args.table)])
        if args.acts_table:
            # Imported HERE, not at module scope: emit_act_delta reuses this module's
            # own `parse_table`, so a top-level import would be a cycle.
            import emit_act_delta
            frag.update(emit_act_delta.fragment(args.acts_table))
    except Refuse as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    blob = json.dumps(frag, indent=2, ensure_ascii=False)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(css)
    if args.manifest:
        open(args.manifest, "w", encoding="utf-8").write(blob + "\n")
    if args.format in ("css", "both") and not args.out:
        print(css, end="")
    if args.format in ("json", "both") and not args.manifest:
        print(blob)
    return 0


if __name__ == "__main__":
    sys.exit(main())
