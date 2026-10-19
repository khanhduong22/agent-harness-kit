#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Search tuning constants: tokenizer vocabulary, synonym expansion, domain
routing keywords, score floors and the strong-evidence bypass.

Split out of csv_config.py (2026-08-26) because these are *calibrated* values --
they change whenever the probe suite in tests/probes/ says they must, on a
completely different cadence from the CSV schema declarations that stay in
csv_config.py. Keeping them together made one 300-line module where every
recalibration touched the same file as the column contracts.

Anything here that carries a number should be justified by a probe row in
tests/probes/<domain>.tsv and replayable through tools/calibrate_floors.py.
"""

# --- Tokenizer configuration -------------------------------------------------
# Deliberately short: domain-critical short tokens people actually type
# (db, mq, lb, k8s, api, ci, cd, css, js, svg) must stay searchable.
STOPWORDS = {
    "to", "in", "on", "at", "is", "of", "by", "or", "an", "if", "no", "so",
    "do", "be", "we", "it", "as", "the", "and", "for", "are", "was",
}

# Query/corpus normalization. Unlike a strict replace, each pattern APPENDS
# its canonical expansion after the matched abbreviation instead of deleting
# it (see bm25_engine._normalize). Rationale: several abbreviations here
# (db, async, auth, ws) are themselves literal corpus vocabulary -- Keywords
# and Semantic Role cells were authored with "the abbreviations people
# actually type" per docs/code-standards.md. A destructive replace would
# delete the very token that already matches the corpus. Appending the
# canonical term is strictly additive: it never removes a token that used to
# match, and it adds a second chance to match longer canonical phrasing.
SYNONYMS = {
    "db": "database", "dbs": "databases", "mq": "queue", "k8s": "kubernetes",
    "lb": "load balancer", "gw": "gateway", "svc": "service", "msg": "message",
    "pubsub": "publish subscribe", "ps": "publish subscribe", "fifo": "queue",
    "cdn": "content delivery network", "vpc": "network", "api gateway": "gateway",
    "micro-service": "microservice", "micro services": "microservices",
    "e-commerce": "ecommerce", "req": "request", "res": "response",
    "auth": "authentication", "authz": "authorization", "sso": "single sign on",
    "ha": "high availability", "dr": "disaster recovery", "rps": "throughput",
    "qps": "throughput", "p99": "latency", "oltp": "transactional database",
    "olap": "analytics warehouse", "s3": "object storage", "redis": "cache",
    "kafka": "event stream", "rabbitmq": "message queue", "sqs": "message queue",
    "grpc": "rpc", "ws": "websocket", "lambda": "serverless function",
    "faas": "serverless function", "a11y": "accessibility", "anim": "animation",
    "dashed": "dash", "marching ants": "dash flow", "async": "asynchronous",
    # --- Intent phrasing, added 2026-08-26 (G9) ------------------------------
    # These map a PHRASE to the vocabulary of the archetype it implies, the same
    # way "marching ants" -> "dash flow" already maps a phrase to a motion ID.
    # They live here rather than in the CSV Keywords cells because they are
    # facts about how users phrase a request, not about what the row IS: a
    # `comparison` row should not have to list every English way of saying
    # "two panes", and stuffing them in would distort that row's IDF for
    # everyone else. Both probes below were failing to a near-tie against
    # c4-container, whose Example Scenario happens to say "chat system ...
    # message queue" and so matched the surrounding nouns of both queries.
    #   `auction bidding system with and without a bid queue`
    #   `realtime chat message fanout to subscribers`
    "with and without": "comparison before after",
    "before and after": "comparison before after",
    "vs": "comparison versus", "versus": "comparison versus",
    "with vs without": "comparison before after",
    # Fan-out phrasing. "fanout" is already literal vocabulary on
    # event-driven-pubsub, but the surrounding nouns of a realtime-chat query
    # out-weighed it; expanding to the pattern's own vocabulary puts the
    # pattern back in front without touching any floor.
    "fanout": "fan-out publish subscribe topic",
    "fan out": "fan-out publish subscribe topic",
    "subscribers": "subscriber publish subscribe topic",
    "subscriber": "publish subscribe topic",
}

# Weight carried by a token the user did NOT type -- one that only entered the
# query through SYNONYMS. Originals score at 1.0.
#
# Why not 1.0: an expansion is a guess about intent, and treating it as though
# the user typed it lets one guess out-rank the literal term. The query `redis`
# expands to `cache`, and `cache` is genuine corpus vocabulary in rows that have
# nothing to do with redis -- cdn says "edge cache", kv-cache says "attention
# cache". At equal weight those rows ride the guess into the results and the
# tail reads as "three components match redis" when one does. At 0.5 the literal
# hit still decides the ranking and the expansion only breaks ties / rescues a
# query whose literal terms miss the corpus entirely.
#
# SWEPT 2026-08-26 (deferred from phase-04, where 0.5 was asserted from the
# argument above but never measured). `python3 tools/calibrate_floors.py
# --sweep-expansion` replays every tests/probes/*.tsv suite at each weight:
#
#   weight  fails   headroom to the weakest positive, per domain
#                   components layouts motion payloads states styles types
#     0.3      0         1.54     1.46   0.66     1.27   0.59   2.17  1.33
#     0.4      0         1.54     1.46   0.66     1.27   0.59   2.17  1.33
#     0.5      0         1.54     1.46   0.66     1.27   0.59   2.17  1.33  <- shipped
#     0.6      1         (same)                                             kv-cache 2.31 > floor 2.00
#     0.7      1         (same)                                             kv-cache 2.69, cdn 2.29 > 2.00
#
# Two readings, and the flat columns are the interesting one. Headroom does not
# move AT ALL across the range: no weakest-positive in the suite is carried by a
# token the expander invented, so raising the weight cannot help a correct
# answer. It can only feed the junk tail -- and at 0.6 the `redis` probe's
# forbidden rows (kv-cache and cdn, which match nothing but the INJECTED word
# "cache") clear the components floor and the suite goes red. That is the exact
# failure the paragraph above predicted, now measured rather than argued.
#
# 0.5 is therefore kept: it is the largest weight that keeps the tail under the
# floor, and dropping to 0.3/0.4 would buy no measurable headroom while costing
# the expansion its documented job of rescuing a query whose literal terms miss
# the corpus. Re-run the sweep if k1, the floors, or SYNONYMS change -- all three
# move the tail.
QUERY_EXPANSION_WEIGHT = 0.5

# Routing words per domain for detect_domain(). Longer phrases score higher
# (see core._domain_score) so multi-word intent beats a single generic term.
#
# ENRICHMENT PASS 2026-08-26 (deferred from phase-04). The router.tsv diagnostic
# counted 25 of 38 abstains as BLIND: the true domain was not even among the
# candidates, so the caller was told "I don't know" without being told where to
# look. Every keyword added below is lifted from the Keywords cell of the row
# that query should reach -- routing vocabulary must be the CATALOG's vocabulary,
# not invented phrasing, or it drifts away from what the data can answer.
#
# Two rules learned the hard way and re-applied here:
#   * _contains_phrase is WORD-BOUNDED. "color" does not match "colors",
#     "swimlane" does not match "swimlanes", "flow" does not match "flows".
#     Plurals that queries actually use are listed explicitly.
#   * A keyword that a SYNONYM already injects is redundant: "kafka" expands to
#     "event stream" and "lb" to "load balancer", so only the canonical phrase is
#     listed. Listing both would double-score the same evidence.
# Collisions were checked query-by-query against the whole probe file; where two
# domains have an honest claim on a word the score TIES and the router abstains
# with both named, which is the correct answer to a genuinely ambiguous query.
DOMAIN_KEYWORDS = {
    # + whiteboard/excalidraw (hand-drawn-sketch), cyberpunk/glowing/dark
    # (neon-dark), clean (flat-minimal). "stripe" was deliberately NOT added for
    # `clean stripe docs style` even though flat-minimal lists "stripe-style":
    # stripe is also the payment-provider component, and a bare "stripe" query
    # means the component at least as often as the aesthetic. "clean" carries
    # that probe on its own without claiming a word another domain owns.
    "styles": ["style", "aesthetic", "look", "sketch", "hand-drawn", "neon", "blueprint",
               "flat", "isometric", "glassmorphic", "ascii", "pixel", "comic", "theme", "dark mode",
               "whiteboard", "excalidraw", "cyberpunk", "glowing", "dark", "clean"],
    # "comparison" (not "compare"): routing runs on the EXPANDED query, so the
    # SYNONYMS entries for "with and without"/"vs" put this token in front of the
    # router for free. Plain "compare" would have stolen the layouts query
    # "arrange the canvas as split compare panes", which is about panes.
    # + request-lifecycle vocabulary ("http request", "request path", "hop by
    # hop", "and back" -- the round-trip signature), deployment-topology
    # ("kubernetes", "pods"; k8s expands to kubernetes for free) and
    # scaling-story ("evolution", "concurrent users", "ccu"). "tiers" is
    # deliberately LAYOUTS-only: `arrange tiers from user to storage` wants the
    # layered arrangement and `... 500k concurrent users in tiers` wants the
    # scaling story, and giving types the word would only tie both into
    # abstains. The phrase "concurrent users" (4.0) carries the scaling query.
    "types": ["diagram", "architecture", "c4", "lifecycle", "pipeline", "topology",
              "sequence", "pubsub", "saga", "state machine", "auth flow", "comparison",
              "http request", "request path", "request lifecycle", "hop by hop", "and back",
              "kubernetes", "pods", "deployment topology", "evolution", "concurrent users",
              "ccu", "scaling story"],
    # + queue-fill ("piling up", "backlog"), fanout-broadcast ("fans out",
    # "consumer"/"consumers"), dash-flow ("traffic", "connector", "moving") and
    # the failure recipes ("dies", "cascade", "collapse"). NOT added:
    # "publish"/"topic"/"subscriber", which SYNONYMS already injects into any
    # query containing "pubsub" or "fanout" -- claiming them for motion would
    # have hijacked `compare chat fanout with and without pubsub side by side`,
    # a comparison DIAGRAM, on evidence the expander invented.
    "motion": ["animation", "animate", "motion", "flow", "pulse", "travel", "particle",
               "marching ants", "loop", "stagger", "glow", "fanout", "broadcast",
               "piling up", "backing up", "backlog", "fans out", "consumer", "consumers",
               "traffic", "connector", "moving", "dies", "cascade", "collapse"],
    # + the product nouns people actually type for a box on the canvas:
    # load-balancer ("load balancer"; "lb" expands to it), reverse-proxy
    # ("nginx", "reverse proxy"), microservice ("microservice(s)", "instance",
    # "running", "services", "app servers"), sql-database/read-replica
    # ("postgres", "replica", "read replica"), cache ("in-memory store"),
    # event-stream ("event stream"; "kafka" expands to it).
    # "app servers" rather than bare "servers": `messages flowing between chat
    # servers` is a PAYLOAD question, and the bare plural would have tied that
    # probe away from payloads for no gain.
    "components": ["component", "node", "icon", "service", "database", "queue", "cache",
                   "gateway", "cluster", "broker", "moe", "mixture of experts", "router",
                   "expert", "tokenizer", "kv cache", "inference",
                   "load balancer", "nginx", "reverse proxy", "app servers", "services",
                   "microservice", "microservices", "instance", "running",
                   "postgres", "replica", "read replica", "in-memory store", "event stream"],
    # "colors"/"palettes" plurals are listed explicitly: _contains_phrase is
    # word-bounded, so "color" does NOT match "hand-drawn-sketch colors" -- which
    # is how the single most obvious colors query scored zero on this domain and
    # routed to styles instead.
    "colors": ["color", "colors", "palette", "palettes", "hex", "token", "contrast",
               "role color", "dark variant"],
    # + layered-lr/tb ("left", "right", "left to right", "top to bottom",
    # "tiers"/"tiered", "arrange"), clustered-domains ("group", "grouping",
    # "grouped", "team", "per-team") and timeline-sequence ("over time" -- its
    # Keywords cell literally says "over-time"). "swimlanes" is listed next to
    # "swimlane" for the same word-boundary reason "colors" is listed next to
    # "color": `per-team grouping in swimlanes` scored zero on this domain.
    "layouts": ["layout", "arrangement", "direction", "swimlane", "swimlanes", "hub spoke",
                "tree", "ring", "grid", "spacing", "pane", "panes", "split", "side by side",
                "left", "right", "left to right", "top to bottom", "tiers", "tiered",
                "arrange", "group", "grouping", "grouped", "team", "per-team", "over time"],
    "states": ["state", "status", "degraded", "as degraded", "down", "unhealthy", "overloaded",
               "throttled", "failure mode", "circuit open", "cache hit", "cache miss", "leader",
               "follower", "cold start", "draining", "idle", "selected", "dim", "chip",
               "idle expert", "frozen weights", "backpressure edge"],
    # Cargo words, not transport words: "packet"/"travels" route here, but the
    # bare verbs "send"/"flow" deliberately do NOT -- they belong to motion and
    # would hijack every animation question. Phrases beat single words in
    # _domain_score, so "what travels" outranks a stray "file".
    # "messages" (plural) earns its place: _contains_phrase is word-bounded, so
    # the singular "chat message" does NOT match "messages flowing between chat
    # servers" -- which auto-routed to types (the no-match default) before this.
    # It does not steal motion/component queries: "show messages piling up in the
    # mq" ties with components at 2.0 and the tiebreak order keeps it there.
    # + binary-stream's own plural: its Keywords cell says "binary; bytes; byte
    # stream; raw stream", but only the singular-bearing phrases were listed, so
    # `raw bytes replicating to the follower` scored zero here and left states
    # (via "follower") as the sole candidate.
    "payloads": ["payload", "cargo", "packet type", "what travels", "carries",
                 "envelope packet", "binary stream", "byte stream", "file transfer",
                 "chat message", "messages", "event packet", "media stream", "token packet",
                 "bytes", "raw bytes"],
}

# --- HARD BAN: genre-straddling words may NEVER be routing vocabulary ---------
# `workflow`, `process` and `step by step` each read as BOTH genres at once:
# "workflow" is a system-design component (workflow-orchestrator), a Vietnamese
# user's word for "the diagram I want drawn", a k8s/CI noun, AND the plain-English
# name of the `process` genre. "process" is a Unix process and a business
# procedure. A router keyword makes one of those readings win silently, with no
# score to argue with and no abstain -- which is exactly the confidently-wrong
# answer G11 exists to prevent.
#
# The genre is chosen by the CALLER (`--genre`), never guessed from a word. This
# is a permanent ban, not a calibration: no probe row may ever be "fixed" by
# adding one of these. banned_router_terms() is called by calibrate_floors, so
# adding one fails the smoke gate rather than a review six weeks later.
GENRE_STRADDLE_BAN = ("workflow", "process", "step by step")


def banned_router_terms():
    """Violations of GENRE_STRADDLE_BAN in DOMAIN_KEYWORDS. Empty = clean."""
    return [f"DOMAIN_KEYWORDS[{domain!r}] contains banned genre-straddling term "
            f"{term!r} -- the genre is chosen by --genre, never by a keyword "
            f"(search_tuning.GENRE_STRADDLE_BAN)"
            for domain, terms in DOMAIN_KEYWORDS.items()
            for term in terms if term.strip().casefold() in GENRE_STRADDLE_BAN]
# Fixed tie-break order when routing scores are equal (highest priority first).
# Since 2026-08-26 (G11) this only makes the candidate LIST deterministic -- it
# no longer decides anything, because a near-tie now abstains.
DOMAIN_TIEBREAK_ORDER = ["types", "styles", "motion", "components", "states", "payloads",
                         "layouts", "colors"]

# Minimum lead the top routing candidate must hold over the runner-up before
# auto-routing commits to it; below this, search() returns ranked candidates and
# picks NOTHING. Routing scores are 2.0 per matched single-word keyword and
# 2.0*words for a phrase, so 2.0 means "one more keyword hit than the runner-up".
#
# Chosen by replaying tests/probes/router.tsv (the 48 positive smoke queries with
# their recorded domains) at every candidate margin and taking the largest one
# that keeps CONFIDENT-WRONG at zero -- see tools/calibrate_floors.py, which
# prints the whole sweep. Larger margins abstain more and so are strictly safer
# on wrongness; the tie-break at the top of the sweep is decided by how many
# queries still route confidently.
DOMAIN_ROUTE_MARGIN = 4.0

# --- Score floors ------------------------------------------------------------
# Calibrated 2026-08-25 against tests/smoke-queries.tsv PLUS a held-out probe set of
# natural rephrasings the smoke queries do not contain. Calibrating on the smoke set
# alone produced floors up to 3x too high (components sat at 9.0 while a correct
# top-1 for "in-memory store to avoid hitting postgres" scores 6.78), which made the
# engine abstain on ordinary questions. Each floor is the midpoint of the observed
# window, rounded down to the nearest 0.5:
#
# Re-measured 2026-08-25 after bm25_engine dropped k1 to 0.3 (see the rationale in
# that module). Lower k1 compresses the whole score scale, so the previous floors
# would have been silently too strict -- floors and k1 must be calibrated together.
#
#   domain      negative max   correct-top1 min   floor
#   styles             0.00               3.67     1.5
#   types              2.61               4.04     3.0   <- only domain with a nonzero
#   motion             0.00               4.13     2.0      negative ("write a python
#   components         0.00               3.19     1.5      decorator" grazes c4-component)
#   layouts            0.00               2.24     1.0
#   colors                -                  -     2.0   <- lookup domain, coverage gate off
#
# Off-topic queries match no token at all and score exactly zero, so the floors are
# not what rejects them; they guard against a single common word carrying a query.
DOMAIN_SCORE_FLOORS = {
    "styles": 1.5,
    "types": 3.0,
    # motion 2.0 -> 3.0 (2026-08-26, G8/G9). The floor vouched for the top hit
    # and nothing else, so `show messages piling up in the mq` returned
    # queue-fill at 8.09 and then dragged `backpressure` (2.59) and
    # `node-boot-sequence` (2.54) over the old 2.0 floor -- a tail that reads as
    # "three recipes match" when one does. Window from tests/probes/motion.tsv:
    # negatives max 0.00, weakest positive 4.12. Old window was the same shape;
    # 2.0 was simply lower than it needed to be. 3.0 is the midpoint of
    # [2.59 tail junk .. 4.12 weakest positive] rounded down to the nearest 0.5.
    "motion": 3.0,
    # components 1.5 -> 2.0 (2026-08-26, G8/G9). Same tail problem, from the
    # `redis` probe: the right answer `cache` scores 6.07, and `kv-cache` (1.92,
    # an ML decode cache) and `cdn` (1.64, whose Keywords say "edge cache") rode
    # the query-side expansion redis->cache over the old 1.5 floor. Window from
    # tests/probes/components.tsv: negatives max 0.00, weakest positive 3.54.
    # 2.0 clears both artifacts with 1.54 of headroom to the weakest positive.
    "components": 2.0,
    "colors": 2.0,
    "layouts": 1.0,
    # states: calibrated 2026-08-26 on an 8-positive / 4-negative probe set:
    #   negative max 3.21 ("my mood is down today" -- "down" IS corpus vocabulary;
    #   "the app state library for react" grazes is-healthy's "steady state" at 3.11)
    #   correct-top1 min 3.59 ("show a node as degraded")
    #   midpoint 3.40 -> floor 3.0. The floor matters doubly here: at the provisional
    #   1.5 the STRONG_EVIDENCE bar sat at 2.25 and "my mood is down today" (3.21,
    #   coverage 0.25) bypassed the coverage gate; at 3.0 the bar is 4.5 and that
    #   query abstains. States shares everyday words (down, state, leader) with
    #   ordinary prose, so its floor must clear them -- like types, not like colors.
    "states": 3.0,
    # payloads: calibrated 2026-08-26 on a 10-positive / 6-negative probe set of
    # natural phrasings absent from the smoke file:
    #   negative max      2.46 ("play some media" -- "media" and "play" are both
    #                     corpus vocabulary; "send me an email later" 2.45 and
    #                     "what file should i open" 2.42 sit just under it)
    #   correct-top1 min  4.26 ("the packet carries a jwt to the gateway")
    #   midpoint 3.36 -> floor 3.0
    # At 3.0 the STRONG_EVIDENCE bar is 4.50, comfortably above every negative,
    # so no common-word query can skip the coverage gate the way "my mood is down
    # today" did at the provisional states floor. Calibrating also moved the DATA:
    # transaction originally listed "transfer" and "money movement" as Keywords and
    # "how do i transfer money to my friend" scored 3.65 -- above two real positives.
    # Everyday money verbs were dropped from that row rather than papered over with
    # a higher floor, which would have cost the genuine payment queries.
    "payloads": 3.0,
}
SEARCH_THRESHOLDS = {
    domain: {"min_score": floor, "min_coverage": 0.0 if domain == "colors" else 0.34}
    for domain, floor in DOMAIN_SCORE_FLOORS.items()
}

# --- Per-(domain x genre) floor overrides ------------------------------------
# A floor is NOT a property of a domain alone. BM25's IDF term is
# log((N - df + 0.5)/(df + 0.5) + 1), so the whole score scale of a corpus moves
# with N -- and a genre IS a corpus (core.search partitions before the fit). The
# floors above were calibrated against the system-design partition and are the
# default for every genre; this table is the documented, probe-backed exception,
# exactly as the genre proposal predicted ("per-genre floors only when a window
# inverts", tests/probes/README.md).
#
#   ("types", "process") -> 0.45
#   The process partition of diagram-types.csv holds ONE row (process-loop), and
#   at N=1 every term in the corpus has the SAME idf, 0.2877. A query matching
#   eight of its tokens tops out at 2.43, so the shipped types floor of 3.0 is
#   not strict -- it is unreachable, and `--genre process --domain types` would
#   abstain on every query ever asked, including the ones the row exists to
#   answer. Window measured 2026-08-26 from tests/probes/types.tsv's process rows
#   (all natural phrasings, none of them written to fit a number):
#       negative max     0.33  ("how a http request flows through my api" --
#                        matches the single token `how`; the COVERAGE gate at
#                        0.14 rejects it as well, so this is belt and braces)
#       correct-top1 min 0.58  ("the handoff between a designer and a developer")
#       midpoint 0.45
#   Calibrating moved the DATA first, per the README's rule that an inverted
#   window is fixed in the data or the ranking and never by a nudged floor: the
#   row's Example Scenario and Edge Semantics cells (both searchable) originally
#   carried the generic tokens `what`, `with`, `through` and `from`, which let
#   "what is the capital of france" match at coverage 0.333 -- 0.007 under the
#   gate. Those cells were tightened and `support ticket journey` / `handoff
#   between roles` added as the honest keywords they were missing; the negatives
#   then fell to 0.00 on their own.
#   EXPECTED TO BE RETIRED, not grown: the second process type row lifts N to 2
#   and re-scales the partition. Re-run calibrate_floors.py when one lands.
#
# `components` needs no override: its process partition has 10 rows, negatives
# score 0.00 and the weakest positive 3.19, so the shipped 2.0 separates them
# with more headroom than it has under system-design.
GENRE_SCORE_FLOORS = {
    ("types", "process"): 0.45,
}


def thresholds(domain, genre=None):
    """The accept thresholds for one domain UNDER ONE GENRE.

    The single resolver: core.search, the accept predicate and calibrate_floors
    all read floors through here, so a per-genre floor can never be honoured by
    the calibrator and ignored by the shipping search (the exact split
    search_accept.py exists to prevent). `genre=None` means "no genre context",
    which resolves to the domain default.
    """
    base = SEARCH_THRESHOLDS[domain]
    override = GENRE_SCORE_FLOORS.get((domain, genre))
    return base if override is None else {**base, "min_score": override}

# A query whose top score reaches this multiple of the domain floor is treated as
# strong enough to stand without meeting the coverage ratio. Set from probe queries
# written in natural phrasing that the smoke set does not contain (2026-08-25):
# rare product nouns such as "nginx" or "redis" score far above the floor on their
# own, while off-topic queries match nothing and score zero regardless.
STRONG_EVIDENCE_FACTOR = 1.5
