# Dashboard Instructions: AI Economic Footprint

How to reproduce the key findings on the AEA Dashboard website.

---

## Chart 1: Combined Source Footprint (Major Categories)

- **Page:** Occupation Categories
- **Group A:** Datasets = AEI Cumul. v4, MCP v4, Microsoft | Combine = Average | Method = Time | Geo = National | Physical = All | Auto-aug = ON
- **Aggregation:** Major Category
- **Sort by:** Workers Affected
- **Top N:** 30
- **Note:** The dashboard shows the combined view. Total workers/wages in the chart tooltips match the analysis values.

## Chart 2: Current Usage Floor

- **Page:** Occupation Categories
- **Group A:** Datasets = AEI Cumul. v4, Microsoft | Combine = Average | Method = Time | Geo = National | Physical = All | Auto-aug = ON
- **Aggregation:** Major Category
- **Sort by:** Workers Affected
- **Top N:** 30

## Chart 3: Capability Ceiling

- **Page:** Occupation Categories
- **Group A:** Datasets = MCP v4 | Method = Time | Geo = National | Physical = All | Auto-aug = ON
- **Aggregation:** Major Category
- **Sort by:** Workers Affected
- **Top N:** 30

## Chart 4: Floor vs Ceiling Side-by-Side

- **Page:** Occupation Categories
- **Group A:** Datasets = AEI Cumul. v4, Microsoft | Combine = Average | (rest same as above)
- **Group B:** Datasets = MCP v4 | (rest same as above)
- **Sort by:** Workers Affected
- **Top N:** 22
- **Note:** Use the cross-group delta in tooltips to see the gap per category. The dumbbell chart in the analysis is easier to read than the dashboard's side-by-side bars.

## Chart 5: Agentic vs Conversational

- **Page:** Occupation Categories
- **Group A:** Datasets = AEI API v3, AEI API v4, MCP v4 | Combine = Average | (rest same)
- **Group B:** Datasets = AEI Cumul. v4, Microsoft | Combine = Average | (rest same)
- **Sort by:** Workers Affected
- **Top N:** 22
- **Note:** The butterfly chart in the analysis is a better visualization for this comparison. Dashboard shows side-by-side bars.

## Chart 6: Physical vs Non-Physical

- **Page:** Occupation Categories
- **Group A:** Same as Chart 1 but Physical = Exclude Physical
- **Group B:** Same as Chart 1 but Physical = Physical Only
- **Sort by:** Workers Affected
- **Note:** Compare total workers in tooltips between Group A and B.

## Chart 7: Auto-aug Toggle Effect

- **Page:** Occupation Categories
- **Group A:** Same as Chart 1 (Auto-aug ON)
- **Group B:** Same as Chart 1 but Auto-aug = OFF
- **Sort by:** Workers Affected
- **Note:** Total workers jumps from ~42M to ~70M.

## Charts NOT Reproducible on Dashboard

The following analysis charts have no dashboard equivalent:
- **Economy overview** (% of total economy) — dashboard doesn't show economy share
- **Treemap** — dashboard only shows bar charts
- **Heatmap** — dashboard can't show multi-source comparison in one view
- **Auto-aug distribution** — dashboard doesn't show score distributions
- **Impact scatter** — dashboard doesn't support scatter plots
- **Toggle sensitivity dot plot** — requires running multiple configs and comparing
