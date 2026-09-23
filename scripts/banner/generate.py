#!/usr/bin/env python3
"""Generates the terminal-style profile banner (dark + light SVG).

Run manually and commit the result (versioned filename, e.g. banner-dark.v1.svg).
Not wired into a workflow: the banner text/avatar only changes when you
intentionally re-run this, not on every push.
"""

import argparse
import base64

THEMES = {
    "dark": {"bg": "#0d1117", "border": "#21262d", "text": "#c9d1d9", "muted": "#8b949e",
             "accent": "#aa9bef", "prompt": "#7ee787"},
    "light": {"bg": "#ffffff", "border": "#d0d7de", "text": "#24292f", "muted": "#57606a",
              "accent": "#6f5bd6", "prompt": "#1a7f37"},
}

LINES = [
    ("$", "whoami"),
    (">", "Jackson Merma -- AI & Software Engineer"),
    ("$", "cat focus.txt"),
    (">", "Agentic workflows, RAG systems, production GenAI"),
    ("$", "status --live"),
    (">", "building at NTT DATA, SimiAI, researching Quechua NLP"),
]

W, H = 1000, 260
AVATAR_R = 56


def render(theme_name, avatar_path):
    t = THEMES[theme_name]
    with open(avatar_path, "rb") as f:
        avatar_b64 = base64.b64encode(f.read()).decode("ascii")

    cx, cy = W - 110, H / 2

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" font-family="JetBrains Mono, ui-monospace, monospace">',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" '
        f'fill="{t["bg"]}" stroke="{t["border"]}"/>',
        # terminal titlebar
        f'<circle cx="28" cy="26" r="6" fill="#ff5f56"/>',
        f'<circle cx="48" cy="26" r="6" fill="#ffbd2e"/>',
        f'<circle cx="68" cy="26" r="6" fill="#27c93f"/>',
        f'<text x="{W/2}" y="31" fill="{t["muted"]}" font-size="12" text-anchor="middle">profile.sh --live</text>',
        f'<line x1="0" y1="48" x2="{W}" y2="48" stroke="{t["border"]}"/>',
    ]

    y = 84
    for prompt, text in LINES:
        color = t["prompt"] if prompt == "$" else t["text"]
        prefix = f'<tspan fill="{t["prompt"]}">{prompt}</tspan> ' if prompt == "$" else "  "
        parts.append(
            f'<text x="32" y="{y}" font-size="15" fill="{color}">{prefix}{text if prompt == "$" else text}</text>'
        )
        y += 28

    # avatar, clipped to a circle, right side
    parts.append(f'<clipPath id="avatarClip"><circle cx="{cx}" cy="{cy}" r="{AVATAR_R}"/></clipPath>')
    parts.append(
        f'<image href="data:image/png;base64,{avatar_b64}" '
        f'x="{cx-AVATAR_R}" y="{cy-AVATAR_R}" width="{AVATAR_R*2}" height="{AVATAR_R*2}" '
        f'clip-path="url(#avatarClip)" preserveAspectRatio="xMidYMid slice"/>'
    )
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{AVATAR_R}" fill="none" stroke="{t["accent"]}" stroke-width="2"/>')

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--avatar", required=True)
    ap.add_argument("-o", "--out", required=True, help="output path prefix (no extension)")
    args = ap.parse_args()

    for theme in ("dark", "light"):
        svg = render(theme, args.avatar)
        out_path = f"{args.out}-{theme}.svg"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(svg)
        print("wrote", out_path)


if __name__ == "__main__":
    main()
