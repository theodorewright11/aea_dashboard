# Tier Churn: Exposure Tier Mobility Over Time

*Config: all_confirmed series (AEI Both + Micro, 4 dates Mar 2025 – Feb 2026) | Method: freq | Auto-aug ON | National*

---

In March 2025, just 12 occupations had >= 60% confirmed AI exposure. By February 2026, 145 did — 133 new high-tier entrants in 11 months. Alongside that, 33% of all occupations changed tier over the period — mostly moving upward from the "restructuring" (20–39%) band toward moderate (40–59%) and high (>=60%). 104 occupations crossed the 33% risk gate for the first time. Legal Occupations was the most unstable sector, with 100% of its occupations changing tier. Transportation and Material Moving was the most stable — 92% stayed put.

---

## The Tier System

Four tiers based on confirmed pct_tasks_affected:
- **High**: >= 60%
- **Moderate**: 40–59%
- **Restructuring**: 20–39%
- **Low**: < 20%

The 33% threshold also matters as the risk-scoring "exposure gate" — occupations below 33% can't be classified as high-risk regardless of other factors.

---

## From 12 to 145

The measurement window opens in March 2025 with just 12 occupations already above the 60% confirmed threshold. By February 2026, 145 are — 133 occupations made that transition during the 11-month window. The bulk of the high-exposure tier is a product of this recent measurement period.

The 133 new high-tier entrants weren't evenly distributed. Three sectors account for the bulk:
- **Educational Instruction and Library**: the largest single-sector contributor of new high-tier occupations
- **Computer and Mathematical**: second-largest contributor
- **Office and Administrative Support**: third-largest contributor

![Tier Counts Over Time](../questions/time_trends/tier_churn/figures/tier_counts_over_time.png)

---

## The Tier Transition Matrix

Of 923 occupations:
- **302 (33%) changed tier** from their March 2025 position to February 2026
- **621 (67%) stayed in the same tier**

But "stayed" covers very different situations. The 259 occupations that stayed in the Low tier were stable because nothing changed for them — these are the physical and operational occupations where AI hasn't made confirmed inroads. Many occupations that stayed in the Restructuring tier moved within that band but didn't cross a threshold.

The most movement was in the Restructuring (20–39%) band. Of the 378 occupations there in March 2025, a substantial portion moved up to Moderate or High. The Restructuring tier is functionally a waiting room — a band that occupations pass through on their way to higher exposure.

![Tier Transition Sankey](../questions/time_trends/tier_churn/figures/tier_transition_sankey.png)

---

## The 33% Risk Gate: 104 Crossings

The risk scoring framework uses 33% as an exposure gate — occupations below it can't be classified as high-risk regardless of other factors. During the measurement window, 104 occupations crossed this threshold for the first time (starting below 33%, ending at or above it). That's 11% of all 923 occupations — a meaningful shift in the risk-eligible population in 11 months.

For risk scoring purposes, this matters significantly. Any risk tier assignment from before March 2025 would have excluded occupations that are now gate-eligible. The risk portrait has changed materially.

---

## Sector Tier Stability

Tier stability varies enormously by sector. The sectors that changed the most have two different underlying dynamics:

**Fastest-changing sectors:**
- Legal Occupations (0% stable): All 7 legal occupations changed tier. Legal AI went from minimal confirmed presence to significant confirmed exposure during this period.
- Educational Instruction and Library (25.8% stable): Only 16 of 62 education occupations stayed in the same tier.
- Sales (27.3% stable) and Computer/Math (30.6% stable)

**Most stable sectors:**
- Transportation and Material Moving (92.3% stable): 48 of 52 occupations didn't move. This isn't because transportation is exposed — it's because transportation is overwhelmingly in the Low tier and stayed there.
- Farming, Fishing, and Forestry (91.7% stable)
- Installation, Maintenance, and Repair (88.0% stable)
- Production (86.9% stable)

The most stable sectors are the ones where AI hasn't arrived at all. The most unstable are the ones where AI was actively expanding its confirmed footprint. "Stability" in this context is bimodal: either you're stable because nothing happened (physical sectors), or you're stable because you were already at peak exposure (very few occupations). Everyone in between was moving.

![Sector Tier Stability](../questions/time_trends/tier_churn/figures/sector_tier_stability.png)

---

## What This Means for Risk Assessment

Risk assessments based on static snapshots have a short shelf life. The numbers from this window alone show the tier roster is not a stable property of an occupation:
- 133 occupations newly entered the high-exposure tier during the window
- 104 occupations crossed the risk gate (now risk-eligible that weren't before)
- 302 occupations changed tier entirely in 11 months

A risk tier assignment older than 12 months should be treated as provisional. Given the pace of change observed here, the risk portrait needs to be re-evaluated with each major dataset update.

![New High-Tier Entrants by Sector](../questions/time_trends/tier_churn/figures/new_high_tier_by_sector.png)

---

## Config

Dataset: `AEI Both + Micro` series (4 dates: 2025-03-06, 2025-08-11, 2025-11-13, 2026-02-12) | Method: freq | Auto-aug ON | National | Thresholds: Low <20%, Restructuring 20-39%, Moderate 40-59%, High >=60%

## Files

| File | Description |
|------|-------------|
| `results/tier_first_last.csv` | All 923 occupations: tier at first and last date, whether tier changed |
| `results/tier_transition_matrix.csv` | Count of occupations in each (first tier, last tier) pair |
| `results/tier_counts_over_time.csv` | Count of occupations in each tier at each date |
| `results/new_high_tier_entrants.csv` | All 133 occupations that crossed into the high tier (>=60%) |
| `results/gate_crossings_33pct.csv` | All 104 occupations that crossed the 33% risk gate |
| `results/sector_tier_stability.csv` | Per-sector: n stable, n changed, stability rate |
| `figures/tier_counts_over_time.png` | Stacked area: tier roster over time (committed) |
| `figures/tier_transition_sankey.png` | Sankey diagram of tier transitions (committed) |
| `figures/sector_tier_stability.png` | Sector stability rates (committed) |
| `figures/new_high_tier_by_sector.png` | New high-tier entrants by sector (committed) |
