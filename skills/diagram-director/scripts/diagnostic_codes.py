#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stable diagnostic codes for diagram-director/scripts/verify_all.py --json.

An agent repairing a cut must not have to scrape our prose. A code is the ONE thing in
the envelope that is promised to keep its spelling across releases: reasons get reworded,
evidence gains fields, codes do not.

  code       `<namespace>/<slug>`, both kebab-case. The namespace says which gate family
             owns the defect (`manifest`, `structure`, `camera`, `edge`, `text`, `acts`,
             `runner`, ...). NAMESPACES ARE OPEN: `is_well_formed()` accepts any
             well-formed pair, so a later plan can ship `episode/...` codes without
             editing this validator. MEMBERSHIP is closed: a code the runner emits must
             be in CODES, and a `##DIAG` line carrying an unknown one is folded into
             `runner/check-missing` rather than inventing vocabulary at run time.
  severity   `error` | `warning` | `unverified`. The CODE carries a default; the ROW's
             status can override it -- an UNVERIFIED row is `unverified` whatever its
             code says, because "the check could not run" is not "the check found this".
             `warning` is for the one shape a gate MEASURES but is willing to ship:
             `caption/occludes-edge` (a card over plain scenery) is reported with its
             overlap and never blocks `ok`. Everything else defaults to `error`.

`code_for(label)` maps a stage-table label to its code and RAISES on an unmapped one, so
a new check cannot ship codeless. Checks whose subject is dynamic (a camera hold's id) or
whose defect classes are several (a `##DIAG` emitter) attach their code themselves; those
codes are listed in EXPLICIT so the stale-code guard can see them.
"""

import re

ERROR, WARNING, UNVERIFIED = "error", "warning", "unverified"

# `<namespace>/<slug>`; the namespace is NOT constrained to the list used today.
CODE_PATTERN = re.compile(r"^[a-z][a-z0-9-]*/[a-z][a-z0-9-]*$")

# code -> (default severity, stage it is reported from, one-line meaning)
CODES = {
    "manifest/feature-empty": (ERROR, "A manifest", "a declared feature carries no evidence"),
    "manifest/feature-unknown": (ERROR, "A manifest", "manifest shape or closed vocabulary"),
    "manifest/source-unresolved": (ERROR, "A manifest", "a cited dataset row does not resolve"),
    "manifest/shrink-unamended": (ERROR, "A manifest", "features/holds shrank vs HEAD with no "
                                                       "dated AMENDMENT naming what went"),
    "manifest/hold-missing-field": (ERROR, "A manifest", "a hold is missing a required field"),
    "structure/not-well-formed": (ERROR, "B structural", "an element does not close in order"),
    "structure/external-host": (ERROR, "B structural", "a host the runtime target forbids"),
    "structure/aria-missing": (ERROR, "B structural", "role/title/desc or per-frame label absent"),
    "structure/animated-property": (ERROR, "B structural", "width/height/top/left animated"),
    "structure/master-divisor": (ERROR, "B structural", "a duration does not divide master_ms"),
    "structure/keyframe-offgrid": (ERROR, "B structural", "a stop is not an instant the "
                                                          "manifest names"),
    "camera/hold-text-floor": (ERROR, "D camera", "essential text lands below the gate's floor"),
    "camera/hold-containment": (ERROR, "D camera", "the must-show bbox is not inside the frame"),
    "camera/pmin-below-policy": (ERROR, "D camera", "the manifest declares a p_min below policy"),
    "camera/live-mismatch": (ERROR, "E geometry", "the page's own camera is not the hold's"),
    "acts/recap-order": (ERROR, "C browser", "a recap replays out of order"),
    # --- act identity, act delta and the role lens (all stage B, all stdlib) ---
    "acts/identity-role-drift": (ERROR, "B structural", "one id carries two data-roles"),
    "acts/identity-shape-drift": (ERROR, "B structural", "one id carries two shape signatures"),
    "acts/identity-zone-drift": (ERROR, "B structural", "an id lands in another viewbox "
                                                        "grid cell with no declared move"),
    "acts/retired-id-returns": (ERROR, "B structural", "a retired id is drawn again"),
    "acts/debut-accent-missing": (ERROR, "B structural", "an added id has no debut accent"),
    "acts/node-id-missing": (ERROR, "B structural", "an act node has no id, or two share one"),
    "acts/delta-caption-empty": (ERROR, "B structural", "no caption names anything the act "
                                                        "changed"),
    "acts/delta-mismatch": (ERROR, "B structural", "the declared delta is not the delta the "
                                                   "DOM draws"),
    "acts/retired-ghost-missing": (ERROR, "B structural", "a retired component has no "
                                                          "outline-only ghost"),
    "acts/delta-chip-mismatch": (ERROR, "B structural", "a delta chip's numbers are not the "
                                                        "delta's"),
    "acts/anchor-not-shared": (ERROR, "B structural", "an anchor hold names an id one of its "
                                                      "two acts does not have"),
    "lens/edge-set-mismatch": (ERROR, "B structural", "the animated edges are not the "
                                                      "cross-role edges"),
    "lens/node-not-idled": (ERROR, "B structural", "a node outside the lens is not idled"),
    "lens/edge-unattributed": (ERROR, "B structural", "an edge in a lens act declares "
                                                     "no data-from/data-to endpoints"),
    "legend/entry-unbacked": (ERROR, "B structural", "a legend entry names a role the DOM "
                                                     "does not draw"),
    "legend/count-wrong": (ERROR, "B structural", "a legend count is not the final act's "
                                                  "count for that role"),
    "legend/member-retired": (ERROR, "B structural", "a legend entry names a component the "
                                                     "final act no longer draws"),
    "acts/window-bleed": (ERROR, "C browser", "a staged window bleeds through its successor"),
    "edge/endpoint-unknown": (ERROR, "B structural", "an edge declares an endpoint no node "
                                                    "in the file carries"),
    "edge/floating-endpoint": (ERROR, "C browser", "an edge endpoint is rooted on nothing"),
    "edge/wrong-side": (ERROR, "C browser", "an edge leaves a station by the wrong side"),
    "edge/frame-margin": (ERROR, "E geometry", "a teaching line hugs the frame edge"),
    "text/containment": (ERROR, "C browser", "node text crosses its own shape"),
    "text/ink-vertical": (ERROR, "E geometry", "measured ink leaves the box that holds it"),
    "caption/box-overflow": (ERROR, "C browser", "caption text spills its own card"),
    "caption/occludes-edge-label": (ERROR, "E geometry", "a caption card covers a rendered "
                                                         "edge label"),
    "caption/occludes-subject-edge": (ERROR, "E geometry", "a caption card covers an edge of "
                                                           "its own beat's subjects"),
    # The one WARNING in the registry, and the reason the severity exists: the house
    # tolerates a lower-third over plain scenery (references/camera-beat.md -> Captions),
    # so this is REPORTED with its measured overlap and never fails a run.
    "caption/occludes-edge": (WARNING, "E geometry", "a caption card crosses an edge that is "
                                                     "not its beat's subject"),
    "glyph/label-gap": (ERROR, "C browser", "a badge glyph touches its node's label"),
    "console/error": (ERROR, "C browser", "a console error, exception or failed subresource"),
    "runner/unverified": (ERROR, "runner", "a check could not run and is not named by a code"),
    "runner/check-missing": (ERROR, "runner", "a ##DIAG line the registry cannot place"),
}

# Stage-table label -> code. Every check that reports through a FIXED label lives here.
LABEL_CODE = {
    "validate": "manifest/feature-unknown",
    "shrink": "manifest/shrink-unamended",
    "well-formed": "structure/not-well-formed",
    "external-hosts": "structure/external-host",
    "aria": "structure/aria-missing",
    "animation-props": "structure/animated-property",
    "master-divisors": "structure/master-divisor",
    "keyframe-grid": "structure/keyframe-offgrid",
    "text-containment": "text/containment",
    "console-clean": "console/error",
    "caption-boxes": "caption/box-overflow",
    "glyph-label-gap": "glyph/label-gap",
    "staged-windows": "acts/window-bleed",
    "staged-windows --acts": "acts/recap-order",
    "staged-windows --reduced-motion": "acts/window-bleed",
    "html-edge-anchors": "edge/floating-endpoint",
    "hold-geometry": "text/ink-vertical",
    # The row can fail on either error class; the headline one names it, and every
    # measured defect rides beside it as its own `##DIAG` payload with its own code.
    "caption-occlusion": "caption/occludes-subject-edge",
    "frame-edge-margin": "edge/frame-margin",
    "camera-live": "camera/live-mismatch",
    "holds": "manifest/feature-empty",
    "tier-identity": "acts/node-id-missing",
    "act-delta": "acts/delta-mismatch",
    "delta-chip": "acts/delta-chip-mismatch",
    "retired-ghost": "acts/retired-ghost-missing",
    "role-lens": "lens/edge-set-mismatch",
    "legend-fact": "legend/entry-unbacked",
}

# Codes attached in code rather than derived from a label: per-hold camera results, the
# stage-A error classifier, `##DIAG` payloads, and the folding fallbacks.
EXPLICIT = frozenset({
    "camera/hold-text-floor", "camera/hold-containment", "camera/pmin-below-policy",
    "manifest/hold-missing-field", "manifest/source-unresolved",
    "runner/unverified", "runner/check-missing",
    # The two stage-B identity modules report ONE row per gate family and hang every
    # measured defect off it as a payload, so these codes are attached in code -- the
    # row's label names the family, the payload names which of the family's defects.
    "acts/identity-role-drift", "acts/identity-shape-drift", "acts/identity-zone-drift",
    "acts/retired-id-returns", "acts/debut-accent-missing", "acts/delta-caption-empty",
    "acts/delta-chip-mismatch", "acts/anchor-not-shared",
    "lens/node-not-idled", "lens/edge-unattributed", "legend/count-wrong",
    "legend/member-retired", "edge/endpoint-unknown",
    # The caption-occlusion sweep reports three classes through one row: the row's label
    # carries the subject-edge code, these two arrive as `##DIAG` payloads beside it.
    "caption/occludes-edge-label", "caption/occludes-edge",
})

# Declared today, wired by a later phase. An entry here that becomes reachable is STALE
# and the guard in tests/test_diagnostics_envelope.py refuses it -- same rule as the
# stale-exemption check in tests/run_golden_regression.py.
RESERVED = frozenset({"edge/wrong-side"})

# validate_manifest.py error text -> the manifest code that names that defect class.
# Ordered: the first substring that matches wins.
_MANIFEST_ERROR_CODES = (
    ("carries no evidence", "manifest/feature-empty"),
    ("closed vocabulary", "manifest/feature-unknown"),
    ("does not resolve", "manifest/source-unresolved"),
    ("is missing", "manifest/hold-missing-field"),
)


def is_well_formed(code):
    """Syntax only. Namespace-agnostic on purpose (see the module docstring)."""
    return bool(CODE_PATTERN.match(code or ""))


def code_for(label, reason=None):
    """The code for a stage-table label. Unmapped labels raise -- codeless checks are
    the failure mode this registry exists to prevent.

    Stage A validates many rules through the single label `validate`, so when its reason
    line is available the classifier below narrows it to the manifest code that actually
    spoke. Every other label maps one to one.
    """
    if label == "validate" and reason:
        return code_for_manifest_error(reason)
    try:
        return LABEL_CODE[label]
    except KeyError:
        raise KeyError(f"no diagnostic code for check label {label!r}; known labels: "
                       f"{sorted(LABEL_CODE)}. Register it in diagram-director/scripts/diagnostic_codes.py "
                       f"rather than emitting an untyped diagnostic.") from None


def code_for_manifest_error(message):
    """Stage A validates many rules through one label; this names which one spoke."""
    for needle, code in _MANIFEST_ERROR_CODES:
        if needle in (message or ""):
            return code
    return LABEL_CODE["validate"]


def severity_for(code, status):
    """Row status beats the code's default: UNVERIFIED is never an error, and never a pass."""
    if status == "UNVERIFIED":
        return UNVERIFIED
    entry = CODES.get(code)
    return entry[0] if entry else ERROR
