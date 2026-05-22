# Appendix figures

Auxiliary paper figures that don't fit in the main body but should be on hand. Lives under `analysis/paper/results/` alongside the part folders; committed (the parent `paper/results/` is not gitignored).

Each chart is generated fresh by `run.py` (no copying from elsewhere). The charts are surfaced in the assembled `paper/results/results.md` (appended after Part 3) — this folder no longer carries its own chart-listing markdown.

## Charts

Ordered to match the paper's chart flow — correlation, aggregate economy, trend, then SKA.

- **convergence_full_{major,minor,broad,occ}** — full square 17×17 lower-tri correlation matrix: all 4 internal AI sources + 5 `ANALYSIS_CONFIGS` data configurations + 8 external academic benchmarks on both axes, split into an Internal block and an External block by a gap row/column. One single-panel chart per SOC level. The main paper's per-level convergence charts show only the source/config split for Major + Occ; these appendix charts give the full all-vs-all matrix at every level. Cell rendering, group headers, and the Eloundou contamination gray-out match the main charts.
- **overview_no_autoaug** — paper part_1 `overview` chart, recomputed with `use_auto_aug=False`. Each affected task contributes its full freq weight regardless of its 0–5 automatability score. Each bar carries `Δ±X.Xpp` vs. the paper chart inside the bar text, with a thin black tick mark at the paper chart's value position.
- **temporal_trend_nonphys** — single-panel non-physical variant of Part 1's `temporal_trend`. % Tasks Exposed across the time series for All Confirmed (solid) vs All Sources / Ceiling (dashed), computed with `physical_mode='exclude'`. Shares the linear-OLS 2yr projection, staggered confirmed labels, and sparse ceiling labels with the main chart. Workers / wages panels omitted because a non-phys workers number requires splitting each occupation's employment between its phys and non-phys task load (out of scope).
- **ska_full** — element-level SKA chart for skills, knowledge, and abilities, with the full ladder of workforce reference markers (Mean, P95, Top-10). The Part 2 chart trims this for the main text; this preserves the full version with abilities at the element level.
- **nonphys_gwa_diff_phys_excluded** — within the 409 non-physical occupations (`pct_physical < 33%`), the General Work Activity composition gap between the top and bottom exposure quartile, computed over only the non-physical tasks of each occupation. Robustness test: confirms the GWA discrimination signal is not just a pct_physical residual proxy.

## Run

```
venv/Scripts/python -m analysis.paper.results.appendix.run
```

## Files

- `run.py` — generates all appendix charts
- `figures/` — committed PNGs (referenced from `paper/results/results.md`)
- `results/` — auto-created CSVs + figures (gitignored via `analysis/paper/results/*/results/` rule)

## Data conventions

- `pct_physical` per occupation always computed over UNIQUE (occ, task) pairs. eco_2025 expands tasks across GWA/IWA/DWA non-proportionally between physical and non-physical tasks, so the dedup is required before counting. See `analysis/ANALYSIS_ARCHITECTURE.md` Common Pitfalls.
- For GWA-level shares, dedup is per (task, gwa_title) since one task legitimately belongs to multiple GWAs.
