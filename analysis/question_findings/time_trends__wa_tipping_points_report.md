# Work Activity Tipping Points: What Crossed the Threshold

*Config: all_confirmed series (AEI Both + Micro, 6 dates Sep 2024 – Feb 2026) | IWA level | eco_2025 baseline | Method: freq | Auto-aug ON | National*

---

## TLDR

Every single work activity currently in the high-exposure zone (>=66%) crossed that threshold during the measurement window — there were zero IWAs at >=66% in September 2024. By February 2026, 52 IWAs are there. Another 32 IWAs crossed the 33% threshold for the first time, and 72 are currently in the 10–33% active expansion zone, growing consistently. The fastest-growing IWA by total gain is "Evaluate scholarly work" (+76.7pp), which went from a niche AI application to near-ubiquitous in 16 months. Three of the top-five fastest-growing IWAs are education-adjacent. The next wave — 10 IWAs currently between 25-33% and growing — includes financial planning, legal document work, and patient data management.

---

## The High Zone Was Empty in September 2024

The 66% threshold is the tipping point where a majority of an IWA's associated task weight is confirmed AI-exposed. In September 2024, no IWA was above it. By February 2026, 52 are.

This is a stronger version of the same pattern seen in the tier churn analysis at the occupation level: the high-exposure zone as a category didn't exist in the first dataset. Everything that's now "high exposure" at the IWA level made that transition during observation.

| Zone | Count (Sep 2024) | Count (Feb 2026) | Change |
|------|-----------------|-----------------|--------|
| High (>=66%) | 0 | 52 | +52 |
| Moderate (33–66%) | 84 | 116 | +32 |
| Emerging (10–33%) | 127 | 86 | -41 |
| Low (<10%) | 121 | 78 | -43 |

The Emerging zone shrank (127 → 86) because its members graduated to Moderate or High. The Low zone also shrank (121 → 78). Both directions of flow are visible: Low → Emerging, Emerging → Moderate, Moderate → High. The high zone wasn't seeded from outside — it was created by activity moving through the pipeline.

---

## The Fastest Growers

The top IWAs by total gain over the 16-month window reflect a concentrated story in education and professional information work:

| IWA | Gain | Final Level |
|-----|------|-------------|
| Evaluate scholarly work | +76.7pp | 88.0% |
| Assess student capabilities, needs, or performance | +53.6pp | 67.5% |
| Implement security measures for computer or information systems | +49.7pp | 72.8% |
| Set up classrooms, facilities, educational materials, or equipment | +49.7pp | 49.7% |
| Monitor financial data or activities | +48.6pp | 52.2% |
| Develop business or marketing plans | +48.6pp | 58.6% |
| Research laws, precedents, or other legal data | +43.5pp | 92.5% |
| Prepare health or medical documents | +42.2pp | 47.6% |
| Develop patient or client care or treatment plans | +41.8pp | 48.2% |
| Alter audio or video recordings | +41.6pp | 50.9% |

Three education IWAs in the top four. Legal research is at 92.5% — the highest final level of any fast grower. Healthcare documentation and care planning appear twice. The pattern is consistent with what other analyses have found: AI's expanding confirmed footprint is heaviest in knowledge work involving document creation, analysis, and evaluation.

![Top 20 Fastest-Growing IWAs](../questions/time_trends/wa_tipping_points/figures/top20_iwa_growth.png)

---

## When IWAs Crossed 33%

The 33% threshold matters as the level at which AI exposure becomes meaningful rather than marginal for an IWA. 32 IWAs crossed it for the first time during the window.

The timing clusters around two major transition dates:

- **March 2025**: 18 IWAs crossed 33% for the first time. This is the largest single-date batch. It includes "Evaluate scholarly work" (now 88%), "Implement security measures" (73%), "Assess student capabilities" (67%), and several healthcare and legal IWAs.

- **August 2025**: Another significant batch. "Develop business or marketing plans" (59%), "Schedule appointments" (58%), and "Alter audio or video recordings" (51%) crossed here.

March 2025 and August 2025 appear to be the two moments where AI capability made the biggest jumps in confirmed coverage at the IWA level. These dates correspond to specific AEI dataset updates (AEI Both + Micro 2025-03-06 and 2025-08-11).

![IWA 33% Crossing Dates](../questions/time_trends/wa_tipping_points/figures/iwa_33pct_crossing_dates.png)

---

## The Active Expansion Zone: What's Coming Next

The 72 IWAs currently between 10% and 33%, with positive growth over the window, represent the next potential wave. These are activities where confirmed AI exposure has been building but hasn't yet crossed the meaningful-presence threshold.

The top approaching IWAs by total gain, currently between 25-33%:

| IWA | Current Level | Gain |
|-----|--------------|------|
| Record information about legal matters | 26.5% | +25.5pp |
| Prepare financial documents, reports, or budgets | 30.2% | +25.0pp |
| Assign work to others | 27.8% | +24.7pp |
| Collect information about patients or clients | 29.1% | +23.9pp |
| Discuss legal matters with clients | 25.1% | +23.7pp |
| Negotiate contracts or agreements | 30.1% | +23.6pp |
| Develop public or community health programs | 31.2% | +23.6pp |

Several of these IWAs involve routine professional documentation — legal recording, financial document preparation, patient intake, contract management. If the growth rates observed over the past 16 months continue, activities like "Prepare financial documents" (currently 30%) and "Negotiate contracts" (30%) could cross the 33% threshold in the next dataset update.

Healthcare work appears repeatedly in this zone: patient intake, care planning, health program development. This is consistent with healthcare being a sector with high confirmed-exposure growth but still trailing the top sectors.

![IWAs Approaching 33%](../questions/time_trends/wa_tipping_points/figures/iwa_approaching_33pct.png)

---

## The Zone Distribution Is Shifting

Looking at all 332 IWAs at each date, the distribution is shifting away from Low and Emerging and toward Moderate and High. The current (Feb 2026) split: 52 High, 116 Moderate, 86 Emerging, 78 Low. The 78 IWAs still in the Low zone are predominantly physical and operational activities — not text, analysis, or document work.

What's notable is how much the Moderate zone has grown (84 → 116 IWAs) while the Emerging zone has simultaneously shrunk. The Moderate zone is filling from below as Emerging IWAs graduate, while simultaneously emptying from above as Moderate IWAs cross into High. It's a fluid zone — not a destination.

![IWA Zone Distribution Over Time](../questions/time_trends/wa_tipping_points/figures/iwa_zone_over_time.png)

---

## Config

Dataset: `AEI Both + Micro` series (6 dates: 2024-09-30, 2024-12-23, 2025-03-06, 2025-08-11, 2025-11-13, 2026-02-12) | IWA level | eco_2025 baseline (mcp_group) | Method: freq | Auto-aug ON | National | Thresholds: Low <10%, Emerging 10-33%, Moderate 33-66%, High >=66%

## Files

| File | Description |
|------|-------------|
| `results/iwa_series.csv` | IWA pct/workers/wages at each date across confirmed series |
| `results/threshold_crossings.csv` | For each IWA × threshold, when (if ever) it crossed |
| `results/new_threshold_crossings.csv` | Threshold crossings that happened during (not at start of) the window |
| `results/iwa_growth.csv` | Per-IWA: first/last pct, total gain, early/late gain split, current zone |
| `results/iwa_approaching_33pct.csv` | IWAs currently 10-33% with positive growth |
| `results/iwa_crossed_33pct.csv` | IWAs that crossed 33% for first time during window |
| `results/iwa_zone_over_time.csv` | Zone counts at each date |
| `figures/top20_iwa_growth.png` | Top 20 fastest-growing IWAs bar chart (committed) |
| `figures/iwa_33pct_crossing_dates.png` | When IWAs first crossed 33% (committed) |
| `figures/iwa_approaching_33pct.png` | Active expansion zone IWAs approaching 33% (committed) |
| `figures/iwa_zone_over_time.png` | Zone distribution stacked bar over time (committed) |
