# Wage Potential

**Question:** Which occupations and sectors have the highest economic value locked in their adoption gap?

---

## What This Measures

Wage gap = `wages_affected(all_ceiling) − wages_affected(all_confirmed)`.

This is the dollar volume of wages associated with AI capabilities that exist but aren't being deployed. A large wage gap means high-wage work is sitting in the adoption gap — valuable work that current AI tools could be doing, but aren't.

Wage hotspots: occupations in the top quartile on **both** median wage and pct_tasks_affected gap. These are the occupations where closing the adoption gap would unlock the most per-worker economic value.

---

## Outputs

| File | Contents |
|------|----------|
| `results/wage_gap_major.csv` | Wages gap at major category level |
| `results/wage_gap_minor.csv` | Wages gap at minor category level (top 30) |
| `results/wage_gap_occupation.csv` | Wages gap at occupation level (top 50) |
| `results/wage_hotspots.csv` | Occupations in top quartile: median wage AND pct gap |
| `results/wa_wage_gap_iwa.csv` | Wages gap at IWA level (top 30) |
| `results/macro_summary.csv` | Aggregate confirmed vs ceiling wage totals |

Key figures (committed):
- `macro_wage_summary.png` — confirmed vs ceiling wages aggregate
- `wage_gap_major.png` — major categories ranked by wages gap
- `wage_gap_occupation.png` — top 30 occupations by wages gap
- `wage_hotspot_scatter.png` — median wage vs pct gap scatter
- `wa_wage_gap_iwa.png` — IWA level wages gap

---

## Run

```bash
venv/Scripts/python -m analysis.questions.potential_growth.wage_potential.run
```
