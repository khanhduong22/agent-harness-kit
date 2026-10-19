#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The machine-readable half of diagram-director/scripts/verify_all.py: `--json` builds THIS envelope.

    {"schemaVersion": 1, "ok": false, "cut": ..., "manifest": ..., "url": ..., "exit": 1,
     "stages": [{"stage", "name", "status", "reason"}, ...],
     "diagnostics": [{"code", "severity", "stage", "subject", "evidence", "supportedFixes"}]}

Contract, so a consumer can be written once:

  stages[]       mirrors the human table one for one, `N-A` rows included. An N-A is never
                 a diagnostic: nothing was declared, so nothing is wrong.
  diagnostics[]  FAIL and UNVERIFIED rows only.
  ok             true only when there is NO `error` AND NO `unverified` diagnostic. A
                 skipped render-side stage is the one lie this whole design exists to
                 prevent, so it costs `ok` exactly as a failure does.
  exit           the process exit code (0/1/2/3), carried in the payload so a consumer
                 that only has the JSON still knows what the runner returned.
  supportedFixes imperative sentences WITH NUMBERS, and only ever a fix that was proven
                 by re-solving. Never "consider", never "try".

Paths are repo-relative: a pasted diagnostic must not carry someone's home directory.
"""

import json
from pathlib import Path

import diagnostic_codes as codes

SCHEMA_VERSION = 1
REPO_ROOT = Path(__file__).resolve().parents[2]
DIAG_PREFIX = "##DIAG "
# CHARACTERS, not bytes: the .mjs streams arrive already decoded as text. A browser check
# emitting a longer single line is malfunctioning, so the line is folded into
# `runner/check-missing` with the raw text truncated to this length.
MAX_DIAG_LINE = 8192


def rel(path):
    """Repo-relative where possible, else the bare name -- never an absolute home path."""
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return resolved.name


def fold_diag_lines(text):
    """(prose without the ##DIAG lines, [payload, ...]).

    A payload is `{"code", "subject", "evidence", "fixes"}`. `fixes` comes from the line's
    optional `supportedFixes` and is subject to the same rule as every other fix in this
    envelope: an imperative sentence WITH NUMBERS that the emitter proved, never advice --
    `verify-caption-occlusion.mjs` re-measures the shifted card before it offers a dx.
    Severity is NOT read from the line --
    the .mjs reports what it measured, the runner owns policy. An unparseable line, an
    over-long one, or one carrying a code the registry does not know becomes
    `runner/check-missing` with the raw line as evidence: never a crash, never silence.
    """
    prose, payloads = [], []
    for line in (text or "").splitlines():
        stripped = line.strip()
        if not stripped.startswith(DIAG_PREFIX):
            prose.append(line)
            continue
        raw = stripped[len(DIAG_PREFIX):]
        try:
            if len(raw) > MAX_DIAG_LINE:
                raise ValueError(f"##DIAG line over {MAX_DIAG_LINE} bytes")
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError("##DIAG payload is not an object")
        except ValueError as exc:
            payloads.append({"code": "runner/check-missing",
                             "evidence": {"raw": raw[:MAX_DIAG_LINE], "why": str(exc)}})
            continue
        code = payload.get("code")
        if code not in codes.CODES:
            payloads.append({"code": "runner/check-missing",
                             "evidence": {"raw": raw[:MAX_DIAG_LINE],
                                          "why": f"code {code!r} is not in the registry"}})
            continue
        payloads.append({"code": code, "subject": payload.get("subject") or {},
                         "evidence": payload.get("evidence") or {},
                         "fixes": [str(f) for f in (payload.get("supportedFixes") or [])]})
    return "\n".join(prose), payloads


def _diagnostic(res, code, cut, subject=None, evidence=None, fixes=()):
    subject_out = {"file": rel(cut)}
    subject_out.update(subject or {})
    return {"code": code, "severity": codes.severity_for(code, res.status),
            "stage": res.stage, "subject": subject_out,
            "evidence": evidence if evidence is not None else {"reason": res.reason},
            "supportedFixes": list(fixes or ())}


def diagnostics_from(results, cut):
    """One entry per FAIL/UNVERIFIED row, PLUS one per folded `##DIAG` payload.

    The two are different grains and both are needed. The ROW says which gate failed and
    carries its prose reason, which is the only record of the violation classes no code
    names yet. Each PAYLOAD is one measured defect inside that gate, and a browser sweep
    reports several per run. Payloads are therefore ADDITIVE, never a replacement: a
    check that learns to emit `##DIAG` for one of its classes must not silently drop the
    others out of the envelope.
    """
    out = []
    for res in results:
        if res.status not in ("FAIL", "UNVERIFIED"):
            continue
        evidence = dict(res.evidence or {})
        payloads = evidence.pop("diagnostics", None) or []
        try:
            code = res.code or codes.code_for(res.name, res.reason)
        except KeyError:
            # An unregistered label is a REPO defect, and the unit guard in
            # tests/test_diagnostics_envelope.py is where it is meant to be caught. At
            # RUN time the envelope must still be emitted: a consumer that gets no JSON
            # at all cannot even see that a check failed, which is strictly worse than a
            # diagnostic saying the runner could not place it.
            code = "runner/unverified" if res.status == "UNVERIFIED" else "runner/check-missing"
            evidence = dict(evidence or {}, unregistered_label=res.name)
        out.append(_diagnostic(res, code, cut, res.subject, evidence or None, res.fixes))
        out += [_diagnostic(res, item["code"], cut, item.get("subject"),
                            item.get("evidence"), item.get("fixes"))
                for item in payloads]
    return out


def envelope(results, cut, manifest, url, exit_code):
    """The whole payload. `exit_code` is what main() is about to return."""
    diagnostics = diagnostics_from(results, cut)
    blocking = {codes.ERROR, codes.UNVERIFIED}
    return {"schemaVersion": SCHEMA_VERSION,
            "ok": not any(d["severity"] in blocking for d in diagnostics),
            "cut": rel(cut), "manifest": rel(manifest), "url": url, "exit": exit_code,
            "stages": [{"stage": r.stage, "name": r.name, "status": r.status,
                        "reason": " ".join((r.reason or "").split())} for r in results],
            "diagnostics": diagnostics}


def dumps(results, cut, manifest, url, exit_code):
    return json.dumps(envelope(results, cut, manifest, url, exit_code), indent=2)
