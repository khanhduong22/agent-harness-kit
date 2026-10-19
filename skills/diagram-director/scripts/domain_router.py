#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Domain auto-routing: which of the eight datasets does a bare query mean?

Split out of core.py (2026-08-26, G11) together with the behavior change that
motivated it. The router used to return ONE domain, always, breaking ties with
a fixed priority list and defaulting to "types" when nothing matched. Measured
against the 48 positive rows of tests/smoke-queries.tsv -- whose correct domain
is recorded per row -- that silent tie-break disagreed with the recorded domain
31 times. A caller had no way to tell a confident route from a coin flip.

So routing now returns RANKED CANDIDATES with scores, and commits to the top one
only when it leads the runner-up by DOMAIN_ROUTE_MARGIN. Otherwise it abstains
and names the candidates, and the caller (or the LLM reading the output) passes
--domain explicitly. Abstaining is the honest answer to an ambiguous query;
picking one silently is not.
"""

import re

from bm25_engine import normalize
from search_tuning import DOMAIN_KEYWORDS, DOMAIN_ROUTE_MARGIN, DOMAIN_TIEBREAK_ORDER

_TIEBREAK_RANK = {domain: rank for rank, domain in enumerate(DOMAIN_TIEBREAK_ORDER)}


def _contains_phrase(text, phrase):
    if re.search(r"\w", phrase):
        return bool(re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text))
    return phrase in text


def route_candidates(query, limit=3):
    """Return [(domain, score), ...] best first, scores > 0 only.

    Longer keyword phrases weigh more: a two-word routing phrase is far more
    specific intent than one generic noun. Ordering among equal scores is fixed
    by DOMAIN_TIEBREAK_ORDER so the candidate LIST is deterministic -- that list
    is now advisory, not a decision.
    """
    query_lower = normalize(query.lower())
    scored = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        total = sum(2.0 * max(1, len(kw.split()))
                    for kw in keywords if _contains_phrase(query_lower, kw))
        if total > 0:
            scored.append((domain, total))
    scored.sort(key=lambda item: (-item[1], _TIEBREAK_RANK.get(item[0], 999)))
    return scored[:limit]


def route(query, limit=3):
    """Return (domain_or_None, candidates).

    domain is None -- ABSTAIN -- when nothing matched at all, or when the top
    candidate's lead over the runner-up is below DOMAIN_ROUTE_MARGIN.
    """
    candidates = route_candidates(query, limit=limit)
    if not candidates:
        return None, []
    # A LONE candidate is measured against zero, not waved through. One generic
    # single-word keyword scores 2.0, and "dark glowing conference slide diagram"
    # hitting nothing but the word "diagram" is not evidence that the user wants
    # the diagram-types table -- they wanted a style. Requiring the lead over
    # "nothing at all" to clear the same margin is what turned those into
    # abstains instead of confident wrong answers.
    runner_up = candidates[1][1] if len(candidates) > 1 else 0.0
    if candidates[0][1] - runner_up >= DOMAIN_ROUTE_MARGIN:
        return candidates[0][0], candidates
    return None, candidates


def detect_domain(query):
    """Backwards-compatible single-domain answer, used where a caller has no
    way to act on an abstain. Returns "types" when routing abstains -- the same
    default as before -- but every NEW caller should use route() and surface
    the candidates instead.
    """
    domain, _ = route(query)
    return domain or "types"
