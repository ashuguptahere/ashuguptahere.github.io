# Resume Generator

## Overview
`data.yaml` is the single source. Two renderers read it:

| Output | Built by | Command |
|---|---|---|
| `Resume_Aashish_Gupta_AI_Engineer_Data_Scientist.pdf` | `resume.typ` (Typst) | `typst compile resume.typ Resume_Aashish_Gupta_AI_Engineer_Data_Scientist.pdf` |
| `README.md` (also the GitHub Pages home page) | `yaml_to_md.py` | `uv run yaml_to_md.py data.yaml README.md` |

Edit `data.yaml`, then re-run both.

## Prerequisites
- [Typst](https://github.com/typst/typst) — a single binary; no TeX distribution required
- Python 3.14 (tested), plus `uv`

```bash
uv sync
```

## How `data.yaml` is organised
It holds **candidate data only** — plain values, no markup and no template
syntax. Every string is inserted verbatim, so characters like `#` (C#) and `&`
are always literal.

Section **order** and section **headings** both come from its top-level keys, so
the PDF and the README can never disagree. Renaming a key renames the heading in
both; adding a key needs one rendering rule in each renderer.

Three shapes are reused across every section:

| Shape | Fields | Used by |
|---|---|---|
| Linkable entry | `name`, `url`?, `detail`?, `links`? | projects, achievements, certifications |
| Plain statement | a single string | experience bullets, leadership, activities |
| Dated entry | organisation, location, role, dates | experience, education |

## Conventions worth keeping
- **Name a tool once**, in its role's `stack:` list, not again in the bullets.
  `yaml_to_md.py` warns about any keyword repeated across bullets and about any
  `stack:` entry missing from the skills inventory.
- **Never put `|` in generated Markdown.** GitHub Pages uses kramdown, which
  turns any line containing a pipe into a table.
- **Hyphenated terms go through `nobreak()`** in `resume.typ`. A line break
  inside `RF-DETR` makes PDF text extraction emit `RFDETR`, which no ATS matches.
- **Run `uv run ruff check --select I --fix && uv run ruff format`** after
  editing `yaml_to_md.py`.

## Checking the PDF the way an ATS sees it
```bash
pdftotext Resume_Aashish_Gupta_AI_Engineer_Data_Scientist.pdf - | less
```
Profile URLs should appear as text (not only as clickable annotations), and
hyphenated model names should survive intact.

## Site and profile README
- `assets/css/style.scss` overrides `jekyll-theme-minimal`, which ships
  light-only, with a `prefers-color-scheme` dark palette.
- `.github/workflows/snake.yml` generates the contribution snake here and
  publishes it to the `output` branch.
- The `ashuguptahere/ashuguptahere` profile repo mirrors this `README.md` every
  6 hours; it builds nothing of its own.

## Troubleshooting
- Typst reports the file and line for syntax errors; `typst compile --watch`
  rebuilds on save.
- Validate the YAML with
  `python3 -c "import yaml; yaml.safe_load(open('data.yaml'))"`.
