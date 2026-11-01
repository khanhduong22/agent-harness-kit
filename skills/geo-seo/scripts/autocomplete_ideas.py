#!/usr/bin/env python3
"""
Zero-API Google Autocomplete & Question Expander for GEO/SEO.
Uses Google's public suggest endpoint (no paid API keys required).

Usage: python3 scripts/autocomplete_ideas.py "Dương Phúc Khánh" --lang vi
"""
from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request

PREFIXES = [
    "",
    "là ai",
    "what is",
    "how to",
    "vs",
    "best",
    "review",
    "architecture",
]


def fetch_suggestions(query: str, hl: str = "vi") -> list[str]:
    url = (
        "https://suggestqueries.google.com/complete/search?client=firefox"
        f"&hl={urllib.parse.quote(hl)}&q={urllib.parse.quote(query)}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
            if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
                return [str(item) for item in data[1]]
    except Exception:
        pass
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description="Zero-API Google Autocomplete keyword & question expander")
    parser.add_argument("keyword", help="Seed keyword or entity name")
    parser.add_argument("--lang", "-l", default="vi", help="Language code (default: vi)")
    parser.add_argument("--expand", action="store_true", help="Also query question/intent modifiers")
    args = parser.parse_args()

    seen: set[str] = set()
    queries = [args.keyword]
    if args.expand:
        queries.extend(f"{args.keyword} {p}".strip() for p in PREFIXES if p)

    results: list[str] = []
    for q in queries:
        for item in fetch_suggestions(q, hl=args.lang):
            if item not in seen:
                seen.add(item)
                results.append(item)

    print(json.dumps({"seed": args.keyword, "lang": args.lang, "count": len(results), "suggestions": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
