#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One floor-benchmark case: its declaration, and the ALIAS-BOUND scan of a candidate cut.

    from floor_case import load, semantic
    case = load(Path("benchmarks/floor/cases/scaling-3tier"))
    result = semantic(html_text, manifest_dict, case)

MATCHING IS NEVER ON LABEL TEXT. A cut that draws the right architecture and names its boxes
differently is a pass; a cut that prints the expected words over the wrong topology is a fail.
Both are only expressible if the scan reads `data-node-id`, `data-role` and
`data-from`/`data-to` -- phase 03's attributes -- so those are the only things it reads.

Two absences are FINDINGS, never skips, because a skip would silently improve the score:

  nodes-not-identified        a `g.node` with no `data-node-id` cannot be counted as a distinct
                              component, so its role tally is unknowable rather than zero.
  edges-not-machine-readable  a `path.edge` with no `data-from`/`data-to` says nothing about
                              which roles it joins. That is a finding about the SKILL (the
                              attributes are standard since phase 03), not a harness bug.

Reading is delegated to `act_dom_scan` -- the same reader the act-identity gates use, so the
benchmark and the gates can never disagree about what the DOM contains.

Stdlib only. Read-only: this module opens files for reading and writes nothing, ever.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from act_dom_scan import read_acts, read_edges, read_nodes                  # noqa: E402

# `case.json`'s closed key set. Unknown key = error: a typo'd `requiredEgdes` would otherwise
# make a gate silently vanish and the case would grade itself easier than it reads.
CASE_KEYS = {"case", "genre", "requiredActs", "requiredFeatures", "requiredComponents",
             "requiredEdges", "notes"}
CASE_REQUIRED = ("case", "genre", "requiredActs", "requiredComponents", "requiredEdges")
COMPONENT_KEYS = {"alias", "roles", "min", "anyOfIds"}
COMPONENT_REQUIRED = ("alias", "roles", "min")
# The seven semantic roles of `data/color-semantics.csv`; a case may not invent an eighth.
ROLES = {"client", "service", "data", "infra", "async", "external", "error"}
GENRES = {"system-design", "process"}


class CaseError(ValueError):
    """A malformed `case.json`. Carries a message a human can act on, never a traceback."""


def _require(condition, message):
    if not condition:
        raise CaseError(message)


def _check_component(entry, where):
    _require(isinstance(entry, dict), f"{where}: a requiredComponents entry must be an object")
    unknown = sorted(set(entry) - COMPONENT_KEYS)
    _require(not unknown, f"{where}: unknown component key(s) {unknown}")
    for key in COMPONENT_REQUIRED:
        _require(key in entry, f"{where}: component is missing {key!r}")
    _require(isinstance(entry["roles"], list) and entry["roles"],
             f"{where}: component {entry['alias']!r} needs a non-empty roles list")
    bad = sorted(set(entry["roles"]) - ROLES)
    _require(not bad, f"{where}: component {entry['alias']!r} names unknown role(s) {bad}")
    _require(isinstance(entry["min"], int) and entry["min"] > 0,
             f"{where}: component {entry['alias']!r} needs a positive integer min")
    _require(isinstance(entry.get("anyOfIds", []), list),
             f"{where}: component {entry['alias']!r} anyOfIds must be a list")


def load(case_dir):
    """Read + validate `<case_dir>/case.json`; `prompt.md` must exist beside it."""
    case_dir = Path(case_dir)
    path = case_dir / "case.json"
    try:
        case = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CaseError(f"{path}: cannot be read ({exc})") from exc
    except json.JSONDecodeError as exc:
        raise CaseError(f"{path}: is not valid JSON ({exc})") from exc
    _require(isinstance(case, dict), f"{path}: the case must be a JSON object")
    unknown = sorted(set(case) - CASE_KEYS)
    _require(not unknown, f"{path}: unknown key(s) {unknown}; the case schema is closed")
    for key in CASE_REQUIRED:
        _require(key in case, f"{path}: missing required key {key!r}")
    _require(case["case"] == case_dir.name,
             f"{path}: declares case {case['case']!r} but lives in {case_dir.name!r}")
    _require(case["genre"] in GENRES,
             f"{path}: genre {case['genre']!r} is not in {sorted(GENRES)}")
    _require(isinstance(case["requiredActs"], int) and case["requiredActs"] >= 1,
             f"{path}: requiredActs must be an integer >= 1")
    _require(isinstance(case.get("requiredFeatures", []), list),
             f"{path}: requiredFeatures must be a list")
    _require(isinstance(case["requiredComponents"], list) and case["requiredComponents"],
             f"{path}: requiredComponents must be a non-empty list")
    for entry in case["requiredComponents"]:
        _check_component(entry, str(path))
    _require(isinstance(case["requiredEdges"], list), f"{path}: requiredEdges must be a list")
    for pair in case["requiredEdges"]:
        _require(isinstance(pair, list) and len(pair) == 2,
                 f"{path}: a requiredEdges entry must be a [roleA, roleB] pair, got {pair!r}")
        bad = sorted(set(pair) - ROLES)
        _require(not bad, f"{path}: requiredEdges names unknown role(s) {bad}")
    _require((case_dir / "prompt.md").exists(), f"{case_dir}: prompt.md is missing")
    return case


def _identities(html_text):
    """({id: role}, anonymous_node_count) over the WHOLE cut, acts included.

    Ids repeat across acts by design (that IS the continuity rule), so the map is keyed by id
    and a repeat is not a second component. The first role wins; a drifting role is
    `acts/identity-role-drift`'s business, not this scan's.
    """
    roles, anonymous = {}, 0
    for node in read_nodes(html_text):
        node_id = (node.get("id") or "").strip()
        if not node_id:
            anonymous += 1
            continue
        roles.setdefault(node_id, (node.get("role") or "").strip())
    return roles, anonymous


def _act_count(html_text, manifest):
    """The manifest's own `acts[]` when it declares them, else the act groups in the DOM."""
    declared = (manifest or {}).get("acts")
    if isinstance(declared, list) and declared:
        return len(declared)
    return len(read_acts(html_text))


def _missing_components(case, roles_by_id):
    """Aliases whose role tally (distinct ids) falls short, or whose anyOfIds never appear."""
    missing = []
    for entry in case["requiredComponents"]:
        found = sum(1 for role in roles_by_id.values() if role in entry["roles"])
        row = {"alias": entry["alias"], "roles": entry["roles"], "min": entry["min"],
               "found": found}
        if found < entry["min"]:
            missing.append(row)
            continue
        any_of = entry.get("anyOfIds") or []
        if any_of and not set(any_of) & set(roles_by_id):
            missing.append(dict(row, anyOfIds=any_of, reason="no-declared-id-present"))
    return missing


def _edge_role_pairs(html_text, roles_by_id):
    """({frozenset(roleA, roleB)}, unattributed_edge_count) from `data-from`/`data-to`."""
    pairs, unattributed = set(), 0
    for edge in read_edges(html_text):
        source, target = (edge.get("from") or "").strip(), (edge.get("to") or "").strip()
        if not source or not target:
            unattributed += 1
            continue
        pairs.add(frozenset((roles_by_id.get(source, ""), roles_by_id.get(target, ""))))
    return pairs, unattributed


def semantic(html_text, manifest, case):
    """{ok, missingComponents, missingEdges, missingFeatures, actCount, reasons}.

    `ok` is the conjunction of every check below; `reasons` names the structural absences that
    made a check unanswerable rather than merely unmet.
    """
    roles_by_id, anonymous = _identities(html_text)
    reasons = []
    if anonymous:
        reasons.append("nodes-not-identified")
    pairs, unattributed = _edge_role_pairs(html_text, roles_by_id)
    if unattributed:
        reasons.append("edges-not-machine-readable")
    missing_edges = [pair for pair in case["requiredEdges"]
                     if frozenset(pair) not in pairs]
    declared = set((manifest or {}).get("features") or [])
    missing_features = sorted(set(case.get("requiredFeatures") or []) - declared)
    act_count = _act_count(html_text, manifest)
    if act_count < case["requiredActs"]:
        reasons.append(f"acts-short:{act_count}<{case['requiredActs']}")
    missing_components = _missing_components(case, roles_by_id)
    return {"ok": not (missing_components or missing_edges or missing_features or reasons),
            "missingComponents": missing_components,
            "missingEdges": [list(pair) for pair in missing_edges],
            "missingFeatures": missing_features,
            "actCount": act_count,
            "reasons": reasons}
