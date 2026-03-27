# Dashboard Instructions: Dataset Source Comparison

## Chart 1: Three-Way Footprint (% Tasks Affected by Major Category)
- **Page:** Occupation Categories
- **Group A:** Dataset = AEI Cumul. (Both) v4, Method = Time, Geo = National, Physical = All, Auto-aug = On, Agg = Major Category
- **Group B:** Dataset = MCP Cumul. v4 (same other settings)
- **Sort by:** Workers Affected
- **Top N:** 22
- **Note:** Can only compare two sources at a time on the dashboard. Run Group A vs B, then swap one for Microsoft to see the third. Use tooltip deltas to compare.

## Chart 2: Occupation-Level Ranking Comparison
- **Page:** Occupation Categories
- **Group A:** Dataset = AEI Cumul. (Both) v4, Agg = Occupation, Top N = 20
- **Group B:** Dataset = MCP Cumul. v4, Agg = Occupation, Top N = 20
- **Sort by:** % Tasks Affected
- **Note:** The scatter plots and rank correlations in the analysis are not reproducible on the dashboard --- those require the analysis script. But the side-by-side bar charts with tooltip deltas show the same disagreements.

## Chart 3: Risk Tier Differences
- **Page:** Occupation Categories
- **Group A:** Dataset = AEI Cumul. (Both) v4, Agg = Occupation, Top N = 30
- **Group B:** Dataset = Microsoft, Agg = Occupation, Top N = 30
- **Sort by:** % Tasks Affected (descending)
- **Note:** Observe that Group A (AEI) shows occupations above 60% while Group B (Microsoft) tops out below 60%. The tier bar chart and heatmaps are analysis-only.

## Chart 4: Auto-Aug Sensitivity
- **Page:** Occupation Categories
- **Group A:** Dataset = MCP Cumul. v4, Auto-aug = On, Agg = Major
- **Group B:** Dataset = MCP Cumul. v4, Auto-aug = Off, Agg = Major
- **Sort by:** Workers Affected
- **Note:** Watch MCP's footprint nearly double when auto-aug is turned off. Repeat with AEI to see it barely change.

## Chart 5: Physical Task Filter
- **Page:** Occupation Categories
- **Group A:** Dataset = AEI Cumul. (Both) v4, Physical = Physical Only, Agg = Major
- **Group B:** Dataset = MCP Cumul. v4, Physical = Physical Only, Agg = Major
- **Sort by:** Workers Affected
- **Note:** Compare the total workers affected in each group. AEI will show significantly less physical exposure than MCP.
