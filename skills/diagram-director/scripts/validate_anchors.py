#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cross-reference checks (contract C3): V7 `path#anchor` references, V7s Shape
Hint resolution targets, V11 shipped base templates.

ONE generic checker (`check_ref`) serves every anchor-bearing column, declared in
csv_schema.REF_RULES. It replaced four hand-rolled checks that each had a hole:
  - motion's derived the expected heading from the Motion ID and never read the
    Recipe Ref cell, so a cell pointing anywhere else validated clean;
  - payloads' read the cell but threw the FILE part away, so
    `snippets/typo.html#packet-dot` validated clean;
  - components' and states' each re-implemented the marker forms.
check_ref reads the ACTUAL cell, resolves the file part against the rule's base
directory, and only then looks for the anchor.

A missing target file is an ERROR, not a warning: every referenced file has
shipped (Phases 04/05), so absence now means a broken cross-reference.
"""

import csv
from pathlib import Path

from csv_config import CSV_CONFIG, domain_path
from csv_schema import (BASE_SHAPE_FILE, DEFAULT_HINT_KEY, REF_RULES, SHAPE_HINT_RULES,
                        anchor_present, parse_shape_hint, split_ref)

SKILL_ROOT = Path(__file__).parent.parent
_text_cache = {}


def _read(path):
    """Cached text of a reference target, or None when it does not exist."""
    if path not in _text_cache:
        _text_cache[path] = path.read_text(encoding="utf-8") if path.exists() else None
    return _text_cache[path]


def check_ref(base, ref, form, label, errors, code="V7"):
    """Verify one `path#anchor` reference: the file exists AND holds the anchor.

    base is a directory under the skill root; ref is the raw cell value.
    """
    if "#" not in ref:
        errors.append(f"{label}: reference '{ref}' is not '<path>#<anchor>' ({code})")
        return
    file_part, anchor = split_ref(ref)
    if not file_part or not anchor:
        errors.append(f"{label}: reference '{ref}' has an empty path or anchor ({code})")
        return
    text = _read(SKILL_ROOT / base / file_part)
    if text is None:
        errors.append(f"{label}: reference '{ref}' -> {base}/{file_part} does not exist ({code})")
        return
    if not anchor_present(text, anchor, form):
        errors.append(f"{label}: reference '{ref}' -> no '{anchor}' anchor in {base}/{file_part} ({code})")


def _check_declared_refs(errors):
    """Run check_ref over every anchor-bearing column declared in REF_RULES."""
    for rule in REF_RULES:
        domain = rule["domain"]
        path = domain_path(domain)
        if not path.exists():
            errors.append(f"{CSV_CONFIG[domain]['file']}: file missing -- cannot check references (V7)")
            continue
        id_field = CSV_CONFIG[domain]["id_field"]
        column, derived = rule.get("column"), rule.get("derived")
        for row in csv.DictReader(open(path, encoding="utf-8")):
            row_id = (row.get(id_field) or "").strip()
            label = f"{CSV_CONFIG[domain]['file']}:{row_id or '?'}"
            if derived:
                ref = derived.format(id=row_id)
            else:
                ref = (row.get(column) or "").strip()
                label += f":{column}"
                if not ref:
                    errors.append(f"{label}: empty reference (V7)")
                    continue
            check_ref(rule["base"], ref, rule["form"], label, errors)


def _check_shape_hints(errors):
    """V7s: every components.csv Shape Hint parses, has `default`, and every
    style-specific key is a real Style ID whose token follows that style's
    convention (see csv_schema.SHAPE_HINT_RULES for how those were derived)."""
    style_ids = {row["Style ID"].strip() for row in
                 csv.DictReader(open(domain_path("styles"), encoding="utf-8"))}
    base_text = _read(SKILL_ROOT / "templates" / BASE_SHAPE_FILE) or ""
    for row in csv.DictReader(open(domain_path("components"), encoding="utf-8")):
        label = f"components.csv:{row.get('Component ID')}:Shape Hint"
        hints, problems = parse_shape_hint(row.get("Shape Hint", ""))
        errors.extend(f"{label}: {problem} (V7s)" for problem in problems)
        for key, token in hints.items():
            if key == DEFAULT_HINT_KEY:
                continue
            if key not in style_ids:
                errors.append(f"{label}: override key '{key}' is not a Style ID in styles.csv (V7s)")
                continue
            rule = SHAPE_HINT_RULES.get(key)
            if not rule:
                continue
            if "suffix" in rule and not token.endswith(rule["suffix"]):
                errors.append(f"{label}: '{key}:{token}' must end in '{rule['suffix']}' (V7s)")
            if "prefix" in rule:
                if not token.startswith(rule["prefix"]):
                    errors.append(f"{label}: '{key}:{token}' must start with '{rule['prefix']}' (V7s)")
                    continue
                anchor = rule["anchor_prefix"] + token[len(rule["prefix"]):]
                if not anchor_present(base_text, anchor, "snippet"):
                    errors.append(f"{label}: '{key}:{token}' -> no '{anchor}' anchor in "
                                  f"templates/{rule['anchor_file']} (V7s)")


def _check_shipped_template_files(errors):
    """V11: every styles.csv row with Template Status=shipped must have a
    corresponding templates/base/<Style ID>.html file."""
    templates_dir = SKILL_ROOT / "templates" / "base"
    for row in csv.DictReader(open(domain_path("styles"), encoding="utf-8")):
        if row.get("Template Status", "").strip() != "shipped":
            continue
        style_id = row.get("Style ID", "").strip()
        if style_id and not (templates_dir / f"{style_id}.html").exists():
            errors.append(f"styles.csv:{style_id}: Template Status=shipped but "
                          f"templates/base/{style_id}.html not found (V11)")


def check_anchors(warnings, errors):
    """Run the cross-reference checks (V7, V7s, V11), appending to caller-owned lists."""
    _text_cache.clear()
    _check_declared_refs(errors)
    _check_shape_hints(errors)
    _check_shipped_template_files(errors)
