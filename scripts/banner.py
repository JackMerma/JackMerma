#!/usr/bin/env python3
"""Generates the terminal banner: a stippled portrait next to a SYSTEM.INFO grid.

Run manually and commit the result; it only changes when the portrait or
assets/profile.json does, so it is deliberately not wired into a workflow.

    python scripts/banner.py --portrait assets/portrait.png \
        --profile assets/profile.json -o assets/banner
"""

import argparse
import json
from xml.sax.saxutils import escape

import dotify
from theme import PALETTES, THEMES

W, H = 1060, 510
TITLE_H = 46
PANEL_Y, PANEL_H = 62, 428

LEFT_X, LEFT_W = 20, 352
RIGHT_X, RIGHT_W = 388, 652

COLS, ROWS = 300, 340
STIPPLE_X = LEFT_X + (LEFT_W - COLS) // 2
STIPPLE_Y = PANEL_Y + 46

ROW_X = RIGHT_X + 20
ROW_W = RIGHT_W - 40
ROW_CHARS = 78
ROW_TOP = 120
ROW_STEP = 21

# The portrait is already cropped to frame; these only tune the stipple itself.
# On the dark theme the dots read as light, so the lit side of the face gets
# the density; on white they read as ink and the mapping flips. Densities stay
# well under 1 and the dot under one cell, or the dots merge into a silhouette.
STIPPLE_OPTS = {
    "dark": dict(ink_dark=0.14, ink_light=0.52, gamma=0.8, sharpen=160, fade=0.12),
    "light": dict(ink_dark=0.52, ink_light=0.10, gamma=1.0, sharpen=160, fade=0.12),
}
DOT_WIDTH = 0.8


def info_row(label, value):
    """One fixed-width monospace row: label, leader dots, right-aligned value.

    Every row is padded to the same character count and then forced to the
    same rendered width, so the columns line up even when the viewer has no
    JetBrains Mono and falls back to some other monospace face.
    """
    leader = ROW_CHARS - len(label) - len(value) - 2
    return label, " " + "·" * max(leader, 1) + " ", value


def render(theme_name, points, profile):
    t = PALETTES[theme_name]
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="JetBrains Mono, DejaVu Sans Mono, ui-monospace, monospace">',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="{t["bg"]}" stroke="{t["border"]}"/>',
        # window chrome
        '<circle cx="26" cy="24" r="6" fill="#ff5f56"/>',
        '<circle cx="46" cy="24" r="6" fill="#ffbd2e"/>',
        '<circle cx="66" cy="24" r="6" fill="#27c93f"/>',
        f'<text x="{W/2}" y="29" font-size="13" text-anchor="middle" fill="{t["muted"]}">'
        f'profile.sh <tspan fill="{t["accent"]}">--live</tspan></text>',
        f'<line x1="0" y1="{TITLE_H}" x2="{W}" y2="{TITLE_H}" stroke="{t["border"]}"/>',
        # panels
        f'<rect x="{LEFT_X}.5" y="{PANEL_Y}.5" width="{LEFT_W}" height="{PANEL_H}" rx="10" '
        f'fill="{t["panel"]}" stroke="{t["border"]}"/>',
        f'<rect x="{RIGHT_X}.5" y="{PANEL_Y}.5" width="{RIGHT_W}" height="{PANEL_H}" rx="10" '
        f'fill="{t["panel"]}" stroke="{t["border"]}"/>',
        # left panel header / footer
        f'<text x="{LEFT_X+20}" y="86" font-size="12" font-weight="600" fill="{t["accent"]}">VISUAL.MAP</text>',
        f'<text x="{LEFT_X+LEFT_W-20}" y="86" font-size="10" text-anchor="end" fill="{t["muted"]}">'
        f'{COLS}×{ROWS} / 1-BIT</text>',
        f'<text x="{LEFT_X+20}" y="470" font-size="10" fill="{t["muted"]}">'
        f'PTS {len(points)} · FS/SERPENTINE</text>',
    ]

    # corner brackets around the portrait
    bx0, by0 = STIPPLE_X - 8, STIPPLE_Y - 8
    bx1, by1 = STIPPLE_X + COLS + 8, STIPPLE_Y + ROWS + 8
    arm = 11
    for x, y, dx, dy in ((bx0, by0, 1, 1), (bx1, by0, -1, 1), (bx0, by1, 1, -1), (bx1, by1, -1, -1)):
        parts.append(
            f'<path d="M{x} {y + dy*arm}V{y}H{x + dx*arm}" fill="none" stroke="{t["dim"]}" stroke-width="1.2"/>'
        )

    # the portrait itself: one path, one zero-length dash per inked cell
    dots = "".join(f"M{x} {y}h.01" for x, y in points)
    parts.append(
        f'<g transform="translate({STIPPLE_X},{STIPPLE_Y})">'
        f'<path d="{dots}" fill="none" stroke="{t["accent"]}" stroke-width="{DOT_WIDTH}" stroke-linecap="round"/>'
        f'</g>'
    )

    # right panel header: SYSTEM.INFO, live indicator, handle chip
    handle = profile["handle"]
    chip_w = len(handle) * 6.6 + 22
    chip_x = RIGHT_X + RIGHT_W - 20 - chip_w
    parts += [
        f'<text x="{ROW_X}" y="86" font-size="12" font-weight="600" fill="{t["accent"]}">SYSTEM.INFO</text>',
        f'<circle cx="{chip_x-52:.1f}" cy="81.5" r="3.5" fill="#ff6b6b"/>',
        f'<text x="{chip_x-43:.1f}" y="86" font-size="10" fill="{t["muted"]}">LIVE</text>',
        f'<rect x="{chip_x:.1f}" y="73" width="{chip_w:.1f}" height="18" rx="9" fill="{t["accent"]}"/>',
        f'<text x="{chip_x + chip_w/2:.1f}" y="86" font-size="11" font-weight="600" '
        f'text-anchor="middle" fill="{t["accent_ink"]}">{escape(handle)}</text>',
    ]

    # info rows
    for i, row in enumerate(profile["rows"]):
        label, leader, value = info_row(row["label"], row["value"])
        y = ROW_TOP + i * ROW_STEP
        parts.append(
            f'<text x="{ROW_X}" y="{y}" font-size="13" textLength="{ROW_W}" lengthAdjust="spacingAndGlyphs" '
            f'fill="{t["text"]}" xml:space="preserve">'
            f'<tspan fill="{t["muted"]}">{escape(label)}</tspan>'
            f'<tspan fill="{t["dim"]}">{leader}</tspan>'
            f'<tspan>{escape(value)}</tspan></text>'
        )

    # right panel footer
    parts += [
        f'<circle cx="{ROW_X+3}" cy="466.5" r="3" fill="{t["accent"]}"/>',
        f'<text x="{ROW_X+13}" y="470" font-size="10" fill="{t["accent"]}">ALL SYSTEMS NOMINAL</text>',
        f'<text x="{RIGHT_X+RIGHT_W-20}" y="470" font-size="10" text-anchor="end" fill="{t["muted"]}">'
        f'{escape(profile["node"])}</text>',
        "</svg>",
    ]
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--portrait", required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("-o", "--out", required=True, help="output path prefix (no extension)")
    args = ap.parse_args()

    with open(args.profile, encoding="utf-8") as f:
        profile = json.load(f)

    for theme in THEMES:
        points = dotify.stipple(args.portrait, COLS, ROWS, **STIPPLE_OPTS[theme])
        out_path = f"{args.out}-{theme}.svg"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(render(theme, points, profile))
        print(f"wrote {out_path} ({len(points)} points)")


if __name__ == "__main__":
    main()
