# Part 3 — Action: What To Do About It

In the middle of a content revamp. Currently down to a single chart
(tech commodities); additional charts will be added back in subsequent
sessions and the audience-organized framing rebuilt around them.

## Figures

| Figure | What It Shows |
|--------|--------------|
| `tech_commodities.png` | Top-25 tech commodities ranked by depth × breadth composite (geometric mean of normalized mean % tasks affected and exposed workers). Color = avg % tasks affected. Annotations = workers, wages, % of users, occs, entries. |

## Config

All Confirmed (`final_all_confirmed_usage_2026-02-12`) | National | Freq (time-weighted) | Auto-aug ON

Tech commodities uses `analysis/data/technology_skills_v30.1.csv`.

## Run

```bash
venv/Scripts/python -m analysis.paper.results.part_3.run
```
