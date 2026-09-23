#!/usr/bin/env python3
"""Self-hosted GitHub stat card, rendered as SVG.
Avoids shared public instances (github-readme-stats et al.) that can 503/402.

Needs GITHUB_TOKEN env var. The built-in GITHUB_TOKEN is enough for public
stats; a PAT gives access to the private contribution graph via GraphQL.
"""

import argparse
import json
import os
import urllib.request
from xml.sax.saxutils import escape

from theme import PALETTES, THEMES

API = "https://api.github.com"
GRAPHQL = "https://api.github.com/graphql"


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
    t = PALETTES[theme_name]
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
        parts.append(f'<text x="20" y="{y}" fill="{t["muted"]}" font-size="13">{escape(label)}</text>')
        parts.append(f'<text x="{w-20}" y="{y}" fill="{t["text"]}" font-size="13" text-anchor="end">{escape(str(value))}</text>')
        y += 34
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True)
    ap.add_argument("--out", required=True, help="output directory")
    args = ap.parse_args()

    token = os.environ["GITHUB_TOKEN"]
    os.makedirs(args.out, exist_ok=True)

    stats = collect_stats(token, args.user)
    for theme in THEMES:
        svg = render_stat_card(stats, theme)
        with open(os.path.join(args.out, f"card-stats-{theme}.svg"), "w", encoding="utf-8") as f:
            f.write(svg)

    print("done")


if __name__ == "__main__":
    main()
