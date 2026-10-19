#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static configuration for the eight system-design datasets.

Almost no logic lives here on purpose: file locations, key/required/nullable
column declarations, searchable/output columns, score floors and synonyms are
data, not behavior. Cell grammar, closed vocabularies and cross-reference rules
moved to csv_schema.py (2026-08-26); bm25_engine.py holds the ranking algorithm
and core.py the search orchestration.
"""

from pathlib import Path

from genre_registry import GENRE_COL

DATA_DIR = Path(__file__).parent.parent / "data"

# Result-count defaults (2026-08-26, G10). A skill lookup is normally TARGETED:
# "which component is a redis cache", one question with one right answer. Three
# results invited the caller to treat rank 2 and 3 as alternatives worth
# considering, and the solution sheets showed them doing exactly that. So the
# default is 1, and asking for alternatives is an explicit `-n`.
TARGETED_RESULTS = 1
# What the Query Contract tells the caller to retry a 0-result with. Wide on
# purpose: the retry's job is to find out whether the dataset has anything at
# all in the neighbourhood, and a 0 from an exploration search is the signal
# that there is genuinely no row.
EXPLORATION_RESULTS = 5


def set_data_dir(path):
    """Point every reader at another directory of CSVs (validator --data-dir only)."""
    global DATA_DIR
    DATA_DIR = Path(path)


def domain_path(domain):
    """Absolute path to one domain's CSV under the currently active data dir."""
    return DATA_DIR / CSV_CONFIG[domain]["file"]
# Soft cap used by the composer's checklist warning.
#
# Measured 2026-08-25 with tests/perf-motion-threshold.html on Apple Silicon macOS,
# headless Chrome: 10, 30, 60 and 120 animated edges all held a locked 60fps (95th
# percentile frame interval 16.8ms, no dropped frames), and adding a per-node glow
# to the 60-edge case cost about 8%. Frame rate is therefore NOT what limits this
# number on current hardware — the ceiling is far above any diagram worth drawing.
#
# The real limit is how many simultaneous animations a reader can follow at once.
# Past roughly a dozen, competing motion stops reading as "this is the path" and
# starts reading as noise, which defeats the reason the motion is there. So the cap
# below is a legibility budget, and the perf headroom is recorded in the harness so
# nobody re-derives it from a fear of jank.
MAX_ANIMATED_EDGES = 12

# --- Per-domain CSV schema -------------------------------------------------
# output_cols is the ANSWER a search returns; the file header is
# output_cols + meta_cols, and REQUIRED_HEADERS is derived from the pair so the
# header list is still never written down twice.
#
# meta_cols  columns that exist on disk but are NOT part of an answer: routing
#            metadata the engine consumes before ranking. Today that is exactly
#            `Genres` on types + components. It is deliberately kept out of
#            output_cols: within one search every surviving row carries the
#            active genre by construction, so printing the cell would add a
#            constant line to every result and tell the caller nothing they did
#            not already state on the command line. It is also kept out of
#            search_cols -- a partition key in the BM25 corpus would let the word
#            "process" match a row for belonging to a genre rather than for
#            being about anything.
#
# key_fields  the column(s) whose tuple must be unique in the file. One ID column
#             for the seven catalog domains; colors is a lookup table keyed
#             (Style ID, Palette, Role) -- verified unique across all 175 rows on
#             2026-08-26, and now enforced so a hand-authored second palette can
#             never quietly overwrite a role the composer reads.
# nullable    columns a legitimate ACTIVE row may leave empty. Everything else in
#             output_cols is required and an empty cell is an error (V5). The
#             lists below were derived by auditing every row of every file
#             (2026-08-26), not assumed: exactly four columns are ever blank.
CSV_CONFIG = {
    "styles": {
        "file": "styles.csv", "id_field": "Style ID",
        "key_fields": ["Style ID"],
        # css-only styles ship no CDN dependency; V10 already forbids the reverse.
        "nullable": ["CDN Deps"],
        "search_cols": ["Style ID", "Name", "Keywords", "Aliases", "Best For", "Palette Mood"],
        "output_cols": [
            "Style ID", "Name", "Keywords", "Stroke Treatment", "Fill Treatment", "Palette Mood",
            "Typography", "Background", "Canvas Light", "Canvas Dark",
            "Node Rendering", "Connector Rendering", "Motion Affinity",
            "Runtime", "CDN Deps", "Best For", "Do Not Use For", "Dark Mode", "Complexity",
            "Accessibility Notes", "CSS Techniques", "Template Status", "Status", "Aliases",
            # Which named palette in color-semantics.csv this style ships with.
            # Appended last (2026-08-26) so the existing column order -- and every
            # downstream index into it -- stays untouched.
            "Default Palette",
        ],
    },
    "types": {
        "file": "diagram-types.csv", "id_field": "Type ID",
        "key_fields": ["Type ID"], "nullable": [],
        "search_cols": ["Type ID", "Name", "Keywords", "Category", "Example Scenario", "Edge Semantics"],
        "output_cols": [
            "Type ID", "Name", "Keywords", "Category", "Default Layout", "Node Kinds", "Edge Semantics",
            "Recommended Motion", "Labeling Level", "Best Styles", "Anti-Patterns", "Example Scenario", "Status",
        ],
        "meta_cols": [GENRE_COL],
    },
    "motion": {
        "file": "motion.csv", "id_field": "Motion ID",
        "key_fields": ["Motion ID"], "nullable": [],
        "search_cols": ["Motion ID", "Name", "Keywords", "Semantic Meaning", "Technique"],
        "output_cols": [
            "Motion ID", "Name", "Keywords", "Semantic Meaning", "Technique", "Runtime", "Inline Snippet",
            "Recipe Ref", "Duration", "Easing", "Stagger Rule", "Performance Note",
            "Reduced-Motion Fallback", "Do", "Don't", "Status",
        ],
    },
    "components": {
        "file": "components.csv", "id_field": "Component ID",
        "key_fields": ["Component ID"],
        # Not every component has a metric worth annotating (a CLI, a subnet).
        "nullable": ["Common Metrics Annotation"],
        "search_cols": ["Component ID", "Name", "Keywords", "Category", "Semantic Role"],
        "output_cols": [
            "Component ID", "Name", "Keywords", "Category", "Semantic Role", "Shape Hint", "Snippet Ref",
            "Label Convention", "Common Metrics Annotation", "Status",
        ],
        "meta_cols": [GENRE_COL],
    },
    "states": {
        "file": "states.csv", "id_field": "State ID",
        "key_fields": ["State ID"],
        # Motion Ref blank = static by design (C3); Chip Text blank = the state
        # needs no badge (is-healthy, flow-active).
        "nullable": ["Motion Ref", "Chip Text"],
        "search_cols": ["State ID", "Name", "Keywords", "Use When", "Applies To"],
        "output_cols": [
            "State ID", "Name", "Keywords", "Applies To", "Static Encoding", "Motion Ref",
            "Chip Text", "Color Guidance", "Reduced-Motion Fallback", "Use When", "Don't", "Status",
        ],
    },
    # What travels ALONG an edge, as opposed to what a node IS (components)
    # or what condition it is in (states). Added 2026-08-26 after a user review
    # found every flow rendering the same dot: cargo has meaning, and naming it
    # is what lets the packet show a message / envelope / file / raw bits.
    "payloads": {
        "file": "payloads.csv", "id_field": "Payload ID",
        "key_fields": ["Payload ID"], "nullable": [],
        "search_cols": ["Payload ID", "Name", "Keywords", "Use When"],
        "output_cols": [
            "Payload ID", "Name", "Keywords", "Glyph Ref", "Use When", "Don't", "Status",
        ],
    },
    # Lookup domain: composite key (Style ID + Palette + Role), not a
    # fuzzy-searched catalog. No single id_field -- exact-ID short-circuit does
    # not apply. Palette was added 2026-08-26: the vertical-fork session
    # hand-authored a second set of role tokens per style and they only lived in
    # a scratch generator, so the skill's own dataset and its shipped forks had
    # already drifted apart. A named palette per style is what stops that -- see
    # validate_colors.check_color_coverage for the per-palette contract.
    "colors": {
        "file": "color-semantics.csv", "id_field": None,
        "key_fields": ["Style ID", "Palette", "Role"], "nullable": [],
        "search_cols": ["Style ID", "Palette", "Role"],
        "output_cols": [
            "Style ID", "Palette", "Role", "Fill", "Stroke", "Accent", "On Color", "Dark Fill",
            "Dark Stroke", "Dark Accent", "Dark On Color", "Contrast Note",
        ],
    },
    "layouts": {
        "file": "layouts.csv", "id_field": "Layout ID",
        "key_fields": ["Layout ID"], "nullable": [],
        "search_cols": ["Layout ID", "Name", "Keywords", "Flow Direction", "When to Use"],
        "output_cols": [
            "Layout ID", "Name", "Keywords", "Flow Direction", "When to Use", "When NOT",
            "Node Count Sweet Spot", "Spacing Rules", "Grouping Rule", "Status",
        ],
    },
}

# REQUIRED_HEADERS is the exact-order header contract the validator checks
# against each file on disk: the answer columns first, then the meta columns
# (appended last so every existing downstream index into the header is untouched).
REQUIRED_HEADERS = {
    domain: cfg["output_cols"] + list(cfg.get("meta_cols", []))
    for domain, cfg in CSV_CONFIG.items()
}

# Datasets that PARTITION by genre. Everything else is shared across genres --
# see genre_registry for why absence of the column means shared and an empty
# CELL does not.
GENRE_DOMAINS = [domain for domain, cfg in CSV_CONFIG.items()
                 if GENRE_COL in cfg.get("meta_cols", [])]

# Required = every column that is not declared nullable. Derived rather than
# listed so a new column is required by default: forgetting to classify one
# should fail loudly, not silently become optional.
REQUIRED_COLS = {
    domain: [col for col in cfg["output_cols"] if col not in set(cfg["nullable"])]
    for domain, cfg in CSV_CONFIG.items()
}

# Output columns whose content (inline code, spacing numbers, hatch codes)
# must never be hard-truncated in text output -- truncating mid-rule or
# mid-token makes the value actively misleading rather than merely short.
UNTRUNCATED_COLS = {"Inline Snippet", "Spacing Rules", "Shape Hint", "CSS Techniques"}

# --- Search tuning ----------------------------------------------------------
# STOPWORDS, SYNONYMS, DOMAIN_KEYWORDS, DOMAIN_TIEBREAK_ORDER, DOMAIN_SCORE_FLOORS,
# SEARCH_THRESHOLDS and STRONG_EVIDENCE_FACTOR moved to search_tuning.py
# (2026-08-26). They are calibrated values with their own change cadence -- the
# probe suite in tests/probes/ moves them, not a schema edit. Import them from
# search_tuning directly; csv_config deliberately does NOT re-export them, so a
# grep for a floor lands on the module that owns it.

# --- Validator schema -------------------------------------------------------
# Closed vocabularies (ENUMS), cross-file FK rules and cross-reference rules now
# live in csv_schema.py -- they are column grammar, not dataset configuration,
# and this module was 300 lines. Import them from there.
