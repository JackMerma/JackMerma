#!/usr/bin/env python3
"""Self-hosted stat card + featured-repo cards, rendered as SVG.
Avoids shared public instances (github-readme-stats et al.) that can 503/402.

Needs GITHUB_TOKEN env var (a PAT with read access is enough for private
repos listed in projects.json; the built-in GITHUB_TOKEN works for public
data with fewer tiles, e.g. no private-repo cards).
"""

import argparse
import json
import os
import urllib.request

API = "https://api.github.com"
GRAPHQL = "https://api.github.com/graphql"

THEMES = {
    "dark": {"bg": "#0d1117", "border": "#21262d", "text": "#c9d1d9", "muted": "#8b949e", "accent": "#aa9bef"},
    "light": {"bg": "#ffffff", "border": "#d0d7de", "text": "#24292f", "muted": "#57606a", "accent": "#6f5bd6"},
}


def gh(token, url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def gh_graphql(token, query, variables):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(GRAPHQL, data=body, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def collect_stats(token, user):
    profile = gh(token, f"{API}/users/{user}")
    repos = gh(token, f"{API}/users/{user}/repos?per_page=100&type=owner")
    stars = sum(r["stargazers_count"] for r in repos if not r["fork"])

    contributions = None
    try:
        q = """
        query($login: String!) {
          user(login: $login) {
            contributionsCollection {
              contributionCalendar { totalContributions }
              totalCommitContributions
              totalPullRequestContributions
              totalIssueContributions
            }
          }
        }"""
        data = gh_graphql(token, q, {"login": user})
        cc = data["data"]["user"]["contributionsCollection"]
        contributions = cc["contributionCalendar"]["totalContributions"]
    except Exception as e:
        print("graphql contributions unavailable:", e)

    return {
        "public_repos": profile.get("public_repos", len(repos)),
        "followers": profile.get("followers", 0),
        "stars": stars,
        "contributions_last_year": contributions,
    }


def render_stat_card(stats, theme_name):
    t = THEMES[theme_name]
    rows = [
        ("public repos", stats["public_repos"]),
        ("followers", stats["followers"]),
        ("stars earned", stats["stars"]),
    ]
    if stats["contributions_last_year"] is not None:
        rows.append(("contributions / yr", stats["contributions_last_year"]))

    w, h = 480, 56 + 34 * len(rows)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="JetBrains Mono, ui-monospace, monospace">',
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="10" '
        f'fill="{t["bg"]}" stroke="{t["border"]}"/>',
        f'<text x="20" y="34" fill="{t["accent"]}" font-size="15" font-weight="600">GitHub stats</text>',
    ]
    y = 66
    for label, value in rows:
        parts.append(f'<text x="20" y="{y}" fill="{t["muted"]}" font-size="13">{label}</text>')
        parts.append(f'<text x="{w-20}" y="{y}" fill="{t["text"]}" font-size="13" text-anchor="end">{value}</text>')
        y += 34
    parts.append("</svg>")
    return "\n".join(parts)


def wrap_text(text, width):
    words = text.split()
    lines, current = [], ""
    for w in words:
        candidate = f"{current} {w}".strip()
        if len(candidate) > width:
            lines.append(current)
            current = w
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def render_project_cards(projects, theme_name):
    t = THEMES[theme_name]
    card_w, card_h, gap = 420, 100, 16
    w = card_w
    h = len(projects) * card_h + (len(projects) - 1) * gap

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="JetBrains Mono, ui-monospace, monospace">',
    ]
    for i, p in enumerate(projects):
        y0 = i * (card_h + gap)
        name = p["repo"]
        desc = p.get("description") or ""
        lang = p.get("language") or ""
        badge = "private" if p.get("private") else lang
        parts.append(
            f'<g transform="translate(0,{y0})">'
            f'<rect x="0.5" y="0.5" width="{card_w-1}" height="{card_h-1}" rx="10" '
            f'fill="{t["bg"]}" stroke="{t["border"]}"/>'
            f'<text x="18" y="28" fill="{t["accent"]}" font-size="14" font-weight="600">{name}</text>'
            f'<text x="{card_w-18}" y="28" fill="{t["muted"]}" font-size="11" text-anchor="end">{badge}</text>'
        )
        ty = 48
        for line in wrap_text(desc, 58)[:3]:
            parts.append(f'<text x="18" y="{ty}" fill="{t["text"]}" font-size="12">{line}</text>')
            ty += 17
        parts.append("</g>")
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True)
    ap.add_argument("--projects", required=True)
    ap.add_argument("--out", required=True, help="output directory")
    args = ap.parse_args()

    token = os.environ["GITHUB_TOKEN"]
    os.makedirs(args.out, exist_ok=True)

    stats = collect_stats(token, args.user)
    for theme in ("dark", "light"):
        svg = render_stat_card(stats, theme)
        with open(os.path.join(args.out, f"card-stats-{theme}.svg"), "w", encoding="utf-8") as f:
            f.write(svg)

    with open(args.projects, encoding="utf-8") as f:
        projects = json.load(f)

    for p in projects:
        try:
            r = gh(token, f'{API}/repos/{args.user}/{p["repo"]}')
            p["language"] = r.get("language")
            p["private"] = r.get("private", False)
            p["stars"] = r.get("stargazers_count", 0)
        except Exception as e:
            print("repo lookup failed for", p["repo"], e)

    for theme in ("dark", "light"):
        svg = render_project_cards(projects, theme)
        with open(os.path.join(args.out, f"card-projects-{theme}.svg"), "w", encoding="utf-8") as f:
            f.write(svg)

    print("done")


if __name__ == "__main__":
    main()
