#!/usr/bin/env python3
"""Renders a radar/spider chart SVG (dark + light) from a JSON list of
{"label": str, "value": 0..1} entries. No external dependencies."""

import argparse
import json
import math

THEMES = {
    "dark": {
        "bg": "#0d1117",
        "grid": "#21262d",
        "axis": "#30363d",
        "fill": "#aa9bef",
        "fill_opacity": "0.28",
        "stroke": "#aa9bef",
        "text": "#c9d1d9",
        "muted": "#8b949e",
    },
    "light": {
        "bg": "#ffffff",
        "grid": "#d0d7de",
        "axis": "#d0d7de",
        "fill": "#6f5bd6",
        "fill_opacity": "0.18",
        "stroke": "#6f5bd6",
        "text": "#24292f",
        "muted": "#57606a",
    },
}

SIZE = 420
CENTER = SIZE / 2
RADIUS = 140
RINGS = 4


def point(angle, r):
    x = CENTER + r * math.cos(angle)
    y = CENTER + r * math.sin(angle)
    return x, y


def render(data, theme_name, show_values):
    t = THEMES[theme_name]
    n = len(data)
    angles = [-math.pi / 2 + i * (2 * math.pi / n) for i in range(n)]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" '
        f'viewBox="0 0 {SIZE} {SIZE}" font-family="JetBrains Mono, ui-monospace, monospace">',
        f'<rect width="{SIZE}" height="{SIZE}" fill="{t["bg"]}" rx="12"/>',
    ]

    # grid rings
    for ring in range(1, RINGS + 1):
        r = RADIUS * ring / RINGS
        pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in (point(a, r) for a in angles))
        parts.append(
            f'<polygon points="{pts}" fill="none" stroke="{t["grid"]}" stroke-width="1"/>'
        )

    # axis lines + labels
    for i, a in enumerate(angles):
        x, y = point(a, RADIUS)
        parts.append(
            f'<line x1="{CENTER}" y1="{CENTER}" x2="{x:.2f}" y2="{y:.2f}" '
            f'stroke="{t["axis"]}" stroke-width="1"/>'
        )
        lx, ly = point(a, RADIUS + 26)
        anchor = "middle"
        if math.cos(a) > 0.3:
            anchor = "start"
        elif math.cos(a) < -0.3:
            anchor = "end"
        label = data[i]["label"]
        if show_values:
            label += f'  ({data[i]["value"] * 100:.0f}%)'
        parts.append(
            f'<text x="{lx:.2f}" y="{ly:.2f}" fill="{t["text"]}" font-size="12" '
            f'text-anchor="{anchor}" dominant-baseline="middle">{label}</text>'
        )

    # value polygon
    pts = " ".join(
        f"{x:.2f},{y:.2f}"
        for x, y in (point(a, RADIUS * d["value"]) for a, d in zip(angles, data))
    )
    parts.append(
        f'<polygon points="{pts}" fill="{t["fill"]}" fill-opacity="{t["fill_opacity"]}" '
        f'stroke="{t["stroke"]}" stroke-width="2"/>'
    )
    for a, d in zip(angles, data):
        x, y = point(a, RADIUS * d["value"])
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3" fill="{t["stroke"]}"/>')

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("-o", "--out", required=True, help="output path prefix (no extension)")
    ap.add_argument("--values", action="store_true", help="show percentage next to labels")
    args = ap.parse_args()

    with open(args.data, encoding="utf-8") as f:
        data = json.load(f)

    for theme in ("dark", "light"):
        svg = render(data, theme, args.values)
        out_path = f"{args.out}-{theme}.svg"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(svg)
        print("wrote", out_path)


if __name__ == "__main__":
    main()
