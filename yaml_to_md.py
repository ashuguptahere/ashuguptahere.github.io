#!/usr/bin/env python3
"""
yaml_to_md.py

Generate a Markdown resume from the SAME data.yaml used by the LaTeX resume.

Section order (matches resume.tex):
  summary
  experience (internships merged in)
  education
  skills & interests
  projects
  achievements
  leadership & activities
  certifications
  stats
  socials

Also lints for keyword repetition: a tool should be named once, in its role's
`stack:`, not restated across bullets.

Usage:
  python3 yaml_to_md.py data.yaml README.md

Dependency:
  pip install pyyaml
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import quote, urlparse

import yaml

# --- Minimal LaTeX-ish -> Markdown normalization (keep content "in sync") ---

RE_HREF = re.compile(r"""\\href\s*{\s*([^}]+?)\s*}\s*{\s*([^}]+?)\s*}""")
RE_TEXTBF = re.compile(r"""\\textbf\s*{\s*([^}]+?)\s*}""")
RE_IT = re.compile(r"""{\s*\\it\s+([^}]+)\s*}""")
RE_SIM_DOLLAR = re.compile(r"""\$\\sim\$""")
RE_SIM_BRACE = re.compile(r"""\$\\\{\\sim\\\}\$""")
RE_APPROX = re.compile(r"""\$\\approx\s""")
RE_TIMES = re.compile(r"""\\times\s*\$""")

# Keywords shorter than this are too collision-prone to lint (AI, ML, DL, uv).
MIN_LINT_LEN = 5


def links_by_label(links: list[dict]) -> dict[str, str]:
    by_label = {}
    for it in links or []:
        label = str(it.get("label", "")).strip().lower()
        url = str(it.get("url", "")).strip()
        if label and url:
            by_label[label] = url
    return by_label


def url_username(url: str) -> str:
    """Last non-empty path segment, e.g. https://leetcode.com/u/ashu/ -> ashu."""
    parts = [p for p in urlparse(str(url or "")).path.split("/") if p]
    return parts[-1] if parts else ""


def build_stats_cards(links: list[dict]) -> list[str]:
    """
    Profile stat cards/badges.

    github-readme-stats.vercel.app (503) and streak-stats.demolab.com
    (unreachable) are deliberately not used: both are free-tier community
    services that rate-limit and go down, and a dead card renders as a broken
    image on the live site. Only endpoints that actually respond are used.
    """
    by_label = links_by_label(links)
    cards = []

    leetcode = by_label.get("leetcode")
    if leetcode:
        cards.append(
            f"[![LeetCode Stats](https://leetcard.jacoblin.cool/{url_username(leetcode)}?ext=heatmap)]({leetcode})"
        )

    static = [
        ("github", "GitHub", "181717", "github"),
        ("codolio", "Codolio", "1f2937", None),
        ("gfg", "GeeksforGeeks", "2f8d46", "geeksforgeeks"),
        ("kaggle", "Kaggle", "20beff", "kaggle"),
    ]
    for label, name, color, logo in static:
        url = by_label.get(label)
        if not url:
            continue
        badge = f"https://img.shields.io/badge/{quote(name)}-View%20Profile-{color}?style=for-the-badge"
        if logo:
            badge += f"&logo={logo}&logoColor=white"
        cards.append(f"[![{name}]({badge})]({url})")

    return cards


def build_social_badges(links: list[dict]) -> str:
    by_label = links_by_label(links)

    badges = []

    linkedin = by_label.get("linkedin")
    if linkedin:
        badges.append(
            f"[![LinkedIn](https://img.shields.io/badge/LinkedIn-%230077B5.svg?logo=linkedin&logoColor=white)]({linkedin})"
        )

    # x = by_label.get("x") or by_label.get("twitter")
    x = "https://x.com/hey_its_ashu"
    if x:
        badges.append(
            f"[![X](https://img.shields.io/badge/X-black.svg?logo=X&logoColor=white)]({x})"
        )

    github = by_label.get("github")
    if github:
        badges.append(
            f"[![GitHub](https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white)]({github})"
        )

    return " ".join(badges)


def latexish_to_md(s: str) -> str:
    """
    Keep strings as close as possible to YAML/LaTeX (sync),
    only converting a few constructs so Markdown is readable.
    """
    if s is None:
        return ""
    s = str(s)

    # \href{url}{text} -> [text](url)
    s = RE_HREF.sub(lambda m: f"[{m.group(2)}]({m.group(1)})", s)

    # \textbf{X} -> **X**
    s = RE_TEXTBF.sub(lambda m: f"**{m.group(1)}**", s)

    # {\it from} -> _from_
    s = RE_IT.sub(lambda m: f"_{m.group(1)}_", s)

    # Common TeX escapes -> literal
    s = (
        s.replace(r"\&", "&")
        .replace(r"\%", "%")
        .replace(r"\_", "_")
        .replace(r"\#", "#")
    )

    # Layout-only TeX
    s = s.replace(r"\hfill", " — ")

    # LaTeX math symbols -> Markdown equivalent
    s = RE_SIM_DOLLAR.sub("~", s)
    s = RE_SIM_BRACE.sub("~", s)
    s = RE_APPROX.sub("~", s)
    s = RE_TIMES.sub("x", s)

    # Drop braces used only for grouping (keeps content synced)
    s = s.replace("{", "").replace("}", "")

    # Normalize whitespace
    s = re.sub(r"[ \t]+", " ", s).strip()

    return s


def md_link(text: str, url: str) -> str:
    text = str(text or "").strip()
    url = str(url or "").strip()
    return f"[{text}]({url})" if text and url else (text or url)


def join_comma(items) -> str:
    items = [str(x).strip() for x in (items or []) if str(x).strip()]
    return ", ".join(items)


def section(md: list[str], title: str) -> None:
    md.append(f"## {title}")
    md.append("")


def lint_repetition(data: dict) -> list[str]:
    """
    A tool belongs in exactly one place: its role's `stack:`. Report keywords
    restated across bullets, and stack entries missing from the skills
    inventory (which means the SKILLS section has drifted).
    """
    warnings: list[str] = []

    inventory = {
        str(i).strip()
        for cat in data.get("skills", []) or []
        for i in (cat.get("items", []) or [])
        if str(i).strip()
    }

    bullets: list[str] = []
    for job in data.get("experience", []) or []:
        bullets.extend(str(b) for b in (job.get("bullets_latex", []) or []))
    for key in ("leadership", "achievements"):
        bullets.extend(
            str(b) for b in ((data.get(key, {}) or {}).get("items_latex", []) or [])
        )

    stack_terms = {
        str(s).strip()
        for job in data.get("experience", []) or []
        for s in (job.get("stack", []) or [])
        if str(s).strip()
    }

    for term in sorted(stack_terms | inventory):
        if len(term) < MIN_LINT_LEN:
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


def main() -> int:
    in_path = Path(sys.argv[1] if len(sys.argv) > 1 else "data.yaml")
    out_path = Path(sys.argv[2] if len(sys.argv) > 2 else "README.md")

    data = yaml.safe_load(in_path.read_text(encoding="utf-8"))
    basics = data.get("basics", {}) or {}

    # Header (keeps same variables as resume)
    name = str(basics.get("name", "")).strip() or "Resume"
    profile = str(basics.get("headline", "")).strip() or "Resume"
    _titles = str(basics.get("titles", "")).strip()
    email = str(basics.get("email", "")).strip()
    location = str(basics.get("location", "")).strip()
    work_auth = str(basics.get("work_authorization", "")).strip()
    resume_pdf = str(basics.get("resume_pdf", "")).strip()
    links = basics.get("links", []) or []

    # The name is the H1: it is the page title on GitHub Pages and the first
    # thing a reader (or a search engine) sees. Everything else in the header
    # is kept to two compact lines so the page opens on content, not on a wall
    # of metadata.
    md: list[str] = []
    md.append(f"# {name}")
    md.append("")

    # `titles` is ATS title-matching padding for the PDF; next to the headline
    # it just repeats "Data Scientist", so the site shows the headline only.
    if profile:
        md.append(f"### {profile}")
        md.append("")

    where = [b for b in (location, work_auth) if b]
    if where:
        md.append(" · ".join(where))
        md.append("")

    # Short labels here, unlike the PDF. The website is read by humans; only
    # the PDF needs the URL spelled out for ATS text extraction, and eight full
    # URLs on one line render as an unreadable wall.
    header_bits = []
    if email:
        header_bits.append(md_link(email, f"mailto:{email}"))
    for l in links:
        url = str(l.get("url", "")).strip()
        shown = str(l.get("label", "") or l.get("display", "")).strip()
        if shown and url:
            header_bits.append(md_link(shown, url))
    if header_bits:
        md.append(" · ".join(header_bits))
        md.append("")

    if resume_pdf:
        md.append(f"📄 **[Download Resume (PDF)]({quote(resume_pdf)})**")
        md.append("")

    # 1) summary
    summary = str((data.get("summary", {}) or {}).get("text", "") or "").strip()
    if summary:
        section(md, "🎯 SUMMARY")
        md.append(summary)
        md.append("")

    # 2) experience (internships merged in)
    section(md, "💼 EXPERIENCE")
    for job in data.get("experience", []) or []:
        role = str(job.get("role", "")).strip()
        role_url = str(job.get("role_url", "") or "").strip()
        dates = str(job.get("dates", "")).strip()
        company = str(job.get("company", "")).strip()
        loc = str(job.get("location", "")).strip()

        role_display = md_link(role, role_url) if role_url else role
        # Never use "|" as a separator: kramdown (GitHub Pages' Markdown
        # engine) parses any line containing pipes as a table, which turned
        # every job entry into a bordered 2-column table on the site.
        md.append(f"**{company}** · _{loc}_<br>")
        md.append(f"_{role_display}_ · _({dates})_")

        stack = join_comma(job.get("stack", []) or [])
        if stack:
            md.append("")
            md.append(f"**Stack:** {stack}")
        md.append("")

        for b in job.get("bullets_latex", []) or []:
            md.append(f"- {latexish_to_md(b)}")
        md.append("")

    # 3) education
    section(md, "🎓 EDUCATION")
    ed_line = ((data.get("education", {}) or {}).get("line_latex", "") or "").strip()
    if ed_line:
        md.append(latexish_to_md(ed_line))
    md.append("")

    # 4) skills
    section(md, "🛠️ SKILLS & INTERESTS")
    for s in data.get("skills", []) or []:
        cat = str(s.get("category", "")).strip()
        items = join_comma(s.get("items", []) or [])
        if cat and items:
            md.append(f"- **{cat}:** {items}")
        elif cat:
            md.append(f"- **{cat}:**")
    md.append("")

    # 5) projects
    section(md, "📂 PROJECTS")
    for p in data.get("projects", []) or []:
        pname = str(p.get("name", "")).strip()
        url = str(p.get("url", "")).strip()
        tail = str(p.get("tail_latex", "") or "").strip()

        head = f"**{md_link(pname, url)}**" if (pname or url) else "**Project**"
        line = head + ((" " + latexish_to_md(tail)) if tail else "")
        md.append(f"- {line}")
    md.append("")

    # 6) achievements
    section(md, "🏆 ACHIEVEMENTS")
    for a in (data.get("achievements", {}) or {}).get("items_latex", []) or []:
        md.append(f"- {latexish_to_md(a)}")
    md.append("")

    # 7) leadership & activities
    section(md, "🤝 LEADERSHIP & ACTIVITIES")
    for x in (data.get("leadership", {}) or {}).get("items_latex", []) or []:
        md.append(f"- {latexish_to_md(x)}")
    md.append("")

    # 8) certifications
    section(md, "📜 CERTIFICATIONS")
    for c in (data.get("certifications", {}) or {}).get("items", []) or []:
        cname = str(c.get("name", "")).strip()
        curl = str(c.get("url", "")).strip()
        md.append(f"- {md_link(cname, curl)}")
    md.append("")

    stats = build_stats_cards(links)
    if stats:
        section(md, "📈 STATS")
        md.extend(stats)
        md.append("")

    section(md, "📬 SOCIALS")
    md.append(build_social_badges(links))
    md.append("")
    md.append("---")
    md.append("")

    github_url = links_by_label(links).get("github", "")

    if github_url:
        md.append(f"Made with ❤️ by [{name}]({github_url})")
    else:
        md.append(f"Made with ❤️ by {name}")

    out_path.write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
    print(f"Wrote {out_path} from {in_path}")

    warnings = lint_repetition(data)
    if warnings:
        print(f"\nkeyword repetition ({len(warnings)}):")
        print("\n".join(warnings))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
