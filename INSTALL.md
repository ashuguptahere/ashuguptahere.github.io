# Resume Generator

## Overview
A single `data.yaml` file drives both the LaTeX resume (`Resume_Aashish_Gupta_AI_Engineer_Data_Scientist.tex`) and an automatically generated Markdown version (`README.md`, which is also the GitHub Pages home page) via `yaml_to_md.py`.

## Prerequisites
- Python 3.14 (tested)
- Optional: a virtual environment tool such as `uv`
- To export PDF: a LaTeX distribution (TeX Live, MikTeX, etc.) that provides `lualatex`

## Environment Setup
```bash
uv sync
```

## Generate the Markdown Resume
```bash
uv run yaml_to_md.py data.yaml README.md
```
- The first argument is the YAML source (defaults to `data.yaml`).
- The second argument is the Markdown destination (defaults to `README.md`).
- The script prints `Wrote README.md from data.yaml` upon success and overwrites the target file each run.
- `README.md` is what GitHub Pages renders as the site home page, so regenerate it after every `data.yaml` edit.

## Update the LaTeX/PDF Resume
1. Edit `data.yaml` and re-run `yaml_to_md.py` if you also want the Markdown copy refreshed.
2. Compile the LaTeX resume to PDF:
```bash
lualatex "Resume_Aashish_Gupta_AI_Engineer_Data_Scientist.tex"
```
Run `lualatex` twice if you need cross-references to settle. The resulting PDF (`Resume_Aashish_Gupta_AI_Engineer_Data_Scientist.pdf`) will be regenerated in the project root.

## Troubleshooting
- Ensure the YAML file remains valid; run `python -m yaml data.yaml` or `python - <<'PY'` snippet to quickly validate if needed.
- Delete `.aux`, `.log`, and other LaTeX artifacts before recompiling if `lualatex` reports stale references.
