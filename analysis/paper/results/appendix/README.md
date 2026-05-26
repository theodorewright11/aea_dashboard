# Appendix figures

Auxiliary paper figures that don't fit in the main body but should be on hand. Lives under `analysis/paper/results/` alongside the part folders; committed (the parent `paper/results/` is not gitignored).

Each chart is generated fresh by `run.py` (no copying from elsewhere). The charts are surfaced in the assembled `paper/results/results.md` (appended after Part 3) — this folder no longer carries its own chart-listing markdown.

## Charts

Ordered to match the paper's chart flow — correlation, aggregate economy, trend, then SKA.

- **convergence_full_{major,minor,broad,occ}** — full square 17×17 lower-tri correlation matrix: all 4 internal AI sources + 5 `ANALYSIS_CONFIGS` data configurations + 8 external academic benchmarks on both axes, split into an Internal block and an External block by a gap row/column. One single-panel chart per SOC level. The main paper's per-level convergence charts show only the source/config split for Major + Occ; these appendix charts give the full all-vs-all matrix at every level. Cell rendering, group headers, and the Eloundou contamination gray-out match the main charts.
- **overview_no_autoaug** — paper part_1 `overview` chart, recomputed with `use_auto_aug=False`. Each affected task contributes its full freq weight regardless of its 0–5 automatability score. Each bar carries `Δ±X.Xpp` vs. the paper chart inside the bar text, with a thin black tick mark at the paper chart's value position.
- **temporal_trend_nonphys** — single-panel non-physical variant of Part 1's `temporal_trend`. % Tasks Exposed across the time series for All Confirmed (solid) vs All Sources / Ceiling (dashed), computed with `physical_mode='exclude'`. Shares the linear-OLS 2yr projection, staggered confirmed labels, and sparse ceiling labels with the main chart. Workers / wages panels omitted because a non-phys workers number requires splitting each occupation's employment between its phys and non-phys task load (out of scope).
- **ska_knowledge_full / ska_abilities_full** — two element-level appendix charts, one per SKA type. Mirror the main-body Part 2 framing (bar = AI Top-10 Avg as % of workforce max, colored by phys-mix tier; AI Max ◆ + Workforce Mean ●), expanded to the full element list. Labels carry their O*NET subcategory in parentheses. Manual 3-row legend rendered via shapes + annotations (more reliable than Plotly multi-legend for the larger left-margin layouts). The skills element-level chart was promoted to the main body and now lives at `part_2/figures/ska_skills.png`.
- **state_clusters_each_ranked** — companion to Part 3's `state_clusters_map`. Two-panel ranked bar chart with each panel sorted independently: left panel sorts the 51 states by % workforce exposed descending, right panel sorts by % in High AI Exp & <0 Emp Proj occupations descending. Cluster colors (Ward labels from `deepdive_state_clusters.compute_clusters()`) stay consistent across panels — a state's color is the same in both, so the reader can compare its left rank vs. right rank visually. Knowledge-economy states (mid blue) top the left panel but sit near the bottom of the right; the high-vulnerability cluster (dark blue) dominates the top of the right panel and spreads through the middle of the left.
- **underadoption_gap** — per-major underadoption relative to potential as informed by task exposure. `raw_gap = pct_tasks_affected / ratio_full_pct` (Part 3 intensity model's full-eco share of AI usage), then anchored on Office and Administrative Support so values read as a clean multiple: `gap_ratio = raw_gap / raw_gap[Office and Admin]`. Office sits at x=1 with a dashed median line; majors above 1 are more underadopted than the anchor, below 1 less. Color encodes `pct_tasks_affected` with the same gradient legend as `intensity_anchor_fulleco`. Reads as the companion to that chart — same anchor, same median framing. **Both sides of the gap ratio use `AEI Both 2025 2026-02-12` (AEI-only, eco_2025-rebased, no Microsoft) — see Config below.**
- **intensity_drivers_{occ,task}_{comp_math,arts_design_ent,life_phys_soc_sci}** — six within-major decompositions of Part 3's `intensity_anchor_fulleco` for the three high-lift majors (Computer/Mathematical, Arts/Design/Entertainment, Life/Phys/Sci). Per occ or task: `lift = (Σ debiased adj_pct / Σ freq×emp) ÷ within-major median ratio`. Bars are top-10 by lift, sorted descending. Color: `pct_tasks_affected` on occ charts (mirrors main body), `auto_aug_mean` on task charts. Outside text on each bar shows `lift× (raw pct)` where raw pct is the un-debiased `pct_normalized` sum. Task charts use the original task statement (with case + punctuation), not `task_normalized`. Median annotation only on occ charts (task charts' long wrapped labels and tight title spacing leave no room above the plot). **Uses `AEI Both 2025 2026-02-12` (no Microsoft) — see Config below.**

## Config

Most appendix charts use the standard `all_confirmed` (`final_all_confirmed_usage_2026-02-12.csv` — AEI + MS) at National geography, Freq method, Auto-aug ON.

**Intensity-figure exception:** `intensity_drivers_*` (6 charts) and `underadoption_gap` use `AEI Both 2025 2026-02-12` (`final_aei_all_usage_2025_2026-02-12.csv` — AEI Conv + AEI API pooled on eco_2025, no Microsoft) instead. This matches the Part 3 main `intensity_anchor_fulleco` chart so the intensity series stays end-to-end on no-Microsoft data; the equal 3-source debias (Claude/Copilot/ChatGPT GWA priors) is unchanged. Set via `_INTENSITY_DATASET` / `_INTENSITY_V3_KEY` at the top of `run.py`.

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
