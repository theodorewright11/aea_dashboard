# Dashboard Instructions: AI Transformative Potential

How to reproduce these results (or approximations) on the live dashboard.

## Capability Ceiling (MCP v4 alone)

- **Page:** Occupation Categories
- **Group A:** Dataset = MCP v4, Method = Time, Geo = National, Auto-aug = On, Physical = All
- **Aggregation:** Major Category (or Minor / Occupation for deeper views)
- **Sort by:** Workers Affected
- **Top N:** 20

## Current Adoption (AEI Cumul. v4 alone)

- **Page:** Occupation Categories
- **Group A:** Dataset = AEI Cumul. v4, Method = Time, Geo = National, Auto-aug = On, Physical = All
- **Aggregation:** Major Category
- **Sort by:** Workers Affected
- **Top N:** 20

## Side-by-Side Comparison (Gap)

The dashboard's two-group layout is perfect for this comparison:

- **Page:** Occupation Categories
- **Group A:** Dataset = MCP v4, Method = Time, Geo = National, Auto-aug = On, Physical = All
- **Group B:** Dataset = AEI Cumul. v4, Method = Time, Geo = National, Auto-aug = On, Physical = All
- **Aggregation:** Major Category
- **Sort by:** Workers Affected (or % Tasks Affected)
- **Top N:** 20
- **Tip:** Hover any bar to see the delta vs the other group — that delta IS the gap this analysis measures. Use "Sync B -> A" then change only the dataset to quickly set this up.

### Sensitivity: Auto-aug toggle

Run the same side-by-side but with Auto-aug = Off on both groups. Compare the bar lengths vs the ON version to see how much larger the gap gets.

### Sensitivity: Method toggle

Run the same side-by-side but with Method = Value on both groups.

## Not reproducible on dashboard

- **The gap rankings** (sorted by MCP minus AEI) can't be directly computed on the dashboard. The dashboard shows two groups side by side and delta on hover, but it doesn't sort by the delta itself. The CSVs in this analysis provide that sorted view.
- **The stability summary** across 4 config variants requires running all 4 and comparing, which isn't a single dashboard view.
- **Toggle mover analysis** (which categories shift most when a toggle changes) requires cross-config comparison.
