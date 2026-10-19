#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Advisory keyword-quality report. WARNING ONLY -- never a gate.

Two signals, per domain:
  * high document frequency -- a keyword on many rows discriminates between
    none of them, so a query carrying it spreads score instead of pointing.
  * exact collisions -- the same keyword verbatim on two or more rows, which
    is the extreme case of the above and usually a copy/paste.

Neither is automatically a defect: "cache" belongs on several rows honestly.
This prints what to LOOK at; it exits 0 always and is deliberately not wired
into validate_csv.py or tests/run_smoke.py. Judgement stays human.

    python3 diagram-director/scripts/report_keyword_df.py [--domain <d>] [--top 15] [--min-df 3]
"""

import argparse
import csv
import sys
from collections import defaultdict

from csv_config import CSV_CONFIG, domain_path
from csv_schema import split_terms


def _keyword_index(domain):
    """keyword -> sorted list of row ids that carry it, for one domain."""
    cfg = CSV_CONFIG[domain]
    path = domain_path(domain)
    id_field = cfg["id_field"]
    index = defaultdict(list)
    if not path.exists() or not id_field:
        return index
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if "Keywords" not in row:
                return index
            row_id = row.get(id_field, "?")
            for term in {t.casefold() for t in split_terms(row.get("Keywords", ""))}:
                index[term].append(row_id)
    return index


def _print_block(title, entries, top, note):
    if not entries:
        print(f"  {title}: none.")
        return
    print(f"  {title}:")
    for count, term, ids in entries[:top]:
        print(f"    df={count:2}  {term!r}: {', '.join(sorted(ids))}")
    if len(entries) > top:
        print(f"    ... {len(entries) - top} more (raise --top to see them). {note}")


def report(domains, top, min_df):
    for domain in domains:
        index = _keyword_index(domain)
        if not index:
            continue
        ranked = sorted(((len(ids), term, ids) for term, ids in index.items() if len(ids) > 1),
                        key=lambda item: (-item[0], item[1]))
        rows = len({r for ids in index.values() for r in ids})
        print(f"\n=== {domain} ({CSV_CONFIG[domain]['file']}) -- "
              f"{len(index)} distinct keywords over {rows} rows")
        _print_block(f"WEAK DISCRIMINATORS (df >= {min_df})",
                     [e for e in ranked if e[0] >= min_df], top, "")
        _print_block("EXACT COLLISIONS (same keyword on exactly 2 rows)",
                     [e for e in ranked if e[0] == 2], top,
                     "Two rows sharing a term is often fine; check the pairs that mean "
                     "different things.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--domain", choices=list(CSV_CONFIG.keys()), default=None,
                        help="Restrict to one domain (default: every domain with a Keywords column)")
    parser.add_argument("--top", type=int, default=15, help="Rows to print per domain (default 15)")
    parser.add_argument("--min-df", type=int, default=3, dest="min_df",
                        help="Only report keywords on this many rows or more (default 3)")
    args = parser.parse_args(argv)

    report([args.domain] if args.domain else list(CSV_CONFIG), args.top, args.min_df)
    print("\nAdvisory only -- this report never fails a build.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
