#!/usr/bin/env python3
"""One-off authoring helper: append four styles + their colour rows.

Every palette here is CHECKED with the repo's own contrast function before it is
written, against the same thresholds the validator enforces (on-colour vs fill
>= 4.5:1, stroke vs canvas >= 3.0:1, both light and dark). Authoring a style by
eye and letting validate_csv.py reject it afterwards wastes a round trip; this
fails loudly at the source instead.

Run once from the repo root:  python3 diagram-director/scripts/add_styles_batch.py
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from color_contrast import contrast_ratio  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
STYLES = REPO / "data" / "styles.csv"
COLORS = REPO / "data" / "color-semantics.csv"

ROLES = ["client", "service", "data", "async", "external", "error", "infra"]

# --------------------------------------------------------------------------
# style rows, keyed by Style ID. Column order is read from the CSV header.
# --------------------------------------------------------------------------
STYLE_ROWS = {
    "neubrutalism": {
        "Name": "Neubrutalism",
        "Keywords": "neubrutalism; brutalist; hard-shadow; acid; sticker; bold-border; playful; indie",
        "Stroke Treatment": "uniform 3px pure-black border on every shape; no tapering; no opacity variation",
        "Fill Treatment": "flat acid fills at full saturation; zero gradients; a hard 4px offset shadow in the same black as the border",
        "Palette Mood": "acid yellow, hot red, sky blue and mint on warm paper; loud, deliberately unsubtle, confident",
        "Typography": "Archivo Black or Inter 800 for node titles; JetBrains Mono for sub-labels; nothing lighter than 600",
        "Background": "warm paper (#fffdf5) with no grid; the shadows do the depth work",
        "Canvas Light": "#fffdf5",
        "Canvas Dark": "#141414",
        "Node Rendering": "square-cornered rectangle with a 3px black border and a solid 4px offset shadow; no radius anywhere",
        "Connector Rendering": "3px black orthogonal lines with a solid triangular arrowhead; joins stay square",
        "Motion Affinity": "dash-flow|packet-travel|queue-fill|state-transition-arrow|fanout-broadcast|scale-out-spawn|batch-tick|node-boot-sequence",
        "Runtime": "css-only",
        "CDN Deps": "",
        "Best For": "developer-tool product sites; indie product docs; workshop handouts; anything that should look built rather than designed",
        "Do Not Use For": "enterprise compliance decks; dense topologies over 15 nodes; contexts where the loud palette reads as unserious",
        "Dark Mode": "supported",
        "Complexity": "low",
        "Accessibility Notes": "the black border carries the shape and the acid fill only tints it, so role never rests on colour alone; the offset shadow must stay the same black as the border or it reads as a second element",
        "CSS Techniques": "box-shadow with zero blur for the hard offset; rx:0 on every shape; no filter, no gradient",
        "Template Status": "shipped",
        "Status": "active",
        "Aliases": "neo-brutalism; hard-shadow; sticker-ui; acid-brutalist",
    },
    "e-ink-paper": {
        "Name": "E-Ink Paper",
        "Keywords": "e-ink; paper; print; monochrome; kindle; serif; grain; document; low-power",
        "Stroke Treatment": "1px hairline ink; weight is the only emphasis axis, never colour",
        "Fill Treatment": "four flat grey levels standing in for what colour would carry elsewhere; a faint dither texture on the darkest level",
        "Palette Mood": "ink black on off-white paper; no hue at all, the way print has none",
        "Typography": "a serif (Source Serif / Georgia) for node titles, mono for data; print measure and generous leading",
        "Background": "off-white paper (#fdfbf7) with a faint grain overlay; no grid",
        "Canvas Light": "#fdfbf7",
        "Canvas Dark": "#1a1a1a",
        "Node Rendering": "square-cornered rectangle, hairline border, grey level chosen by role; a mono role chip in the corner",
        "Connector Rendering": "hairline orthogonal lines; open arrowheads; async as a dashed run",
        "Motion Affinity": "batch-tick|state-transition-arrow|connection-draw-in|node-boot-sequence|queue-fill",
        "Runtime": "css-only",
        "CDN Deps": "",
        "Best For": "print handouts; PDF specs; e-reader documentation; anywhere the diagram must survive a photocopier",
        "Do Not Use For": "motion-led explainers; diagrams whose story needs colour coding; conference-screen work",
        "Dark Mode": "supported",
        "Complexity": "low",
        "Accessibility Notes": "no colour is used at all, so no colour legend exists and none is needed; role is carried by the label, the mono chip and the grey level, and every grey level clears 4.5:1 against the ink; motion is deliberately minimal because e-ink panels smear",
        "CSS Techniques": "repeating-radial-gradient for the grain; stroke-dasharray for the dither; transition-free state changes",
        "Template Status": "shipped",
        "Status": "active",
        "Aliases": "eink; paper-print; kindle-style; monochrome-print",
    },
    "bauhaus": {
        "Name": "Bauhaus",
        "Keywords": "bauhaus; geometric; primary-colors; constructivist; modernist; poster; circle-square-triangle",
        "Stroke Treatment": "2px black rule on every form; the line is structure, never decoration",
        "Fill Treatment": "flat primary red, blue and yellow plus black and off-white; each form takes exactly one flat colour",
        "Palette Mood": "the three primaries against black on off-white; disciplined, constructed, poster-like",
        "Typography": "a geometric sans (Futura-like: Jost, Poppins) in caps for titles; mono for data",
        "Background": "off-white (#f5f2eb) with an optional widely-spaced dot grid",
        "Canvas Light": "#f5f2eb",
        "Canvas Dark": "#121212",
        "Node Rendering": "square-cornered rectangle in one flat primary, 2px black rule, hard 4px offset shadow; role marked by a small circle/square/triangle glyph",
        "Connector Rendering": "2px black lines, right angles only, solid triangular heads; no curves anywhere",
        "Motion Affinity": "dash-flow|packet-travel|state-transition-arrow|batch-tick|connection-draw-in|fanout-broadcast|queue-fill",
        "Runtime": "css-only",
        "CDN Deps": "",
        "Best For": "teaching posters; conference slides; editorial explainers; anything that benefits from looking composed",
        "Do Not Use For": "dense infrastructure maps; subtle brand contexts; diagrams needing more than three role colours",
        "Dark Mode": "supported",
        "Complexity": "medium",
        "Accessibility Notes": "only three hues exist, so roles beyond three share a colour and must be separated by the shape glyph and the label; the black rule keeps every form legible if colour is lost entirely",
        "CSS Techniques": "box-shadow with zero blur; clip-path for the triangle glyph; rx:0 throughout",
        "Template Status": "shipped",
        "Status": "active",
        "Aliases": "constructivist; primary-geometric; modernist-poster; de-stijl-adjacent",
    },
    "claymorphism": {
        "Name": "Claymorphism",
        "Keywords": "claymorphism; clay; puffy; soft-3d; pastel; rounded; friendly; toy; playful",
        "Stroke Treatment": "no visible border; the form is defined by a light rim highlight and a soft cast shadow",
        "Fill Treatment": "soft pastel fills with a paired inner highlight and inner shadow so each shape reads as moulded rather than drawn",
        "Palette Mood": "milky lavender ground with candy pastels; soft, friendly, low-contrast by nature so text must work harder",
        "Typography": "a rounded sans (Nunito, Quicksand) at 600+; mono only for data",
        "Background": "milky lavender (#f4f1fb); no grid, so the shadows read cleanly",
        "Canvas Light": "#f4f1fb",
        "Canvas Dark": "#1d1a2b",
        "Node Rendering": "heavily rounded rectangle (24px+) with a light top-inner rim, a dark bottom-inner shadow and a wide soft drop shadow",
        "Connector Rendering": "thick soft-capped pastel lines with a faint shadow; rounded joins; blunt rounded arrowheads",
        "Motion Affinity": "pulse-glow|queue-fill|packet-travel|heartbeat|scale-out-spawn|fanout-broadcast|connection-draw-in",
        "Runtime": "css-only",
        "CDN Deps": "",
        "Best For": "onboarding material; product marketing; educational content for non-technical audiences; kids/consumer contexts",
        "Do Not Use For": "formal architecture reviews; dense diagrams (the shadows need breathing room); print output",
        "Dark Mode": "supported",
        "Complexity": "medium",
        "Accessibility Notes": "pastel fills sit close to the ground, so the on-colour must be a deep tint of the same hue rather than mid-grey; the shape has no border, meaning shadow contrast is the only edge cue and must not be softened further",
        "CSS Techniques": "layered inset box-shadow (light top + dark bottom) plus an outer drop-shadow; large border-radius; no gradient fills",
        "Template Status": "shipped",
        "Status": "active",
        "Aliases": "clay-ui; puffy-3d; soft-clay; play-doh-ui",
    },
}

# --------------------------------------------------------------------------
# colour rows: (fill, stroke, accent, on) light  +  (fill, stroke, accent, on) dark
# --------------------------------------------------------------------------
PALETTES = {
    "neubrutalism": {
        "client":   (("#a5d8ff", "#000000", "#1971c2", "#000000"), ("#1971c2", "#ffffff", "#a5d8ff", "#ffffff")),
        "service":  (("#ffd43b", "#000000", "#e8590c", "#000000"), ("#a16207", "#ffffff", "#ffd43b", "#ffffff")),
        "data":     (("#b2f2bb", "#000000", "#2f9e44", "#000000"), ("#166534", "#ffffff", "#b2f2bb", "#ffffff")),
        "async":    (("#ffc9c9", "#000000", "#e03131", "#000000"), ("#9f1239", "#ffffff", "#ffc9c9", "#ffffff")),
        "external": (("#e9ecef", "#000000", "#495057", "#000000"), ("#374151", "#ffffff", "#e9ecef", "#ffffff")),
        "error":    (("#ff6b6b", "#000000", "#c92a2a", "#000000"), ("#991b1b", "#ffffff", "#ff6b6b", "#ffffff")),
        "infra":    (("#dee2e6", "#000000", "#343a40", "#000000"), ("#262626", "#ffffff", "#dee2e6", "#ffffff")),
    },
    # role is carried by grey LEVEL, label and chip -- there is no hue to lose
    "e-ink-paper": {
        "client":   (("#ffffff", "#1a1a1a", "#4a4a4a", "#1a1a1a"), ("#2e2e2e", "#f2efe9", "#b8b8b8", "#f2efe9")),
        "service":  (("#efece6", "#1a1a1a", "#4a4a4a", "#1a1a1a"), ("#3a3a3a", "#f2efe9", "#b8b8b8", "#f2efe9")),
        "data":     (("#e4e0d8", "#1a1a1a", "#3a3a3a", "#1a1a1a"), ("#454545", "#f2efe9", "#c9c9c9", "#f2efe9")),
        "async":    (("#f5f2ec", "#1a1a1a", "#5a5a5a", "#1a1a1a"), ("#333333", "#e8e5df", "#b0b0b0", "#e8e5df")),
        "external": (("#d9d5cc", "#1a1a1a", "#2e2e2e", "#1a1a1a"), ("#4f4f4f", "#f2efe9", "#d0d0d0", "#f2efe9")),
        "error":    (("#1a1a1a", "#1a1a1a", "#fdfbf7", "#fdfbf7"), ("#f2efe9", "#f2efe9", "#1a1a1a", "#1a1a1a")),
        "infra":    (("#ebe8e1", "#1a1a1a", "#4a4a4a", "#1a1a1a"), ("#383838", "#f2efe9", "#bcbcbc", "#f2efe9")),
    },
    "bauhaus": {
        "client":   (("#1040c0", "#121212", "#f0c020", "#ffffff"), ("#1040c0", "#f5f2eb", "#f0c020", "#ffffff")),
        "service":  (("#d02020", "#121212", "#f0c020", "#ffffff"), ("#d02020", "#f5f2eb", "#f0c020", "#ffffff")),
        "data":     (("#f0c020", "#121212", "#1040c0", "#121212"), ("#f0c020", "#f5f2eb", "#1040c0", "#121212")),
        "async":    (("#ffffff", "#121212", "#d02020", "#121212"), ("#2a2a2a", "#f5f2eb", "#f0c020", "#f5f2eb")),
        "external": (("#e2ded4", "#121212", "#1040c0", "#121212"), ("#333333", "#f5f2eb", "#bdbdbd", "#f5f2eb")),
        "error":    (("#121212", "#121212", "#d02020", "#f5f2eb"), ("#d02020", "#f5f2eb", "#f0c020", "#ffffff")),
        "infra":    (("#cfcabd", "#121212", "#121212", "#121212"), ("#3d3d3d", "#f5f2eb", "#cfcabd", "#f5f2eb")),
    },
    # pastel on pastel: the on-colour is always a DEEP tint of the fill's own hue
    # The card itself has no border -- the template renders the rim as an inner
    # highlight. The Stroke token still has to be legible on the canvas because
    # it is also the connector colour, so it holds a DEEP tint of the hue rather
    # than the pale rim colour a clay card would suggest.
    "claymorphism": {
        "client":   (("#cfe0ff", "#2f5fc4", "#5b8def", "#17356b"), ("#33406b", "#8fb3ff", "#b7ceff", "#e6eeff")),
        "service":  (("#e2d5ff", "#6d3fd4", "#8b5cf6", "#3b1d75"), ("#3b3164", "#c4b5fd", "#ddd2ff", "#f0eaff")),
        "data":     (("#cdf3e4", "#128a68", "#34c79a", "#0d4c39"), ("#24493f", "#7ee0c0", "#a9ecd8", "#e4fbf3")),
        "async":    (("#ffe8c7", "#a56a0c", "#f59e0b", "#6b3d05"), ("#4d3a1e", "#fbd38d", "#fde3b4", "#fff4e2")),
        "external": (("#e6e3f0", "#5f5a7c", "#8b86a8", "#33304a"), ("#33314a", "#b6b1d4", "#d2cfe6", "#efedf7")),
        "error":    (("#ffd6dd", "#c02745", "#f43f5e", "#6b0f22"), ("#4f2130", "#ffa8b8", "#ffc8d2", "#ffe8ed")),
        "infra":    (("#e4e1ee", "#57537a", "#8480a0", "#2f2c45"), ("#2f2c45", "#b3afcd", "#cdcae0", "#eceaf5")),
    },
}


def _check(label, fg, bg, floor):
    ratio = contrast_ratio(fg, bg)
    if ratio < floor:
        raise SystemExit(f"FAIL {label}: {fg} on {bg} = {ratio:.2f}:1, need {floor}:1")
    return ratio


def main():
    style_header = next(csv.reader(STYLES.open(encoding="utf-8")))
    color_header = next(csv.reader(COLORS.open(encoding="utf-8")))

    existing = {r["Style ID"] for r in csv.DictReader(STYLES.open(encoding="utf-8"))}
    new_ids = [sid for sid in STYLE_ROWS if sid not in existing]
    if not new_ids:
        print("nothing to add -- all four styles already present")
        return

    color_rows = []
    for sid in new_ids:
        canvas_l = STYLE_ROWS[sid]["Canvas Light"]
        canvas_d = STYLE_ROWS[sid]["Canvas Dark"]
        for role in ROLES:
            (fl, sl, al, ol), (fd, sd, ad, od) = PALETTES[sid][role]
            r_light = _check(f"{sid}/{role} light text", ol, fl, 4.5)
            r_dark = _check(f"{sid}/{role} dark text", od, fd, 4.5)
            _check(f"{sid}/{role} light stroke", sl, canvas_l, 3.0)
            _check(f"{sid}/{role} dark stroke", sd, canvas_d, 3.0)
            color_rows.append({
                # A style added here ships one palette and it is the house one;
                # named palettes (2026-08-26) are blessed separately, never batched.
                "Style ID": sid, "Palette": "house", "Role": role,
                "Fill": fl, "Stroke": sl, "Accent": al, "On Color": ol,
                "Dark Fill": fd, "Dark Stroke": sd, "Dark Accent": ad, "Dark On Color": od,
                "Contrast Note": f"{ol} on {fl} = {r_light:.1f}:1; dark {od} on {fd} = {r_dark:.1f}:1",
            })

    with STYLES.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=style_header)
        for sid in new_ids:
            w.writerow({"Style ID": sid, "Default Palette": "house", **STYLE_ROWS[sid]})
    with COLORS.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=color_header)
        for row in color_rows:
            w.writerow(row)

    print(f"added {len(new_ids)} styles, {len(color_rows)} colour rows -- all contrast checks passed")


if __name__ == "__main__":
    main()
