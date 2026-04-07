# Wage Impact

**Question:** How do our wages-affected dollar figures compare to Seampoint's Utah estimates?

Compares the dollar magnitude of AI's economic footprint in our data to Seampoint's
Utah figures — the only external source with public wage-dollar estimates at the state
level we can directly compare to.

## Key benchmarks

- Seampoint Utah (2026 prelim.): $21B "AI can take over," $15B augmentation, $36B total
- Our Utah all_confirmed: sum of wages_affected for Utah occupations
- Our national all_confirmed: ~$3.99T wages affected nationally

## Outputs

| File | Description |
|------|-------------|
| `figures/utah_wage_comparison.png` | Our Utah confirmed/ceiling vs Seampoint $21B/$36B |
| `figures/utah_pct_comparison.png` | All values as % of $104B Utah wage base |
| `figures/national_wage_totals.png` | National wages_affected across all 5 configs |
| `results/national_wages.csv` | National wages by config |
| `results/utah_wages.csv` | Utah wages by config |
| `results/seampoint_benchmarks.csv` | Seampoint dollar figures |

## Run

```bash
venv/Scripts/python -m analysis.questions.field_benchmarks.wage_impact.run
```
