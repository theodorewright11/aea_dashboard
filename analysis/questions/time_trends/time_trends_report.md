*Primary config: All Confirmed (AEI Both + Micro series, Sep 2024–Feb 2026) | Ceiling: All Sources (All series) | IWA level: eco_2025 baseline | Method: freq | Auto-aug ON | National*

The trends don't tell a smooth story. AI exposure expanded significantly over 16 months — but the expansion was concentrated in a minority of occupations that grew substantially, while nearly half of all occupations barely moved at all. The high-exposure tier at both the occupation and work activity level was entirely created during the measurement window: zero occupations were at >=60% confirmed exposure in September 2024, and zero IWAs were above 66%. The gap between confirmed usage and ceiling capability opened in August 2025 when MCP data was incorporated, and has barely moved since — confirmed is growing slightly faster than ceiling, but neither is pulling away. Some of the highest-profile "AI-adjacent" occupations — Software Developers, Data Scientists — have had completely stable confirmed exposure since September 2024, while lower-profile occupations like HR Specialists and Customer Service Representatives saw the largest absolute gains.

---

## 1. Trajectory Shapes: How Occupations Grew

*Full detail: [trajectory_shapes_report.md](trajectory_shapes/trajectory_shapes_report.md)*

44% of occupations — 406 of 923 — are laggards: less than 5 percentage points of total confirmed exposure gain over 16 months. These are overwhelmingly physical, operational occupations where AI hasn't made confirmed inroads. The AI expansion story is concentrated in a 222-occupation "steady grower" cohort that moved from an average of 29% to 60% confirmed exposure over the period.

The sectors driving the steady-grower cohort: Educational Instruction and Library (44 steady growers — more than any other sector), Management (26), Healthcare Practitioners (23). Not Computer and Mathematical, which led the "early mover" category — occupations that were already high-exposure in September 2024 and added little. The early movers averaged 44% exposure at the start and ended at 48%. The steady growers started at 29% and reached 60%.

Eight occupations fit a "late mover" pattern — starting below 28% at the midpoint and jumping 10+ percentage points in the second half of the window. The small count suggests truly new AI footholds in previously untouched work were uncommon. Most of the action was growth in already-exposed work, not new beachheads.

![Trajectory Type Mix by Sector](trajectory_shapes/figures/trajectory_type_by_sector.png)

![Trajectory Scatter](trajectory_shapes/figures/trajectory_scatter.png)

---

## 2. Tier Churn: Exposure Tier Mobility Over Time

*Full detail: [tier_churn_report.md](tier_churn/tier_churn_report.md)*

The headline is stark: in September 2024, zero occupations had >=60% confirmed AI exposure. By February 2026, 145 did. The entire high-exposure tier was created during the measurement window.

41% of all occupations (381 of 923) changed exposure tier over the period. The Restructuring tier (20–39%) was the most dynamic: 433 occupations were there in September 2024; 80 moved up to High, 131 moved up to Moderate, 222 stayed. More than half of September 2024's Restructuring occupations moved upward. The 33% risk gate — which determines eligibility for high-risk classification — was crossed by 212 occupations that started below it.

Sector stability was bimodal. Legal Occupations: 0% stable (all 7 legal occupations changed tier). Transportation: 92% stable. But "stable" in Transportation means frozen in the Low tier; "stable" in Computer/Math means holding at high exposure. The two stability stories are structurally different.

![Tier Counts Over Time](tier_churn/figures/tier_counts_over_time.png)

![New High-Tier Entrants by Sector](tier_churn/figures/new_high_tier_by_sector.png)

---

## 3. Confirmed vs. Ceiling Convergence

*Full detail: [confirmed_ceiling_convergence_report.md](confirmed_ceiling_convergence/confirmed_ceiling_convergence_report.md)*

There was no confirmed/ceiling gap before April 2025. The gap didn't exist because MCP — the primary source that makes the ceiling larger than confirmed — launched in April 2025. When MCP was incorporated in the August 2025 dataset, the ceiling jumped to 47.8% while confirmed was at 37.0%, creating a 10.8pp gap and pushing the confirmed/ceiling ratio down to 77%.

Since then: modest improvement. The ratio has moved from 77% (Aug 2025) to 80% (Feb 2026). Confirmed is growing slightly faster than ceiling, but both are growing, and the absolute gap has barely changed.

The sector-level breakdown reveals where MCP adds the most exposure above what conversational AI confirms. Transportation (59% ratio) and Production (68%) have the largest MCP-specific gaps — these are sectors where tool-use AI has theoretical reach into logistics, scheduling, and production systems that isn't yet reflected in confirmed human usage. Legal and Education (both ~88%) have the smallest gaps, reflecting that MCP doesn't add much in those domains beyond what conversational AI already covers.

![National Confirmed vs Ceiling](confirmed_ceiling_convergence/figures/national_confirmed_vs_ceiling.png)

![Sector Ratio Delta](confirmed_ceiling_convergence/figures/sector_ratio_delta.png)

---

## 4. Work Activity Tipping Points

*Full detail: [wa_tipping_points_report.md](wa_tipping_points/wa_tipping_points_report.md)*

At the IWA level, the pattern mirrors what tier churn shows for occupations: the high-exposure zone was empty in September 2024. Zero IWAs were at >=66% confirmed exposure. By February 2026, 52 are.

The fastest-growing IWA — "Evaluate scholarly work" — went from 11.3% to 88.0% over 16 months (+76.7pp). Three of the top five fastest-growing IWAs are education-adjacent. "Research laws, precedents, or other legal data" is at 92.5% — the highest final level of any fast grower, and a direct reflection of legal AI's rapid confirmed expansion.

The timing of threshold crossings concentrates in two dataset updates: March 2025 and August 2025. These are the step-function moments where large batches of IWAs crossed the 33% meaningful-presence threshold simultaneously. The pattern isn't smooth accumulation — it's discrete jumps as new capabilities get confirmed across clusters of related activities.

72 IWAs are currently in the active expansion zone (10–33%, growing), including "Prepare financial documents" (30.2%), "Negotiate contracts" (30.1%), "Collect information about patients or clients" (29.1%), and "Record information about legal matters" (26.5%). These are the IWAs most likely to cross 33% in the next dataset update.

![Top 20 Fastest-Growing IWAs](wa_tipping_points/figures/top20_iwa_growth.png)

![IWAs Approaching 33%](wa_tipping_points/figures/iwa_approaching_33pct.png)

---

## 5. Occupations of Interest Timeline

*Full detail: [occs_timeline_report.md](occs_timeline/occs_timeline_report.md)*

The 29 named occupations divide sharply between dramatic movers and complete non-movers. Human Resources Specialists gained 53.5pp (22.4% → 75.8%), with 34.1pp of that in a single March 2025 update. Market Research Analysts: +49.7pp to 89.5%. Customer Service Representatives: +39.0pp to 84.1%.

Meanwhile: Software Developers (45.16%), Data Scientists (46.04%), and Accountants and Auditors (28.09%) have the exact same confirmed value at every one of the six dataset dates. Not approximately equal — identical to the hundredth of a percentage point. Their confirmed exposure profile was fully established by September 2024 and hasn't changed since.

Registered Nurses crossed from 9.3% to 33.4%, crossing the 33% risk gate only in the final period (the August 2025 update added 22.1pp at once). The jump reflects healthcare documentation and care planning tasks getting broader confirmed coverage.

The occupations with the biggest gains are not the headline-grabbing AI-disruption targets. HR Specialists, Market Research Analysts, and Customer Service Reps aren't typically at the top of "jobs AI will transform" lists. The data says otherwise.

![All Occupations of Interest](occs_timeline/figures/all_occs_confirmed.png)

![Total Gain Bar Chart](occs_timeline/figures/occs_total_gain.png)

---

## Cross-Cutting Findings

**The high-exposure zone didn't exist at the start.** At the occupation level, zero occupations were at >=60% confirmed in September 2024. At the IWA level, zero activities were at >=66%. Both thresholds were created during the measurement window. This means every current "high-exposure" classification is a product of growth observed during the study period — there's no stable baseline to compare against.

**March 2025 and August 2025 were the inflection points.** Across occupation-level trajectory analysis, tier transitions, IWA threshold crossings, and occupation-of-interest timelines, these two dataset dates consistently appear as the moments of largest confirmed capability expansion. The confirmed series doesn't grow smoothly — it advances in discrete jumps corresponding to specific AEI dataset updates.

**The gap is a MCP artifact, not a deployment failure.** The confirmed/ceiling gap opened in August 2025 when MCP data was incorporated. Before that, confirmed = ceiling. The framing of "deployment isn't keeping up with capability" is accurate only for post-April 2025 data — and even then, confirmed usage has been growing faster than ceiling since the gap opened. The gap reflects a different measurement (tool-use benchmarks vs. confirmed deployment), not necessarily a deployment failure.

**The "obvious" AI occupations are flat; the "soft" ones are growing.** Software Developers, Data Scientists, and Accountants show zero confirmed growth. HR Specialists, Market Research Analysts, and Customer Service Representatives show the largest absolute gains. This reversal of expectations is consistent across the confirmed series: the occupations where AI was most discussed as a disruptor reached their confirmed plateau early, while the occupations involving human interaction, communication, and professional service tasks continued expanding.

**Tier instability is concentrated in specific sectors.** Legal (0% stable), Education (26% stable), Sales (27%) are the most volatile. Physical sectors (Transportation 92%, Farming 92%, Installation/Repair 88%) are frozen — but in the Low tier. Middle-ground sectors like Management (52%), Healthcare Practitioners (53%) are about evenly split. The two-speed structure of the AI transition — some sectors transforming rapidly, others not moving — is visible in the tier stability data.

**The next wave is identifiable.** 72 IWAs are in the active expansion zone (10–33%, growing consistently), including financial document preparation, legal record-keeping, patient data collection, and contract negotiation. These are the activities most likely to cross the 33% meaningful-presence threshold in the next 12–18 months at current growth rates.

---

## Key Takeaways

1. **Zero to 145 high-tier occupations in 16 months.** The >=60% confirmed exposure category was empty in September 2024. Every occupation currently classified as high-exposure earned that designation during the observation window.

2. **44% of occupations barely moved (+0.8pp avg gain for laggards).** The AI expansion is concentrated in a fraction of occupations, mostly in information-intensive, knowledge-based, and professional service sectors. Physical and operational occupations are largely untouched.

3. **Two dates drove most of the change: March 2025 and August 2025.** Confirmed exposure advances in discrete jumps, not smooth curves. Single dataset updates can shift large batches of occupations simultaneously.

4. **The confirmed/ceiling gap is ~10pp nationally and barely moving.** Confirmed is growing slightly faster, but both are growing. The gap was created by MCP's addition to the ceiling — not by deployment falling behind.

5. **Software Developers and Data Scientists haven't grown at all in confirmed exposure.** Their confirmed values are identical across all six dataset dates. The occupations with the largest gains — HR Specialists, Market Research Analysts, Customer Service Representatives — are not the ones that dominate AI disruption narratives.

6. **212 occupations crossed the 33% risk gate during the window.** Any risk tier assignment from September 2024 would misclassify a fifth of the occupational landscape. Risk profiles need to be treated as time-indexed, not permanent.

7. **The next exposure wave is in financial, legal, and healthcare documentation work.** The top approaching IWAs include "Prepare financial documents" (30.2%), "Negotiate contracts" (30.1%), and "Collect patient information" (29.1%) — all currently growing and approaching the 33% threshold.

---

## Sub-Report Index

| Sub-Analysis | Report | What It Answers |
|-------------|--------|-----------------|
| Trajectory Shapes | [trajectory_shapes_report.md](trajectory_shapes/trajectory_shapes_report.md) | How did occupations grow? Steady, plateaued, laggard, early mover, late mover patterns |
| Tier Churn | [tier_churn_report.md](tier_churn/tier_churn_report.md) | How stable are exposure tiers? Which occupations crossed into high-tier or past the 33% gate? |
| Confirmed/Ceiling Convergence | [confirmed_ceiling_convergence_report.md](confirmed_ceiling_convergence/confirmed_ceiling_convergence_report.md) | Is deployment catching up to capability? Sector-level gap dynamics |
| WA Tipping Points | [wa_tipping_points_report.md](wa_tipping_points/wa_tipping_points_report.md) | Which work activities crossed meaningful thresholds, and what's next? |
| Occupations of Interest Timeline | [occs_timeline_report.md](occs_timeline/occs_timeline_report.md) | Full time-series for the 29 named occupations |

---

## Config Reference

| Config Key | Dataset | Role |
|-----------|---------|------|
| `all_confirmed` | `AEI Both + Micro` series (6 dates) | Primary — all confirmed usage trends |
| `all_ceiling` | `All` series (10 dates) | Comparison — ceiling for convergence analysis |
| — | IWA level via `compute_work_activities` | Work activity tipping points (eco_2025 baseline) |
