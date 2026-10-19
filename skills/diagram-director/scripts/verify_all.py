#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ONE runner for every mechanical pre-delivery gate on a built diagram.

    python3 diagram-director/scripts/verify_all.py diagram-director/examples/compare-chat-pubsub.html --serve
    python3 diagram-director/scripts/verify_all.py my-cut.html --base http://localhost:8942 --target local

It orchestrates, it does not reimplement: the validators, `solve_camera.py --check` and the
browser checks keep their jobs; this decides WHICH are mandatory for THIS cut from its manifest.

  A manifest   validate_manifest.validate() -- shape, vocabulary, source ids; then manifest_shrink_gate (declarations may shrink only with a dated AMENDMENT)
  B structural stdlib, from the file: well-formed HTML, external hosts vs target, ARIA,
               banned animated props, master divisors, keyframe grid, act-identity family
  C browser    manifest-gated render-side checks (declared-but-empty FAILS, undeclared N-A)
  D camera     every declared hold re-checked with the per-format/per-gate text floor
  E geometry   ink-vertical containment + straight-segment intersections AT the holds

SERVER ROOT. `--serve` serves the HTML's OWN DIRECTORY on a free 127.0.0.1 port (a
delivered cut is self-contained, so that root also works for a fixture in /tmp). Never
file:// -- fonts, CDN scripts and media features all behave differently there.

EXIT  0 every stage green (N-A counts as green)
      1 at least one FAIL
      2 bad usage / unreadable input
      3 nothing failed but the render-side stages could not run (no puppeteer):
        an UNVERIFIED cut, which the delivery message must SAY, never a pass
"""

import argparse
import functools
import json
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_manifest                                              # noqa: E402
import verify_all_structural as structural                            # noqa: E402
import verify_keyframe_grid                                           # noqa: E402
from genre_registry import DEFAULT_GENRE                              # noqa: E402
from manifest_shrink_gate import stage_result as shrink_row           # noqa: E402
from verify_all_json import dumps as json_envelope                    # noqa: E402
from verify_act_family import act_family_rows                        # noqa: E402
from verify_all_browser import run_stage_c, run_stage_e               # noqa: E402
from verify_all_camera import camera_holds, check_holds               # noqa: E402
from verify_all_report import FAIL, UNVERIFIED, bad, na, ok, render, worst   # noqa: E402


class _Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(directory):
    """(base_url, shutdown). Port 0 -- the OS picks a free one, so no port collisions."""
    handler = functools.partial(_Quiet, directory=str(directory))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{httpd.server_address[1]}", httpd.shutdown


def stage_a(manifest_path):
    errs = validate_manifest.validate(manifest_path)
    if errs:
        return [bad("A manifest", "validate", f"{len(errs)} error(s): {errs[0]}")]
    return [ok("A manifest", "validate", f"{Path(manifest_path).name} valid (schema 1)")] \
        + shrink_row(manifest_path)


def stage_b(html_text, manifest, target, genre=DEFAULT_GENRE):
    css = structural.styles(html_text)
    master = float((manifest.get("target") or {}).get("master_ms") or 0)
    results = []

    errs = structural.check_well_formed(html_text)
    results.append(bad("B structural", "well-formed", f"{len(errs)} problem(s): {errs[0]}")
                   if errs else ok("B structural", "well-formed", "every element closes in order"))

    errs, seen = structural.check_external_hosts(html_text, target)
    results.append(bad("B structural", "external-hosts", f"disallowed: {'; '.join(errs)}") if errs
                   else ok("B structural", "external-hosts",
                           f"target {target}; hosts {seen or ['(none)']}"))

    errs = structural.check_aria(html_text, genre)
    aria_ok = ('[process] <figure aria-label> per frame, aria-hidden edge overlay, narration'
               if genre == "process" else 'role="img" + <title> + <desc> present')
    results.append(bad("B structural", "aria", "; ".join(errs)) if errs
                   else ok("B structural", "aria", aria_ok))

    errs = structural.check_animation_properties(css)
    results.append(bad("B structural", "animation-props", f"{len(errs)}: {errs[0]}") if errs
                   else ok("B structural", "animation-props",
                           "no width/height/top/left animated or transitioned"))

    if not master:
        results.append(na("B structural", "master-divisors", "manifest declares no master_ms"))
    else:
        errs, notes = structural.check_master_divisors(css, master)
        suffix = f"; {len(notes)} unresolved var() duration(s)" if notes else ""
        results.append(bad("B structural", "master-divisors", f"{errs[0]}{suffix}") if errs
                       else ok("B structural", "master-divisors",
                               f"every animation-duration divides {master:g}ms{suffix}"))

    # The KEYFRAME half of the same rule: a duration that divides the master says
    # nothing about where the stops inside it land. Needs both times -- without a
    # beat_ms the cut declares no grid, so there is nothing to be right about.
    beat = float((manifest.get("target") or {}).get("beat_ms") or 0)
    if not master or not beat:
        results.append(na("B structural", "keyframe-grid",
                          "manifest declares no master_ms/beat_ms -- no grid to land on"))
    else:
        errs, notes, checked, exempted = verify_keyframe_grid.check_keyframe_stops(
            css, manifest)
        detail = (f"{len(checked)} hand-authored master-length block(s) "
                  f"{sorted(checked)}; {len(exempted)} exempt "
                  f"{sorted(exempted) or '(none)'}")
        if notes:
            detail += f"; {len(notes)} note(s): {notes[0]}"
        results.append(bad("B structural", "keyframe-grid",
                           f"{len(errs)}: {errs[0]}") if errs
                       else ok("B structural", "keyframe-grid",
                               f"every stop is an instant the manifest names -- {detail}"))
    # The act-identity family (ids, delta, ghosts, chip, lens, legend) -- manifest-gated.
    results += act_family_rows(html_text, manifest)
    return results


def run(html_path, manifest_path, base, target, no_browser=False):
    html_path, manifest_path = Path(html_path), Path(manifest_path)
    html_text = html_path.read_text(encoding="utf-8", errors="replace")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        manifest = {}
    features = set(manifest.get("features") or [])
    # ABSENT means system-design (references/output-manifest.md): every manifest
    # written before the field existed is a system-design cut, so the three frozen
    # goldens keep taking exactly the path they always took.
    genre = manifest.get("genre") or DEFAULT_GENRE
    url = f"{base.rstrip('/')}/{html_path.name}"

    results = stage_a(str(manifest_path))
    results += stage_b(html_text, manifest, target, genre)
    if no_browser:
        results.append(na("C browser", "all", "--no-browser: render-side stages skipped"))
    else:
        results += run_stage_c(url, features, genre, html_text)
    results += check_holds(manifest)
    if no_browser:
        results.append(na("E geometry", "hold-geometry", "--no-browser: skipped"))
    else:
        results += run_stage_e(url, manifest_path, features, camera_holds(manifest), genre)
    return results, url


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("html", help="the built diagram")
    ap.add_argument("--manifest", help="default: <stem>.manifest.json beside the HTML")
    ap.add_argument("--base", help="base URL the HTML is already served at")
    ap.add_argument("--serve", action="store_true",
                    help="spawn an http.server on a free port, rooted at the HTML's directory")
    ap.add_argument("--target", choices=("artifact", "local"), default="artifact",
                    help="external-host rule's runtime target; default artifact, the stricter")
    ap.add_argument("--no-browser", action="store_true",
                    help="stdlib stages only; C and E report N-A")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    html = Path(args.html)
    if not html.exists():
        print(f"BAD INPUT: {html} does not exist", file=sys.stderr)
        return 2
    manifest = Path(args.manifest) if args.manifest else html.with_suffix(".manifest.json")
    if not manifest.exists():
        print(f"BAD INPUT: no manifest at {manifest} (references/output-manifest.md: every "
              f"delivered diagram ships one)", file=sys.stderr)
        return 2
    if not args.base and not args.serve:
        print("BAD INPUT: pass --base <url> or --serve (never file://)", file=sys.stderr)
        return 2

    stop = None
    base = args.base
    if args.serve and not base:
        base, stop = serve(html.resolve().parent)
    try:
        results, url = run(html, manifest, base, args.target, args.no_browser)
    finally:
        if stop:
            stop()

    status = worst(results)
    code = 1 if status == FAIL else 3 if status == UNVERIFIED else 0
    if args.json:
        print(json_envelope(results, html, manifest, url, code))
        return code
    print(render(results, f"verify-all  {html.name}  ({url})"))
    if status == UNVERIFIED:
        print("\n" + "UNVERIFIED -- the render-side stages did not run. This cut is UNVERIFIED "
              "and the delivery message must say which checks were skipped and why.")
    return code


if __name__ == "__main__":
    sys.exit(main())
