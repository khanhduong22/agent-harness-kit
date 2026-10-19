#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagram Director search CLI.

Run from the skill root; every documented invocation is the relative path
`diagram-director/scripts/search.py`, so the skill works wherever it is checked out.

Usage:
  python3 diagram-director/scripts/search.py "<query>" --domain styles|types|motion|components|states|payloads|colors|layouts
                                       [-n 1-20] [--genre system-design|process] [--json] [--full]

`--domain` is the contract. Omitting it does not pick one for you: the router
returns ranked candidates and searches NOTHING when no domain leads clearly.
`-n` defaults to 1 because a targeted lookup has one right answer; `-n>1` is the
opt-in for alternatives, every one of which must clear the domain floor on its
own, with raw scores printed.
  python3 diagram-director/scripts/search.py "<scenario>" --blueprint [--type <type-id>] [--style <style-id>]
                                       [--target artifact|local] [--genre system-design|process]
                                       [-f markdown|ascii] [--json]

`--genre` picks WHICH CORPUS the question is asked of (what the cast is:
deployed software components vs participants + work items + actions). It
partitions before ranking, so it is not a filter on the answer. Default
system-design.
"""

import argparse
import io
import json
import sys

from blueprint_composer import compose
from blueprint_render import render_ascii, render_markdown
from core import search
from csv_config import CSV_CONFIG, EXPLORATION_RESULTS, TARGETED_RESULTS, UNTRUNCATED_COLS
from genre_registry import DEFAULT_GENRE, GENRES

# Force UTF-8 stdout/stderr so box-drawing/ascii output survives Windows' cp1252 default.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

TRUNCATE_AT = 300


def format_output(result, full=False):
    """Render a core.search() result dict as Claude-consumable markdown text."""
    if "error" in result:
        return f"Error: {result['error']}"

    # GENRE-NEUTRAL banner. This engine serves the `system-design` and `process`
    # genres from the same eight datasets (and whatever genre ships next), so the
    # heading names the tool, not one genre. The `--domain` line below already says
    # what was searched.
    lines = ["## Search Results"]

    if result.get("route_abstained"):
        return "\n".join(_format_route_abstain(result))

    domain_note = result["domain"] + (" (auto-detected)" if result.get("auto_detected") else "")
    lines.append(f"**Domain:** {domain_note} | **Query:** {result['query']}")
    lines.append(f"**Source:** {result['file']} | **Found:** {result['count']} results")
    if result.get("auto_detected") and result.get("route_candidates"):
        shown = ", ".join(f"{name} ({score:g})" for name, score in result["route_candidates"])
        lines.append(f"**Route candidates:** {shown} -- pass `--domain` to be sure.")
    if result.get("lookup") == "palette":
        lines.append(f"**Palette:** {result['style_id']} / {result['palette']} "
                     f"(one logical palette, every role)")
    for warning in result.get("warnings") or []:
        lines.append(f"**Warning:** {warning}")
    lines.append("")

    if result["count"] == 0:
        if result.get("cross_genre"):
            # The database HAS this row -- it lives in another genre. Falling
            # through to "No matches" would send the caller inventing a default
            # for something one flag away.
            lines.append(result["cross_genre"]["message"])
            return "\n".join(lines)
        if result.get("excluded_by_target"):
            # NOT a database miss. Saying "no matches" here would send the caller
            # off inventing a fallback while the answer sits one flag away.
            lines.append(
                f"Every hit that cleared the floor was withheld by "
                f"`--target {result.get('target')}` -- "
                f"{', '.join(result['excluded_by_target'])} needs a JS runtime or a CDN "
                f"asset and cannot ship inside a CSP-sandboxed artifact. The database "
                f"DOES have an answer -- re-run with `--target local` to see it, or "
                f"search for a css-only alternative. Record the constraint in the sheet."
            )
            return "\n".join(lines)
        floor = (result.get("accept") or {}).get("floor")
        top = (result.get("accept") or {}).get("top_score")
        lines.append(
            "No matches. This is not a match with an empty value -- the query did not "
            "hit the database. Retry with broader/different keywords (exploration mode: "
            f"`-n {EXPLORATION_RESULTS}`) before falling back to general defaults, and say "
            "explicitly that no database match was found if you do fall back. Record this "
            "0-result in the solution sheet."
        )
        if floor is not None:
            lines.append(f"**Best score:** {top} (domain floor {floor})")
        suggestions = result.get("suggestions") or []
        if suggestions:
            lines.append(f"**Closest known terms:** {', '.join(suggestions)}")
        return "\n".join(lines)

    scores = result.get("scores") or []
    for i, row in enumerate(result["results"], 1):
        score_note = f" (score {scores[i - 1]})" if i <= len(scores) else ""
        lines.append(f"### Result {i}{score_note}")
        for key, value in row.items():
            value_str = str(value)
            if not full and key not in UNTRUNCATED_COLS and len(value_str) > TRUNCATE_AT:
                value_str = value_str[:TRUNCATE_AT] + "..."
            lines.append(f"- **{key}:** {value_str}")
        lines.append("")
    return "\n".join(lines)


def _format_route_abstain(result):
    """Auto-routing found no clear winner. Name the candidates, pick nothing.

    The old behavior picked the top candidate silently and, measured against the
    smoke file's recorded domains, was wrong 31 times out of 48. Naming the
    candidates costs the caller one flag and never invents an answer.
    """
    lines = ["## Search Results",
             f"**Domain:** not routed | **Query:** {result['query']}", ""]
    candidates = result.get("route_candidates") or []
    if candidates:
        shown = ", ".join(f"`--domain {name}` ({score:g})" for name, score in candidates)
        lines.append(f"Auto-routing did not find a clear domain. Ranked candidates: {shown}")
    else:
        lines.append("Auto-routing matched no domain vocabulary at all.")
    lines.append(
        "Nothing was searched. Re-run with an explicit `--domain` -- that is the "
        "contract anyway; auto mode is only a helper that names candidates."
    )
    return lines


def build_parser():
    parser = argparse.ArgumentParser(description="Diagram Director search")
    parser.add_argument("query", help="Search query or scenario description")
    parser.add_argument("--domain", "-d", choices=list(CSV_CONFIG.keys()),
                         help="Restrict search to one domain (auto-detected if omitted)")
    parser.add_argument("-n", "--max-results", type=int, choices=range(1, 21),
                         default=TARGETED_RESULTS, metavar="1-20", dest="max_results",
                         help=(f"Max results (default: {TARGETED_RESULTS} -- a targeted lookup has one "
                               f"right answer). -n>1 is the opt-in for alternatives: every result "
                               f"still has to clear the domain floor on its own and raw scores are "
                               f"printed. Retry a 0-result with -n {EXPLORATION_RESULTS}."))
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--full", action="store_true",
                         help="Do not truncate long field values in text output")
    parser.add_argument("--blueprint", action="store_true",
                         help="Compose a diagram-type + style + layout + motion + component blueprint")
    parser.add_argument("--style", type=str, default=None, help="Force a specific Style ID")
    parser.add_argument("--type", type=str, default=None, dest="type_id",
                         help="Force a specific Type ID (use this when --blueprint abstains)")
    # Default is `artifact` to agree with SKILL.md STEP 1 ("if unable to ask, default
    # to artifact"): artifact output renders everywhere, local does not degrade
    # gracefully inside a CSP sandbox, so the safe default is the constrained one.
    # Applies to `--domain` searches too, not just `--blueprint`: a domain that
    # carries a Runtime column (styles, motion) drops its needs-js / CDN rows and
    # NAMES them in the output. Domains without one are unaffected.
    parser.add_argument("--target", choices=["artifact", "local"], default="artifact",
                         help="artifact (default) restricts to css-only techniques with no CDN dependency")
    # The genre is WHAT THE CAST IS: system-design draws deployed software
    # components, process draws participants + work items + actions. It partitions
    # the corpus before ranking, so a genre is not a filter on the answer -- it is
    # which database the question is asked of. Default system-design keeps every
    # existing invocation byte-identical.
    parser.add_argument("--genre", choices=list(GENRES), default=DEFAULT_GENRE,
                         help=f"Which corpus to search (default: {DEFAULT_GENRE})")
    parser.add_argument("-f", "--format", choices=["markdown", "ascii"], default="markdown",
                         help="Blueprint output format (ignored with --json)")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.blueprint:
        spec = compose(args.query, style_id=args.style, target=args.target,
                       type_id=args.type_id, genre=args.genre)
        if args.json:
            print(json.dumps(spec, indent=2, ensure_ascii=False))
        elif args.format == "ascii":
            print(render_ascii(spec))
        else:
            print(render_markdown(spec))
        return

    result = search(args.query, domain=args.domain, max_results=args.max_results,
                    target=args.target, genre=args.genre)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_output(result, full=args.full))


if __name__ == "__main__":
    main()
