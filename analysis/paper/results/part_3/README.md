# Part 3 — Action: What To Do About It

In the middle of a content revamp. Currently three charts. Audience
scaffolding will be reintroduced once more charts come in.

## Figures

| Figure | What It Shows |
|--------|--------------|
| `tech_commodities.png` | Top-25 tech commodities ranked by depth × breadth composite (geometric mean of normalized mean % tasks affected and exposed workers). Color = avg % tasks affected. Annotations = workers, wages, % of users, occs, entries. |
| `conv_confirmed_ceiling_gap.png` | All 22 major occ categories. Stacked horizontal bar with three segments per row: Conversational confirmed (`human_conversation`) base + Conv → Confirmed gap (`all_confirmed` − `human_conversation`, focal segment color-encoded by workers added) + Confirmed → Ceiling extension (`all_ceiling` − `all_confirmed`). Sorted by Conv → Confirmed % tasks gap (largest at top). Right-side per-row annotations: pp / workers / wages deltas for both gaps. |
| `intensity_anchor_fulleco.png` | Major occ categories ranked by AI intensity ratio: Σ pct (rated, equal 3-source bias-corrected) / Σ (freq × emp) over the FULL eco_2025 universe, renormalized to 100% across the 22 majors, then divided by the anchor major's value so the anchor reads as 1.00×. Anchor: 12th of 22 sorted ascending on chart 12's rated-denom ratio (Educational Instruction). Dashed vertical line at the lift distribution's statistical median. Bars shaded by `pct_tasks_affected` (darker = higher). Reuses compute from `analysis/exploratory/audit_pct_norm_eco/run_v3.py` chart 15. |

## Config

All Confirmed (`final_all_confirmed_usage_2026-02-12`) | National | Freq (time-weighted) | Auto-aug ON

- `tech_commodities` — uses `analysis/data/technology_skills_v30.1.csv`.
- `conv_confirmed_ceiling_gap` — runs three configs side by side: `human_conversation`, `all_confirmed`, `all_ceiling`.
- `intensity_anchor_fulleco` — imports from `analysis/exploratory/audit_pct_norm_eco/run_v3.py`. The exploratory folder is gitignored, so this build step is skipped (with a warning) on machines without the v3 script available.

## Run

```bash
venv/Scripts/python -m analysis.paper.results.part_3.run
```
