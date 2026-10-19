#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render a composed blueprint spec (see blueprint_composer.compose) as the
9 fixed sections, in markdown or ascii. Both renderers read from the same
_sections() list -- no duplicated content logic (DRY).

An abstained spec (no diagram type matched) renders as the abstain message
instead, in both formats: there is nothing to fill nine sections with, and a
half-filled blueprint reads as a composed one.
"""

# Wording matters more than usual here: the previous "Nodes" heading was read
# as a paste list and shipped a chat diagram for an auction prompt.
CATALOG_PREAMBLE = [
    "CATALOG EXAMPLES -- NOT a paste list, NOT this diagram's component list.",
    "These are components the diagram type tends to involve (the type's Node Kinds",
    "cell freezes ONE worked example of the archetype). Build the real component",
    "list by querying `--domain components` once per component in your solution",
    "sheet and recording the hits in the Phase 3 mapping table",
    "(references/workflow-phases.md). Copy a shape from below only when that same",
    "Component ID came back from your own query.",
    "",
]

ABSTAIN_HEAD = "BLUEPRINT ABSTAINED -- nothing was composed."


def render_abstain(spec):
    """The type-miss output. No type is guessed and no default is substituted."""
    return "\n".join([
        ABSTAIN_HEAD,
        "=" * 60,
        f"Scenario: {spec['scenario']}",
        f"Reason:   {spec['abstain_reason']}",
        "",
        "There is no default diagram type on purpose. A type carries the layout, the",
        "edge semantics, the recommended motion set and the anti-patterns with it, so",
        "a guessed type is four wrong answers wearing the dataset's authority.",
        "",
        "Do one of these, then re-run:",
        "  1. Name the type yourself:",
        "       python3 diagram-director/scripts/search.py \"<scenario>\" --blueprint --type <type-id>",
        # De-funnelled deliberately: this list used to name system-design types only,
        # which read as "rephrase until one of these fits" to anyone whose scenario
        # belongs to another genre. It now names the SPLIT, and promises no pack.
        "  2. Rephrase the scenario in the vocabulary of the genre being searched -- this",
        f"     run searched `{spec.get('genre', 'system-design')}`. The genre is what the BOXES ARE",
        "     (deployed software components vs participants, work items and steps), so a",
        "     scenario whose cast belongs to another genre abstains here however it is",
        "     worded; that one is re-run with `--genre <name>`, and only a genre this skill",
        "     actually ships can answer it. Item 3 prints THIS genre's real type",
        "     vocabulary -- read it rather than guessing at the words.",
        "  3. See what the type domain thinks is close:",
        "       python3 diagram-director/scripts/search.py \"<scenario>\" --domain types -n 5",
        "",
        "Do NOT proceed on a type you picked from memory without saying so.",
        *([""] + [f"Warning: {w}" for w in spec["warnings"]] if spec.get("warnings") else []),
    ]) + "\n"


def _sections(spec):
    """Build the 9 fixed sections as (heading, body_lines)."""
    type_row, style_row, layout_row = spec["type"], spec["style"], spec["layout"]
    sections = [("Meta", [
        "AUTHORITATIVE in this blueprint: diagram type, layout, style, palette.",
        "NOT authoritative: the component catalog in section 2 (see its header).",
        "",
        f"Diagram type: {type_row.get('Name')} ({type_row.get('Type ID')})" +
        (" [named via --type]" if spec.get("type_was_named") else " [matched from the scenario]"),
        f"Style: {style_row.get('Name')} ({style_row.get('Style ID')})" +
        (" [fallback]" if spec["style_is_fallback"] else ""),
        f"Layout: {layout_row.get('Name')} ({layout_row.get('Layout ID')})",
        f"Palette: {style_row.get('Default Palette') or 'house'} (style default)",
        f"Target: {spec['target']}",
        f"Runtime: {style_row.get('Runtime')}",
        f"CDN Deps: {style_row.get('CDN Deps') or 'none'}",
    ])]

    nodes = list(CATALOG_PREAMBLE)
    # One shape per row, already resolved for this style (blueprint_style
    # .resolve_catalog_shapes) -- never the raw multi-style Shape Hint cell.
    nodes += [f"Shapes below are resolved for style '{style_row.get('Style ID')}'.", ""]
    nodes += ["id | label | role | shape | shape from | snippet ref", "---|---|---|---|---|---"]
    nodes += [f"{c.get('Component ID')} | {c.get('Name')} | {c.get('Semantic Role')} | "
              f"{c.get('Shape Hint')} | {c.get('Shape Hint Source')} | {c.get('Snippet Ref')}"
              for c in spec["catalog_components"]]
    sections.append(("Component catalog (illustrative -- query your own)", nodes))

    sections.append(("Edges & semantics", [
        type_row.get("Edge Semantics", "(none specified)"),
        f"Labeling level: {type_row.get('Labeling Level')}",
        f"Anti-patterns to avoid: {type_row.get('Anti-Patterns')}",
    ]))

    sections.append(("Layout rules", [
        f"Flow direction: {layout_row.get('Flow Direction')}",
        f"Spacing rules: {layout_row.get('Spacing Rules')}",
        f"Grouping rule: {layout_row.get('Grouping Rule')}",
        f"Node count sweet spot: {layout_row.get('Node Count Sweet Spot')} "
        f"(the catalog above lists {spec['catalog_node_count']}; measure YOUR list against this)",
        "The sweet spot is ADVISORY -- guidance for the default case, not a gate. A tier or pane "
        "that passes the hard gates (containment at its hold, the per-gate text floor, clearance) "
        "may exceed it when the storyboard demands; the solution sheet must then say why.",
    ]))

    motion_lines = ["(fallback set -- see Warnings)"] if spec["motions_is_fallback"] else []
    motion_lines += [
        f"{m.get('Motion ID')} -> primary flow path | duration {m.get('Duration')} | "
        f"easing {m.get('Easing')} | stagger {m.get('Stagger Rule')} | "
        f"reduced-motion: {m.get('Reduced-Motion Fallback')} | recipe: {m.get('Recipe Ref')}"
        for m in spec["motions"]
    ]
    sections.append(("Motion assignments", motion_lines or ["(none resolved)"]))

    palette_lines = []
    for row in spec["palette"]:
        role = row.get("Role")
        palette_lines.append(
            f"--color-{role}-fill: {row.get('Fill')}; --color-{role}-stroke: {row.get('Stroke')}; "
            f"--color-{role}-accent: {row.get('Accent')}; --color-{role}-on: {row.get('On Color')};"
        )
        palette_lines.append(
            f"--color-{role}-dark-fill: {row.get('Dark Fill')}; --color-{role}-dark-stroke: {row.get('Dark Stroke')}; "
            f"--color-{role}-dark-accent: {row.get('Dark Accent')}; --color-{role}-dark-on: {row.get('Dark On Color')};"
        )
    sections.append(("Palette tokens", palette_lines or ["(style has no rows for its default palette)"]))

    # snippet_files entries already start with "snippets/" (Snippet Ref cells
    # are "snippets/<file>#<id>" per contract C3) -- do not prepend it again.
    template_lines = [f"Base template: {spec['template_path']}" +
                       (" [substituted]" if spec["template_is_fallback"] else "")]
    if spec["catalog_snippet_files"]:
        template_lines.append(
            "Snippet files behind the CATALOG (illustrative): " +
            ", ".join(f"templates/{f}" for f in spec["catalog_snippet_files"]) +
            " -- copy the snippet files your OWN component queries name instead.")
    sections.append(("Template to copy", template_lines))

    sections.append(("Checklist", [
        "[ ] every drawn shape traces to a Phase 3 mapping-table row from your own "
        "--domain components query (the catalog above is not that table)",
        "[ ] prefers-reduced-motion block renders the informative end state for every animated element",
        "[ ] every SVG root has role=\"img\" plus <title> and <desc>",
        f"[ ] contrast verified for style '{style_row.get('Style ID')}' (validate_csv.py enforces this)",
        "[ ] no meaning encoded in color alone -- pair with label, icon, or line style",
        f"[ ] animated edge count ({len(spec['motions'])}) checked against MAX_ANIMATED_EDGES",
    ]))

    sections.append(("Warnings", spec["warnings"] or ["(none)"]))
    return sections


def render_markdown(spec):
    """Render the composed spec as the 9 fixed markdown sections."""
    if spec.get("abstained"):
        return render_abstain(spec)
    lines = [f"# Blueprint: {spec['scenario']}", ""]
    for i, (heading, body) in enumerate(_sections(spec), 1):
        lines.append(f"## {i}. {heading}")
        lines.extend(body)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_ascii(spec):
    """Render the composed spec as the same 9 sections, box-drawn for a terminal."""
    if spec.get("abstained"):
        return render_abstain(spec)
    lines = [f"BLUEPRINT: {spec['scenario']}", "=" * 60]
    for i, (heading, body) in enumerate(_sections(spec), 1):
        title = f"{i}. {heading}"
        lines += [title, "-" * len(title), *body, ""]
    return "\n".join(lines).rstrip() + "\n"
