# Adoption Gap

**Question:** Where is confirmed AI usage furthest below the demonstrated capability ceiling, across both occupations and work activities?

---

## What This Measures

Gap = `all_ceiling − all_confirmed` for `pct_tasks_affected`, `workers_affected`, and `wages_affected`.

- A large gap means AI is demonstrably capable of affecting more work than people are currently using it for.
- The gap is not a prediction — it's the distance between confirmed deployment and demonstrated capability as of Feb 2026.

---

## Outputs

| File | Contents |
|------|----------|
| `results/occ_gap_major.csv` | Gap at major category level |
| `results/occ_gap_minor.csv` | Gap at minor category level (top 30) |
| `results/occ_gap_broad.csv` | Gap at broad occupation level (top 30) |
| `results/occ_gap_occupation.csv` | Gap at individual occupation level (top 50) |
| `results/wa_gap_gwa.csv` | Gap at GWA level |
| `results/wa_gap_iwa.csv` | Gap at IWA level (top 30) |
| `results/wa_gap_dwa.csv` | Gap at DWA level (top 30) |
| `results/config_robustness.csv` | Major-level exposure across all 5 configs |
| `results/gap_trend.csv` | Confirmed workers_affected over time vs ceiling |

Key figures (committed):
- `confirmed_vs_ceiling_scatter.png` — scatter per occupation
- `occ_gap_major.png` — dumbbell at major level
- `occ_gap_occupation.png` — top 30 occupations by workers gap
- `wa_gap_iwa.png` — top 20 IWAs by workers gap
- `gap_trend.png` — confirmed growth vs ceiling baseline

---

## Run

```bash
venv/Scripts/python -m analysis.questions.potential_growth.adoption_gap.run
```
