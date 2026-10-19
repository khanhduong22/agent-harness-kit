#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The floor benchmark's append-only ledger: naming, reading, writing, and `derive()`.

Split from `diagram-director/scripts/run_floor.py` so the CLI holds argument handling and the measurement
sequence while THIS file holds the one thing the whole benchmark rests on -- the single
derivation of `firstPassUsable` -- plus everything that touches the results directory.

APPEND-ONLY. `results/YYYY-MM-DD-<case>-<attempt>.json` is refused if it already exists: a
round is re-run under a NEW `--attempt`, never written over the record of the last one. The
only in-place edit in the whole harness is `review`, which fills a PENDING review exactly
once (`fill_review`) and re-derives the boolean from the filled record.

DERIVED, NEVER STORED AS AN OPINION. `derive()` is called when a record is written and again
for every record on every `report`; a stored value that disagrees with it exits 1 and names
the file. That is the property the ledger exists for: it cannot be argued with, only re-run.
"""

import json
import subprocess
from datetime import date as date_cls
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_ROOT.parent
RESULTS_DIR = SKILL_ROOT / "benchmarks" / "floor" / "results"
FLOOR_DIR = SKILL_ROOT / "benchmarks" / "floor"
CASES_DIR = FLOOR_DIR / "cases"
SCHEMA_VERSION = 1
# An absent candidate still costs a round: skipped is not passed.
FAILURE_REASONS = ("timeout", "no_candidate", "provider_error")
REVIEW_STATUSES = ("passed", "failed", "pending", "absent")
RECORD_KEYS = ("schemaVersion", "case", "date", "attempt", "candidate", "semantic",
               "validation", "visualReview", "firstPassUsable", "failureReason",
               "skillSha", "skillDirty")


class LedgerError(RuntimeError):
    """A ledger operation that must not be retried blindly: names the file and the reason."""


def derive(rec):
    """`firstPassUsable` -- the ONE definition, used by `run`, `review` and `report`.

    All four conjuncts are load-bearing. Attempt 2 is a repaired round and cannot be a FIRST
    pass. `validation.ok` is phase 02's envelope `ok`, so an UNVERIFIED cut (exit 3) is not
    usable -- a render-side stage that could not run is not a stage that passed. And a review
    with no reviewer is nobody's judgement: `A green runner is the floor, not the delivery`.
    """
    review = rec.get("visualReview") or {}
    return bool(rec.get("attempt") == 1
                and (rec.get("semantic") or {}).get("ok")
                and (rec.get("validation") or {}).get("ok")
                and review.get("status") == "passed"
                and (review.get("reviewer") or "").strip())


def skill_sha():
    """(short SHA, dirty?) of the repo the round measured -- the tripwire's comparison key.

    A dirty worktree is recorded as `<sha>-dirty` because the measured skill is then NOT the
    commit: two rounds at the same SHA with different uncommitted work are not comparable and
    the record must say so rather than imply a clean baseline.
    """
    def git(*args):
        return subprocess.run(("git", *args), cwd=str(REPO_ROOT), capture_output=True,
                              text=True, timeout=30, check=False)
    try:
        head = git("rev-parse", "--short", "HEAD")
        status = git("status", "--porcelain")
    except (OSError, subprocess.SubprocessError):
        return "unknown", False
    if head.returncode != 0:
        return "unknown", False
    dirty = status.returncode == 0 and bool(status.stdout.strip())
    sha = head.stdout.strip() or "unknown"
    return (f"{sha}-dirty" if dirty else sha), dirty


def record_path(results_dir, date, case, attempt):
    return Path(results_dir) / f"{date}-{case}-{attempt}.json"


def new_record(case, attempt, candidate, semantic, validation, review, failure_reason=None,
               today=None):
    """Assemble a record and derive its boolean. Nothing else may set `firstPassUsable`."""
    sha, dirty = skill_sha()
    rec = {"schemaVersion": SCHEMA_VERSION, "case": case,
           "date": today or date_cls.today().isoformat(), "attempt": attempt,
           "candidate": candidate, "semantic": semantic, "validation": validation,
           "visualReview": review, "firstPassUsable": False,
           "failureReason": failure_reason, "skillSha": sha, "skillDirty": dirty}
    rec["firstPassUsable"] = derive(rec)
    return rec


def write_record(rec, results_dir=RESULTS_DIR):
    """Write a NEW record. Refuses an existing path -- the ledger is append-only."""
    results_dir = Path(results_dir)
    path = record_path(results_dir, rec["date"], rec["case"], rec["attempt"])
    if path.exists():
        raise LedgerError(f"{path} already exists. The ledger is append-only: re-run the round "
                          f"with a different --attempt rather than overwriting a record.")
    try:
        results_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise LedgerError(f"{path}: could not be written ({exc})") from exc
    return path


def rewrite_record(path, rec):
    """In-place rewrite -- `review` only, and only after `fill_review` re-derived."""
    try:
        Path(path).write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise LedgerError(f"{path}: could not be rewritten ({exc})") from exc


def read_record(path):
    try:
        rec = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise LedgerError(f"{path}: cannot be read ({exc})") from exc
    except json.JSONDecodeError as exc:
        raise LedgerError(f"{path}: is not valid JSON ({exc})") from exc
    if not isinstance(rec, dict):
        raise LedgerError(f"{path}: a result record must be a JSON object")
    return rec


def read_all(results_dir=RESULTS_DIR, case=None, since=None):
    """[(path, record_or_None, problem_or_None)] sorted by filename -- date, then case."""
    rows = []
    for path in sorted(Path(results_dir).glob("*.json")):
        try:
            rec = read_record(path)
        except LedgerError as exc:
            rows.append((path, None, str(exc)))
            continue
        problem = missing_keys(rec)
        if case and rec.get("case") != case:
            continue
        if since and str(rec.get("date") or "") < since:
            continue
        rows.append((path, rec, problem))
    return rows


def missing_keys(rec):
    """The record-shape complaint, or None. A record missing a gate is not a passing round."""
    absent = [key for key in RECORD_KEYS if key not in rec]
    return f"record is missing {absent}" if absent else None


def fill_review(rec, reviewer, status, defects):
    """Fill a PENDING review exactly once, then re-derive. Raises on any other status.

    The user reviews asynchronously, so a round is recorded before anyone has looked at the
    contact sheet. `pending` is the honest state for that gap -- and it derives to false, so
    an un-reviewed round can never read as a pass while it waits.
    """
    current = (rec.get("visualReview") or {}).get("status")
    if current != "pending":
        raise LedgerError(f"review already recorded: visualReview.status is {current!r}, not "
                          f"'pending'. A recorded verdict is not re-opened; run a new attempt.")
    if status not in ("passed", "failed"):
        raise LedgerError(f"--review must be 'passed' or 'failed' here, got {status!r}")
    if not (reviewer or "").strip():
        raise LedgerError("--reviewer must name a person; 'the harness' is not a reviewer")
    rec["visualReview"] = {"status": status, "reviewer": reviewer.strip(),
                           "defects": list(defects or ())}
    rec["firstPassUsable"] = derive(rec)
    return rec
