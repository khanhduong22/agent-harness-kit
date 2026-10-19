#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage B of diagram-director/scripts/verify_all.py: everything provable from the FILE, stdlib only.

Six checks, each mechanising one pre-delivery-checklist item:

  well-formed        every element that opens closes, in order (html.parser)
  external-hosts     item 5 -- artifact target: fonts.googleapis/gstatic only;
                     local target: those plus the CDN URLs PINNED in
                     references/style-guides.md, read from that file so the list
                     has exactly one home
  aria               item 3 -- <svg role="img"> plus a <title> and a <desc>
  animation-props    item 9 -- no width/height/top/left animated or transitioned
  master-divisors    camera-beat.md -- every animation-duration divides master_ms

Stage B's SIXTH check, `keyframe-grid` (every STOP of a hand-authored master-length
@keyframes lands on an instant the manifest declares), lives in its own module:
verify_keyframe_grid.py. It is the one stage-B check that needs the MANIFEST as
well as the file, and it imports the CSS regexes and helpers below rather than
re-spelling them.

REGEX LIMITS, stated because they bound what a green means: the CSS is scanned with
regexes, not parsed. `var(--x)` is resolved from the file's own custom properties by
textual substitution (3 passes); a duration that is still a `var()` after that, or
that comes from an @media/@supports override of a custom property, is reported as
`unresolved` and does NOT fail the run. A shorthand `animation:` is read as
"first time token is the duration" -- which is the CSS rule, but a shorthand split
across a `var()` that carries two times would fool it. Anything this cannot see is
the browser stages' job, not this one's.
"""

import re
from html.parser import HTMLParser
from pathlib import Path

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}
ARTIFACT_HOSTS = {"fonts.googleapis.com", "fonts.gstatic.com"}
BANNED_ANIMATED = ("width", "height", "top", "left")
_URL_ATTR = re.compile(r"""(?:src|href)\s*=\s*["']([^"']+)["']""", re.I)
_CSS_URL = re.compile(r"""url\(\s*["']?([^"')]+)""", re.I)
_HOST = re.compile(r"^https?://([^/]+)", re.I)
_CUSTOM_PROP = re.compile(r"(--[A-Za-z0-9_-]+)\s*:\s*([^;{}]+)")
_VAR = re.compile(r"var\(\s*(--[A-Za-z0-9_-]+)\s*(?:,[^()]*)?\)")
_TIME = re.compile(r"(-?\d*\.?\d+)\s*(ms|s)\b")
_DECL = re.compile(r"([-a-zA-Z]+)\s*:\s*([^;{}]+)")


class _WellFormed(HTMLParser):
    """Tag stack. Mismatch or leftovers = malformed; that is the whole contract."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"</{tag}> at line {self.getpos()[0]} closes nothing")
            return
        open_tag, line = self.stack.pop()
        if open_tag != tag:
            self.errors.append(
                f"</{tag}> at line {self.getpos()[0]} closes <{open_tag}> opened at line {line}")


def check_well_formed(html_text):
    parser = _WellFormed()
    parser.feed(html_text)
    errs = list(parser.errors)
    errs += [f"<{tag}> opened at line {line} never closes" for tag, line in parser.stack]
    return errs


def styles(html_text):
    """Every <style> block plus every inline style="" attribute, concatenated."""
    blocks = re.findall(r"<style[^>]*>(.*?)</style>", html_text, re.S | re.I)
    inline = re.findall(r"""\sstyle\s*=\s*["']([^"']*)["']""", html_text, re.I)
    return "\n".join(blocks + inline)


def pinned_cdn_hosts(style_guides=None):
    """Hosts of the CDN URLs recorded in references/style-guides.md.

    The URLs live in that human-reviewed file per the repo's security rule; reading
    them back is how this check avoids becoming a second, drifting copy of the list.
    """
    path = Path(style_guides or Path(__file__).resolve().parents[1]
                / "references" / "style-guides.md")
    if not path.exists():
        return set(), []
    urls = re.findall(r"https?://[^\s\"'<>)]+", path.read_text(encoding="utf-8"))
    hosts, kept = set(), []
    for url in urls:
        match = _HOST.match(url)
        if match and "cdn" in url:
            hosts.add(match.group(1).lower())
            kept.append(url)
    return hosts, kept


def check_external_hosts(html_text, target, style_guides=None):
    """(violations, hosts_seen). `target` is `artifact` or `local`."""
    allowed = set(ARTIFACT_HOSTS)
    if target == "local":
        allowed |= pinned_cdn_hosts(style_guides)[0]
    seen, bad = {}, []
    for url in _URL_ATTR.findall(html_text) + _CSS_URL.findall(styles(html_text)):
        match = _HOST.match(url.strip())
        if not match:
            continue                      # relative, data:, blob: -- not an external host
        host = match.group(1).lower()
        seen.setdefault(host, url)
    for host, url in sorted(seen.items()):
        if host not in allowed:
            bad.append(f"{host} (target {target}; first seen {url[:70]})")
    return bad, sorted(seen)


def check_aria(html_text, genre="system-design"):
    """Item 3, per construction mode.

    `system-design` cuts ARE SVG documents, so the rule is unchanged:
    `role="img"` + <title> + <desc> on the root. A `process` cut is an HTML page
    whose stations are divs (references/genres/process.md -> HTML-mode contract),
    where that trio would be a lie: the only <svg> is the connector overlay, which
    is pure geometry and is `aria-hidden` ON PURPOSE. Its a11y contract is a
    <figure aria-label> per frame plus a narration element, so that is what gets
    checked. The default keeps every existing caller byte-identical.
    """
    if genre == "process":
        return _check_aria_html_mode(html_text)
    errs = []
    roots = re.findall(r"<svg\b[^>]*>", html_text, re.I)
    if not roots:
        return ["no <svg> element at all"]
    if not any(re.search(r"""role\s*=\s*["']img["']""", tag, re.I) for tag in roots):
        errs.append('no <svg> carries role="img"')
    if not re.search(r"<title\b", html_text, re.I):
        errs.append("no <title> element")
    if not re.search(r"<desc\b", html_text, re.I):
        errs.append("no <desc> element")
    return errs


def _check_aria_html_mode(html_text):
    """The `process` genre's three clauses, and nothing else."""
    errs = []
    figures = re.findall(r"<figure\b[^>]*>", html_text, re.I)
    if not figures:
        errs.append("no <figure> element -- an HTML-mode beat frame is a <figure>")
    elif not any(re.search(r"aria-label\s*=", tag, re.I) for tag in figures):
        errs.append("no <figure> carries an aria-label saying what the frame SHOWS")
    overlays = re.findall(r'<svg\b[^>]*class\s*=\s*["\'][^"\']*\bedges\b[^"\']*["\'][^>]*>',
                          html_text, re.I)
    if not overlays:
        errs.append('no <svg class="edges"> overlay -- the connector layer is missing')
    else:
        unhidden = [t for t in overlays if not re.search(r'aria-hidden\s*=\s*["\']true',
                                                         t, re.I)]
        if unhidden:
            errs.append(f'{len(unhidden)} <svg class="edges"> overlay(s) are not '
                        f'aria-hidden="true" -- geometry has nothing to announce')
    if not re.search(r"<figcaption\b", html_text, re.I) and \
       not re.search(r"data-narration\s*=", html_text, re.I):
        errs.append("no <figcaption> and no [data-narration] -- the beat-by-beat "
                    "narration must exist as text, not only as motion")
    return errs


def _keyframe_blocks(css):
    """(name, body) per @keyframes, brace-matched so nested percent blocks survive."""
    out = []
    for match in re.finditer(r"@keyframes\s+([-\w]+)\s*\{", css):
        depth, i = 1, match.end()
        while i < len(css) and depth:
            depth += (css[i] == "{") - (css[i] == "}")
            i += 1
        out.append((match.group(1), css[match.end():i - 1]))
    return out


def check_animation_properties(css):
    """Item 9: nothing that triggers layout may be animated or transitioned."""
    errs = []
    for name, body in _keyframe_blocks(css):
        for prop, _value in _DECL.findall(body):
            if prop.lower() in BANNED_ANIMATED:
                errs.append(f"@keyframes {name} animates {prop!r} (layout property)")
    for prop, value in _DECL.findall(css):
        low = prop.lower()
        if low in ("transition", "transition-property"):
            for word in re.split(r"[,\s]+", value.strip()):
                if word.lower() in BANNED_ANIMATED:
                    errs.append(f"{prop}: {value.strip()[:40]!r} transitions {word!r}")
    return errs


def _resolve_vars(text, table):
    for _ in range(3):
        new = _VAR.sub(lambda m: table.get(m.group(1), m.group(0)), text)
        if new == text:
            break
        text = new
    return text


def _ms(token):
    match = _TIME.fullmatch(token.strip())
    if not match:
        return None
    value = float(match.group(1))
    return value if match.group(2) == "ms" else value * 1000.0


def check_master_divisors(css, master_ms):
    """(violations, notes). Every animation-duration must divide the master exactly."""
    table = {name: value.strip() for name, value in _CUSTOM_PROP.findall(css)}
    errs, notes, seen = [], [], set()
    for prop, value in _DECL.findall(css):
        low = prop.lower()
        if low not in ("animation", "animation-duration"):
            continue
        resolved = _resolve_vars(value, table)
        for part in resolved.split(","):
            times = _TIME.findall(part)
            if not times:
                if "var(" in part:
                    note = f"{prop}: {part.strip()[:44]} -- duration unresolved"
                    if note not in notes:
                        notes.append(note)
                continue
            # CSS shorthand: the FIRST <time> is the duration, the second is the delay.
            number, unit = times[0]
            dur = _ms(f"{number}{unit}")
            if dur is None or dur <= 0 or dur in seen:
                continue
            seen.add(dur)
            if master_ms and abs(master_ms / dur - round(master_ms / dur)) > 1e-9:
                errs.append(f"{dur:g}ms does not divide master {master_ms:g}ms "
                            f"(in {prop}: {part.strip()[:40]})")
    return errs, notes
