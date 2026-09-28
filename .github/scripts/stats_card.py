"""Render a neon GitHub stats card (SVG) from the GraphQL API.

Usage: GITHUB_TOKEN=... python stats_card.py <login> <output.svg>
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    repositories(ownerAffiliations: OWNER) { totalCount }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalIssueContributions
      restrictedContributionsCount
      contributionCalendar { totalContributions }
    }
  }
}
"""

BG, BORDER, PURPLE, CYAN, TEXT, MUTED = "#0D1117", "#30363D", "#A855F7", "#22D3EE", "#E6EDF3", "#8B949E"


def fetch(login: str, token: str) -> dict:
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if "errors" in payload:
        raise SystemExit(f"GraphQL error: {payload['errors']}")
    return payload["data"]["user"]


def fmt(n: int) -> str:
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def render(user: dict) -> str:
    c = user["contributionsCollection"]
    years = max(1, datetime.now(timezone.utc).year - int(user["createdAt"][:4]) + 1)
    rows = [
        ("Contributions (last year)", c["contributionCalendar"]["totalContributions"], CYAN),
        ("Commits", c["totalCommitContributions"] + c["restrictedContributionsCount"], PURPLE),
        ("Pull requests", c["totalPullRequestContributions"], CYAN),
        ("Code reviews", c["totalPullRequestReviewContributions"], PURPLE),
        ("Issues", c["totalIssueContributions"], CYAN),
        ("Repositories", user["repositories"]["totalCount"], PURPLE),
    ]

    lines = []
    for i, (label, value, color) in enumerate(rows):
        y = 78 + i * 26
        delay = 0.15 * i
        lines.append(
            f'<g class="row" style="animation-delay:{delay:.2f}s">'
            f'<circle cx="32" cy="{y - 5}" r="4" fill="{color}"/>'
            f'<text x="46" y="{y}" class="label">{label}</text>'
            f'<text x="300" y="{y}" class="value" text-anchor="end">{fmt(value)}</text>'
            "</g>"
        )

    total = c["contributionCalendar"]["totalContributions"]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="495" height="240" viewBox="0 0 495 240">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{PURPLE}"/><stop offset="100%" stop-color="{CYAN}"/>
    </linearGradient>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <style>
    .title {{ font: 700 18px 'Segoe UI', Ubuntu, sans-serif; fill: url(#g); }}
    .label {{ font: 400 14px 'Segoe UI', Ubuntu, sans-serif; fill: {TEXT}; }}
    .value {{ font: 700 14px 'Segoe UI', Ubuntu, sans-serif; fill: {TEXT}; }}
    .big {{ font: 800 34px 'Segoe UI', Ubuntu, sans-serif; fill: url(#g); }}
    .small {{ font: 400 12px 'Segoe UI', Ubuntu, sans-serif; fill: {MUTED}; }}
    .row {{ opacity: 0; animation: fade .6s ease forwards; }}
    @keyframes fade {{ from {{ opacity: 0; transform: translateX(-6px); }} to {{ opacity: 1; transform: none; }} }}
    @keyframes spin {{ to {{ stroke-dashoffset: 0; }} }}
  </style>
  <rect x="0.5" y="0.5" width="494" height="239" rx="12" fill="{BG}" stroke="{BORDER}"/>
  <text x="25" y="38" class="title">Yasein's GitHub Stats</text>
  {''.join(lines)}
  <circle cx="400" cy="128" r="58" fill="none" stroke="{BORDER}" stroke-width="8"/>
  <circle cx="400" cy="128" r="58" fill="none" stroke="url(#g)" stroke-width="8" stroke-linecap="round"
          stroke-dasharray="364" stroke-dashoffset="364" transform="rotate(-90 400 128)" filter="url(#glow)"
          style="animation: spin 1.4s ease-out .2s forwards"/>
  <text x="400" y="134" class="big" text-anchor="middle">{fmt(total)}</text>
  <text x="400" y="156" class="small" text-anchor="middle">contributions</text>
  <text x="400" y="218" class="small" text-anchor="middle">{years}+ years on GitHub</text>
</svg>
"""


def main() -> None:
    login, out = sys.argv[1], sys.argv[2]
    svg = render(fetch(login, os.environ["GITHUB_TOKEN"]))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)


if __name__ == "__main__":
    main()
