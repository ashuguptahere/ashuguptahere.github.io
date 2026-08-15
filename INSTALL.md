# Resume Generator

## Overview
A single `data.yaml` file drives both outputs:

| Output | Built by | Command |
|---|---|---|
| `Resume_Aashish_Gupta_AI_Engineer_Data_Scientist.pdf` | `resume.typ` (Typst) | `typst compile resume.typ Resume_Aashish_Gupta_AI_Engineer_Data_Scientist.pdf` |
| `README.md` (also the GitHub Pages home page) | `yaml_to_md.py` | `uv run yaml_to_md.py data.yaml README.md` |

Edit `data.yaml`, then re-run both.

## Prerequisites
- [Typst](https://github.com/typst/typst) — a single binary; no TeX distribution required
- Python 3.14 (tested), plus `uv` for the Markdown generator

## Environment Setup
```bash
uv sync
```

## Markup in `data.yaml`
Prose fields — `bullets`, `tail`, `line`, and `items` under `achievements` and
`leadership` — hold **Typst markup**:

| Markup | Renders as |
|---|---|
| `*text*` | bold |
| `_text_` | italic |
| `#link("url")[text]` | hyperlink |
| `#h(1fr)` | push the rest of the line to the right margin |

`yaml_to_md.py` translates the same markup into Markdown, so both outputs stay
in sync from one source. Every other field is plain text and is inserted
verbatim, which keeps characters like `#` (C#) and `&` from being parsed as
markup.

## Conventions worth keeping
- **Name a tool once**, in its role's `stack:` list, not again in the bullets.
  `yaml_to_md.py` warns about any keyword repeated across bullets and about any
  `stack:` entry missing from the skills inventory.
- **Never put `|` in generated Markdown.** GitHub Pages uses kramdown, which
  turns any line containing a pipe into a table.
- **Hyphenated terms go through `nobreak()`** in `resume.typ`. A line break
  inside `RF-DETR` makes PDF text extraction emit `RFDETR`, which no ATS will
  match.

## Checking the PDF the way an ATS sees it
```bash
pdftotext Resume_Aashish_Gupta_AI_Engineer_Data_Scientist.pdf - | less
```
Profile URLs should appear as text (not only as clickable annotations), and
hyphenated model names should survive intact.

## Troubleshooting
- Typst reports the file and line for syntax errors; `typst compile --watch`
  rebuilds on save.
- If a prose field fails to evaluate, look for a stray `#` or `@` — both start
  code in Typst markup.
- Validate the YAML with `python3 -c "import yaml;yaml.safe_load(open('data.yaml'))"`.
