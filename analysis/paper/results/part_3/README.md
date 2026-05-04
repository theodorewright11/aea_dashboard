# Part 3 — Action: What To Do About It

Audience-organized action levers built on the structure characterized in
Parts 1 & 2. Three audience sections (organizations, policy, individuals)
preceded by a single framing chart that motivates why those cuts of the
12-property task space are the load-bearing ones.

## Figures

| Figure | What It Shows |
|--------|--------------|
| `property_biplot.png` | PC1/PC2 of the 12 LLM-rated task properties (m, d, s, r, h, e, t, tf, df, de, nt, ac), aggregated to occupation level. Points = occupations colored by major; arrows = property loadings. PC1 = phys/info; PC2 = frictions. Variance explained shown in subtitle. |
| `tech_commodities.png` | Top-25 tech commodities ranked by depth × breadth composite (geometric mean of normalized mean % tasks affected and exposed workers). Color = avg % tasks affected. Annotations = workers, wages, % of users, occs, entries. |
| `conv_vs_agentic.png` | Top sectors (major occ category) showing human conversation footprint vs. agentic ceiling footprint side by side. Sorted by agentic-confirmed–human-conversation gap. |
| `gap_to_ceiling.png` | Top-15 sectors by all_confirmed → all_ceiling worker gap. Stacked bars: confirmed bar + extension to ceiling, with the gap labeled. |
| `risk_x_ska.png` | Risk × recovery option (a). Scatter: x = 8-flag risk score, y = SKA overall_gap (negative = human advantage). Sized by employment, colored by major. Annotated with top-risk and most-resilient occupations. |
| `pct_x_nt_de.png` | Risk × recovery option (b). Scatter: x = pct_tasks_affected, y = mean(nt + de) per occ. Sized by employment, colored by major. Quadrant labels: high pct + low nt+de = displacement risk; high pct + high nt+de = exposure with offset. |
| `phys_info_frictions.png` | Phys/Mixed/Non-physical buckets each split into low/mid/high friction sub-bands (mean(r + df + tf) within bucket). Box plots of % tasks affected. Shows that frictions discriminate within the non-physical bucket. |
| `tacit_duration_safe.png` | Two-panel. Left: scatter of occs on (mean(t), mean(e)), colored by SKA overall_gap, sized by employment, AI-safe occupations annotated. Right: mean(e) by employment quartile. |

## Config

All Confirmed (`final_all_confirmed_usage_2026-02-12`) | National | Freq (time-weighted) | Auto-aug ON

Risk × recovery (a) cross-references job_exposure/job_risk_scoring (8-flag composite) and job_exposure/worker_resilience (SKA overall_gap). Risk × recovery (b) and the property biplot, frictions, and tacit-duration charts use task-level properties from `data/final_eco_2025_with_task_properties.csv`. Tech commodities uses `analysis/data/technology_skills_v30.1.csv`. Conv vs. agentic uses human_conversation and agentic_ceiling configs.

## Run

```bash
venv/Scripts/python -m analysis.paper.results.part_3.run
```
