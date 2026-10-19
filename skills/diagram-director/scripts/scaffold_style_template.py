#!/usr/bin/env python3
"""Scaffold templates/base/<style>.html from the reference template.

The four base templates that shipped first are already derived from
flat-minimal.html with byte-identical class names -- only the token blocks, the
font link and a short style-specific rule set differ. This makes that derivation
explicit instead of a copy-paste ritual: role tokens are read straight out of
data/color-semantics.csv (so a template can never drift from the palette the
validator checks), and each style contributes its surface tokens, its font link
and its skin.

Usage:  python3 diagram-director/scripts/scaffold_style_template.py [style-id ...]
"""
import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REF = REPO / "templates" / "base" / "flat-minimal.html"
COLORS = REPO / "data" / "color-semantics.csv"
STYLES = REPO / "data" / "styles.csv"

ROLES = ["client", "service", "data", "async", "external", "error", "infra"]

# surface tokens per style: light then dark. Keys match the reference template's
# token names; anything omitted keeps the reference value.
SURFACE = {
    "neubrutalism": (
        {"--bg": "#fffdf5", "--surface": "#fffdf5", "--grid": "transparent",
         "--ink": "#141414", "--muted": "#4a4a4a", "--stroke": "#000000",
         "--stroke-w": "3px", "--radius": "0px"},
        {"--bg": "#141414", "--surface": "#141414", "--grid": "transparent",
         "--ink": "#fffdf5", "--muted": "#b8b8b8", "--stroke": "#ffffff"},
    ),
    "e-ink-paper": (
        {"--bg": "#fdfbf7", "--surface": "#fdfbf7",
         "--grid": "color-mix(in srgb, #1a1a1a 6%, transparent)",
         "--ink": "#1a1a1a", "--muted": "#5a5a5a", "--stroke": "#1a1a1a",
         "--stroke-w": "1px", "--radius": "2px"},
        {"--bg": "#1a1a1a", "--surface": "#1a1a1a",
         "--grid": "color-mix(in srgb, #f2efe9 7%, transparent)",
         "--ink": "#f2efe9", "--muted": "#b0b0b0", "--stroke": "#f2efe9"},
    ),
    "bauhaus": (
        {"--bg": "#f5f2eb", "--surface": "#f5f2eb",
         "--grid": "color-mix(in srgb, #121212 8%, transparent)",
         "--ink": "#121212", "--muted": "#4a4a4a", "--stroke": "#121212",
         "--stroke-w": "2px", "--radius": "0px"},
        {"--bg": "#121212", "--surface": "#121212",
         "--grid": "color-mix(in srgb, #f5f2eb 8%, transparent)",
         "--ink": "#f5f2eb", "--muted": "#bdbdbd", "--stroke": "#f5f2eb"},
    ),
    "claymorphism": (
        {"--bg": "#f4f1fb", "--surface": "#f4f1fb", "--grid": "transparent",
         "--ink": "#2f2c45", "--muted": "#5f5a7c", "--stroke": "#5f5a7c",
         "--stroke-w": "3px", "--radius": "24px"},
        {"--bg": "#1d1a2b", "--surface": "#1d1a2b", "--grid": "transparent",
         "--ink": "#efedf7", "--muted": "#b6b1d4", "--stroke": "#b6b1d4"},
    ),
}

FONTS = {
    "neubrutalism": '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=JetBrains+Mono:wght@400;500&display=swap">',
    "e-ink-paper": '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=JetBrains+Mono:wght@400;500&display=swap">',
    "bauhaus": '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jost:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap">',
    "claymorphism": '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Nunito:wght@600;700;800&family=JetBrains+Mono:wght@400;500&display=swap">',
}

TYPO = {
    "neubrutalism": ('"Archivo",ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif',
                     '"Archivo",ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif'),
    "e-ink-paper": ('"Source Serif 4",ui-serif,Georgia,"Times New Roman",serif',
                    '"Source Serif 4",ui-serif,Georgia,"Times New Roman",serif'),
    "bauhaus": ('"Jost",ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif',
                '"Jost",ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif'),
    "claymorphism": ('"Nunito",ui-rounded,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif',
                     '"Nunito",ui-rounded,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif'),
}

SKIN = {
    "neubrutalism": """
/* ===== style: neubrutalism ==========================================
   The identity is the hard offset shadow. It is a DUPLICATE of the shape
   drawn behind it in the border's own black -- zero blur, zero opacity
   change -- so it reads as printed, not as depth. SVG has no box-shadow,
   so it comes from a drop-shadow filter with 0 blur radius.                */
.node__shape{stroke:#000;stroke-width:3px;stroke-opacity:1;rx:0;ry:0;
  filter:drop-shadow(4px 4px 0 #000)}
.node__label{font-weight:800;letter-spacing:-.01em}
.edge{stroke:#000;stroke-width:3px;stroke-opacity:1;stroke-linejoin:miter;stroke-linecap:butt}
.marker{fill:#000}
@media (prefers-color-scheme: dark){
  .node__shape{stroke:#fff;filter:drop-shadow(4px 4px 0 #fff)}
  .edge{stroke:#fff}
  .marker{fill:#fff}
}
@media (prefers-reduced-motion: reduce){
  .node__shape{filter:drop-shadow(4px 4px 0 #000) !important}
}
""",
    "e-ink-paper": """
/* ===== style: e-ink-paper ===========================================
   No hue exists here, so role rests on the grey LEVEL plus the label and
   the mono chip -- the same contract hud-monochrome uses, which is why
   neither ships a colour legend. Motion is deliberately sparse: e-ink
   panels smear, and the style is meant to survive being printed.          */
.diagram__canvas{background-image:
  radial-gradient(color-mix(in srgb, var(--ink) 7%, transparent) .5px, transparent .5px);
  background-size:3px 3px}
.node__shape{rx:2;ry:2;stroke-width:1px;stroke-opacity:1}
.node--primary .node__shape{stroke-width:2px}
.node__label{font-weight:600}
.node__sub{font-family:var(--font-mono, ui-monospace, monospace)}
.edge{stroke-width:1px;stroke-opacity:1;stroke-linejoin:miter}
""",
    "bauhaus": """
/* ===== style: bauhaus ===============================================
   Three hues only, so any role past the third shares a colour -- the
   shape glyph and the label are what keep them apart. Everything is
   square, every angle is right, and the shadow is a hard offset.          */
.node__shape{rx:0;ry:0;stroke:#121212;stroke-width:2px;stroke-opacity:1;
  filter:drop-shadow(4px 4px 0 rgba(18,18,18,.9))}
.node__label{text-transform:uppercase;letter-spacing:.04em;font-weight:600}
.edge{stroke:#121212;stroke-width:2px;stroke-opacity:1;stroke-linejoin:miter}
.marker{fill:#121212}
@media (prefers-color-scheme: dark){
  .node__shape{stroke:#f5f2eb;filter:drop-shadow(4px 4px 0 rgba(245,242,235,.85))}
  .edge{stroke:#f5f2eb}
  .marker{fill:#f5f2eb}
}
""",
    "claymorphism": """
/* ===== style: claymorphism ==========================================
   A clay form has no outline: the edge is a light rim on top and a dark
   rim underneath, over a wide soft cast shadow. SVG cannot do an inset
   shadow, so the rim is two stacked 1px drop-shadows in opposite
   directions -- the cheapest honest stand-in.                             */
.node__shape{rx:24;ry:24;stroke:none;
  filter:drop-shadow(0 -1.5px 0 rgba(255,255,255,.9))
         drop-shadow(0 2px 0 rgba(47,44,69,.13))
         drop-shadow(0 12px 20px rgba(47,44,69,.18))}
.node--primary .node__shape{filter:drop-shadow(0 -2px 0 rgba(255,255,255,.95))
         drop-shadow(0 3px 0 rgba(47,44,69,.16))
         drop-shadow(0 16px 26px rgba(47,44,69,.22))}
.node__label{font-weight:700}
.edge{stroke-width:4px;stroke-opacity:.85;stroke-linecap:round;stroke-linejoin:round}
@media (prefers-color-scheme: dark){
  .node__shape{filter:drop-shadow(0 -1.5px 0 rgba(255,255,255,.16))
         drop-shadow(0 2px 0 rgba(0,0,0,.5))
         drop-shadow(0 12px 20px rgba(0,0,0,.45))}
}
""",
}


def role_block(style_id, dark, indent):
    """Emit the seven role token lines, verbatim from color-semantics.csv.

    Filtered to the style's Default Palette: since 2026-08-26 a style may have
    several named palettes, and keying only by Role would silently let whichever
    palette sorted last win -- a base template must ship the style's default.
    """
    default = next((r.get("Default Palette", "house") for r in csv.DictReader(STYLES.open(encoding="utf-8"))
                    if r["Style ID"] == style_id), "house")
    rows = {r["Role"]: r for r in csv.DictReader(COLORS.open(encoding="utf-8"))
            if r["Style ID"] == style_id and r.get("Palette") == default}
    if len(rows) != 7:
        raise SystemExit(f"{style_id}: expected 7 '{default}' colour rows, found {len(rows)}")
    out = []
    for role in ROLES:
        r = rows[role]
        f, s, a, o = ((r["Dark Fill"], r["Dark Stroke"], r["Dark Accent"], r["Dark On Color"])
                      if dark else (r["Fill"], r["Stroke"], r["Accent"], r["On Color"]))
        out.append(f"{indent}--role-{role}:{f};".ljust(len(indent) + 26)
                   + f"--ink-{role}:{s};".ljust(22)
                   + f"--accent-{role}:{a};".ljust(24)
                   + f"--on-{role}:{o};")
    return "\n".join(out)


def apply_tokens(block, tokens):
    for name, value in tokens.items():
        block = re.sub(rf"(\n\s*{re.escape(name)}:)[^;]*;", rf"\g<1>{value};", block, count=1)
    return block


def build(style_id):
    src = REF.read_text(encoding="utf-8")
    light, dark = SURFACE[style_id]

    # split at the dark-mode media query so each :root is edited in isolation
    marker = "@media (prefers-color-scheme: dark){"
    head, tail = src.split(marker, 1)

    head = apply_tokens(head, light)
    head = re.sub(r"( *--role-client:.*?--on-infra:[^;]*;)", role_block(style_id, False, "  "),
                  head, count=1, flags=re.S)
    tail = apply_tokens(tail, dark)
    tail = re.sub(r"( *--role-client:.*?--on-infra:[^;]*;)", role_block(style_id, True, "    "),
                  tail, count=1, flags=re.S)

    out = head + marker + tail

    title_f, label_f = TYPO[style_id]
    out = re.sub(r"(\n  --font-title:)[^\n]*", rf"\g<1>{title_f};", out, count=1)
    out = re.sub(r"(\n  --font-label:)[^\n]*", rf"\g<1>{label_f};", out, count=1)
    out = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^"]*">',
                 FONTS[style_id], out, count=1)
    out = out.replace("</style>", SKIN[style_id].strip("\n") + "\n</style>", 1)

    out = out.replace("<title>Checkout request flow — flat-minimal</title>",
                      f"<title>Checkout request flow — {style_id}</title>")
    out = out.replace(
        "     STYLE: flat-minimal  (data/styles.csv#flat-minimal) — REFERENCE TEMPLATE",
        f"     STYLE: {style_id}  (data/styles.csv#{style_id})\n"
        f"     Scaffolded from flat-minimal.html by diagram-director/scripts/scaffold_style_template.py.\n"
        f"     Class names are byte-identical to the reference so every snippet in\n"
        f"     templates/snippets/ stays portable; only tokens, fonts and the skin differ.")

    dst = REPO / "templates" / "base" / f"{style_id}.html"
    dst.write_text(out, encoding="utf-8")
    print(f"{dst.relative_to(REPO)}: {len(out.splitlines())} lines")


if __name__ == "__main__":
    ids = sys.argv[1:] or list(SURFACE)
    for sid in ids:
        build(sid)
