#!/usr/bin/env python3
"""
Deterministic Agentic, Transport/Stack CVE, Robots, Hreflang & 2026 JSON-LD Checker.

Pure Python 3 stdlib (zero third-party dependencies, zero paid API keys), SSRF-safe
with strict IP/DNS validation and hop-by-hop redirect verification.

Inspired by AgriciDaniel/claude-seo (`agentic_check.py`, `transport_check.py`,
`page_checks.py`, `validate-schema.py`, and `url_safety.py`).

Inspects one or more live URLs for:
  (a) HTTP status, redirect chain, HSTS/CSP/X-Content-Type-Options & stack CVE fingerprinting
  (b) X-Robots-Tag header & <meta name="robots">
  (c) robots.txt AI crawler rules + IETF Content-Signal (RFC 9309 group scoping)
  (d) /llms.txt, /llms-full.txt, /.well-known/mcp.json, /.well-known/ai-catalog.json,
      RFC 8288 Link headers & Accept: text/markdown content negotiation
  (e) <link rel="canonical"> & hreflang validation (plus cross-URL reciprocity)
  (f) JSON-LD @graph parse validity, entity @id presence & 2024-2026 deprecated types

Usage:
    python3 agentic_and_schema_check.py <url> [<url2> ...] [--json] [--timeout 15]
"""

from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import ipaddress
import json
import os
import re
import socket
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import zlib
from contextlib import contextmanager
from html.parser import HTMLParser
from typing import Any, Iterator, Optional
from urllib.parse import unquote, urljoin, urlparse, urlunparse

MAX_BODY_BYTES = 2_000_000
MAX_REDIRECTS = 10
MAX_JSON_DEPTH = 64
ONE_YEAR_SEC = 31_536_000
USER_AGENT = (
    "Mozilla/5.0 (compatible; GEO-SEO-Auditor/2.6; +https://developers.google.com/search/docs)"
)

# ---------------------------------------------------------------------------
# SSRF & DNS-Rebinding Protection (pure stdlib port of url_safety.py)
# ---------------------------------------------------------------------------

_IPV4_OBFUSCATED_RE = re.compile(
    r"^(?:0x[0-9a-f]+|[0-9]+)(?:\.(?:0x[0-9a-f]+|[0-9]+)){0,3}$", re.IGNORECASE
)
_SHARED_ADDRESS_SPACE = ipaddress.ip_network("100.64.0.0/10")
_NAT64_WELL_KNOWN = ipaddress.ip_network("64:ff9b::/96")
_UNSAFE_IPV6_NETWORKS = tuple(
    ipaddress.ip_network(net)
    for net in (
        "::/96",
        "64:ff9b::/96",
        "64:ff9b:1::/48",
        "2001::/32",
        "2001:10::/28",
        "2001:20::/28",
        "2001:db8::/32",
        "2002::/16",
        "3fff::/20",
        "fc00::/7",
        "fe80::/10",
        "fec0::/10",
        "ff00::/8",
    )
)
_BLOCKED_HOSTNAMES = frozenset(
    {
        "localhost",
        "ip6-localhost",
        "ip6-loopback",
        "metadata",
        "metadata.goog",
        "metadata.google.internal",
        "metadata.azure.com",
        "metadata.ec2.internal",
        "metadata.oraclecloud.com",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
        "169.254.169.254",
        "100.100.100.200",
        "192.0.0.192",
        "fd00:ec2::254",
        "fd20:ce::254",
    }
)
_NEVER_ALLOWLISTABLE = frozenset(
    {
        "metadata",
        "metadata.goog",
        "metadata.google.internal",
        "metadata.azure.com",
        "metadata.ec2.internal",
        "metadata.oraclecloud.com",
        "169.254.169.254",
        "100.100.100.200",
        "192.0.0.192",
        "fd00:ec2::254",
        "fd20:ce::254",
        "0.0.0.0",
    }
)
_DNS_LOCK = threading.Lock()


class URLSafetyError(ValueError):
    """Raised when a URL or redirect hop fails SSRF/DNS-rebinding policy."""


def _raw_authority(url: str) -> str:
    match = re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://([^/?#]*)", url)
    return match.group(1) if match else ""


def _reject_authority_confusion(url: str, parsed: urllib.parse.ParseResult) -> None:
    auth = _raw_authority(url)
    auth_low = auth.lower()
    url_low = url.lower()
    if "\\" in auth or "%5c" in auth_low:
        raise URLSafetyError("URL authority contains a backslash")
    if "%" in auth:
        raise URLSafetyError("URL authority contains percent-encoding")
    if parsed.username is not None or parsed.password is not None or "@" in auth:
        raise URLSafetyError("URL userinfo is not allowed")
    if "#@" in url or "%23@" in url_low:
        raise URLSafetyError("URL fragment/userinfo confusion refused")


def normalize_hostname(hostname: str) -> str:
    if not hostname:
        raise URLSafetyError("Empty hostname")
    h = hostname.lower().strip()
    if h.endswith(".") and not h.endswith(".."):
        h = h[:-1]
    if _IPV4_OBFUSCATED_RE.match(h):
        try:
            packed = socket.inet_aton(h)
        except OSError as exc:
            raise URLSafetyError(f"Malformed IPv4 literal {hostname!r}: {exc}") from exc
        h = socket.inet_ntoa(packed)
    return h


def is_safe_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    if ip.version == 6:
        if ip.scope_id is not None:
            return False
        if ip.ipv4_mapped is not None:
            ip = ip.ipv4_mapped
        elif any(ip in net for net in _UNSAFE_IPV6_NETWORKS):
            return False
    return not (
        ip.is_private
        or (ip.version == 4 and ip in _SHARED_ADDRESS_SPACE)
        or ip.is_loopback
        or ip.is_reserved
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_unspecified
    )


def _is_allowlistable_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    if ip.version == 6 and ip.scope_id is not None:
        return False
    if ip.version == 6 and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    if ip.version == 6 and ip.sixtofour is not None:
        ip = ip.sixtofour
    if str(ip) in _NEVER_ALLOWLISTABLE:
        return False
    if ip.is_link_local or ip.is_multicast or ip.is_unspecified:
        return False
    if ip.is_loopback:
        return True
    return not ip.is_reserved


def _local_targets() -> tuple[tuple[str, Optional[int]], ...]:
    raw = (
        os.environ.get("GEO_SEO_LOCAL_TARGETS", "").strip()
        or os.environ.get("CLAUDE_SEO_LOCAL_TARGETS", "").strip()
    )
    if not raw:
        return ()
    out: list[tuple[str, Optional[int]]] = []
    for part in raw.split(","):
        entry = part.strip()
        if not entry:
            continue
        if entry.count(":") > 1 and "[" not in entry:
            cand, port = entry, None
        else:
            try:
                p = urlparse(f"//{entry}")
                cand, port = p.hostname or "", p.port
            except ValueError:
                continue
        if not cand:
            continue
        try:
            out.append((normalize_hostname(cand), port))
        except URLSafetyError:
            continue
    return tuple(out)


def _is_allowlisted_local_target(hostname: str, port: int) -> bool:
    if hostname in _NEVER_ALLOWLISTABLE:
        return False
    for entry_host, entry_port in _local_targets():
        if entry_host == hostname and (entry_port is None or entry_port == port):
            return True
    return False


def validate_url_strict(url: str, *, allow_local: bool = False) -> tuple[str, str, int, str]:
    """Validate URL + resolve DNS; return ``(url, normalized_host, port, pinned_ip)``."""
    try:
        parsed = urlparse(url)
    except ValueError as exc:
        raise URLSafetyError(f"Invalid URL: {exc}") from exc
    _reject_authority_confusion(url, parsed)
    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        raise URLSafetyError(f"Unsupported scheme: {scheme!r}")
    if not parsed.hostname:
        raise URLSafetyError("URL has no hostname")
    try:
        port = parsed.port or (443 if scheme == "https" else 80)
    except ValueError as exc:
        raise URLSafetyError(f"Invalid port: {exc}") from exc

    host = normalize_hostname(parsed.hostname)
    allowlisted = allow_local and _is_allowlisted_local_target(host, port)
    if host in _BLOCKED_HOSTNAMES and not allowlisted:
        raise URLSafetyError(f"Blocked hostname: {host}")

    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None

    if literal is not None:
        if not is_safe_ip(host) and not (allowlisted and _is_allowlistable_ip(host)):
            raise URLSafetyError(f"Blocked IP literal: {host}")
        return url, host, port, str(literal)

    try:
        infos = socket.getaddrinfo(host, port, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM)
    except (socket.gaierror, UnicodeError) as exc:
        raise URLSafetyError(f"DNS resolution failed for {host}: {exc}") from exc

    resolved_ips = sorted(
        {info[4][0] for info in infos if info[4]}, key=lambda ip: (":" in ip, ip)
    )
    if not resolved_ips:
        raise URLSafetyError(f"No DNS address records for {host}")

    has_ipv4 = ":" not in resolved_ips[0]
    accepted: list[str] = []
    for ip_str in resolved_ips:
        if is_safe_ip(ip_str):
            accepted.append(ip_str)
            continue
        if allowlisted and _is_allowlistable_ip(ip_str):
            accepted.append(ip_str)
            continue
        if has_ipv4:
            try:
                ip_obj = ipaddress.ip_address(ip_str)
                if ip_obj.version == 6 and ip_obj.scope_id is None and ip_obj in _NAT64_WELL_KNOWN:
                    continue
            except ValueError:
                pass
        raise URLSafetyError(f"DNS rebinding guard refused non-public IP {ip_str} for {host}")
    return url, host, port, accepted[0]


@contextmanager
def _pin_dns(target_host: str, pinned_ip: str, target_port: int) -> Iterator[None]:
    """Pin ``socket.getaddrinfo`` to ``pinned_ip`` during direct HTTP connection."""
    if not _DNS_LOCK.acquire(timeout=5.0):
        raise URLSafetyError("Timed out acquiring DNS pin lock")
    orig_getaddrinfo = socket.getaddrinfo
    is_v6 = ":" in pinned_ip
    family = socket.AF_INET6 if is_v6 else socket.AF_INET
    sockaddr: Any = (pinned_ip, target_port, 0, 0) if is_v6 else (pinned_ip, target_port)

    def pinned_getaddrinfo(
        host: Any,
        port: Any,
        fam: int = 0,
        socktype: int = 0,
        proto: int = 0,
        flags: int = 0,
    ) -> list[Any]:
        h_str = host.decode("ascii", "ignore") if isinstance(host, bytes) else str(host or "")
        try:
            norm = normalize_hostname(h_str)
        except URLSafetyError:
            norm = h_str.lower()
        if norm != target_host:
            raise socket.gaierror(f"Unexpected DNS lookup during pinned request: {h_str}")
        if fam not in (socket.AF_UNSPEC, 0, family):
            raise socket.gaierror("Address family mismatch for pinned IP")
        req_port = int(port) if port else target_port
        sa: Any = (pinned_ip, req_port, 0, 0) if is_v6 else (pinned_ip, req_port)
        return [(family, socktype or socket.SOCK_STREAM, proto or 6, "", sa)]

    socket.getaddrinfo = pinned_getaddrinfo  # type: ignore[assignment]
    try:
        yield
    finally:
        socket.getaddrinfo = orig_getaddrinfo
        _DNS_LOCK.release()


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


_NO_REDIRECT_OPENER = urllib.request.build_opener(_NoRedirectHandler())


def _decode_http_bytes(raw: bytes, headers: dict[str, list[str]]) -> str:
    encoding = ", ".join(headers.get("content-encoding", [])).lower()
    data = raw
    if "gzip" in encoding:
        try:
            data = gzip.decompress(raw)
        except OSError:
            data = raw
    elif "deflate" in encoding:
        try:
            data = zlib.decompress(raw)
        except zlib.error:
            try:
                data = zlib.decompress(raw, -zlib.MAX_WBITS)
            except zlib.error:
                data = raw
    ctype = ", ".join(headers.get("content-type", []))
    m = re.search(r"charset\s*=\s*['\"]?([A-Za-z0-9_.:-]+)", ctype, re.I)
    charset = m.group(1) if m else "utf-8"
    try:
        text = data.decode(charset, errors="replace")
    except LookupError:
        text = data.decode("utf-8", errors="replace")
    return text.lstrip("\ufeff")


def _headers_to_multimap(msg: Any) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    if msg is None:
        return out
    for k, v in msg.items():
        out.setdefault(str(k).lower(), []).append(str(v))
    return out


def safe_fetch(
    url: str,
    *,
    headers: Optional[dict[str, str]] = None,
    timeout: float = 15.0,
    allow_local_first_hop: bool = True,
) -> dict[str, Any]:
    """Fetch ``url`` safely, validating initial URL and every redirect hop."""
    req_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
    }
    if headers:
        req_headers.update(headers)

    current_url = url
    redirect_chain: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for hop_idx in range(MAX_REDIRECTS + 1):
        try:
            validated_url, host, port, pinned_ip = validate_url_strict(
                current_url, allow_local=(hop_idx == 0 and allow_local_first_hop)
            )
        except URLSafetyError as exc:
            return {
                "url": url,
                "final_url": current_url,
                "status_code": None,
                "redirect_chain": redirect_chain,
                "headers": {},
                "text": "",
                "raw_bytes_len": 0,
                "error": f"url_safety: {exc}",
            }

        req = urllib.request.Request(validated_url, headers=req_headers, method="GET")
        status: Optional[int] = None
        hdrs: dict[str, list[str]] = {}
        raw_body = b""
        try:
            with _pin_dns(host, pinned_ip, port):
                with _NO_REDIRECT_OPENER.open(req, timeout=timeout) as resp:
                    status = int(resp.status)
                    hdrs = _headers_to_multimap(resp.headers)
                    raw_body = resp.read(MAX_BODY_BYTES + 1)
        except urllib.error.HTTPError as exc:
            status = int(exc.code)
            hdrs = _headers_to_multimap(exc.headers)
            if status in (301, 302, 303, 307, 308):
                loc = (hdrs.get("location") or [""])[0].strip()
                if not loc:
                    return {
                        "url": url,
                        "final_url": validated_url,
                        "status_code": status,
                        "redirect_chain": redirect_chain,
                        "headers": hdrs,
                        "text": "",
                        "raw_bytes_len": 0,
                        "error": f"Redirect HTTP {status} missing Location header",
                    }
                next_url = urljoin(validated_url, loc)
                redirect_chain.append(
                    {
                        "url": validated_url,
                        "status": status,
                        "location": next_url,
                        "has_hsts": "strict-transport-security" in hdrs,
                    }
                )
                if next_url in seen_urls:
                    return {
                        "url": url,
                        "final_url": validated_url,
                        "status_code": status,
                        "redirect_chain": redirect_chain,
                        "headers": hdrs,
                        "text": "",
                        "raw_bytes_len": 0,
                        "error": "Redirect loop detected",
                    }
                seen_urls.add(validated_url)
                current_url = next_url
                continue
            try:
                raw_body = exc.read(MAX_BODY_BYTES + 1)
            except Exception:
                raw_body = b""
        except URLSafetyError as exc:
            return {
                "url": url,
                "final_url": validated_url,
                "status_code": None,
                "redirect_chain": redirect_chain,
                "headers": {},
                "text": "",
                "raw_bytes_len": 0,
                "error": f"url_safety: {exc}",
            }
        except Exception as exc:
            return {
                "url": url,
                "final_url": validated_url,
                "status_code": None,
                "redirect_chain": redirect_chain,
                "headers": {},
                "text": "",
                "raw_bytes_len": 0,
                "error": f"{type(exc).__name__}: {str(exc)[:220]}",
            }

        truncated = len(raw_body) > MAX_BODY_BYTES
        text = _decode_http_bytes(raw_body[:MAX_BODY_BYTES], hdrs)
        return {
            "url": url,
            "final_url": validated_url,
            "status_code": status,
            "redirect_chain": redirect_chain,
            "headers": hdrs,
            "text": text,
            "raw_bytes_len": len(raw_body[:MAX_BODY_BYTES]),
            "truncated": truncated,
            "error": None,
        }

    return {
        "url": url,
        "final_url": current_url,
        "status_code": None,
        "redirect_chain": redirect_chain,
        "headers": {},
        "text": "",
        "raw_bytes_len": 0,
        "error": f"Exceeded maximum {MAX_REDIRECTS} redirects",
    }


# ---------------------------------------------------------------------------
# HTML Parsing & URL Canonicalization
# ---------------------------------------------------------------------------


class _PageParser(HTMLParser):
    """Lightweight stdlib HTML extractor for SEO, Agentic & JSON-LD signals."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.html_lang: Optional[str] = None
        self.base_href: Optional[str] = None
        self.titles: list[str] = []
        self.meta_tags: list[dict[str, str]] = []
        self.link_tags: list[dict[str, Any]] = []
        self.h1s: list[str] = []
        self.jsonld_blocks: list[str] = []
        self.forms: list[dict[str, Any]] = []
        self.inline_scripts: list[str] = []
        self.visible_chunks: list[str] = []
        self.js_shell_div_ids: list[str] = []

        self._in_title = False
        self._title_buf: list[str] = []
        self._in_h1 = False
        self._h1_buf: list[str] = []
        self._in_jsonld = False
        self._jsonld_buf: list[str] = []
        self._in_script = False
        self._script_buf: list[str] = []
        self._in_svg = 0
        self._skip_depth = 0
        self._div_stack: list[tuple[Optional[str], bool]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        t = tag.lower()
        attr_map = {k.lower(): (v if v is not None else "") for k, v in attrs}
        if t == "svg":
            self._in_svg += 1
        if t in ("script", "style", "noscript", "template", "svg"):
            self._skip_depth += 1

        if t == "html" and self.html_lang is None:
            if "lang" in attr_map and attr_map["lang"].strip():
                self.html_lang = attr_map["lang"].strip()
        elif t == "base" and self.base_href is None and attr_map.get("href"):
            self.base_href = attr_map["href"].strip()
        elif t == "title" and self._in_svg == 0:
            self._in_title = True
            self._title_buf = []
        elif t == "h1":
            self._in_h1 = True
            self._h1_buf = []
        elif t == "meta":
            self.meta_tags.append(attr_map)
        elif t == "link":
            rels = [r.lower() for r in attr_map.get("rel", "").split() if r]
            self.link_tags.append({**attr_map, "rels": rels})
        elif t == "form":
            self.forms.append(
                {
                    "id": attr_map.get("id", ""),
                    "name": attr_map.get("name", ""),
                    "action": attr_map.get("action", ""),
                    "toolname": attr_map.get("toolname", ""),
                    "tooldescription": attr_map.get("tooldescription", ""),
                }
            )
        elif t == "div":
            div_id = attr_map.get("id", "")
            is_shell = div_id.lower() in ("root", "app", "__next", "__nuxt")
            self._div_stack.append((div_id if is_shell else None, False))
        elif t == "script":
            stype = attr_map.get("type", "").lower()
            if "ld+json" in stype:
                self._in_jsonld = True
                self._jsonld_buf = []
            elif not attr_map.get("src"):
                self._in_script = True
                self._script_buf = []

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t == "svg" and self._in_svg > 0:
            self._in_svg -= 1
        if t in ("script", "style", "noscript", "template", "svg") and self._skip_depth > 0:
            self._skip_depth -= 1

        if t == "title" and self._in_title:
            self._in_title = False
            txt = re.sub(r"\s+", " ", "".join(self._title_buf)).strip()
            if txt:
                self.titles.append(txt)
        elif t == "h1" and self._in_h1:
            self._in_h1 = False
            txt = re.sub(r"\s+", " ", "".join(self._h1_buf)).strip()
            if txt:
                self.h1s.append(txt)
        elif t == "script" and self._in_jsonld:
            self._in_jsonld = False
            raw = "".join(self._jsonld_buf).strip()
            if raw:
                self.jsonld_blocks.append(raw)
        elif t == "script" and self._in_script:
            self._in_script = False
            raw = "".join(self._script_buf).strip()
            if raw:
                self.inline_scripts.append(raw)
        elif t == "div" and self._div_stack:
            shell_id, has_text = self._div_stack.pop()
            if shell_id and not has_text:
                self.js_shell_div_ids.append(shell_id)

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_buf.append(data)
        if self._in_h1:
            self._h1_buf.append(data)
        if self._in_jsonld:
            self._jsonld_buf.append(data)
        if self._in_script:
            self._script_buf.append(data)
        if self._skip_depth == 0:
            stripped = data.strip()
            if stripped:
                self.visible_chunks.append(stripped)
                if self._div_stack:
                    sid, _ = self._div_stack[-1]
                    self._div_stack[-1] = (sid, True)


def _first_hdr(headers: dict[str, list[str]], key: str) -> Optional[str]:
    vals = headers.get(key.lower())
    return ", ".join(vals) if vals else None


def url_match_key(url: str) -> str:
    """Normalize URL for canonical/hreflang equality (ignore trailing slash & UTM)."""
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return url
    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https") or not parsed.hostname:
        return url
    host = parsed.hostname.lower().rstrip(".")
    port = parsed.port
    default_port = 443 if scheme == "https" else 80
    netloc = f"{host}:{port}" if port and port != default_port else host
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/") or "/"
    tracking = {"fbclid", "gclid", "mc_cid", "mc_eid", "_ga", "ref"}
    kept = [
        q
        for q in parsed.query.split("&")
        if q and not (unquote(q.split("=", 1)[0]).lower().startswith("utm_") or unquote(q.split("=", 1)[0]).lower() in tracking)
    ]
    return urlunparse((scheme, netloc, path, "", "&".join(kept), ""))


def parse_link_header(values: list[str]) -> list[dict[str, Any]]:
    """RFC 8288 Link header parser."""
    out: list[dict[str, Any]] = []
    for raw_hdr in values:
        for match in re.finditer(r"<([^<>]*)>([^,<]*)", raw_hdr or ""):
            params: dict[str, str] = {}
            for p in re.finditer(r';\s*([a-zA-Z*-]+)\s*=\s*("([^"]*)"|[^;,\s]+)', match.group(2)):
                params[p.group(1).lower()] = p.group(3) if p.group(3) is not None else p.group(2)
            out.append(
                {
                    "uri": match.group(1).strip(),
                    "rel": [r.lower() for r in params.get("rel", "").split()],
                    "type": params.get("type", "").lower(),
                    "hreflang": params.get("hreflang", ""),
                }
            )
    return out


# ---------------------------------------------------------------------------
# (a) Security Headers & Passive Stack CVE Fingerprinting
# ---------------------------------------------------------------------------

_REFERRER_POLICIES = frozenset(
    {
        "no-referrer",
        "no-referrer-when-downgrade",
        "origin",
        "origin-when-cross-origin",
        "same-origin",
        "strict-origin",
        "strict-origin-when-cross-origin",
        "unsafe-url",
    }
)
_PHP_FIXED_VERSIONS = {
    (8, 5): (8, 5, 12),
    (8, 4): (8, 4, 27),
    (8, 3): (8, 3, 36),
    (8, 2): (8, 2, 35),
}


def _parse_csp(value: str) -> dict[str, list[str]]:
    directives: dict[str, list[str]] = {}
    for chunk in value.split(";"):
        tokens = chunk.strip().split()
        if tokens:
            directives.setdefault(tokens[0].lower(), [t.lower() for t in tokens[1:]])
    return directives


def _grade_security_headers(headers: dict[str, list[str]], https: bool) -> dict[str, Any]:
    hsts_raw = _first_hdr(headers, "strict-transport-security")
    hsts: dict[str, Any] = {
        "present": hsts_raw is not None,
        "value": hsts_raw[:200] if hsts_raw else None,
        "max_age": None,
        "include_subdomains": False,
        "preload": False,
        "meets_preload_header_requirements": False,
        "issues": [],
    }
    if hsts_raw is None:
        if https:
            hsts["issues"].append("Missing Strict-Transport-Security header on HTTPS response.")
    else:
        directives: dict[str, str] = {}
        dup = False
        for part in hsts_raw.split(",")[0].split(";"):
            k, _, v = part.strip().partition("=")
            kl = k.strip().lower()
            if kl in directives:
                dup = True
                hsts["issues"].append("Duplicate HSTS directives invalidate the header.")
                break
            if kl:
                directives[kl] = v.strip().strip('"')
        if not dup:
            ma = directives.get("max-age", "")
            hsts["max_age"] = int(ma) if ma.isascii() and ma.isdigit() else None
            hsts["include_subdomains"] = "includesubdomains" in directives
            hsts["preload"] = "preload" in directives
            if hsts["max_age"] is None or hsts["max_age"] == 0:
                hsts["issues"].append("HSTS max-age is missing or 0 (disabled).")
            elif hsts["max_age"] < ONE_YEAR_SEC:
                hsts["issues"].append("HSTS max-age is below 31536000s (1 year).")
            if not hsts["include_subdomains"]:
                hsts["issues"].append("HSTS missing includeSubDomains.")
            hsts["meets_preload_header_requirements"] = (
                (hsts["max_age"] or 0) >= ONE_YEAR_SEC
                and hsts["include_subdomains"]
                and hsts["preload"]
            )

    enforced_csp = _first_hdr(headers, "content-security-policy")
    report_csp = _first_hdr(headers, "content-security-policy-report-only")
    csp_policy = enforced_csp if enforced_csp is not None else report_csp
    csp: dict[str, Any] = {
        "present": enforced_csp is not None,
        "report_only": enforced_csp is None and report_csp is not None,
        "issues": [],
    }
    if csp_policy is None:
        csp["issues"].append("Missing Content-Security-Policy header.")
    else:
        if csp["report_only"]:
            csp["issues"].append("CSP is Report-Only (not enforced).")
        parsed_csp = _parse_csp(csp_policy.split(",")[0])
        script_key = next((k for k in ("script-src", "default-src") if k in parsed_csp), None)
        if script_key is None:
            csp["issues"].append("CSP lacks script-src and default-src.")
        else:
            vals = parsed_csp[script_key]
            if "'unsafe-eval'" in vals:
                csp["issues"].append(f"'unsafe-eval' allowed in {script_key}.")
            strict = any(s.startswith(("'nonce-", "'sha256-", "'sha384-", "'sha512-")) for s in vals)
            if "'unsafe-inline'" in vals and not strict:
                csp["issues"].append(f"'unsafe-inline' without nonce/hash in {script_key}.")
            for loose in ("*", "https:", "http:", "data:"):
                if loose in vals:
                    csp["issues"].append(f"Overly broad source {loose!r} in {script_key}.")
        if "object-src" not in parsed_csp and parsed_csp.get("default-src") != ["'none'"]:
            csp["issues"].append("CSP missing object-src restriction.")
        if "base-uri" not in parsed_csp:
            csp["issues"].append("CSP missing base-uri restriction.")

    nosniff = _first_hdr(headers, "x-content-type-options")
    xfo = _first_hdr(headers, "x-frame-options")
    frame_ancestors = bool(enforced_csp and "frame-ancestors" in _parse_csp(enforced_csp.split(",")[0]))
    framing_ok = frame_ancestors or (xfo is not None and xfo.strip().upper() in ("DENY", "SAMEORIGIN"))
    ref_pol = _first_hdr(headers, "referrer-policy")
    ref_tokens = [t.strip().lower() for t in (ref_pol or "").split(",") if t.strip().lower() in _REFERRER_POLICIES]
    ref_effective = ref_tokens[-1] if ref_tokens else None

    cookies_summary: list[dict[str, Any]] = []
    for raw_cookie in (headers.get("set-cookie") or [])[:40]:
        parts = [p.strip() for p in raw_cookie.split(";")]
        cname = parts[0].split("=", 1)[0].strip() if "=" in parts[0] else "(unnamed)"
        attrs = {p.partition("=")[0].strip().lower(): p.partition("=")[2].strip() for p in parts[1:]}
        cookies_summary.append(
            {
                "name": cname[:80],
                "secure": "secure" in attrs,
                "http_only": "httponly" in attrs,
                "same_site": attrs.get("samesite"),
            }
        )

    return {
        "hsts": hsts,
        "csp": csp,
        "x_content_type_options": {
            "present": nosniff is not None,
            "value": nosniff[:60] if nosniff else None,
            "ok": nosniff is not None and nosniff.strip().lower() == "nosniff",
        },
        "framing": {
            "x_frame_options": xfo[:60] if xfo else None,
            "frame_ancestors": frame_ancestors,
            "ok": framing_ok,
        },
        "referrer_policy": {
            "present": ref_pol is not None,
            "value": ref_pol[:120] if ref_pol else None,
            "ok": ref_effective is not None and ref_effective != "unsafe-url",
        },
        "permissions_policy_present": "permissions-policy" in headers,
        "cookies": cookies_summary,
    }


def _detect_stack_exposure(
    headers: dict[str, list[str]], html: str, parser: _PageParser
) -> dict[str, Any]:
    banner_headers = {}
    for hname in (
        "server",
        "x-powered-by",
        "x-aspnet-version",
        "x-aspnetmvc-version",
        "x-generator",
        "via",
        "x-runtime",
        "cf-ray",
        "x-vercel-id",
        "x-netlify-request-id",
    ):
        val = _first_hdr(headers, hname)
        if val:
            banner_headers[hname] = val[:160]

    cookie_names = [
        raw.split(";", 1)[0].split("=", 1)[0].strip()
        for raw in (headers.get("set-cookie") or [])
        if "=" in raw
    ]
    generators = [
        m.get("content", "")[:120]
        for m in parser.meta_tags
        if m.get("name", "").lower() == "generator" and m.get("content")
    ]
    link_raw = " ".join(headers.get("link", []))
    wp_signals = bool(
        "api.w.org" in link_raw
        or any("wordpress" in g.lower() for g in generators)
        or "wp-content/" in html
        or "wp-includes/" in html
    )
    php_signals: list[str] = []
    php_version: Optional[str] = None
    xpb = banner_headers.get("x-powered-by", "")
    m_php = re.search(r"\bPHP/(\d+\.\d+(?:\.\d+)?)", xpb, re.I)
    if m_php:
        php_version = m_php.group(1)
        php_signals.append(f"X-Powered-By: PHP/{php_version}")
    elif "php" in xpb.lower():
        php_signals.append(f"X-Powered-By: {xpb}")
    if any(c.upper() == "PHPSESSID" for c in cookie_names):
        php_signals.append("Set-Cookie: PHPSESSID")
    if wp_signals:
        php_signals.append("WordPress signals detected")

    php_cve_status = "none"
    php_cve_note: Optional[str] = None
    if php_version:
        parts = tuple(int(x) for x in php_version.split("."))
        ver_tuple = parts + (0,) * (3 - len(parts))
        major_minor = (ver_tuple[0], ver_tuple[1])
        if major_minor in _PHP_FIXED_VERSIONS:
            fixed = _PHP_FIXED_VERSIONS[major_minor]
            if ver_tuple[:3] < fixed:
                php_cve_status = "high_likely_exposed"
                php_cve_note = (
                    f"PHP/{php_version} is below fixed {'.'.join(map(str, fixed))} "
                    "(CVE-2026-109618 / CVE-2026-109619); confirm OS backport or upgrade."
                )
            else:
                php_cve_status = "patched_version_string"
        elif major_minor < (8, 2):
            php_cve_status = "high_eol_branch"
            php_cve_note = (
                f"PHP/{php_version} is EOL (<8.2); confirm distro backport for CVE-2026-109618/109619."
            )
    elif php_signals:
        php_cve_status = "info_php_detected_version_unknown"
        php_cve_note = "PHP signals detected without version banner; verify patch level (>=8.5.12/8.4.27/8.3.36/8.2.35)."

    version_leaks = [
        f"{k}: {v}"
        for k, v in banner_headers.items()
        if k in ("server", "x-powered-by", "x-aspnet-version", "x-generator")
        and re.search(r"/\d+\.\d+", v)
    ]
    if generators:
        version_leaks.extend(f"meta generator: {g}" for g in generators)

    node_static_markers = [
        marker
        for marker in ("_next/static", "__NEXT_DATA__", "astro-island", "/_astro/")
        if marker in html
    ]

    return {
        "headers_exposed": banner_headers,
        "generators": generators,
        "stack_markers": node_static_markers + (["WordPress"] if wp_signals else []),
        "version_fingerprint_leaks": version_leaks,
        "php_cve_2026_109618_status": php_cve_status,
        "php_cve_note": php_cve_note,
    }


# ---------------------------------------------------------------------------
# (b) X-Robots-Tag & <meta name="robots">
# ---------------------------------------------------------------------------

_ROBOTS_VALUED = ("max-snippet", "max-image-preview", "max-video-preview", "unavailable_after")
_CRAWLER_NAME_RE = re.compile(r"[a-z][a-z0-9_.-]*")


def _parse_robots_directives(value: str) -> list[tuple[str, str]]:
    rules: list[tuple[str, str]] = []
    agent = ""
    for part in (value or "").lower().split(","):
        name, sep, rest = (p.strip() for p in part.partition(":"))
        if sep and name not in _ROBOTS_VALUED and _CRAWLER_NAME_RE.fullmatch(name):
            agent = name
            name, sep, rest = (p.strip() for p in rest.partition(":"))
        if not sep:
            rules.extend((agent, w) for w in name.split())
    return rules


def _analyze_page_robots(headers: dict[str, list[str]], parser: _PageParser) -> dict[str, Any]:
    x_raw = headers.get("x-robots-tag", [])
    meta_raw = [
        (m.get("name", "").lower(), m.get("content", ""))
        for m in parser.meta_tags
        if m.get("name", "").lower() in ("robots", "googlebot") and m.get("content")
    ]
    header_rules = [r for val in x_raw for r in _parse_robots_directives(val)]
    meta_rules: list[tuple[str, str]] = []
    for n, val in meta_raw:
        for agent, d in _parse_robots_directives(val):
            eff_agent = agent or ("" if n == "robots" else n)
            meta_rules.append((eff_agent, d))

    general_hdr = {d for a, d in header_rules if a in ("", "googlebot")}
    general_meta = {d for a, d in meta_rules if a in ("", "googlebot")}
    return {
        "x_robots_tag": x_raw,
        "meta_robots": [{"name": n, "content": c} for n, c in meta_raw],
        "header_noindex": bool(general_hdr & {"noindex", "none"}),
        "meta_noindex": bool(general_meta & {"noindex", "none"}),
        "noindex": bool((general_hdr | general_meta) & {"noindex", "none"}),
        "nofollow": bool((general_hdr | general_meta) & {"nofollow", "none"}),
        "other_agent_rules": sorted({f"{a}: {d}" for a, d in header_rules + meta_rules if a not in ("", "googlebot")}),
    }


# ---------------------------------------------------------------------------
# (c) robots.txt AI Crawlers + Content-Signal (RFC 9309)
# ---------------------------------------------------------------------------

AI_AGENTS = [
    ("GPTBot", "OpenAI", "training", "honours"),
    ("OAI-SearchBot", "OpenAI", "search", "honours"),
    ("ChatGPT-User", "OpenAI", "user", "may not apply"),
    ("ClaudeBot", "Anthropic", "training", "honours"),
    ("Claude-SearchBot", "Anthropic", "search", "honours"),
    ("Claude-User", "Anthropic", "user", "honours"),
    ("PerplexityBot", "Perplexity", "search", "honours"),
    ("Perplexity-User", "Perplexity", "user", "generally ignores"),
    ("Google-Extended", "Google", "control", "honours"),
    ("Google-Agent", "Google", "user", "generally ignores"),
    ("Applebot-Extended", "Apple", "control", "honours"),
    ("CCBot", "Common Crawl", "training", "honours"),
    ("Googlebot", "Google", "search-core", "honours"),
    ("Bingbot", "Microsoft", "search-core", "honours"),
]
_LINE_BREAK = re.compile(r"\r\n|\n|\r")
_PRODUCT_TOKEN = re.compile(r"[A-Za-z_-]+")
_STAR_RUN = re.compile(r"\*{2,}")
_CONTENT_SIGNAL_KEYS = {"search", "ai-input", "ai-train"}
_CONTENT_SIGNAL_EXP = {"use": {"immediate", "reference", "full"}}


def _parse_robots_txt(text: str) -> dict[str, Any]:
    groups: list[dict[str, Any]] = []
    sitemaps: list[str] = []
    agentmaps: list[str] = []
    orphan_signals: list[str] = []
    current: Optional[dict[str, Any]] = None
    last_was_ua = False
    for raw in _LINE_BREAK.split(text.lstrip("\ufeff")):
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, val = (p.strip() for p in line.split(":", 1))
        fl = field.lower()
        if fl == "user-agent":
            if current is None or not last_was_ua:
                current = {"agents": [], "rules": [], "content_signal": []}
                groups.append(current)
            current["agents"].append(val)
            last_was_ua = True
            continue
        last_was_ua = False
        if fl == "sitemap":
            sitemaps.append(val)
        elif fl == "agentmap":
            agentmaps.append(val)
        elif current is None:
            if fl == "content-signal":
                orphan_signals.append(val)
        elif fl in ("allow", "disallow"):
            current["rules"].append((fl, val))
        elif fl == "content-signal":
            current["content_signal"].append(val)
    return {
        "groups": groups,
        "sitemaps": sitemaps,
        "agentmaps": agentmaps,
        "orphan_content_signal": orphan_signals,
    }


def _product_token(val: str) -> str:
    v = (val or "").strip()
    if v == "*":
        return "*"
    m = _PRODUCT_TOKEN.match(v)
    return m.group(0).lower() if m else ""


def _pattern_matches(pattern: str, path: str = "/") -> bool:
    anchored = pattern.endswith("$")
    body = pattern[:-1] if anchored else pattern
    if "*" not in body:
        return path == body if anchored else path.startswith(body)
    first, *middle, last = _STAR_RUN.sub("*", body).split("*")
    if not path.startswith(first):
        return False
    pos = len(first)
    for piece in middle:
        idx = path.find(piece, pos)
        if idx < 0:
            return False
        pos = idx + len(piece)
    if anchored:
        return len(path) - len(last) >= pos and path.endswith(last)
    return path.find(last, pos) >= 0


def _is_root_allowed(rules: list[tuple[str, str]]) -> bool:
    best_len, allowed = -1, True
    for field, val in rules:
        if field == "disallow" and val == "":
            continue
        if _pattern_matches(val, "/"):
            ln = len(val)
            if ln > best_len or (ln == best_len and field == "allow"):
                best_len, allowed = ln, field == "allow"
    return allowed


def _parse_content_signal(val: str) -> dict[str, Any]:
    signals: dict[str, str] = {}
    issues: list[str] = []
    for part in val.split(","):
        p = part.strip()
        if not p:
            continue
        if "=" not in p:
            issues.append(f"malformed entry {p!r}")
            continue
        k, v = (s.strip().lower() for s in p.split("=", 1))
        signals[k] = v
        if k in _CONTENT_SIGNAL_EXP:
            if v not in _CONTENT_SIGNAL_EXP[k]:
                issues.append(f"invalid experimental value {k}={v}")
        elif k not in _CONTENT_SIGNAL_KEYS:
            issues.append(f"unknown key {k!r}")
        elif v not in ("yes", "no"):
            issues.append(f"value for {k!r} must be yes/no")
    return {"signals": signals, "issues": issues}


def audit_robots_txt(site_root: str, timeout: float) -> dict[str, Any]:
    rec = safe_fetch(f"{site_root}/robots.txt", timeout=timeout)
    status = rec["status_code"]
    if rec["error"] or status is None:
        return {"url": f"{site_root}/robots.txt", "status": status, "reachable": False, "error": rec["error"]}
    if status == 429:
        return {
            "url": f"{site_root}/robots.txt",
            "status": 429,
            "reachable": False,
            "inconclusive": True,
            "note": "HTTP 429 rate-limited; crawlers treat as temporary server error, not 'all allowed'.",
        }
    if status >= 500:
        return {
            "url": f"{site_root}/robots.txt",
            "status": status,
            "reachable": False,
            "note": "HTTP 5xx causes compliant crawlers to treat the entire site as disallowed.",
        }
    if status >= 400:
        return {
            "url": f"{site_root}/robots.txt",
            "status": status,
            "reachable": False,
            "note": "No robots.txt (4xx); all crawlers allowed by default, no Content-Signal declared.",
        }

    parsed = _parse_robots_txt(rec["text"])
    star_groups = [g for g in parsed["groups"] if any(_product_token(a) == "*" for a in g["agents"])]
    star_has_cs = any(g["content_signal"] for g in star_groups)
    agents_eval: list[dict[str, Any]] = []
    cs_group_gap: list[str] = []

    for token, vendor, role, behaviour in AI_AGENTS:
        tl = token.lower()
        named = [g for g in parsed["groups"] if any(_product_token(a) == tl for a in g["agents"])]
        chosen = named or star_groups
        rules = [r for g in chosen for r in g["rules"]]
        cs_lines = [c for g in chosen for c in g["content_signal"]]
        if named and not cs_lines and star_has_cs:
            cs_group_gap.append(token)
        agents_eval.append(
            {
                "token": token,
                "vendor": vendor,
                "role": role,
                "group": "named" if named else ("star" if star_groups else "none"),
                "root_allowed": _is_root_allowed(rules),
                "robots_behaviour": behaviour,
                "content_signal": cs_lines,
            }
        )

    all_cs = [c for g in parsed["groups"] for c in g["content_signal"]]
    cs_parsed = [_parse_content_signal(c) for c in all_cs + parsed["orphan_content_signal"]]
    cs_issues = [iss for item in cs_parsed for iss in item["issues"]]
    nonstandard_ua = sorted(
        {
            a
            for g in parsed["groups"]
            for a in g["agents"]
            if a != "*" and not _PRODUCT_TOKEN.fullmatch(a)
        }
    )

    return {
        "url": f"{site_root}/robots.txt",
        "status": status,
        "reachable": True,
        "cloudflare_managed": "# begin cloudflare managed content" in rec["text"].lower(),
        "sitemaps": parsed["sitemaps"],
        "agentmaps": parsed["agentmaps"],
        "nonstandard_user_agent_lines": nonstandard_ua,
        "content_signal": {
            "declared": bool(all_cs or parsed["orphan_content_signal"]),
            "group_lines": all_cs,
            "parsed_signals": [item["signals"] for item in cs_parsed if item["signals"]],
            "orphan_outside_group": parsed["orphan_content_signal"],
            "named_groups_missing_signal_from_star": cs_group_gap,
            "issues": cs_issues,
        },
        "agents": agents_eval,
    }


# ---------------------------------------------------------------------------
# (d) /llms.txt, /llms-full.txt, /.well-known/mcp.json, ARD, RFC 8288, Markdown
# ---------------------------------------------------------------------------


def _json_depth_exceeds(raw: str, limit: int = MAX_JSON_DEPTH) -> bool:
    depth = 0
    in_str = False
    esc = False
    for ch in raw:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            depth += 1
            if depth > limit:
                return True
        elif ch in "}]":
            depth -= 1
    return False


def _evaluate_llms_txt(status: Optional[int], ctype: str, text: str) -> dict[str, Any]:
    if status is None or status >= 500:
        return {"status": status, "lighthouse_verdict": "fail", "errors": [f"HTTP {status}"]}
    if status >= 400:
        return {"status": status, "lighthouse_verdict": "not-applicable", "errors": []}
    soft_404 = bool(re.match(r"^\s*<(!doctype|html)", text, re.I))
    has_h1 = bool(re.search(r"^[^\S\n]*#\s+.+", text, re.M))
    has_md_link = any(
        "[" in ln and "](" in ln and ")" in ln[ln.find("](") + 2 :]
        for ln in text.splitlines()
    )
    errors: list[str] = []
    if not has_h1:
        errors.append("missing H1 ('# Name')")
    if not has_md_link:
        errors.append("missing Markdown links '[title](url)'")
    if len(text) < 50:
        errors.append("shorter than 50 characters")
    if soft_404:
        errors.append("served HTML (soft 404)")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return {
        "status": status,
        "content_type": ctype,
        "bytes": len(text.encode("utf-8", errors="replace")),
        "soft_404_html": soft_404,
        "lighthouse_verdict": "pass" if not errors else "fail",
        "errors": errors,
        "hygiene": {
            "h1_first_line": bool(lines and lines[0].startswith("# ")),
            "has_summary_blockquote": any(ln.startswith("> ") for ln in lines),
            "h2_sections": sum(1 for ln in lines if ln.startswith("## ")),
            "markdown_links_count": len(re.findall(r"-\s*\[[^\]]+\]\([^)]+\)", text)),
            "oversize_100kb": len(text.encode("utf-8", errors="replace")) > 100 * 1024,
        },
    }


def _check_well_known_json(url: str, timeout: float, *, note: Optional[str] = None) -> dict[str, Any]:
    rec = safe_fetch(url, timeout=timeout)
    ctype = (_first_hdr(rec["headers"], "content-type") or "").split(";")[0].strip().lower()
    status = rec["status_code"]
    soft_404 = status == 200 and ctype.startswith("text/html")
    valid_json = False
    parsed_keys: list[str] = []
    if status == 200 and not soft_404 and not _json_depth_exceeds(rec["text"]):
        try:
            obj = json.loads(rec["text"])
            valid_json = True
            if isinstance(obj, dict):
                parsed_keys = list(obj.keys())[:12]
        except ValueError:
            valid_json = False
    out: dict[str, Any] = {
        "url": url,
        "status": status,
        "content_type": ctype or None,
        "soft_404_html": soft_404,
        "valid_json": valid_json,
        "top_keys": parsed_keys,
    }
    if note:
        out["standard_note"] = note
    if rec["error"]:
        out["error"] = rec["error"]
    return out


def audit_site_discovery(site_root: str, timeout: float) -> dict[str, Any]:
    robots = audit_robots_txt(site_root, timeout)
    llms_rec = safe_fetch(f"{site_root}/llms.txt", timeout=timeout)
    llms_ctype = (_first_hdr(llms_rec["headers"], "content-type") or "").split(";")[0].strip().lower()
    llms_eval = _evaluate_llms_txt(llms_rec["status_code"], llms_ctype, llms_rec["text"])

    llms_full_rec = safe_fetch(f"{site_root}/llms-full.txt", timeout=timeout)
    llms_full_ctype = (_first_hdr(llms_full_rec["headers"], "content-type") or "").split(";")[0].strip().lower()
    llms_full_soft404 = llms_full_rec["status_code"] == 200 and llms_full_ctype.startswith("text/html")

    mcp_wk = _check_well_known_json(
        f"{site_root}/.well-known/mcp.json",
        timeout,
        note="SEP-1649 (/.well-known/mcp.json) was closed; SEP-2127 recommends MCP Server Card via ARD ai-catalog.json.",
    )
    ard_wk = _check_well_known_json(
        f"{site_root}/.well-known/ai-catalog.json",
        timeout,
        note="Agentic Resource Discovery (ARD) 1.0 catalog.",
    )

    return {
        "site_root": site_root,
        "robots_txt": robots,
        "llms_txt": llms_eval,
        "llms_full_txt": {
            "status": llms_full_rec["status_code"],
            "content_type": llms_full_ctype or None,
            "bytes": llms_full_rec["raw_bytes_len"],
            "soft_404_html": llms_full_soft404,
            "exists": llms_full_rec["status_code"] == 200 and not llms_full_soft404,
        },
        "well_known_mcp_json": mcp_wk,
        "well_known_ai_catalog_json": ard_wk,
    }


def _check_markdown_negotiation(url: str, timeout: float) -> dict[str, Any]:
    rec = safe_fetch(url, headers={"Accept": "text/markdown"}, timeout=timeout)
    ctype = (_first_hdr(rec["headers"], "content-type") or "").lower()
    vary = _first_hdr(rec["headers"], "vary") or ""
    vary_tokens = {t.strip().lower() for t in vary.split(",") if t.strip()}
    supported = rec["status_code"] == 200 and "text/markdown" in ctype
    return {
        "status": rec["status_code"],
        "content_type": ctype or None,
        "supported": supported,
        "vary": vary or None,
        "vary_covers_accept": "accept" in vary_tokens or "*" in vary_tokens,
        "x_markdown_tokens": _first_hdr(rec["headers"], "x-markdown-tokens"),
        "content_signal_header": _first_hdr(rec["headers"], "content-signal"),
        "bytes": rec["raw_bytes_len"],
        "error": rec["error"],
    }


# ---------------------------------------------------------------------------
# (e) Canonical & Hreflang Validation
# ---------------------------------------------------------------------------

_ISO639_1_INVALID = {"eng", "jp", "ger", "fre", "spa", "chi", "kor"}
_INVALID_REGIONS = {"uk", "eu", "un", "la", "ap", "latam"}


def _validate_hreflang_code(code: str) -> Optional[str]:
    c = code.strip()
    if c.lower() == "x-default":
        return None
    parts = c.split("-")
    if len(parts) > 3:
        return f"invalid BCP 47 tag {code!r}"
    lang = parts[0]
    if not re.fullmatch(r"[a-z]{2}", lang) or lang in _ISO639_1_INVALID:
        return f"invalid/non-ISO-639-1 language code {lang!r} in {code!r}"
    idx = 1
    if idx < len(parts) and len(parts[idx]) == 4:
        if not re.fullmatch(r"[A-Za-z]{4}", parts[idx]):
            return f"invalid ISO 15924 script subtag {parts[idx]!r} in {code!r}"
        idx += 1
    if idx < len(parts):
        reg = parts[idx]
        if reg.lower() in _INVALID_REGIONS or not re.fullmatch(r"[A-Za-z]{2}", reg):
            hint = " (use 'GB' not 'UK')" if reg.lower() == "uk" else ""
            return f"invalid ISO 3166-1 region {reg!r} in {code!r}{hint}"
        idx += 1
    if idx < len(parts):
        return f"unexpected trailing subtag in {code!r}"
    return None


def _analyze_canonical_and_hreflang(
    parser: _PageParser,
    page_url: str,
    header_links: list[dict[str, Any]],
) -> dict[str, Any]:
    base = urljoin(page_url, parser.base_href) if parser.base_href else page_url
    canon_tags = [
        urljoin(base, lk.get("href", ""))
        for lk in parser.link_tags
        if "canonical" in lk["rels"] and lk.get("href")
    ]
    canonical = canon_tags[0] if canon_tags else None
    self_key = url_match_key(page_url)
    if not canonical:
        canon_status = "missing"
    elif url_match_key(canonical) == self_key:
        canon_status = "self"
    else:
        canon_status = "other"

    og_url = next(
        (
            urljoin(base, m.get("content", ""))
            for m in parser.meta_tags
            if m.get("property", "").lower() == "og:url" and m.get("content")
        ),
        None,
    )
    og_matches_canon = (
        url_match_key(og_url) == url_match_key(canonical)
        if og_url and canonical
        else None
    )

    hreflang_entries: list[dict[str, str]] = []
    for lk in parser.link_tags:
        if "alternate" in lk["rels"] and lk.get("hreflang") and lk.get("href"):
            hreflang_entries.append(
                {
                    "hreflang": lk["hreflang"].strip(),
                    "href": urljoin(base, lk["href"].strip()),
                    "source": "html",
                }
            )
    for hlk in header_links:
        if "alternate" in hlk["rel"] and hlk.get("hreflang") and hlk.get("uri"):
            hreflang_entries.append(
                {
                    "hreflang": hlk["hreflang"].strip(),
                    "href": urljoin(base, hlk["uri"].strip()),
                    "source": "header",
                }
            )

    code_errors: list[str] = []
    protocols: set[str] = set()
    x_default_count = 0
    self_ref_target = url_match_key(canonical or page_url)
    has_self_ref = False

    for entry in hreflang_entries:
        code = entry["hreflang"]
        if code.lower() == "x-default":
            x_default_count += 1
        err = _validate_hreflang_code(code)
        if err:
            code_errors.append(err)
        p = urlparse(entry["href"])
        if p.scheme:
            protocols.add(p.scheme.lower())
        if url_match_key(entry["href"]) == self_ref_target:
            has_self_ref = True

    issues: list[str] = []
    if len(canon_tags) > 1:
        issues.append(f"Duplicate canonical tags ({len(canon_tags)}).")
    if canon_status == "missing":
        issues.append("Missing <link rel='canonical'>.")
    elif canon_status == "other":
        issues.append(f"Canonical points elsewhere ({canonical}); hreflang on non-canonical pages is ignored.")
    if og_matches_canon is False:
        issues.append(f"og:url ({og_url}) differs from canonical ({canonical}).")
    if hreflang_entries:
        if not has_self_ref:
            issues.append("Hreflang set is missing a self-referencing alternate matching the canonical URL.")
        if x_default_count == 0:
            issues.append("Hreflang set has no x-default fallback.")
        elif x_default_count > 1:
            issues.append(f"Multiple x-default entries ({x_default_count}).")
        if len(protocols) > 1:
            issues.append(f"Mixed protocols in hreflang URLs: {sorted(protocols)}.")
        issues.extend(code_errors)

    return {
        "canonical": canonical,
        "canonical_count": len(canon_tags),
        "canonical_status": canon_status,
        "og_url": og_url,
        "og_url_matches_canonical": og_matches_canon,
        "hreflang_count": len(hreflang_entries),
        "hreflang_entries": hreflang_entries,
        "has_self_referencing_hreflang": has_self_ref if hreflang_entries else None,
        "has_x_default": x_default_count > 0 if hreflang_entries else None,
        "issues": issues,
    }


# ---------------------------------------------------------------------------
# (f) JSON-LD @graph Validity, @id Presence & 2024-2026 Deprecated Types
# ---------------------------------------------------------------------------

SCHEMA_CONTEXTS = frozenset(
    {"https://schema.org", "http://schema.org", "https://schema.org/", "http://schema.org/"}
)
DEPRECATED_SCHEMA_TYPES_2024_2026 = {
    "HowTo": ("Error", "Rich results retired September 2023; use clear H2 step headings instead."),
    "VehicleListing": ("Error", "Retired June 12, 2025; use Product if sold online."),
    "Vehicle": ("Error", "Vehicle listing rich results retired June 12, 2025."),
    "ClaimReview": ("Warning", "Search rich result retired June 12, 2025 (Fact Check Explorer still reads it)."),
    "EstimatedSalary": ("Error", "Retired June 12, 2025; use JobPosting.baseSalary for specific roles."),
    "OccupationalAggregateRating": ("Error", "Retired June 12, 2025."),
    "LearningVideo": ("Error", "Retired June 12, 2025; replace with VideoObject."),
    "CourseInfo": ("Error", "Retired June 12, 2025; use Course + ItemList carousel."),
    "SpecialAnnouncement": ("Error", "Deprecated July 31, 2025; use Event or Article."),
    "PracticeProblem": ("Error", "Deprecated Nov 2025, tooling/docs removed Jan 2026."),
    "FAQPage": (
        "Info",
        "FAQ rich results fully retired for all sites May 7, 2026 (not Critical; keep if useful or use QAPage for user Q&A).",
    ),
}
BRACKET_PLACEHOLDERS = (
    "[Business Name]",
    "[City]",
    "[State]",
    "[Phone]",
    "[Address]",
    "[Your",
    "[INSERT",
    "[URL]",
    "[Email]",
)
BARE_PLACEHOLDER_RE = re.compile(r"\bREPLACE(?:_[A-Z]+)*\b")


def _is_schema_context(val: Any) -> bool:
    if isinstance(val, str):
        return val.strip() in SCHEMA_CONTEXTS
    if isinstance(val, list):
        return any(_is_schema_context(x) for x in val)
    if isinstance(val, dict):
        return _is_schema_context(val.get("@vocab"))
    return False


def _walk_schema_node(
    node: dict[str, Any],
    block_idx: int,
    *,
    inherited_context: bool,
    is_primary_node: bool,
    errors: list[str],
    warnings: list[str],
    info_notes: list[str],
    types_found: list[str],
    ids_found: list[str],
    missing_id_types: list[str],
    deprecated_hits: list[dict[str, str]],
) -> None:
    prefix = f"Block {block_idx}"
    if "@context" not in node and not inherited_context:
        errors.append(f"{prefix}: missing @context")
    elif "@context" in node and not _is_schema_context(node["@context"]):
        errors.append(f"{prefix}: unexpected @context {node['@context']!r}")

    has_graph = "@graph" in node and isinstance(node.get("@graph"), (dict, list))
    if "@type" not in node and not has_graph:
        errors.append(f"{prefix}: entity missing @type")

    raw_type = node.get("@type")
    node_types: list[str] = []
    if "@type" in node:
        candidates = raw_type if isinstance(raw_type, list) else [raw_type]
        if not candidates or any(not isinstance(t, str) or not t.strip() for t in candidates):
            errors.append(f"{prefix}: malformed @type {raw_type!r}")
        else:
            node_types = list(dict.fromkeys(t.strip() for t in candidates))
            types_found.extend(node_types)

    node_id = node.get("@id")
    if isinstance(node_id, str) and node_id.strip():
        ids_found.append(node_id.strip())
        if not node_id.startswith(("http://", "https://", "_:")):
            warnings.append(f"{prefix}: relative or non-URI @id {node_id!r}")
    elif is_primary_node and node_types:
        missing_id_types.extend(node_types)

    for t in node_types:
        if t in DEPRECATED_SCHEMA_TYPES_2024_2026:
            sev, note = DEPRECATED_SCHEMA_TYPES_2024_2026[t]
            deprecated_hits.append({"type": t, "severity": sev, "note": note})
            if sev == "Error":
                errors.append(f"{prefix}: deprecated @type '{t}' — {note}")
            elif sev == "Warning":
                warnings.append(f"{prefix}: retired Search rich result @type '{t}' — {note}")
            else:
                info_notes.append(f"{prefix}: retired rich result @type '{t}' — {note}")

    # Check placeholders & relative URLs on local node fields (excluding @graph)
    local_scope = {k: v for k, v in node.items() if k != "@graph"}
    serialized = json.dumps(local_scope, ensure_ascii=False)
    for ph in BRACKET_PLACEHOLDERS:
        if ph.lower() in serialized.lower():
            errors.append(f"{prefix}: placeholder text {ph!r}")
    for m in BARE_PLACEHOLDER_RE.findall(serialized):
        errors.append(f"{prefix}: placeholder token {m!r}")
    for url_key in ("url", "image"):
        val = node.get(url_key)
        if isinstance(val, str) and val.strip().startswith("/"):
            warnings.append(f"{prefix}: relative URL in {url_key!r}: {val!r}")

    if "@graph" in node:
        g = node["@graph"]
        if not isinstance(g, (dict, list)):
            errors.append(f"{prefix}: @graph must be a list or object")
        else:
            members = [g] if isinstance(g, dict) else g
            ctx_ok = inherited_context or ("@context" in node)
            for idx, m in enumerate(members, 1):
                if not isinstance(m, dict):
                    errors.append(f"{prefix}: @graph[{idx}] must be an object")
                    continue
                _walk_schema_node(
                    m,
                    block_idx,
                    inherited_context=ctx_ok,
                    is_primary_node=True,
                    errors=errors,
                    warnings=warnings,
                    info_notes=info_notes,
                    types_found=types_found,
                    ids_found=ids_found,
                    missing_id_types=missing_id_types,
                    deprecated_hits=deprecated_hits,
                )

    for k, v in local_scope.items():
        if isinstance(v, dict) and "@type" in v:
            _walk_schema_node(
                v,
                block_idx,
                inherited_context=True,
                is_primary_node=False,
                errors=errors,
                warnings=warnings,
                info_notes=info_notes,
                types_found=types_found,
                ids_found=ids_found,
                missing_id_types=missing_id_types,
                deprecated_hits=deprecated_hits,
            )
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict) and "@type" in item:
                    _walk_schema_node(
                        item,
                        block_idx,
                        inherited_context=True,
                        is_primary_node=False,
                        errors=errors,
                        warnings=warnings,
                        info_notes=info_notes,
                        types_found=types_found,
                        ids_found=ids_found,
                        missing_id_types=missing_id_types,
                        deprecated_hits=deprecated_hits,
                    )


def _analyze_jsonld(blocks: list[str]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    info_notes: list[str] = []
    types_found: list[str] = []
    ids_found: list[str] = []
    missing_id_types: list[str] = []
    deprecated_hits: list[dict[str, str]] = []
    parse_errors = 0
    has_graph = False

    for idx, raw in enumerate(blocks, 1):
        if _json_depth_exceeds(raw):
            parse_errors += 1
            errors.append(f"Block {idx}: JSON-LD nesting exceeds {MAX_JSON_DEPTH} levels")
            continue
        try:
            data = json.loads(raw)
        except (ValueError, RecursionError) as exc:
            parse_errors += 1
            errors.append(f"Block {idx}: invalid JSON ({exc})")
            continue

        roots = data if isinstance(data, list) else [data]
        for root in roots:
            if not isinstance(root, dict):
                errors.append(f"Block {idx}: JSON-LD root must be an object or list of objects")
                continue
            if "@graph" in root:
                has_graph = True
            _walk_schema_node(
                root,
                idx,
                inherited_context=False,
                is_primary_node=True,
                errors=errors,
                warnings=warnings,
                info_notes=info_notes,
                types_found=types_found,
                ids_found=ids_found,
                missing_id_types=missing_id_types,
                deprecated_hits=deprecated_hits,
            )

    if missing_id_types:
        warnings.append(
            f"Primary/graph node(s) missing @id: {', '.join(list(dict.fromkeys(missing_id_types))[:10])}"
        )

    return {
        "blocks_count": len(blocks),
        "parse_valid": parse_errors == 0,
        "uses_graph": has_graph,
        "types": list(dict.fromkeys(types_found)),
        "entity_ids": list(dict.fromkeys(ids_found)),
        "missing_id_types": list(dict.fromkeys(missing_id_types)),
        "deprecated_types_detected": deprecated_hits,
        "errors": errors,
        "warnings": warnings,
        "info_notes": info_notes,
    }


# ---------------------------------------------------------------------------
# Audit Orchestrator & CLI
# ---------------------------------------------------------------------------


def audit_url(url: str, site_cache: dict[str, dict[str, Any]], timeout: float) -> dict[str, Any]:
    norm_url = url.strip()
    if "://" not in norm_url:
        norm_url = f"https://{norm_url}"

    rec = safe_fetch(norm_url, timeout=timeout)
    if rec["error"] or rec["status_code"] is None:
        return {"url": norm_url, "error": rec["error"] or "Fetch failed"}

    final_url = rec["final_url"] or norm_url
    parsed_final = urlparse(final_url)
    site_root = f"{parsed_final.scheme}://{parsed_final.netloc}"
    if site_root not in site_cache:
        site_cache[site_root] = audit_site_discovery(site_root, timeout)

    parser = _PageParser()
    try:
        parser.feed(rec["text"])
        parser.close()
    except Exception:
        pass

    https = parsed_final.scheme == "https"
    header_links = parse_link_header(rec["headers"].get("link", []))
    visible_text = " ".join(parser.visible_chunks)
    words_no_js = len(visible_text.split())
    inline_blob = "\n".join(parser.inline_scripts)

    return {
        "url": norm_url,
        "final_url": final_url,
        "site_root": site_root,
        "status_code": rec["status_code"],
        "redirect_chain": rec["redirect_chain"],
        "html_bytes": rec["raw_bytes_len"],
        "html_over_2mb": rec.get("truncated", False) or rec["raw_bytes_len"] >= MAX_BODY_BYTES,
        "page_basics": {
            "html_lang": parser.html_lang,
            "title": parser.titles[0] if parser.titles else None,
            "h1_count": len(parser.h1s),
            "h1_first": parser.h1s[0][:140] if parser.h1s else None,
            "words_without_js": words_no_js,
            "js_shell_empty_roots": parser.js_shell_div_ids,
        },
        "transport_and_security": _grade_security_headers(rec["headers"], https),
        "stack_exposure": _detect_stack_exposure(rec["headers"], rec["text"], parser),
        "robots_directives": _analyze_page_robots(rec["headers"], parser),
        "rfc8288_link_headers": header_links,
        "html_discovery_links": [
            {"rel": lk["rels"], "type": lk.get("type", ""), "href": urljoin(final_url, lk.get("href", ""))}
            for lk in parser.link_tags
            if lk.get("href")
            and (
                "ai-catalog" in lk["rels"]
                or ("alternate" in lk["rels"] and "markdown" in lk.get("type", "").lower())
            )
        ],
        "markdown_negotiation": _check_markdown_negotiation(final_url, timeout),
        "webmcp_markup": {
            "forms_total": len(parser.forms),
            "forms_annotated": sum(1 for f in parser.forms if f["toolname"] or f["tooldescription"]),
            "inline_registerTool_calls": len(re.findall(r"\bregisterTool\s*\(", inline_blob)),
            "document_modelContext": "document.modelContext" in inline_blob,
            "navigator_modelContext": "navigator.modelContext" in inline_blob,
        },
        "canonical_and_hreflang": _analyze_canonical_and_hreflang(parser, final_url, header_links),
        "jsonld": _analyze_jsonld(parser.jsonld_blocks),
    }


def check_cross_url_reciprocity(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Verify bidirectional hreflang return tags between URLs audited in the same run."""
    by_key: dict[str, dict[str, Any]] = {}
    for p in pages:
        if "error" in p:
            continue
        target = p["canonical_and_hreflang"].get("canonical") or p["final_url"]
        by_key[url_match_key(target)] = p
        by_key[url_match_key(p["final_url"])] = p

    findings: list[dict[str, Any]] = []
    for p in pages:
        if "error" in p:
            continue
        src_url = p["canonical_and_hreflang"].get("canonical") or p["final_url"]
        src_key = url_match_key(src_url)
        for entry in p["canonical_and_hreflang"].get("hreflang_entries", []):
            tgt_key = url_match_key(entry["href"])
            if tgt_key == src_key or tgt_key not in by_key:
                continue
            peer = by_key[tgt_key]
            peer_targets = {
                url_match_key(e["href"])
                for e in peer["canonical_and_hreflang"].get("hreflang_entries", [])
            }
            if src_key not in peer_targets:
                findings.append(
                    {
                        "source_url": src_url,
                        "target_url": entry["href"],
                        "hreflang": entry["hreflang"],
                        "issue": f"Missing reciprocal hreflang back to {src_url}",
                    }
                )
    return findings


def _print_human_report(report: dict[str, Any]) -> None:
    print("=" * 90)
    print(f"AGENTIC, TRANSPORT, HREFLANG & 2026 SCHEMA AUDIT ({report['checked_at']})")
    print("=" * 90)
    for root, site in report["site_roots"].items():
        rb = site["robots_txt"]
        llms = site["llms_txt"]
        mcp = site["well_known_mcp_json"]
        ard = site["well_known_ai_catalog_json"]
        print(f"\n[SITE ROOT] {root}")
        print(f"  robots.txt       : HTTP {rb.get('status')} | reachable={rb.get('reachable')} | cf_managed={bool(rb.get('cloudflare_managed'))}")
        if rb.get("reachable"):
            blocked = [a["token"] for a in rb.get("agents", []) if not a["root_allowed"]]
            cs = rb["content_signal"]
            print(f"    AI blocked     : {blocked or 'none'}")
            print(f"    Content-Signal : declared={cs['declared']} | lines={cs['group_lines']} | group_gaps={cs['named_groups_missing_signal_from_star']}")
        print(f"  /llms.txt        : HTTP {llms.get('status')} | verdict={llms.get('lighthouse_verdict')} | errors={llms.get('errors')}")
        print(f"  /llms-full.txt   : HTTP {site['llms_full_txt']['status']} | exists={site['llms_full_txt']['exists']} | bytes={site['llms_full_txt']['bytes']}")
        print(f"  /.well-known/mcp.json        : HTTP {mcp['status']} | valid_json={mcp['valid_json']} | soft_404={mcp['soft_404_html']}")
        print(f"  /.well-known/ai-catalog.json : HTTP {ard['status']} | valid_json={ard['valid_json']} | soft_404={ard['soft_404_html']}")

    for p in report["pages"]:
        print(f"\n[PAGE] {p['url']}")
        if "error" in p:
            print(f"  ERROR: {p['error']}")
            continue
        sec = p["transport_and_security"]
        stk = p["stack_exposure"]
        rob = p["robots_directives"]
        md = p["markdown_negotiation"]
        ch = p["canonical_and_hreflang"]
        jld = p["jsonld"]
        print(f"  HTTP             : {p['status_code']} -> {p['final_url']} (hops={len(p['redirect_chain'])}, words_no_js={p['page_basics']['words_without_js']})")
        print(f"  Security Headers : HSTS={sec['hsts']['present']} (preload_hdr={sec['hsts']['meets_preload_header_requirements']}) | CSP={sec['csp']['present']} | nosniff={sec['x_content_type_options']['ok']} | framing={sec['framing']['ok']}")
        print(f"  Stack / CVE      : exposed={stk['headers_exposed']} | php_cve={stk['php_cve_2026_109618_status']} | leaks={stk['version_fingerprint_leaks']}")
        print(f"  Robots Meta/Hdr  : noindex={rob['noindex']} | nofollow={rob['nofollow']} | X-Robots-Tag={rob['x_robots_tag']}")
        print(f"  Link / Markdown  : RFC8288_links={len(p['rfc8288_link_headers'])} | accept_md={md['supported']} (vary_accept={md['vary_covers_accept']}, ctype={md['content_type']})")
        print(f"  Canonical/Hreflang: canonical={ch['canonical_status']} ({ch['canonical']}) | hreflang={ch['hreflang_count']} | self_ref={ch['has_self_referencing_hreflang']} | x-default={ch['has_x_default']}")
        if ch["issues"]:
            print(f"    Issues         : {ch['issues']}")
        print(f"  JSON-LD Schema   : blocks={jld['blocks_count']} | valid={jld['parse_valid']} | @graph={jld['uses_graph']} | types={jld['types']} | @ids={len(jld['entity_ids'])}")
        if jld["errors"] or jld["warnings"] or jld["info_notes"]:
            print(f"    Errors         : {jld['errors']}")
            print(f"    Warnings       : {jld['warnings']}")
            print(f"    Info           : {jld['info_notes']}")

    if report["cross_url_hreflang_reciprocity"]:
        print("\n[CROSS-URL HREFLANG RECIPROCITY GAPS]")
        for gap in report["cross_url_hreflang_reciprocity"]:
            print(f"  - {gap['source_url']} -> {gap['target_url']} ({gap['hreflang']}): {gap['issue']}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="SSRF-safe Agentic, Transport/CVE, Robots, Hreflang & 2026 Schema Checker."
    )
    parser.add_argument("urls", nargs="+", help="One or more http(s) URLs to inspect")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON output")
    parser.add_argument("--timeout", type=float, default=15.0, help="Per-request timeout in seconds (default: 15)")
    args = parser.parse_args(argv)

    timeout = min(max(args.timeout, 2.0), 60.0)
    site_cache: dict[str, dict[str, Any]] = {}
    pages = [audit_url(u, site_cache, timeout) for u in args.urls]
    reciprocity_gaps = check_cross_url_reciprocity(pages)

    report = {
        "checked_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "targets_count": len(pages),
        "site_roots": site_cache,
        "pages": pages,
        "cross_url_hreflang_reciprocity": reciprocity_gaps,
        "summary": {
            "pages_ok": sum(1 for p in pages if "error" not in p),
            "pages_errored": sum(1 for p in pages if "error" in p),
            "jsonld_errors": sum(len(p.get("jsonld", {}).get("errors", [])) for p in pages if "error" not in p),
            "canonical_hreflang_issues": sum(
                len(p.get("canonical_and_hreflang", {}).get("issues", [])) for p in pages if "error" not in p
            )
            + len(reciprocity_gaps),
        },
    }

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        _print_human_report(report)

    return 1 if report["summary"]["pages_ok"] == 0 else 0


if __name__ == "__main__":
    sys.exit(main())
