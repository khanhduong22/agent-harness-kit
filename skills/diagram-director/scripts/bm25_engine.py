#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BM25 ranking over small in-memory document lists. Pure and data-agnostic:
this module knows nothing about CSVs, domains, or scoring floors -- it only
tokenizes text and ranks documents against a query.
"""

import re
from collections import defaultdict
from math import log

from search_tuning import QUERY_EXPANSION_WEIGHT, STOPWORDS, SYNONYMS

# Compiled longest-first so multi-word synonyms (e.g. "api gateway") are
# matched before any of their component single words.
_SYNONYM_PATTERNS = [
    (re.compile(r"(?<!\w)" + re.escape(variant) + r"(?!\w)", re.IGNORECASE), canonical)
    for variant, canonical in sorted(SYNONYMS.items(), key=lambda item: len(item[0]), reverse=True)
]


def normalize(text):
    """Append each matched abbreviation's canonical expansion (see
    search_tuning.SYNONYMS docstring for why this appends rather than replaces).

    QUERY SIDE ONLY. Applied by tokenize_query() and by core's domain router --
    never by fit(). Expanding the corpus destroys row identity: `redis -> cache`
    used to stamp "cache" onto every row mentioning redis and "content delivery
    network" onto the cdn row, so the query `redis` ranked cache, kv-cache, then
    *cdn* -- a tail matching the injected canonical term rather than redis.
    Injection also inflates the canonical term's document frequency, depressing
    its IDF and making the genuinely canonical row harder to find.
    """
    normalized = str(text)
    for pattern, canonical in _SYNONYM_PATTERNS:
        normalized = pattern.sub(lambda m: f"{m.group(0)} {canonical}", normalized)
    return normalized


class BM25:
    """BM25 ranking (k1=0.3, b=0.75) over a fitted document list.

    k1 is deliberately far below the textbook 1.2-2.0. That range assumes prose,
    where a term repeating genuinely signals aboutness. These documents are
    keyword lists a few dozen tokens long, and a repeat is almost always an
    artifact of the same word appearing in the ID, the Name and the Keywords cell
    of one row -- "mobile-app" carries the token "app" three times without being
    any more about proxies than a row that says "nginx" once. Left at 1.5, that
    inflation let filler words outweigh the one rare term that actually mattered:
    "nginx sitting in front of my app servers" ranked mobile-app over
    reverse-proxy. Lowering k1 flattens the term-frequency curve so ranking is
    driven by IDF -- which term is rare -- which is what keyword lookup wants.
    Measured on a held-out probe set of natural rephrasings (2026-08-25):
    top-1 accuracy 12/14 at k1=1.5 versus 13/14 at k1=0.3, with off-topic queries
    scoring lower at the same time. Floors in csv_config were recalibrated for
    this scale; changing k1 invalidates them.
    """

    def __init__(self, k1=0.3, b=0.75):
        self.k1 = k1
        self.b = b
        self.corpus = []
        self.doc_lengths = []
        self.avgdl = 0.0
        self.idf = {}
        self.doc_freqs = defaultdict(int)
        self.N = 0
        self._term_freqs = []  # per-doc term frequency counters

    def tokenize(self, text):
        """Corpus tokenizer: lowercase, punctuation stripped, stopwords removed,
        minimum length 2 (keeps short domain tokens like db, mq, k8s, lb, ci).

        VERBATIM -- no synonym expansion. What an author wrote in a Keywords
        cell is what is searchable; see normalize()'s docstring for why.
        """
        text = re.sub(r"[^\w\s]", " ", str(text).lower())
        return [w for w in text.split() if len(w) >= 2 and w not in STOPWORDS]

    def tokenize_query(self, text):
        """Query tokenizer: corpus tokenization PLUS synonym expansion, with
        the original terms kept and the expansions appended deduped.

        Dedup matters: `mq` expands to `queue`, and a query that already says
        "queue" would otherwise carry that token twice and score a row higher
        for a word the user typed once.
        """
        seen = set()
        ordered = []
        for token in self.tokenize(normalize(str(text).lower())):
            if token in seen:
                continue
            seen.add(token)
            ordered.append(token)
        return ordered

    def query_weights(self, text):
        """{token: weight} for scoring -- terms the user actually typed weigh
        1.0, terms that only arrived via SYNONYMS weigh QUERY_EXPANSION_WEIGHT.
        See that constant's rationale in search_tuning.py.
        """
        literal = set(self.tokenize(text))
        return {token: (1.0 if token in literal else QUERY_EXPANSION_WEIGHT)
                for token in self.tokenize_query(text)}

    def fit(self, documents):
        """Build the index (term frequencies, document frequencies, idf)."""
        self.corpus = [self.tokenize(doc) for doc in documents]
        self.N = len(self.corpus)
        if self.N == 0:
            return
        self.doc_lengths = [len(doc) for doc in self.corpus]
        self.avgdl = (sum(self.doc_lengths) / self.N) or 1.0

        self._term_freqs = []
        for doc in self.corpus:
            tf = defaultdict(int)
            for word in doc:
                tf[word] += 1
            self._term_freqs.append(tf)
            for word in tf:
                self.doc_freqs[word] += 1

        for word, freq in self.doc_freqs.items():
            self.idf[word] = log((self.N - freq + 0.5) / (freq + 0.5) + 1)

    def score(self, query):
        """Return [(doc_index, score), ...] sorted by score descending."""
        query_tokens = self.query_weights(query)
        scores = []
        for idx in range(self.N):
            total = 0.0
            doc_len = self.doc_lengths[idx]
            term_freqs = self._term_freqs[idx]
            for token, weight in query_tokens.items():
                if token not in self.idf:
                    continue
                tf = term_freqs.get(token, 0)
                idf = self.idf[token]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
                total += weight * idf * numerator / denominator
            scores.append((idx, total))
        return sorted(scores, key=lambda item: item[1], reverse=True)

    def vocabulary(self):
        """All indexed terms, for typo-recovery suggestions."""
        return list(self.idf.keys())
