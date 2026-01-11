#!/usr/bin/env python3
"""
yaml_to_resume_md.py

Generate a Markdown resume from the SAME data.yaml used by your LaTeX resume.

Section order:
  experience
  internships
  skills
  projects
  achievements
  education
  extra (Extra-Curricular Activities)
  certifications

Usage:
  python3 yaml_to_resume_md.py data.yaml README.md

Dependency:
  pip install pyyaml
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

# --- Minimal LaTeX-ish -> Markdown normalization (keep content "in sync") ---

RE_HREF = re.compile(r"""\\href\s*{\s*([^}]+?)\s*}\s*{\s*([^}]+?)\s*}""")
RE_TEXTBF = re.compile(r"""\\textbf\s*{\s*([^}]+?)\s*}""")
RE_IT = re.compile(r"""{\s*\\it\s+([^}]+)\s*}""")


def build_social_badges(links: list[dict]) -> str:
    by_label = {}
    for it in links or []:
        label = str(it.get("label", "")).strip().lower()
        url = str(it.get("url", "")).strip()
        if label and url:
            by_label[label] = url

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

    # Drop braces used only for grouping (keeps content synced)
    s = s.replace("{", "").replace("}", "")

    # Escape pipe symbol to prevent markdown table issues
    s = s.replace("|", "\\|")

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


def main() -> int:
    in_path = Path(sys.argv[1] if len(sys.argv) > 1 else "data.yaml")
    out_path = Path(sys.argv[2] if len(sys.argv) > 2 else "README.md")

    data = yaml.safe_load(in_path.read_text(encoding="utf-8"))
    basics = data.get("basics", {}) or {}

    # Header (keeps same variables as resume)
    name = str(basics.get("name", "")).strip() or "Resume"
    profile = "Data Scientist & AI Engineer"
    # phone = str(basics.get("phone", "")).strip()
    email = str(basics.get("email", "")).strip()
    links = basics.get("links", []) or []

    md: list[str] = []
    md.append(f"# {profile}")
    md.append("")
    header_bits = []
    # if phone:
    #     header_bits.append(phone)
    if email:
        header_bits.append(md_link(email, f"mailto:{email}"))
    for l in links:
        label = str(l.get("label", "")).strip()
        url = str(l.get("url", "")).strip()
        if label and url:
            header_bits.append(md_link(label, url))
    if header_bits:
        md.append(" • ".join(header_bits))
        md.append("")

    # 1) experience
    section(md, "💼 EXPERIENCE")
    for job in data.get("experience", []) or []:
        role = str(job.get("role", "")).strip()
        dates = str(job.get("dates", "")).strip()
        company = str(job.get("company", "")).strip()
        location = str(job.get("location", "")).strip()

        md.append(f"**{role}** | _({dates})_<br>")
        md.append(f"**{company}** | _{location}_")

        for b in job.get("bullets_latex", []) or []:
            md.append(f"- {latexish_to_md(b)}")
        md.append("")

    # 2) internships
    section(md, "🧑‍💻 INTERNSHIPS")
    for it in data.get("internships", []) or []:
        title = str(it.get("title", "")).strip()
        dates = str(it.get("dates", "")).strip()
        company = str(it.get("company", "")).strip()
        location = str(it.get("location", "")).strip()

        md.append(f"**{title}** | _({dates})_<br>")
        md.append(f"**{company}** | _{location}_")

        for b in it.get("bullets_latex", []) or []:
            md.append(f"- {latexish_to_md(b)}")
        md.append("")

    # 3) skills
    section(md, "🛠️ SKILLS")
    for s in data.get("skills", []) or []:
        cat = str(s.get("category", "")).strip()
        items = join_comma(s.get("items", []) or [])
        if cat and items:
            md.append(f"- **{cat}:** {items}")
        elif cat:
            md.append(f"- **{cat}:**")
    md.append("")

    # 4) projects
    section(md, "📂 PROJECTS")
    for p in data.get("projects", []) or []:
        pname = str(p.get("name", "")).strip()
        url = str(p.get("url", "")).strip()
        tail = str(p.get("tail_latex", "") or "").strip()

        head = f"**{md_link(pname, url)}**" if (pname or url) else "**Project**"
        line = head + ((" " + latexish_to_md(tail)) if tail else "")
        md.append(f"- {line}")
    md.append("")

    # 5) achievements
    section(md, "🏆 Achievements")
    for a in (data.get("achievements", {}) or {}).get("items_latex", []) or []:
        md.append(f"- {latexish_to_md(a)}")
    md.append("")

    # 6) education
    section(md, "🎓 Education")
    ed_line = ((data.get("education", {}) or {}).get("line_latex", "") or "").strip()
    if ed_line:
        md.append(latexish_to_md(ed_line))
    md.append("")

    # 7) extra
    section(md, "🎨 Extra-Curricular Activities")
    for x in (data.get("extra", {}) or {}).get("items_latex", []) or []:
        md.append(f"- {latexish_to_md(x)}")
    md.append("")

    # 8) certifications
    section(md, "📜 CERTIFICATIONS")
    for c in (data.get("certifications", {}) or {}).get("items", []) or []:
        cname = str(c.get("name", "")).strip()
        curl = str(c.get("url", "")).strip()
        md.append(f"- {md_link(cname, curl)}")
    md.append("")

    out_path.write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
    # print(f"Wrote {out_path} from {in_path}")
    # return 0

    section(md, "📬 SOCIALS")
    md.append(build_social_badges(links))
    md.append("")
    md.append("---")
    md.append("")

    github_url = ""
    for l in links:
        if str(l.get("label", "")).strip().lower() == "github":
            github_url = str(l.get("url", "")).strip()
            break

    if github_url:
        md.append(f"Made with ❤️ by [{name}]({github_url})")
    else:
        md.append(f"Made with ❤️ by {name}")

    out_path.write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
    print(f"Wrote {out_path} from {in_path}")


if __name__ == "__main__":
    raise SystemExit(main())
