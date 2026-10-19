#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Search orchestration: genre partition, exact-ID short-circuit, composite
palette lookup, the accept predicate (score floor + query coverage +
strong-evidence bypass), per-result floors, did-you-mean on zero results.

CSV loading and BM25 index caching live in csv_cache.py; domain auto-routing in
domain_router.py; palette resolution in palette_lookup.py; direct-ID resolution
(including the wrong-genre pointer) in id_lookup.py. load_rows(), get_row() and
detect_domain() are re-exported here unchanged so callers can keep importing
them from core (named export, per the module split in the plan).

The accept predicate itself (accept(), suggest_terms()) lives in
search_accept.py and is re-exported here -- it is the SINGLE definition of
"does this result stand", and tools/calibrate_floors.py replays probe sets
through this module so it can never test a second copy of those rules.
"""

from csv_cache import get_bm25, get_row, load_csv_snapshot, load_rows  # noqa: F401 (re-exported)
from csv_config import CSV_CONFIG, TARGETED_RESULTS, domain_path
from csv_schema import artifact_safe, domain_has_runtime
from domain_router import detect_domain, route  # noqa: F401 (detect_domain re-exported)
from genre_registry import DEFAULT_GENRE, row_in_genre
from id_lookup import cross_genre_pointer, exact_id_match
from palette_lookup import parse_palette_query, resolve_palette
from search_accept import _query_coverage, accept, suggest_terms  # noqa: F401 (re-exported)
from search_tuning import thresholds


def project_row(domain, row):
    """One row reduced to its ANSWER columns (csv_config.output_cols).

    Meta columns -- today just `Genres` -- are on disk for the engine and never
    travel into an answer. The blueprint composer calls this too, so its catalog
    and a `--domain` search can never disagree about an answer's shape.
    """
    return {col: row.get(col, "") for col in CSV_CONFIG[domain]["output_cols"] if col in row}


def _target_applies(domain, target):
    """True when `--target artifact` has anything to say about this domain.

    Only datasets carrying a `Runtime` column (styles, motion) can be judged
    artifact-safe; the rest are unaffected -- a layout has no runtime.
    """
    return target == "artifact" and domain_has_runtime(CSV_CONFIG[domain]["output_cols"])


def _palette_result(query, config, max_results):
    """Composite (style, palette[, role]) lookup, or None to fall through to BM25.

    max_results is deliberately IGNORED on this path: a palette is one logical
    object, and handing back 3 of its 7 role rows because the caller said -n 3
    would produce a diagram missing colour tokens. The role filter is the way to
    ask for less.
    """
    style_id, palette, role = parse_palette_query(query)
    if not style_id:
        return None
    rows, resolved, warning = resolve_palette(style_id, palette, role)
    if not rows:
        return None
    out = {
        "domain": "colors", "query": query, "file": config["file"],
        "lookup": "palette", "style_id": style_id, "palette": resolved,
        "count": len(rows),
        "results": [project_row("colors", row) for row in rows],
        "scores": [],
    }
    if role:
        out["role"] = role
    if warning:
        out["warnings"] = [warning]
    return out


def search(query, domain=None, max_results=TARGETED_RESULTS, target=None, genre=DEFAULT_GENRE):
    """Run a calibrated BM25 search against one domain's CSV.

    Returns a dict: domain, query, file, count, results, scores (aligned with
    results), accept detail, plus route_candidates/routed when domain was
    omitted and suggestions when nothing was accepted.

    Every returned row cleared the domain floor on its own -- results below it
    are DROPPED, not labelled. A labelled-but-present row gets pasted into a
    solution sheet anyway (this repo has already watched that happen with the
    blueprint's illustrative catalog), and dropping is what keeps `count == 0`
    meaning "the database has no answer" rather than "scroll past the junk".
    Raw scores travel alongside so the caller can still see 6.07 vs 1.64.

    `target="artifact"` enforces the delivery constraint SKILL.md STEP 1 already
    promised: rows needing a JS runtime or a CDN asset are withheld. That filter
    used to live only inside `--blueprint`, so `--domain motion --target artifact`
    handed the needs-js recipe back unchanged. Withheld rows are NEVER silent --
    they come back in `excluded_by_target` with a warning, because a row that
    vanishes without a word is indistinguishable from one the database lacks.
    `target=None` (the default) keeps the unfiltered behaviour.

    `genre` partitions the corpus BEFORE the BM25 fit: rows outside the active
    genre never reach active_rows, so they never enter the index, never enter
    the IDF table and cannot move the score of a row that DID survive. Filtering
    after scoring was the rejected alternative -- it leaves the other genre in
    the statistics and can empty an `-n 1` result while reporting a healthy top
    score. Datasets with no `Genres` column are shared and pass through.
    """
    if not isinstance(max_results, int) or isinstance(max_results, bool) or not 1 <= max_results <= 20:
        return {"error": "max_results must be an integer from 1 to 20", "domain": domain}

    auto_detected = domain is None
    candidates = []
    if domain is None:
        domain, candidates = route(query)
        if domain is None:
            return {
                "domain": None, "query": query, "count": 0, "results": [], "scores": [],
                "auto_detected": True, "routed": False, "route_candidates": candidates,
                "route_abstained": True,
            }
    if domain not in CSV_CONFIG:
        return {"error": f"Unknown domain: {domain}", "domain": domain}

    config = CSV_CONFIG[domain]
    filepath = domain_path(domain)
    if not filepath.exists():
        return {"error": f"File not found: {filepath}", "domain": domain}

    if domain == "colors":
        palette_out = _palette_result(query, config, max_results)
        if palette_out is not None:
            if auto_detected:
                palette_out["auto_detected"] = True
                palette_out["routed"] = True
                palette_out["route_candidates"] = candidates
            return palette_out

    try:
        rows, signature = load_csv_snapshot(filepath)
    except (OSError, UnicodeDecodeError) as exc:
        return {"error": f"Unable to read search data: {filepath.name} ({exc})", "domain": domain}

    # THE PARTITION. Everything below this line only ever sees in_genre.
    in_genre = [row for row in rows if row_in_genre(row, genre)]

    id_field = config["id_field"]
    exact = exact_id_match(in_genre, id_field, query) if id_field else None
    cross_genre = (cross_genre_pointer(rows, id_field, query, genre)
                   if exact is None and id_field else None)
    active_rows = [row for row in in_genre if row.get("Status", "active") == "active"] or in_genre

    detail = None
    picked = []      # (row, score-or-None) that cleared the floor, pre --target filter
    if exact is not None:
        picked = [(exact, None)]
        bm25 = None
    elif cross_genre is not None:
        bm25 = None   # named row, wrong genre -- see id_lookup.cross_genre_pointer
    else:
        bm25 = get_bm25(filepath, config["search_cols"], active_rows, signature, partition=genre)
        ranked = bm25.score(query)
        top_score = ranked[0][1] if ranked else 0.0
        accepted, detail = accept(domain, top_score, _query_coverage(bm25, query), genre)
        if accepted:
            for idx, score in ranked[:max_results]:
                # Per-result floor: the accept predicate vouched for the TOP hit,
                # not for whatever trailed it. `show messages piling up in the mq`
                # returns queue-fill at 8.09 and then two recipes near 2.5 that
                # have nothing to do with queues.
                if score <= detail["floor"]:
                    continue
                picked.append((active_rows[idx], round(score, 4)))

    excluded = []
    if _target_applies(domain, target):
        excluded = [row for row, _ in picked if not artifact_safe(row)]
        picked = [pair for pair in picked if artifact_safe(pair[0])]

    results = [project_row(domain, row) for row, _ in picked]
    scores = [score for _, score in picked if score is not None]

    out = {
        "domain": domain,
        "query": query,
        "file": config["file"],
        "count": len(results),
        "results": results,
        "scores": scores,
    }
    if detail is not None:
        out["accept"] = detail
    if exact is not None:
        out["lookup"] = "exact-id"
    if cross_genre is not None:
        out["lookup"] = "cross-genre-id"
        out["cross_genre"] = cross_genre
    if target:
        out["target"] = target
    if excluded:
        ids = [row.get(id_field, "?") if id_field else "?" for row in excluded]
        out["excluded_by_target"] = ids
        out.setdefault("warnings", []).append(
            f"{len(ids)} result(s) excluded by --target {target} "
            f"(a JS runtime or a CDN asset): {', '.join(ids)}. "
            f"Re-run with `--target local` to see them."
        )
    if auto_detected:
        out["auto_detected"] = True
        out["routed"] = True
        out["route_candidates"] = candidates
    # Did-you-mean only makes sense for a genuine ranking miss: when the target
    # filter emptied the list the database DID answer, and other spellings of the
    # query would send the caller hunting for a row they have already been handed.
    if not results and not excluded and bm25 is not None:
        out["suggestions"] = suggest_terms(bm25, query, threshold=thresholds(domain, genre))
    return out
