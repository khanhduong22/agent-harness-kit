#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Measuring one candidate: its checksum, and the real `verify_all.py` run behind gate two.

Split out of `diagram-director/scripts/run_floor.py` so the CLI file stays argument handling plus the record
sequence. Both functions here are READ-ONLY on the candidate -- the harness measures, it never
edits or repairs what a session produced.

The runner is shelled with a LIST argv and a timeout, never a shell string: a candidate path
is untrusted input from a generation run. `--serve` makes `verify_all.py` serve the candidate's
OWN directory on 127.0.0.1, which is why the round protocol keeps candidates outside this repo.
"""

import json
import hashlib
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import floor_ledger as ledger                                              # noqa: E402

VERIFY_TIMEOUT_S = 900


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:                     # read-only, always
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validation_of(cut, manifest):
    """Shell `verify_all.py --json --serve` and reduce its envelope to the five fields kept.

    `ok` is the envelope's own `ok`, so an UNVERIFIED cut (exit 3, no puppeteer) is not a
    pass here either. A runner that could not be parsed is recorded as a failed validation
    with the reason attached -- never as a silent green.
    """
    argv = [sys.executable, str(ledger.REPO_ROOT / "scripts" / "verify_all.py"),
            str(cut), "--manifest", str(manifest), "--serve", "--json"]
    try:
        done = subprocess.run(argv, capture_output=True, text=True, check=False,
                              timeout=VERIFY_TIMEOUT_S)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "exit": None, "errorCount": 0, "unverifiedCount": 0,
                "codes": [], "reason": f"verify_all.py could not be run: {exc}"}
    text = done.stdout or ""
    start, end = text.find("{"), text.rfind("}")
    try:
        envelope = json.loads(text[start:end + 1]) if start >= 0 < end else None
        if not isinstance(envelope, dict):
            raise ValueError("no JSON object on stdout")
    except ValueError as exc:
        return {"ok": False, "exit": done.returncode, "errorCount": 0, "unverifiedCount": 0,
                "codes": [], "reason": f"envelope unreadable ({exc}); "
                                       f"stderr: {(done.stderr or '').strip()[:300]}"}
    diagnostics = envelope.get("diagnostics") or []
    return {"ok": bool(envelope.get("ok")), "exit": envelope.get("exit", done.returncode),
            "errorCount": sum(1 for d in diagnostics if d.get("severity") == "error"),
            "unverifiedCount": sum(1 for d in diagnostics
                                   if d.get("severity") == "unverified"),
            "codes": sorted({d.get("code", "") for d in diagnostics if d.get("code")})}
