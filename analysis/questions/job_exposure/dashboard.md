# Dashboard Instructions: Job Exposure

How to reproduce these results (or approximations) on the live dashboard.

## Chart 1: High-exposure occupations by employment

- **Page:** Occupation Categories
- **Group A:** datasets=AEI Cumul. (Both) v4 + Microsoft, method=Value, geo=National, agg=Occupation, auto-aug=On, physical=All
- **Sort by:** Workers Affected
- **Top N:** 30
- **Note:** The dashboard shows the top 30 by workers affected. To see only >=60% tasks affected occupations, look at the % Tasks Affected values in tooltips or use the Explorer with threshold filters.

## Chart 2: Major category tier distribution

- **Page:** Occupation Categories
- **Group A:** datasets=AEI Cumul. (Both) v4 + Microsoft, method=Value, geo=National, agg=Major Category, auto-aug=On, physical=All
- **Sort by:** % Tasks Affected
- **Top N:** 30
- **Note:** The dashboard shows absolute metrics, not the tier breakdown. The tier distribution chart is analysis-only.

## Chart 3: Usage vs ceiling on capability comparison

- **Page:** Occupation Categories (two-group comparison)
- **Group A:** datasets=AEI Cumul. (Both) v4 + Microsoft, combine=Average, method=Value, geo=National, agg=Occupation, auto-aug=On, physical=All
- **Group B:** datasets=AEI Cumul. (Both) v4 + MCP Cumul. v4 + Microsoft, combine=Max, method=Value, geo=National, agg=Occupation, auto-aug=On, physical=All
- **Sort by:** % Tasks Affected
- **Top N:** 30
- **Note:** Tooltips show the delta between groups. Look for occupations where Group B (ceiling/Max) is much higher than Group A (usage/Average).

## Not reproducible on dashboard

- **Exposure tier assignments** — the dashboard doesn't tier occupations by threshold. Use the Explorer's threshold filters to approximate (set % Tasks Affected >= 60).
- **Scatter plots** — the dashboard doesn't produce scatter plots (pct vs employment). These are analysis-only.
- **Tier shift matrix** — cross-tabulation of usage vs capability tiers is analysis-only.
- **Method sensitivity comparison** — requires running both Value and Time and comparing. On the dashboard, switch method toggle and compare visually.
