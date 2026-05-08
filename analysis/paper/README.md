# Paper — Research Paper Infrastructure

Folder for the AEA research paper. Each section of the paper gets its own subfolder.

## Structure

```
paper/
├── paper_config.py           — Visual palette and chart formatting constants
├── writing_style_source.md   — ~30 pages of source writing for style calibration
├── paper_writing_style.md    — Condensed dos and don'ts for paper writing
├── results/                  — Results section
│   ├── part_1/               — Scale, Convergence, Growth
│   ├── part_2/               — (TBD)
│   └── part_3/               — (TBD)
```

## Writing Style

Paper writing uses TWO references (both in this folder):
1. `writing_style_source.md` — Read to calibrate voice, argument structure, and organizational patterns
2. `paper_writing_style.md` — Follow these rules for condensed dos/don'ts

Question reports (now archived under `analysis/_archive/questions/`) used a separate reference: `analysis/writing_style_reference.md`

## Running Charts

```bash
venv/Scripts/python -m analysis.paper.results.part_1.run
```
