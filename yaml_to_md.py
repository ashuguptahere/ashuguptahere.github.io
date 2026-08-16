#!/usr/bin/env python3
"""Render README.md from data.yaml, the same source resume.typ renders to PDF.

data.yaml holds candidate data only: plain values, no markup. Section order and
section headings both come from its keys, so the two renderers cannot drift.

Also lints for keyword repetition: a tool should be named once, in its role's
`stack:`, not restated across bullets.

Usage:
    python3 yaml_to_md.py [data.yaml] [README.md]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import quote, urlparse

import yaml

# A keyword shorter than this is too collision-prone to lint (AI, ML, uv).
MIN_LINT_LENGTH = 5

# Transparent background, monochrome ink: black in light mode, white in dark.
INK_LIGHT = "bg_color=00000000&title_color=000000&text_color=000000&icon_color=000000"
INK_DARK = "bg_color=00000000&title_color=ffffff&text_color=ffffff&icon_color=ffffff"

STATS_API = "https://github-stats-extended.vercel.app/api"
SNAKE_RAW = (
    "https://raw.githubusercontent.com/{repo}/output/github-contribution-grid-snake"
)
# github-profile-trophy.vercel.app answers 402 (quota spent); this mirror
# serves the same cards.
TROPHY_API = "https://github-trophies.vercel.app/?username={user}&no-frame=true&column=4&margin-w=6&theme="
# Explicit per-theme URLs. leetcard's default card embeds its own
# prefers-color-scheme rules, which a browser honours but GitHub's image
# pipeline does not, so the card stayed dark in every README.
LEETCARD = "https://leetcard.jacoblin.cool/{user}?ext=heatmap&theme="
QUOTE_API = "https://quotes-github-readme.vercel.app/api?type=horizontal&theme="


# --------------------------------------------------------------------- helpers


def links_by_label(links: list[dict]) -> dict[str, str]:
    """Map a lowercased link label to its URL, e.g. {"github": "https://..."}."""
    return {
        str(it.get("label", "")).strip().lower(): str(it.get("url", "")).strip()
        for it in links or []
        if it.get("label") and it.get("url")
    }


def url_username(url: str) -> str:
    """Last non-empty path segment, e.g. https://leetcode.com/u/ashu/ -> ashu."""
    parts = [p for p in urlparse(str(url or "")).path.split("/") if p]
    return parts[-1] if parts else ""


def md_link(text: str, url: str) -> str:
    text = str(text or "").strip()
    url = str(url or "").strip()
    return f"[{text}]({url})" if text and url else (text or url)


# ------------------------------------------------------------------ image cards


def themed(alt: str, light: str, dark: str, href: str) -> str:
    """An image that follows the reader's system theme.

    Plain Markdown cannot express this. A <picture> can, because kramdown
    passes raw HTML through and the browser resolves prefers-color-scheme.
    It is also the only mechanism that works inside a GitHub README, which
    loads no external stylesheet, so this cannot live in assets/css.
    """
    return (
        f'<a href="{href}">'
        f"<picture>"
        f'<source media="(prefers-color-scheme: dark)" srcset="{dark}">'
        f'<img alt="{alt}" src="{light}">'
        f"</picture></a>"
    )


def build_stats_cards(links: list[dict], repo: str) -> list[str]:
    """Stats cards, ordered by what a visitor looks at first.

    github-readme-stats.vercel.app is not used: it answers 503.
    streak-stats.demolab.com is skipped too, having answered 200 on one check
    and been unreachable on another; a card that is down renders as a broken
    image on the live site.
    """
    by_label = links_by_label(links)
    github = by_label.get("github", "")
    leetcode = by_label.get("leetcode", "")
    cards = []

    if repo:
        snake = SNAKE_RAW.format(repo=repo)
        cards.append(
            themed(
                "Contribution snake",
                f"{snake}.svg",
                f"{snake}-dark.svg",
                f"https://github.com/{repo}",
            )
        )

    if github:
        user = url_username(github)
        for alt, path, extra in (
            ("GitHub Stats", "", "show_icons=true&hide_border=true"),
            (
                "Top Languages",
                "/top-langs",
                "layout=compact&hide_border=true&langs_count=10",
            ),
        ):
            stem = f"{STATS_API}{path}?username={user}&{extra}"
            cards.append(
                themed(alt, f"{stem}&{INK_LIGHT}", f"{stem}&{INK_DARK}", github)
            )

        trophy = TROPHY_API.format(user=user)
        cards.append(
            themed("GitHub Trophies", f"{trophy}flat", f"{trophy}darkhub", github)
        )

    if leetcode:
        card = LEETCARD.format(user=url_username(leetcode))
        cards.append(themed("LeetCode Stats", f"{card}light", f"{card}dark", leetcode))

    return cards


def build_quote() -> str:
    """Random developer quote, following the reader's system colour scheme."""
    return (
        "<picture>"
        f'<source media="(prefers-color-scheme: dark)" srcset="{QUOTE_API}dark">'
        f'<img alt="Random dev quote" src="{QUOTE_API}light">'
        "</picture>"
    )


# --------------------------------------------------------------- section bodies


def entry_line(e: dict) -> str:
    """Render data.yaml's shared name / url? / detail? / links? shape."""
    head = md_link(e["name"], e["url"]) if e.get("url") else e["name"]
    line = f"**{head}**"
    if e.get("detail"):
        line += f": {e['detail']}"
    if e.get("links"):
        joined = ", ".join(md_link(link["name"], link["url"]) for link in e["links"])
        line += f". {e.get('links_label', 'Links')}: {joined}"
    return line


def render_experience(jobs: list[dict]) -> list[str]:
    """Internships are merged in, so their dated entries count toward tenure."""
    out: list[str] = []
    for job in jobs:
        role = job.get("role", "")
        if job.get("role_url"):
            role = md_link(role, job["role_url"])
        # Never use "|" as a separator: kramdown parses any line containing a
        # pipe as a table, which turned every job entry into a bordered table.
        out.append(f"**{job.get('company', '')}** · _{job.get('location', '')}_<br>")
        out.append(f"_{role}_ · _({job.get('dates', '')})_")
        if job.get("stack"):
            out += ["", f"**Stack:** {', '.join(job['stack'])}"]
        out.append("")
        out += [f"- {b}" for b in job.get("bullets", []) or []]
        out.append("")
    return out


def render(key: str, value) -> list[str]:
    """One rendering rule per section key in data.yaml."""
    if key == "summary":
        return [value]
    if key == "experience":
        return render_experience(value)
    if key == "education":
        return [
            f"**{e['degree']}** _from_ {e['institution']} — {e['dates']}<br>"
            for e in value
        ]
    if key == "skills":
        return [f"- **{s['category']}:** {', '.join(s['items'])}" for s in value]
    if key in ("projects", "achievements", "certifications"):
        return [f"- {entry_line(e)}" for e in value]
    # leadership, activities, and any future list of plain statements.
    return [f"- {x}" for x in value]


# --------------------------------------------------------------------- linting


def lint_repetition(data: dict) -> list[str]:
    """Report keyword drift.

    A tool belongs in exactly one place: its role's `stack:`. Flag keywords
    restated across bullets, and stack entries missing from the skills
    inventory, which means the skills section has drifted.
    """
    warnings: list[str] = []

    inventory = {
        str(i).strip()
        for cat in data.get("skills", []) or []
        for i in cat.get("items", []) or []
        if str(i).strip()
    }

    bullets: list[str] = []
    for job in data.get("experience", []) or []:
        bullets += [str(b) for b in job.get("bullets", []) or []]
    for key in ("leadership", "activities"):
        bullets += [str(b) for b in data.get(key, []) or []]

    stack_terms = {
        str(s).strip()
        for job in data.get("experience", []) or []
        for s in job.get("stack", []) or []
        if str(s).strip()
    }

    for term in sorted(stack_terms | inventory):
        if len(term) < MIN_LINT_LENGTH:
            continue
        pattern = re.compile(rf"(?<![\w/]){re.escape(term)}(?![\w/])", re.IGNORECASE)
        hits = sum(1 for b in bullets if pattern.search(b))
        if hits > 1:
            warnings.append(f"  repeated across {hits} bullets: {term!r}")

    for term in sorted(stack_terms - inventory):
        warnings.append(
            f"  in a role stack but missing from skills inventory: {term!r}"
        )

    return warnings


# ---------------------------------------------------------------------- output


def build_readme(data: dict) -> str:
    basics = data.get("basics", {}) or {}
    links = basics.get("links", []) or []
    md: list[str] = []

    # No name heading: GitHub Pages renders this inside a theme whose sidebar
    # already prints the name from _config.yml, so an H1 with the name showed
    # it twice. `titles` is ATS padding for the PDF and only repeats the
    # headline here, so it is left out too.
    md += [f"# {basics.get('headline', '')}", ""]

    where = [b for b in (basics.get("location"), basics.get("work_authorization")) if b]
    if where:
        md += [" · ".join(where), ""]

    # basics["phone"] is deliberately not rendered here. It belongs on the PDF
    # sent to a recruiter, not on a public web page.
    #
    # Short labels, unlike the PDF. Only the PDF needs URLs spelled out for ATS
    # text extraction; eight full URLs on one line render as an unreadable wall.
    bits = []
    if basics.get("email"):
        bits.append(md_link(basics["email"], f"mailto:{basics['email']}"))
    bits += [
        md_link(link.get("label") or link.get("display"), link["url"])
        for link in links
        if link.get("url")
    ]
    if bits:
        md += [" · ".join(bits), ""]

    if basics.get("resume_pdf"):
        md += [f"📄 **[Download Resume (PDF)]({quote(basics['resume_pdf'])})**", ""]

    for key, value in data.items():
        if key == "basics":
            continue
        md += [f"## {key.upper()}", ""]
        md += render(key, value)
        md.append("")

    cards = build_stats_cards(links, str(basics.get("repo", "") or ""))
    if cards:
        md += ["## STATS", ""]
        # Blank line between each: consecutive lines would collapse into one
        # paragraph and the cards would sit side by side.
        for card in cards:
            md += [card, ""]

    md += ["## QUOTE", "", build_quote(), ""]

    # No socials section: the profile links are in the header at the top of the
    # page, and repeating them as badges below was the same destinations twice.
    github = links_by_label(links).get("github", "")
    name = basics.get("name", "")
    md += ["---", "", f"Made with ❤️ by {md_link(name, github) if github else name}"]

    return "\n".join(md).rstrip() + "\n"


def main() -> int:
    argv = sys.argv[1:]
    in_path = Path(argv[0] if argv else "data.yaml")
    out_path = Path(argv[1] if len(argv) > 1 else "README.md")

    data = yaml.safe_load(in_path.read_text(encoding="utf-8")) or {}
    out_path.write_text(build_readme(data), encoding="utf-8")
    print(f"Wrote {out_path} from {in_path}")

    warnings = lint_repetition(data)
    if warnings:
        print(f"\nkeyword repetition ({len(warnings)}):")
        print("\n".join(warnings))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
