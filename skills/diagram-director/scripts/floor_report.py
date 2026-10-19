#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rendering for `run_floor.py report`: the table, the JSON, and the self-check.

Separated from the CLI because the SELF-CHECK is the point of the report and deserves to be
readable on its own. Every row is re-derived from its own gates; a stored `firstPassUsable`
that disagrees, or a record whose shape is short of a gate, is an INCONSISTENCY and makes the
report exit 1 naming the file. Hand-editing the ledger to a nicer number therefore fails
louder than leaving the truthful record alone.

An empty ledger prints the header and exits 0: no rounds recorded is not a failure, it is a
benchmark nobody has run yet.
"""

from floor_ledger import derive

COLUMNS = (("case", 22), ("date", 12), ("skillSha", 16), ("semantic", 9),
           ("validation", 11), ("review", 22), ("usable", 6))


def _cell(value, width):
    text = str(value)
    return text if len(text) >= width else text.ljust(width)


def _gate(flag):
    return "PASS" if flag else "FAIL"


def _review_cell(rec):
    """`status:reviewer` -- the reviewer is half the gate, so it is never hidden."""
    review = rec.get("visualReview") or {}
    reviewer = (review.get("reviewer") or "").strip() or "-"
    return f"{review.get('status', '?')}:{reviewer}"[:21]


def row_cells(rec):
    return [_cell(rec.get("case", "?"), COLUMNS[0][1]),
            _cell(rec.get("date", "?"), COLUMNS[1][1]),
            _cell(rec.get("skillSha", "?"), COLUMNS[2][1]),
            _cell(_gate((rec.get("semantic") or {}).get("ok")), COLUMNS[3][1]),
            _cell(_gate((rec.get("validation") or {}).get("ok")), COLUMNS[4][1]),
            _cell(_review_cell(rec), COLUMNS[5][1]),
            _cell("yes" if derive(rec) else "no", COLUMNS[6][1])]


def inconsistency(path, rec, problem):
    """The complaint about one record, or None. Shape first, then stored-vs-derived."""
    if rec is None:
        return f"{path.name}: {problem}"
    if problem:
        return f"{path.name}: {problem}"
    stored, expected = rec.get("firstPassUsable"), derive(rec)
    if bool(stored) != expected:
        return (f"{path.name}: stored firstPassUsable={stored!r} but the record's own gates "
                f"derive {expected!r} (attempt {rec.get('attempt')!r}, "
                f"semantic.ok={(rec.get('semantic') or {}).get('ok')!r}, "
                f"validation.ok={(rec.get('validation') or {}).get('ok')!r}, "
                f"review={_review_cell(rec)})")
    return None


def render(rows):
    """(lines, exit_code) for `report`. `rows` is `floor_ledger.read_all()`'s output."""
    lines = [" ".join(_cell(name, width) for name, width in COLUMNS)]
    lines.append(" ".join("-" * width for _, width in COLUMNS))
    problems = []
    for path, rec, problem in rows:
        complaint = inconsistency(path, rec, problem)
        if complaint:
            problems.append(complaint)
        if rec is not None:
            lines.append(" ".join(row_cells(rec)))
    if not rows:
        lines.append("(no rounds recorded yet)")
    if problems:
        lines.append("")
        lines.append(f"{len(problems)} INCONSISTENT record(s) -- the ledger disagrees with "
                     f"itself:")
        lines += [f"  {text}" for text in problems]
        lines.append("A record is re-run, never re-written: add a new attempt instead.")
    return lines, (1 if problems else 0)


def as_json(rows):
    """The same content as a payload: records, complaints, and one `ok`."""
    problems = [text for text in
                (inconsistency(path, rec, problem) for path, rec, problem in rows) if text]
    return {"schemaVersion": 1, "ok": not problems,
            "records": [dict(rec, derivedFirstPassUsable=derive(rec))
                        for _, rec, _ in rows if rec is not None],
            "inconsistencies": problems}
