# Question: Which occupations are most at risk of job elimination from AI?

Identifies occupations where AI can do most of the work AND is already being used for it — the triple filter of high task coverage, high auto-aug scores, and evidence from usage data (AEI + Microsoft, not just MCP capability).

## Key Findings

1. **9 occupations reach "high risk" (>=60% tasks affected) with usage-confirmed data.** The largest by employment are Market Research Analysts (431K workers, 63%), Search Marketing Strategists (431K, 66%), and Instructional Coordinators (211K, 61%). These are occupations where the majority of task value is already being performed by AI in practice.

2. **7 of those 9 are stable across both Value and Time methods**, meaning the finding doesn't depend on how you weight task importance. Instructional Coordinators and Financial Quantitative Analysts drop below 60% under Time, but stay close.

3. **146 occupations (35.9M workers) are in the "moderate risk" tier (40-60%)**. These are restructuring candidates — significant AI task overlap but not enough for elimination. Includes large occupations like Customer Service Reps (2.7M), General Office Clerks (2.5M), and Accountants (1.4M).

4. **Capability data (MCP v4) shows 59 occupations at high risk vs only 9 with usage data.** The gap of 54 occupations represents "emerging risk" — jobs where AI CAN do 60%+ of the work but isn't widely being used for it yet. The largest: Cashiers (3.1M workers), Customer Service Reps (2.7M), General Office Clerks (2.5M), Secretaries (1.7M).

5. **Computer & Mathematical, Business & Financial, and Arts/Entertainment have the highest share of high-risk occupations** by major category. Farming, Construction, and Building Maintenance have nearly 100% of occupations in the low-exposure tier.

6. **Method sensitivity is low**: only 3.7% of occupations change tiers between Value and Time methods. The risk picture is stable regardless of whether you weight by task importance.

7. **Important caveat**: High task exposure does NOT equal job loss. It means the occupation's task bundle heavily overlaps with demonstrated AI capability. Whether this leads to elimination, restructuring, fewer hires, or just productivity gains depends on deployment economics, regulation, and organizational inertia.

## Config

Primary: AEI Cumul. v4 + Microsoft | Average | Value | Auto-aug ON | National | Occupation level

## Files

| File | Description |
|------|-------------|
| `results/all_occupations_tiered.csv` | All 923 occupations with risk tier assignments |
| `results/high_risk_by_employment.csv` | 9 high-risk occupations ranked by employment |
| `results/stable_high_risk_both_methods.csv` | 7 occupations high-risk under both Value and Time |
| `results/major_category_tier_rollup.csv` | Risk tier distribution by major SOC category |
| `results/usage_vs_capability_comparison.csv` | All occupations: usage-confirmed vs MCP capability tiers |
| `results/tier_shift_matrix.csv` | Cross-tabulation of usage vs capability tiers |
| `results/emerging_risk_capability_only.csv` | 54 occupations high-risk in capability but not usage |
| `results/method_sensitivity_value_vs_freq.csv` | Full Value vs Time method comparison |
| `results/method_sensitivity_tier_movers.csv` | 30 occupations that change tiers between methods |
| `results/figures/scatter_risk_vs_employment.png` | Scatter: % tasks affected vs employment, colored by tier |
| `results/figures/high_risk_by_employment.png` | Bar: 9 high-risk occupations by employment |
| `results/figures/high_risk_by_pct.png` | Bar: 9 high-risk occupations by % tasks affected |
| `results/figures/tier_distribution_by_major.png` | Stacked bar: % of occupations per tier by major category |
| `results/figures/employment_by_tier_major.png` | Stacked bar: employment per tier by major category |
| `results/figures/usage_vs_capability_scatter.png` | Scatter: usage pct vs capability pct per occupation |
