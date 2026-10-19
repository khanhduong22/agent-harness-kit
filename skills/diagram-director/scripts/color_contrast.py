#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WCAG 2.x relative luminance and contrast ratio, recomputed from raw hex
values in stdlib only. Split out of validate_checks.py so the contrast math
can be sanity-checked (and unit-tested) independently of the CSV plumbing.

Verified against two known pairs: #000000/#ffffff = 21:1, #767676/#ffffff = 4.54:1.
"""


def _linearize(channel):
    return channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color):
    """WCAG relative luminance (0..1) of a 6-digit '#rrggbb' color."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * _linearize(r) + 0.7152 * _linearize(g) + 0.0722 * _linearize(b)


def contrast_ratio(hex_a, hex_b):
    """WCAG contrast ratio between two '#rrggbb' colors, >=1.0."""
    la, lb = relative_luminance(hex_a), relative_luminance(hex_b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)
