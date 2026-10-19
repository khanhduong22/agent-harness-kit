#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Probe file parsing and single-probe replay.

Deliberately separate from calibrate_floors.py, which owns the REPORTING (floor
windows, the router-margin sweep, the CLI). This module owns only "run one probe
row and say whether it held", and it does that by calling core.search() -- the
real path a user gets. There is no second implementation of the accept
predicate here; see core / search_accept.

Probe file format: tests/probes/README.md.
"""

import csv

import core
from csv_config import CSV_CONFIG
from domain_router import route, route_candidates
from genre_registry import DEFAULT_GENRE, GENRES
from search_tuning import thresholds

PROBE_RESULTS = 5          # deep enough for `forbid` to catch tail junk
ACCEPT_VALUES = {"yes", "no", "abstain-ok"}
TARGET_VALUES = {"artifact", "local"}


def read_probes(path):
    """Parse one probe TSV into dicts. Blank lines and #-comments are skipped."""
    rows = []
    with path.open(encoding="utf-8", newline="") as handle:
        for lineno, raw in enumerate(csv.reader(handle, delimiter="\t"), 1):
            if not raw or not raw[0].strip() or raw[0].lstrip().startswith("#"):
                continue
            cells = [cell.strip() for cell in raw] + ["", "", "", "", "", ""]
            query, expect_top1, expect_accept = cells[0], cells[1], cells[2].lower()
            if expect_accept not in ACCEPT_VALUES:
                raise ValueError(f"{path.name}:{lineno}: expect_accept must be one of "
                                 f"{sorted(ACCEPT_VALUES)}, got {cells[2]!r}")
            target = cells[5].lower()
            if target and target not in TARGET_VALUES:
                raise ValueError(f"{path.name}:{lineno}: target must be one of "
                                 f"{sorted(TARGET_VALUES)} or empty, got {cells[5]!r}")
            # Column 7. Empty means the DEFAULT genre, so every pre-genre probe row
            # keeps asserting exactly what it always asserted.
            genre = cells[6] or DEFAULT_GENRE
            if genre not in GENRES:
                raise ValueError(f"{path.name}:{lineno}: genre must be one of "
                                 f"{list(GENRES)} or empty, got {cells[6]!r}")
            rows.append({
                "line": lineno, "query": query, "expect_top1": expect_top1,
                "expect_accept": expect_accept,
                "forbid": [f.strip() for f in cells[3].split(";") if f.strip()],
                "note": cells[4], "target": target or None, "genre": genre,
            })
    return rows


def _row_id(domain, row):
    field = CSV_CONFIG[domain]["id_field"] or "Style ID"
    return row.get(field, "?")


def check_search_probe(domain, probe):
    """Run one catalog probe. Returns (ok, message, top_score, accepted)."""
    result = core.search(probe["query"], domain=domain, max_results=PROBE_RESULTS,
                         target=probe["target"], genre=probe["genre"])
    if "error" in result:
        return False, f"search error: {result['error']}", None, False

    accepted = result["count"] > 0
    # None, not 0.0, when the answer came from a non-scored path (composite
    # palette lookup, exact-ID short-circuit). Those rows say nothing about
    # where a floor belongs and must not drag a window down to zero.
    top_score = (result.get("accept") or {}).get("top_score")
    ids = [_row_id(domain, row) for row in result["results"]]
    got = ids[0] if ids else "NONE"

    if probe["expect_accept"] == "no":
        if accepted:
            return False, f"expected abstain, got {got} (score {top_score})", top_score, accepted
    elif not accepted:
        return False, (f"expected {probe['expect_top1']}, abstained "
                       f"(top_score {top_score} vs floor "
                       f"{thresholds(domain, probe['genre'])['min_score']})"), \
               top_score, accepted
    elif probe["expect_top1"] not in ("", "*") and got != probe["expect_top1"]:
        return False, f"expected top-1 {probe['expect_top1']}, got {got} (score {top_score})", \
               top_score, accepted

    leaked = [bad for bad in probe["forbid"] if bad in ids]
    if leaked:
        pairs = ", ".join(f"{i}={s}" for i, s in zip(ids, result.get("scores") or []) if i in leaked)
        return False, f"forbidden row(s) accepted alongside: {pairs}", top_score, accepted

    # A --target probe asserts two things, and the second is the one the bug was
    # about: the row must be gone AND the caller must be told it was withheld. A
    # silent drop reads exactly like "the database has nothing", which is a lie.
    if probe["target"] and probe["forbid"]:
        withheld = result.get("excluded_by_target") or []
        missing = [bad for bad in probe["forbid"] if bad not in withheld]
        if missing:
            return False, (f"--target {probe['target']} dropped {missing} without reporting it "
                           f"(excluded_by_target={withheld or 'none'})"), top_score, accepted
    return True, "", top_score, accepted


def check_router_probe(probe, margin=None):
    """Run one router-intent probe. expect_top1 holds the expected DOMAIN."""
    if margin is None:
        picked, candidates = route(probe["query"])
    else:
        # Mirrors domain_router.route() exactly, including measuring a LONE
        # candidate against zero rather than waving it through.
        candidates = route_candidates(probe["query"])
        picked = None
        if candidates:
            runner_up = candidates[1][1] if len(candidates) > 1 else 0.0
            if candidates[0][1] - runner_up >= margin:
                picked = candidates[0][0]
    names = [name for name, _ in candidates]
    shown = ", ".join(f"{n}:{s:g}" for n, s in candidates) or "(none)"

    if probe["expect_accept"] == "no":
        ok = picked is None
        return ok, ("" if ok else f"expected abstain, routed to {picked} [{shown}]"), picked
    if probe["expect_accept"] == "abstain-ok":
        # The guarantee G11 exists to give is "never confidently WRONG". An
        # abstain is always a pass here: it costs the caller one explicit
        # --domain, which is the documented contract anyway. Whether the true
        # domain even appears among the candidates is a keyword-coverage
        # question, reported as a diagnostic below rather than asserted -- it
        # would encode routing-vocabulary debt as a red suite.
        if picked is None or picked == probe["expect_top1"]:
            return True, "", picked
        return False, f"routed to {picked}, expected {probe['expect_top1']} [{shown}]", picked
    ok = picked == probe["expect_top1"]
    return ok, ("" if ok else f"routed to {picked or 'ABSTAIN'}, expected "
                              f"{probe['expect_top1']} [{shown}]"), picked
