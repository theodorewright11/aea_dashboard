# Dashboard Instructions: Cross-Source Robustness Analysis

## Chart 1: Three-Way Source Comparison at Major Level
- **Page:** Occupation Categories
- **Group A:** Dataset = AEI Cumul. (Both) v4, Method = Time, Geo = National, Physical = All, Auto-aug = On, Agg = Major Category
- **Group B:** Dataset = MCP Cumul. v4 (same other settings)
- **Sort by:** % Tasks Affected
- **Top N:** 22
- **Note:** Dashboard shows two sources at a time. Run A vs B, then swap one for Microsoft. Use tooltip deltas to compare.

## Chart 2: Minor Category Comparison
- **Page:** Occupation Categories
- **Group A:** Dataset = AEI Cumul. (Both) v4, Agg = Minor Category, Top N = 20
- **Group B:** Dataset = MCP Cumul. v4, Agg = Minor Category, Top N = 20
- **Sort by:** % Tasks Affected
- **Note:** Check the tooltip deltas for cross-source agreement. High-confidence minor categories (e.g., Sales Reps, Computer Occupations, Secretaries) will show small deltas; single-source outliers (e.g., Postsecondary Teachers) will show large deltas.

## Chart 3: Broad Occupation Comparison
- **Page:** Occupation Categories
- **Group A:** Dataset = AEI Cumul. (Both) v4, Agg = Broad Occupation, Top N = 20
- **Group B:** Dataset = MCP Cumul. v4, Agg = Broad Occupation, Top N = 20
- **Sort by:** % Tasks Affected
- **Note:** Expect large disagreements at this level. The rank heatmaps and scatter plots in the analysis capture this better than the dashboard can.

## Chart 4: Occupation-Level Ranking
- **Page:** Occupation Categories
- **Group A:** Dataset = AEI Cumul. (Both) v4, Agg = Occupation, Top N = 30
- **Group B:** Dataset = MCP Cumul. v4, Agg = Occupation, Top N = 30
- **Sort by:** % Tasks Affected
- **Note:** Very low top-30 overlap between sources. The occupation-level scatter plots and confidence tables are analysis-only outputs.

## Chart 5: Exposure Tier Difference (AEI vs Microsoft)
- **Page:** Occupation Categories
- **Group A:** Dataset = AEI Cumul. (Both) v4, Agg = Occupation, Top N = 30
- **Group B:** Dataset = Microsoft, Agg = Occupation, Top N = 30
- **Sort by:** % Tasks Affected (descending)
- **Note:** Group A (AEI) shows occupations above 60%; Group B (Microsoft) tops out below 60%. The tier distribution chart is analysis-only.

## Chart 6: Auto-Aug Sensitivity
- **Page:** Occupation Categories
- **Group A:** Dataset = MCP Cumul. v4, Auto-aug = On, Agg = Major
- **Group B:** Dataset = MCP Cumul. v4, Auto-aug = Off, Agg = Major
- **Sort by:** Workers Affected
- **Note:** Watch MCP's footprint nearly double. Repeat with AEI to see it barely change.

## Chart 7: Physical Task Filter
- **Page:** Occupation Categories
- **Group A:** Dataset = AEI Cumul. (Both) v4, Physical = Physical Only, Agg = Major
- **Group B:** Dataset = MCP Cumul. v4, Physical = Physical Only, Agg = Major
- **Sort by:** Workers Affected
- **Note:** AEI shows significantly less physical exposure than MCP.

## Analysis-Only Outputs (not reproducible on dashboard)
- Scatter plots with Spearman correlation annotations
- Rank heatmaps (all 3 sources side by side)
- Score dot plots (all 3 sources on one chart)
- Confidence summary bar chart
- Tier shift heatmaps
- Multi-level correlation table
