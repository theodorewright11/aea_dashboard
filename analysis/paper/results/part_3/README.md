# Part 3 — Action: What To Do About It

Currently five charts. Audience scaffolding will be reintroduced once
the content settles.

## Figures

| Figure | What It Shows |
|--------|--------------|
| `tech_commodities.png` | Top-25 tech commodities ranked by depth × breadth composite (geometric mean of normalized mean % tasks affected and exposed workers). Color = avg % tasks affected. Annotations = workers, wages, % of users, occs, entries. |
| `conv_confirmed_ceiling_gap.png` | All 22 major occ categories. Stacked horizontal bar with three segments per row: Conversational confirmed (`human_conversation`) base + Conv → Confirmed gap (`all_confirmed` − `human_conversation`, focal segment color-encoded by workers added) + Confirmed → Ceiling extension (`all_ceiling` − `all_confirmed`). Sorted by Conv → Confirmed % tasks gap (largest at top). Right-side per-row annotations: pp / workers / wages deltas for both gaps. |
| `risk_score_5f.png` | The "Occupations Most At Risk" focused set — occupations passing four filters: negative BLS employment projection 2024–2034, >50% tasks exposed, exposure trend above median, AI capability above median for the occupation's SKA need. Horizontal bars ordered by absolute BLS projected decline, colored by % tasks exposed. |
| `state_exposure_at_risk.png` | Two-panel state-level view (50 states + DC). Left: % of each state's employment in occupations with AI-exposed tasks (broad exposure). Right: % of each state's employment in the focused set from `risk_score_5f` (at-risk concentration). Sorted by left panel; the right panel deliberately reverses for the top knowledge-economy states (DC, MA, WA, CA all bottom on right). Reuses compute from `analysis/exploratory/deepdive_state_signal/run.py`. |
| `intensity_anchor_fulleco.png` | Major occ categories ranked by AI intensity ratio: Σ pct (rated, equal 3-source bias-corrected) / Σ (freq × emp) over the FULL eco_2025 universe, renormalized to 100% across the 22 majors, then divided by the anchor major's value so the anchor reads as 1.00×. Anchor: 12th of 22 sorted ascending on chart 12's rated-denom ratio (Educational Instruction). Dashed vertical line at the lift distribution's statistical median. Bars shaded by `pct_tasks_affected` (darker = higher). Reuses compute from `analysis/exploratory/audit_pct_norm_eco/run_v3.py` chart 15. |

## Config

All Confirmed (`final_all_confirmed_usage_2026-02-12`) | National | Freq (time-weighted) | Auto-aug ON

- `tech_commodities` — uses `analysis/data/technology_skills_v30.1.csv`.
- `conv_confirmed_ceiling_gap` — runs three configs side by side: `human_conversation`, `all_confirmed`, `all_ceiling`.
- `risk_score_5f` — imports from `analysis/exploratory/audit_risk_score/run.py` (gitignored; skipped with a warning if absent).
- `state_exposure_at_risk` — imports from `analysis/exploratory/deepdive_state_signal/run.py` (gitignored; skipped with a warning if absent). Uses the same focused set as `risk_score_5f`, plus per-state employment from `emp_tot_{geo}_2024` in eco_2025.
- `intensity_anchor_fulleco` — imports from `analysis/exploratory/audit_pct_norm_eco/run_v3.py`. The exploratory folder is gitignored, so this build step is skipped (with a warning) on machines without the v3 script available.

## Run

```bash
venv/Scripts/python -m analysis.paper.results.part_3.run
```
