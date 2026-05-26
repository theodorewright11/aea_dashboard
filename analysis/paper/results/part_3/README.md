# Part 3 — Action: What To Do About It

Currently five charts. Audience scaffolding will be reintroduced once
the content settles.

## Figures

| Figure | What It Shows |
|--------|--------------|
| `tech_commodities.png` | Top-25 tech commodities ranked by depth × breadth composite (geometric mean of normalized mean % tasks affected and exposed workers). Color = avg % tasks affected. Annotations = workers, wages, % of users, occs, entries. |
| `conv_confirmed_ceiling_gap.png` | All 22 major occ categories. Stacked horizontal bar with three segments per row: Conversational confirmed (`human_conversation`) base + Conv → Confirmed gap (`all_confirmed` − `human_conversation`, focal segment color-encoded by workers added) + Confirmed → Ceiling extension (`all_ceiling` − `all_confirmed`). Sorted by Conv → Confirmed % tasks gap (largest at top). Right-side per-row annotations: pp / workers / wages deltas for both gaps. |
| `risk_score_5f_workers.png` | "Occupations with High AI Exposure and Negative Employment Projection" — same SKA-gated focused set as the prior `risk_score_5f` (negative BLS emp proj, >50% tasks exposed, exposure trend above median, AI capability above median for SKA need). Two-panel horizontal bar chart, shared y-axis: Panel A = % tasks exposed (in-bar number = tasks %), Panel B = workers exposed (in-bar number = formatted worker count). Y-order descending by % tasks exposed. Bars colored by `|emp_proj_pct|` (light tan → dark burgundy; darker = larger decline). A right-side `Emp Proj` column gives the signed emp-proj % per row as one straight vertical line. Bottom legend (gradient swatch) is centered on the PNG via the empirically tuned x=0.104 anchor pattern. Replaces the prior single-panel `risk_score_5f.png` (function `build_risk_score_5f` kept in `run.py` for revert). |
| `state_clusters_map.png` | U.S. choropleth coloring each state by its Ward AI-exposure cluster. Ward hierarchical clustering on two standardized features: % of state workforce exposed and % of state employment in the High AI Exp & <0 Emp Proj set from `risk_score_5f`. k=3 chosen automatically by largest merge-distance jump; DC is shown as a labeled outlier (its 45.9% workforce-exposed score is so extreme it inflates the z-scoring std and distorts the rest of the structure if included). Companion ranked-bars chart in the appendix (`state_clusters_each_ranked.png`). Reuses compute from `analysis/exploratory/deepdive_state_clusters/run.py`. |
| `intensity_anchor_fulleco.png` | Major occ categories ranked by AI intensity ratio: Σ pct (rated, equal 3-source bias-corrected) / Σ (freq × emp) over the FULL eco_2025 universe, renormalized to 100% across the 22 majors, then divided by the anchor major's value so the anchor reads as 1.00×. Anchor: Office and Administrative Support. Dashed vertical line at the lift distribution's statistical median. Bars shaded by `pct_tasks_affected` (darker = higher). **Data source diverges from the rest of Part 3**: this chart uses `AEI Both 2025 2026-02-12` (= `final_aei_all_usage_2025_2026-02-12.csv` — AEI Conv + AEI API pooled onto eco_2025, no Microsoft) for both numerator and colorbar. The equal 3-source bias correction (Claude / Copilot / ChatGPT GWA priors) still applies. Reuses compute from `analysis/exploratory/audit_pct_norm_eco/run_v3.py` chart 15. |

## Config

All Confirmed (`final_all_confirmed_usage_2026-02-12`) | National | Freq (time-weighted) | Auto-aug ON

**Intensity-figure exception:** `intensity_anchor_fulleco` uses `AEI Both 2025 2026-02-12` (`final_aei_all_usage_2025_2026-02-12.csv` — AEI Conv + AEI API pooled on eco_2025, no Microsoft) instead of `all_confirmed`. The intensity-figure series (this chart + appendix `intensity_drivers_*` + `underadoption_gap`) stays end-to-end on no-Microsoft data; the equal 3-source debias is unchanged. Set in `_INTENSITY_DATASET` at the top of `run.py`.

- `tech_commodities` — uses `analysis/data/technology_skills_v30.1.csv`.
- `conv_confirmed_ceiling_gap` — runs three configs side by side: `human_conversation`, `all_confirmed`, `all_ceiling`.
- `risk_score_5f_workers` — imports from `analysis/exploratory/audit_risk_score/run.py` (gitignored; skipped with a warning if absent).
- `state_clusters_map` — imports `compute_clusters()` from `analysis/exploratory/deepdive_state_clusters/run.py` (gitignored; skipped with a warning if absent). The exploratory helper loads its features from `deepdive_state_signal/results/state_metrics.csv` (uses the same focused set as `risk_score_5f`).
- `intensity_anchor_fulleco` — imports from `analysis/exploratory/audit_pct_norm_eco/run_v3.py`. The exploratory folder is gitignored, so this build step is skipped (with a warning) on machines without the v3 script available.

## Run

```bash
venv/Scripts/python -m analysis.paper.results.part_3.run
```
