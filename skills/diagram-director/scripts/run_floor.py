#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The floor benchmark CLI: measure one round, record an absent one, report the ledger.

    python3 diagram-director/scripts/run_floor.py run <case> --candidate <cut>.html [--manifest <m>.json]
            [--attempt N] --review passed|failed|pending [--reviewer "<name>"] [--defect "…"]*
    python3 diagram-director/scripts/run_floor.py review <record>.json --reviewer "<name>"
            --review passed|failed [--defect "…"]*
    python3 diagram-director/scripts/run_floor.py record-failure <case> --reason timeout|no_candidate|provider_error
            [--attempt N] [--note "…"]
    python3 diagram-director/scripts/run_floor.py report [--case <case>] [--since YYYY-MM-DD] [--json]

Every subcommand takes `--results-dir` so a test can exercise a full round without touching
the real ledger.

WHAT THIS IS. One question: after a `SKILL.md` or gate change, can attempt 1 still produce a
usable cut with NO human repair? Three gates, all required -- an alias-bound semantic scan, a
real `verify_all.py` run, and a NAMED human reviewer. It is a tripwire against this repo's own
previous `skillSha`, never a model leaderboard, and no cross-model claim may be made from it.

THE HARNESS MEASURES; IT NEVER REPAIRS. Candidates are opened read-only and are never edited,
moved or regenerated. A full round writes exactly one file, under `benchmarks/floor/results/`.

EXIT 0 the round was recorded / the report is self-consistent
     1 `report` found a record whose stored `firstPassUsable` disagrees with its own gates
     2 bad usage: an unknown case or reason, a missing candidate, an empty `--reviewer` on a
       decided review, or a result path that already exists (the ledger is append-only)
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import floor_ledger as ledger                                              # noqa: E402
import floor_report                                                       # noqa: E402
from floor_case import CaseError, load, semantic                          # noqa: E402
from floor_measure import sha256_of, validation_of                        # noqa: E402

derive = ledger.derive          # the ONE derivation, re-exported so callers cannot fork it


def _usage(message):
    print(f"BAD USAGE: {message}", file=sys.stderr)
    return 2


def cmd_run(args):
    """Measure one candidate through all three gates and append one record."""
    try:
        case = load(ledger.CASES_DIR / args.case)
    except CaseError as exc:
        return _usage(str(exc))
    if args.review != "pending" and not (args.reviewer or "").strip():
        return _usage("--reviewer must name a person for a decided review; only "
                      "`--review pending` may omit it, and pending derives to false")
    cut = Path(args.candidate)
    manifest_path = Path(args.manifest) if args.manifest else cut.with_suffix(".manifest.json")
    if not cut.exists():
        return _usage(f"{cut} does not exist; record an absent round with `record-failure`")
    if not manifest_path.exists():
        return _usage(f"no manifest at {manifest_path}; every delivered diagram ships one")
    try:
        html_text = cut.read_text(encoding="utf-8", errors="replace")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError as exc:
        return _usage(f"candidate could not be read: {exc}")
    except json.JSONDecodeError as exc:
        return _usage(f"{manifest_path} is not valid JSON: {exc}")

    scan = semantic(html_text, manifest, case)
    validation = validation_of(cut, manifest_path)
    review = {"status": args.review, "reviewer": (args.reviewer or "").strip(),
              "defects": list(args.defect or ())}
    rec = ledger.new_record(case["case"], args.attempt,
                            {"html": str(cut.resolve()), "manifest": str(manifest_path.resolve()),
                             "sha256": sha256_of(cut)},
                            scan, validation, review)
    try:
        path = ledger.write_record(rec, args.results_dir)
    except ledger.LedgerError as exc:
        return _usage(str(exc))
    print(f"recorded {path}")
    print(f"  semantic={scan['ok']} validation={validation['ok']} "
          f"review={review['status']} firstPassUsable={rec['firstPassUsable']}")
    if args.review == "pending":
        print(f"  review it with: python3 diagram-director/scripts/run_floor.py review {path} "
              f"--reviewer \"<name>\" --review passed|failed")
    return 0


def cmd_review(args):
    """Fill a PENDING record's visual review in place, exactly once, and re-derive."""
    path = Path(args.record)
    try:
        rec = ledger.read_record(path)
        ledger.fill_review(rec, args.reviewer, args.review, args.defect)
        ledger.rewrite_record(path, rec)
    except ledger.LedgerError as exc:
        return _usage(str(exc))
    print(f"reviewed {path}: {rec['visualReview']['status']} by "
          f"{rec['visualReview']['reviewer']} -- firstPassUsable={rec['firstPassUsable']}")
    return 0


def cmd_record_failure(args):
    """A round with no candidate still costs a round: skipped is never passed."""
    if args.reason not in ledger.FAILURE_REASONS:
        return _usage(f"--reason {args.reason!r} is not in the allow-list "
                      f"{list(ledger.FAILURE_REASONS)}")
    if not (ledger.CASES_DIR / args.case / "case.json").exists():
        return _usage(f"no such case: {args.case}")
    scan = {"ok": False, "missingComponents": [], "missingEdges": [], "missingFeatures": [],
            "actCount": 0, "reasons": [args.reason]}
    validation = {"ok": False, "exit": None, "errorCount": 0, "unverifiedCount": 0,
                  "codes": [], "reason": args.note or args.reason}
    review = {"status": "absent", "reviewer": "", "defects": []}
    rec = ledger.new_record(args.case, args.attempt, None, scan, validation, review,
                            failure_reason=args.reason)
    try:
        path = ledger.write_record(rec, args.results_dir)
    except ledger.LedgerError as exc:
        return _usage(str(exc))
    print(f"recorded {path}: {args.reason} (firstPassUsable=False)")
    return 0


def cmd_report(args):
    """Re-derive every record; exit 1 on any stored/derived disagreement."""
    rows = ledger.read_all(args.results_dir, case=args.case, since=args.since)
    if args.json:
        payload = floor_report.as_json(rows)
        print(json.dumps(payload, indent=2))
        return 0 if payload["ok"] else 1
    lines, code = floor_report.render(rows)
    print("\n".join(lines))
    return code


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    subs = ap.add_subparsers(dest="command", required=True)

    run = subs.add_parser("run", help="measure one candidate and append a record")
    run.add_argument("case")
    run.add_argument("--candidate", required=True, help="the cut the session produced")
    run.add_argument("--manifest", help="default: <stem>.manifest.json beside the candidate")
    run.add_argument("--attempt", type=int, default=1)
    run.add_argument("--review", required=True, choices=("passed", "failed", "pending"),
                     help="never defaulted; `pending` records that nobody has looked yet")
    run.add_argument("--reviewer", default="", help="a named person; required unless pending")
    run.add_argument("--defect", action="append", default=[])
    run.set_defaults(func=cmd_run)

    review = subs.add_parser("review", help="fill a pending record's visual review, once")
    review.add_argument("record", help="path to the result record")
    review.add_argument("--reviewer", required=True)
    review.add_argument("--review", required=True, choices=("passed", "failed"))
    review.add_argument("--defect", action="append", default=[])
    review.set_defaults(func=cmd_review)

    failed = subs.add_parser("record-failure", help="record a round that produced no candidate")
    failed.add_argument("case")
    failed.add_argument("--reason", required=True)
    failed.add_argument("--attempt", type=int, default=1)
    failed.add_argument("--note", default="")
    failed.set_defaults(func=cmd_record_failure)

    report = subs.add_parser("report", help="re-derive the ledger and print it")
    report.add_argument("--case")
    report.add_argument("--since", help="YYYY-MM-DD")
    report.add_argument("--json", action="store_true")
    report.set_defaults(func=cmd_report)

    for parser in (run, review, failed, report):
        parser.add_argument("--results-dir", default=str(ledger.RESULTS_DIR),
                            help="default: benchmarks/floor/results")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
