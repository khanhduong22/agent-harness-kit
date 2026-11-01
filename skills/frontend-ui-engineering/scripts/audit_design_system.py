#!/usr/bin/env python3
"""
Deterministic Design System, Anti-AI-Slop & WCAG 2.1 AA Auditor.
Combines Anthropic's official `/design-system audit` specification
(`anthropics/knowledge-work-plugins`) with `frontend-design` Anti-AI-Slop
detection (`anthropics/skills`) and WCAG 2.1 AA static checks.

Usage:
    python3 scripts/audit_design_system.py [target_directory] [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

IGNORE_DIRS = {
    ".git",
    "node_modules",
    ".next",
    "dist",
    "build",
    "out",
    "coverage",
    ".turbo",
    ".vercel",
    "__pycache__",
    "vendor",
}

COMPONENT_EXTS = {".tsx", ".jsx", ".vue", ".svelte", ".astro", ".html"}
STYLE_EXTS = {".css", ".scss"}

# Regex patterns
CSS_VAR_DEF_RE = re.compile(r"(--[a-zA-Z0-9_-]+)\s*:")
HEX_COLOR_RE = re.compile(r"#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
TW_ARBITRARY_PX_RE = re.compile(
    r"\b(?:p|px|py|pt|pb|pl|pr|m|mx|my|mt|mb|ml|mr|gap|text|rounded)-\[\d+(?:\.\d+)?px\]"
)
TW_ARBITRARY_COLOR_RE = re.compile(
    r"\b(?:bg|text|border|ring|from|via|to|fill|stroke)-\[#[0-9a-fA-F]{3,8}\]"
)

# Anti-AI-Slop tells (Anthropic frontend-design spec)
AI_SLOP_GRADIENT_RE = re.compile(
    r"from-(?:indigo|purple|violet)-[456]00[^\n\"']*to-(?:purple|pink|fuchsia)-[456]00"
)
AI_SLOP_EYEBROW_RE = re.compile(
    r"(?:uppercase[^\n\"']*tracking-(?:widest|\[0\.[123]\d*em\])|tracking-(?:widest|\[0\.[123]\d*em\])[^\n\"']*uppercase)"
)
AI_SLOP_ARROW_CTA_RE = re.compile(r"(?:→|&rarr;|->)\s*</(?:button|a|Button|Link)>")
UI_EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF\u2728\u26A1\U0001F680\U0001F525]")

# Accessibility static checks
IMG_NO_ALT_RE = re.compile(r"<img\b(?![^>]*\balt=)[^>]*>", re.IGNORECASE)
NON_SEMANTIC_CLICK_RE = re.compile(
    r"<(?:div|span)\b(?=[^>]*\bonClick=)(?![^>]*\b(?:role=|tabIndex=))[^>]*>",
    re.IGNORECASE,
)
OUTLINE_NONE_NO_RING_RE = re.compile(
    r"\b(?:focus:)?outline-none\b(?![^\n\"']*\b(?:focus-visible:ring|focus:ring|focus-visible:outline|focus-visible:border))"
)


def walk_files(root: Path) -> Tuple[List[Path], List[Path]]:
    comp_files: List[Path] = []
    style_files: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]
        for fname in filenames:
            if fname.endswith((".test.tsx", ".spec.tsx", ".stories.tsx", ".d.ts")):
                continue
            fpath = Path(dirpath) / fname
            ext = fpath.suffix.lower()
            if ext in COMPONENT_EXTS:
                comp_files.append(fpath)
            elif ext in STYLE_EXTS:
                style_files.append(fpath)
    return sorted(comp_files), sorted(style_files)


def analyze_tokens(style_files: List[Path], comp_files: List[Path]) -> Tuple[List[str], List[Dict[str, str]]]:
    tokens: set[str] = set()
    naming_issues: List[Dict[str, str]] = []

    for fpath in style_files + comp_files:
        try:
            content = fpath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in CSS_VAR_DEF_RE.finditer(content):
            tok = match.group(1)
            tokens.add(tok)

    for tok in sorted(tokens):
        if "_" in tok:
            naming_issues.append(
                {
                    "current": tok,
                    "suggested": tok.replace("_", "-").lower(),
                    "reason": "Mixed snake_case in CSS custom property; use kebab-case.",
                }
            )
        elif any(c.isupper() for c in tok):
            kebab = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", tok).lower()
            naming_issues.append(
                {
                    "current": tok,
                    "suggested": kebab,
                    "reason": "CamelCase token name; standardize on lowercase kebab-case.",
                }
            )

    return sorted(tokens), naming_issues


def analyze_components(
    root: Path, comp_files: List[Path]
) -> Tuple[
    List[Dict[str, str]],
    List[Dict[str, object]],
    List[Dict[str, str]],
    List[Dict[str, str]],
]:
    hardcoded_issues: List[Dict[str, str]] = []
    state_matrix: List[Dict[str, object]] = []
    slop_issues: List[Dict[str, str]] = []
    a11y_issues: List[Dict[str, str]] = []

    interactive_name_re = re.compile(
        r"(button|input|select|modal|dialog|drawer|dropdown|tabs|checkbox|switch|toggle|form|search|filter|combobox|header|nav|card|viewer|menu)",
        re.IGNORECASE,
    )

    for fpath in comp_files:
        rel = str(fpath.relative_to(root))
        try:
            content = fpath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        lines = content.splitlines()
        eyebrow_count = 0

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith(("//", "/*", "*")):
                continue

            # 1. Arbitrary Tailwind colors or pixel values
            for m in TW_ARBITRARY_COLOR_RE.finditer(line):
                hardcoded_issues.append(
                    {
                        "location": f"{rel}:{idx}",
                        "value": m.group(0),
                        "suggestion": "Replace arbitrary hex class with semantic design token (e.g., bg-surface, text-primary).",
                    }
                )
            for m in TW_ARBITRARY_PX_RE.finditer(line):
                hardcoded_issues.append(
                    {
                        "location": f"{rel}:{idx}",
                        "value": m.group(0),
                        "suggestion": "Replace arbitrary pixel bracket with spacing/typography scale token.",
                    }
                )

            # Raw hex in style={{ ... }} or props (ignore SVG paths/defs/gradients where brand art lives)
            if "style=" in line or "color=" in line:
                for m in HEX_COLOR_RE.finditer(line):
                    hardcoded_issues.append(
                        {
                            "location": f"{rel}:{idx}",
                            "value": m.group(0),
                            "suggestion": "Use CSS variable var(--color-*) instead of inline hex color.",
                        }
                    )

            # 2. Anti-AI-Slop checks
            if AI_SLOP_GRADIENT_RE.search(line):
                slop_issues.append(
                    {
                        "location": f"{rel}:{idx}",
                        "tell": "Generic AI indigo/purple/pink gradient",
                        "fix": "Use brand-specific surface or accent tokens instead of stock AI gradients.",
                    }
                )
            if "#D97757" in line.upper() or "#F4F1EA" in line.upper():
                slop_issues.append(
                    {
                        "location": f"{rel}:{idx}",
                        "tell": "Default Claude terracotta/warm-cream palette (#D97757 / #F4F1EA)",
                        "fix": "Use the project's custom brand palette.",
                    }
                )
            if AI_SLOP_EYEBROW_RE.search(line):
                eyebrow_count += 1
            if AI_SLOP_ARROW_CTA_RE.search(line):
                slop_issues.append(
                    {
                        "location": f"{rel}:{idx}",
                        "tell": "Formulaic '→' suffix inside button/link CTA",
                        "fix": "Remove trailing text arrow or use a semantic vector icon only where directional.",
                    }
                )

            # 3. WCAG 2.1 AA static checks
            if IMG_NO_ALT_RE.search(line):
                a11y_issues.append(
                    {
                        "location": f"{rel}:{idx}",
                        "criterion": "WCAG 1.1.1 (Non-text Content, Level A)",
                        "issue": "<img> element missing `alt` attribute",
                        "fix": "Add descriptive `alt=\"...\"` or `alt=\"\"` if decorative.",
                    }
                )
            if NON_SEMANTIC_CLICK_RE.search(line):
                a11y_issues.append(
                    {
                        "location": f"{rel}:{idx}",
                        "criterion": "WCAG 2.1.1 (Keyboard, Level A)",
                        "issue": "Non-semantic <div>/<span> with onClick but no role/tabIndex",
                        "fix": "Replace with native <button type=\"button\"> or <a>.",
                    }
                )
            if OUTLINE_NONE_NO_RING_RE.search(line):
                a11y_issues.append(
                    {
                        "location": f"{rel}:{idx}",
                        "criterion": "WCAG 2.4.7 (Focus Visible, Level AA)",
                        "issue": "`outline-none` used without a replacement `focus-visible:ring` indicator",
                        "fix": "Add `focus-visible:ring-2 focus-visible:ring-offset-2`.",
                    }
                )

        if eyebrow_count > 3:
            slop_issues.append(
                {
                    "location": rel,
                    "tell": f"Tracked-out uppercase eyebrow overload ({eyebrow_count} instances in one file)",
                    "fix": "Limit uppercase tracked-out eyebrow labels to at most 1-2 per page.",
                }
            )

        # 4. Component State Completeness Matrix (for interactive UI components)
        stem = fpath.stem
        if interactive_name_re.search(stem):
            has_hover = bool(re.search(r"hover:|onMouseEnter", content))
            has_focus = bool(re.search(r"focus-visible:|focus:|onFocus", content))
            has_active = bool(re.search(r"active:|aria-pressed|data-state", content))
            has_disabled = bool(re.search(r"disabled|aria-disabled", content))
            has_loading = bool(re.search(r"loading|isLoading|isPending|aria-busy|animate-spin|animate-pulse", content))
            has_error = bool(re.search(r"error|isError|aria-invalid|destructive", content))
            state_matrix.append(
                {
                    "component": f"`{stem}` ({rel})",
                    "default": True,
                    "hover": has_hover,
                    "focus": has_focus,
                    "active": has_active,
                    "disabled": has_disabled,
                    "loading": has_loading,
                    "error": has_error,
                }
            )

    return hardcoded_issues, state_matrix, slop_issues, a11y_issues


def compute_score(
    tokens_count: int,
    naming_issues: int,
    hardcoded_issues: int,
    slop_issues: int,
    a11y_issues: int,
) -> Tuple[int, str]:
    score = 100
    if tokens_count == 0:
        score -= 15
    score -= min(15, naming_issues * 3)
    score -= min(30, hardcoded_issues * 2)
    score -= min(20, slop_issues * 4)
    score -= min(30, a11y_issues * 5)
    score = max(0, score)

    if score >= 85:
        rating = "High"
    elif score >= 65:
        rating = "Medium"
    else:
        rating = "Low"
    return score, rating


def render_markdown(
    target: Path,
    comp_count: int,
    tokens: List[str],
    naming_issues: List[Dict[str, str]],
    hardcoded_issues: List[Dict[str, str]],
    state_matrix: List[Dict[str, object]],
    slop_issues: List[Dict[str, str]],
    a11y_issues: List[Dict[str, str]],
) -> str:
    score, rating = compute_score(
        len(tokens),
        len(naming_issues),
        len(hardcoded_issues),
        len(slop_issues),
        len(a11y_issues),
    )

    lines: List[str] = [
        f"## Design System Audit: `{target.name}` ({score}/100)",
        "",
        "### Summary",
        f"- **Components reviewed**: {comp_count}",
        f"- **CSS tokens defined**: {len(tokens)}",
        f"- **Consistency score**: **{rating}** (`{score}/100`)",
        f"- **Hardcoded token bypasses**: {len(hardcoded_issues)}",
        f"- **Anti-AI-Slop tells detected**: {len(slop_issues)}",
        f"- **WCAG 2.1 AA static warnings**: {len(a11y_issues)}",
        "",
        "### Issues Found",
        "",
        "#### 1. Naming Inconsistencies",
    ]

    if naming_issues:
        lines.extend(
            [
                "| Current | Suggested | Reason |",
                "|---|---|---|",
            ]
        )
        for item in naming_issues[:15]:
            lines.append(
                f"| `{item['current']}` | `{item['suggested']}` | {item['reason']} |"
            )
    else:
        lines.append("- None detected — all CSS custom properties follow lowercase `kebab-case`.")

    lines.extend(["", "#### 2. Missing Token Coverage (Hardcoded Values)"])
    if hardcoded_issues:
        for item in hardcoded_issues[:20]:
            lines.append(
                f"- `{item['location']}` — hardcoded `{item['value']}` ({item['suggestion']})"
            )
        if len(hardcoded_issues) > 20:
            lines.append(f"- *...and {len(hardcoded_issues) - 20} additional instances.*")
    else:
        lines.append("- Zero hardcoded hex/pixel bypasses detected in component files.")

    lines.extend(["", "#### 3. Interactive Component Completeness (State Matrix)"])
    if state_matrix:
        lines.extend(
            [
                "| Component | Default | Hover | Focus | Active | Disabled | Loading | Error |",
                "|---|---|---|---|---|---|---|---|",
            ]
        )
        for row in state_matrix[:20]:
            b = lambda val: "✓" if val else "✗"
            lines.append(
                f"| {row['component']} | {b(row['default'])} | {b(row['hover'])} | {b(row['focus'])} | {b(row['active'])} | {b(row['disabled'])} | {b(row['loading'])} | {b(row['error'])} |"
            )
    else:
        lines.append("- No dedicated interactive primitive files (`Button`, `Input`, `Modal`, etc.) matched by filename.")

    lines.extend(["", "#### 4. Anthropic Anti-AI-Slop Audit"])
    if slop_issues:
        for item in slop_issues[:15]:
            lines.append(f"- `{item['location']}` — **{item['tell']}**: {item['fix']}")
    else:
        lines.append("- Clean — zero stock AI-slop tells detected.")

    lines.extend(["", "#### 5. WCAG 2.1 AA Static Accessibility Check"])
    if a11y_issues:
        for item in a11y_issues[:15]:
            lines.append(
                f"- `{item['location']}` — **{item['criterion']}**: {item['issue']} -> *{item['fix']}*"
            )
    else:
        lines.append("- Clean — zero static WCAG 2.1 AA violations detected.")

    lines.extend(["", "### Priority Fixes"])
    priorities: List[str] = []
    if a11y_issues:
        priorities.append(
            f"**Resolve {len(a11y_issues)} WCAG 2.1 AA accessibility gaps** — ensure every interactive element has keyboard operability and `:focus-visible` rings."
        )
    if hardcoded_issues:
        priorities.append(
            f"**Migrate {len(hardcoded_issues)} hardcoded values to semantic tokens** — replace arbitrary Tailwind brackets (`-[#...]`, `-[Npx]`) with design system variables."
        )
    if slop_issues:
        priorities.append(
            f"**Eliminate {len(slop_issues)} AI-slop visual tells** — strip formulaic CTA arrows, excessive uppercase eyebrows, or stock gradients."
        )
    if naming_issues:
        priorities.append(
            f"**Normalize {len(naming_issues)} CSS custom property names** to lowercase `kebab-case`."
        )
    if not priorities:
        priorities.append(
            "**Maintain token discipline** — design system coverage, accessibility static checks, and anti-slop rules are all green."
        )

    for idx, prio in enumerate(priorities, start=1):
        lines.append(f"{idx}. {prio}")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit a frontend codebase for Design System consistency, Anti-AI-Slop tells, and WCAG 2.1 AA compliance."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target project or src directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON instead of Markdown report",
    )
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.exists():
        print(f"Error: target path '{target}' does not exist.", file=sys.stderr)
        return 1

    comp_files, style_files = walk_files(target)
    tokens, naming_issues = analyze_tokens(style_files, comp_files)
    hardcoded_issues, state_matrix, slop_issues, a11y_issues = analyze_components(
        target, comp_files
    )
    score, rating = compute_score(
        len(tokens),
        len(naming_issues),
        len(hardcoded_issues),
        len(slop_issues),
        len(a11y_issues),
    )

    if args.json:
        payload = {
            "target": target.name,
            "score": score,
            "rating": rating,
            "components_reviewed": len(comp_files),
            "tokens_defined": len(tokens),
            "naming_issues": naming_issues,
            "hardcoded_issues": hardcoded_issues,
            "state_matrix": state_matrix,
            "slop_issues": slop_issues,
            "a11y_issues": a11y_issues,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(
            render_markdown(
                target,
                len(comp_files),
                tokens,
                naming_issues,
                hardcoded_issues,
                state_matrix,
                slop_issues,
                a11y_issues,
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
