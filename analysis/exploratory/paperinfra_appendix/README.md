# paperinfra_appendix

Auxiliary figures that don't fit in the main paper but should be on hand. Committed to git via a gitignore exception (`!analysis/exploratory/paperinfra_appendix/**`).

Each chart is generated fresh by `run.py` (no copying from `paper/results/`).

## Charts

- **phys_zone_faceted** — three panels (Physical | Mixed | Non-physical) of job zone violins. Per-row (zone) and per-column (group) median + n labels are rendered alongside the per-cell annotations.
- **ska_full** — element-level SKA chart for skills, knowledge, and abilities, with the full ladder of workforce reference markers (Mean, P95, Top-10). The Part 2 chart trims this for the main text; this preserves the full version with abilities at the element level.
- **nonphys_gwa_diff_phys_excluded** — within the 409 non-physical occupations (`pct_physical < 33%`), the General Work Activity composition gap between the top and bottom exposure quartile, computed over only the non-physical tasks of each occupation. Robustness test: confirms the GWA discrimination signal is not just a pct_physical residual proxy.
- **major_de_nt_plane** — each of the 22 SOC major occupational categories on the demand-elasticity × new-task-creation plane (LLM-rated task properties, 1-5). Dot size ∝ workers affected; color = % tasks affected from All Confirmed. Dashed lines at the per-axis medians.
- **convergence_full** — combined version of Part 1's `convergence` and `convergence_configs` charts. All 4 internal AI sources + 5 `ANALYSIS_CONFIGS` data configurations on a single y-axis (9 rows); same 9 measures as a lower-tri internal block on x, then the 8 external academic benchmarks. Reuses the paper builder so cell rendering, group headers, and Eloundou contamination gray-out match the main charts exactly.
- **overview_no_autoaug** — paper part_1 `overview` chart, recomputed with `use_auto_aug=False`. Each affected task contributes its full freq weight regardless of its 0–5 automatability score. Each bar carries `Δ±X.Xpp` vs. the paper chart inside the bar text, with a thin black tick mark at the paper chart's value position.

## Run

```
venv/Scripts/python -m analysis.exploratory.paperinfra_appendix.run
```

## Files

- `run.py` — generates all four charts + `appendix_charts.md`
- `appendix_charts.md` — chart-only listing
- `figures/` — committed PNGs
- `results/` — auto-created CSVs + figures (gitignored via `analysis/exploratory/*` rule)

## Data conventions

- `pct_physical` per occupation always computed over UNIQUE (occ, task) pairs. eco_2025 expands tasks across GWA/IWA/DWA non-proportionally between physical and non-physical tasks, so the dedup is required before counting. See `analysis/ANALYSIS_ARCHITECTURE.md` Common Pitfalls.
- For GWA-level shares, dedup is per (task, gwa_title) since one task legitimately belongs to multiple GWAs.
- For major-level property aggregation (`major_de_nt_plane`), dedup is per (major, task_normalized) — each unique task counts once per major regardless of how many occupations within the major use it.
