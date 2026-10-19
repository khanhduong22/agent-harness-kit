#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The accept predicate and its recovery path, in ONE place.

accept() is the single definition of "does this result stand" -- score floor,
query coverage, and the strong-evidence bypass that forgives sparse coverage
when one rare term carries the query. Nothing may reimplement it:
tools/calibrate_floors.py replays the probe sets through core.search(), which
calls this, and a second copy of these rules would let a floor pass a test the
shipping search does not.

suggest_terms() is what turns a 0-result into a next action instead of a dead
end, so it lives beside the predicate that produced the 0.

Split out of core.py 2026-08-26 (G8) to keep that module at orchestration size.
core re-exports both names, so callers keep importing them from core.
"""

import difflib

from search_tuning import STRONG_EVIDENCE_FACTOR, thresholds


def _query_coverage(index, query):
    tokens = set(index.tokenize_query(query))
    if not tokens:
        return 0.0
    vocabulary = set(index.vocabulary())
    return sum(token in vocabulary for token in tokens) / len(tokens)


def accept(domain, top_score, coverage, genre=None):
    """The accept predicate, in one place. Returns (accepted, detail).

    `genre` selects the floor: a genre is a separate CORPUS (core.search
    partitions before the BM25 fit), and BM25's score scale moves with corpus
    size, so a floor calibrated on one partition can be unreachable on another.
    search_tuning.thresholds() is the one resolver; None means the domain
    default.

    Coverage guards against a single common word carrying a whole query, but it
    punishes natural phrasing: "nginx sitting in front of my app servers"
    matches one token out of five and would abstain even though "nginx" is a
    rare, highly discriminative term. So sparse coverage is forgiven when the
    evidence is strong on its own. Queries with no matching token at all score
    zero and still abstain, which is what keeps off-topic questions unanswered.
    """
    threshold = thresholds(domain, genre)
    floor = threshold["min_score"]
    strong_evidence = top_score >= floor * STRONG_EVIDENCE_FACTOR
    thin = coverage < threshold["min_coverage"] and not strong_evidence
    accepted = top_score > floor and not thin
    return accepted, {
        "floor": floor,
        "min_coverage": threshold["min_coverage"],
        "top_score": round(top_score, 4),
        "coverage": round(coverage, 4),
        "strong_evidence": strong_evidence,
        "below_floor": top_score <= floor,
        "thin_coverage": thin,
    }


def suggest_terms(index, query, threshold=None, limit=6):
    """Nearest known vocabulary terms for a query that returned 0 hits, so a
    retry can happen instead of the caller reporting nothing. A candidate
    term must itself pass the same score threshold to be actionable.
    """
    if index is None:
        return []
    query_tokens = set(index.tokenize_query(query))
    if not query_tokens:
        return []

    candidates = []
    for term in index.vocabulary():
        if term in query_tokens:
            continue
        similarity = max(difflib.SequenceMatcher(None, token, term).ratio() for token in query_tokens)
        if similarity < 0.72:
            continue
        if threshold is not None:
            ranked = index.score(term)
            top = ranked[0][1] if ranked else 0.0
            if top <= threshold["min_score"]:
                continue
        candidates.append((-similarity, -index.doc_freqs.get(term, 0), term))
    return [term for _, _, term in sorted(candidates)[:limit]]
