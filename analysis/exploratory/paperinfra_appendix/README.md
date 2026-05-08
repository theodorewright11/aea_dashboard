# paperinfra_appendix

Auxiliary figures that don't fit in the main paper but should be on hand. Committed to git via a gitignore exception (`!analysis/exploratory/paperinfra_appendix/**`).

Each chart is generated fresh by `run.py` (no copying from `paper/results/`).

## Charts

- **phys_zone_faceted** — three panels (Physical | Mixed | Non-physical) of job zone violins. Per-row (zone) and per-column (group) median + n labels are rendered alongside the per-cell annotations.
- **ska_full** — element-level SKA chart for skills, knowledge, and abilities, with the full ladder of workforce reference markers (Mean, P95, Top-10). The Part 2 chart trims this for the main text; this preserves the full version with abilities at the element level.

## Run

```
venv/Scripts/python -m analysis.exploratory.paperinfra_appendix.run
```

## Files

- `run.py` — generates both charts + `appendix_charts.md`
- `appendix_charts.md` — chart-only listing
- `figures/` — committed PNGs
- `results/` — auto-created CSVs + figures (gitignored via `analysis/exploratory/*` rule)
