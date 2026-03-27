# Dashboard Instructions: Utah vs National

Most of this analysis compares the same configurations with only the Nat/Utah toggle changed. The dashboard's two-group (A/B) comparison on the Occupation Categories page is designed exactly for this.

## Economic Footprint — Sector share divergence

- **Page:** Occupation Categories
- **Group A:** datasets = AEI Cumul. (Both) v4 + MCP Cumul. v4 + Microsoft, combine = Average, method = Time, geo = **National**, agg = Major Category, auto-aug = On, physical = All
- **Group B:** Same as A, but geo = **Utah**
- **Sort by:** Workers Affected
- **Top N:** 22 (all major categories)
- **Note:** Hover tooltips show the delta vs the other group. Look at the % change column — the biggest divergences are Computer/Math (higher in Utah) and Sales/Office (lower in Utah).

## Transformative Potential — Gap comparison

This requires two separate runs since the gap is not a native dashboard metric.

### Step 1: MCP capability, National vs Utah
- **Page:** Occupation Categories
- **Group A:** datasets = MCP Cumul. v4, method = Time, geo = **National**, agg = Major Category, auto-aug = On
- **Group B:** Same, geo = **Utah**
- **Sort by:** Workers Affected

### Step 2: AEI usage, National vs Utah
- **Page:** Occupation Categories
- **Group A:** datasets = AEI Cumul. (Both) v4, method = Time, geo = **National**, agg = Major Category, auto-aug = On
- **Group B:** Same, geo = **Utah**
- **Sort by:** Workers Affected

The gap itself (MCP minus AEI) is computed in the analysis script and cannot be directly reproduced on a single dashboard view.

## Job Elimination Risk — Tier composition

- **Page:** Occupation Explorer
- **Level:** Occupation
- **Nat/Utah toggle:** Switch between National and Utah to see how employment and wage numbers change per occupation
- **Pct Compute Panel:** datasets = AEI Cumul. (Both) v4 + Microsoft, combine = Average, method = Value, auto-aug = On
- **Sort by:** % Tasks Affected (descending) to see the high-risk tier first
- **Note:** The % Tasks Affected column is identical in both geos. Only Workers Affected and Wages Affected change. Filter to major categories like Computer/Math or Business/Financial to see the occupations that are uniquely prominent in Utah's at-risk list.
