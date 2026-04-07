# AEA Dashboard Analysis — Full Report

*Primary config: All Confirmed (AEI Both + Micro 2026-02-12) | National | Method: freq | Auto-aug ON*

*Highlighted findings: [report_brief.md](report_brief.md)*

---

Confirmed AI usage currently reaches 61.3 million workers, $3.99 trillion in wages, and 40% of U.S. employment. The capability ceiling — where we include all demonstrated AI capability rather than only confirmed cross-source usage — reaches 77.1 million workers and $4.97 trillion. Both numbers have roughly doubled since September 2024. What changed isn't the composition of the labor market — the occupational mix is stable. What changed is how much of existing work AI can demonstrably do.

This report organizes the full analysis into eight chapters, one per research bucket. Each chapter links to the corresponding detailed report for sub-question-level findings, data tables, and full figure sets. The **[highlighted brief report](report_brief.md)** pulls the eight most important stories if you're looking for the main takeaways first.

---

## Table of Contents

1. [Economic Footprint](#1-economic-footprint) — Total scale, sector distribution, work activities, geography, trends
2. [Time Trends](#2-time-trends) — How exposure evolved over 16 months and what the trajectory shows
3. [Job Exposure](#3-job-exposure) — Which workers are most at risk and what they can do
4. [Potential Growth](#4-potential-growth) — The $980B adoption gap and where it lives
5. [Agentic Usage](#5-agentic-usage) — The full agentic AI footprint and what it's uniquely touching
6. [Source Agreement](#6-source-agreement) — What the four data sources agree and disagree on
7. [State Clusters](#7-state-clusters) — How states compare across five analytical dimensions
8. [Field Benchmarks](#8-field-benchmarks) — How our findings compare to the broader research landscape

---

## 1. Economic Footprint

*Full detail: [economic_footprint/economic_footprint_report.md](../questions/economic_footprint/economic_footprint_report.md)*

*Primary config: All Confirmed | Five configs compared*

### The Scale

61.3 million workers in the confirmed estimate. 77.1 million in the ceiling. The five-config picture:

| Config | Workers | Wages | % Employment |
|--------|---------|-------|-------------|
| All Confirmed (primary) | 61.3M | $3.99T | 40.0% |
| All Sources (ceiling) | 77.1M | $4.97T | 50.3% |
| Human Conversation only | 54.1M | $3.47T | 35.3% |
| Agentic Confirmed (AEI API only) | 31.1M | $2.16T | 20.3% |
| Agentic Ceiling (MCP + AEI API) | 60.4M | $3.97T | 39.4% |

The 15.8M-worker gap between confirmed and ceiling isn't noise. That's tasks where some AI systems have demonstrated capability but the evidence hasn't consolidated across sources. It's also a forward indicator — as capabilities continue to be confirmed, some portion of those 15.8M workers will shift from ceiling-only to confirmed.

The largest sectors by raw workers affected (All Confirmed): Office and Administrative Support (11.2M, 51.1% exposure), Sales (7.6M, 59.5%), Business and Financial Operations (5.5M, 50.7%). By task penetration percentage, Computer and Mathematical leads at 65.7%. By wages, Management tops the list at $613.9B despite moderate task penetration (35.5%) — the sector's massive payroll per worker does the work.

![Aggregate Totals Across Five Configs](../questions/economic_footprint/sector_footprint/figures/aggregate_totals.png)

![Workers Affected by Major Sector](../questions/economic_footprint/sector_footprint/figures/major_workers.png)

![Confirmed vs. Ceiling Range by Sector](../questions/economic_footprint/sector_footprint/figures/floor_ceiling_range.png)

### The Preparation Paradox

The standard automation narrative says low-skill workers face the most AI exposure. The data says otherwise. Average task exposure by O*NET job zone:

| Zone | Description | Avg % Tasks Affected |
|------|-------------|---------------------|
| Zone 1 | Little prep | ~26.9% |
| Zone 2 | Some prep | ~30.6% |
| Zone 3 | Medium prep | ~35.0% |
| **Zone 4** | **Considerable prep (bachelor's + experience)** | **~50.9%** |
| Zone 5 | Extensive prep (advanced degree) | ~45.9% |

Zone 4 — managers, accountants, engineers, analysts, healthcare practitioners — has the highest average AI task exposure. Zone 4 jobs are information-intensive, tool-mediated, and built around knowledge recall, written communication, and data analysis. Zone 1 jobs involve physical activity in unpredictable environments. The AI advantage is largest where the work is most cognitive and most structured.

Zone 5 dips from Zone 4's peak because the most elite professional work — original research, clinical judgment, legal strategy — retains meaningful AI-resistant components. The Zone 4 peak is where structured knowledge work at scale creates the greatest overlap with current AI capability.

Jobs with poor labor market outlooks (DWS Rating 3) carry higher average AI exposure (~39.2%) than bright-outlook jobs (Rating 1: ~29.8%). The labor market is already pricing in some of this — whether AI exposure is causing the poor outlook or merely correlated with it varies by occupation.

![AI Task Exposure by Job Zone](../questions/economic_footprint/job_structure/figures/zone_exposure_violin.png)

![Exposure Tier Breakdown by Job Zone](../questions/economic_footprint/job_structure/figures/zone_tier_heatmap.png)

![AI Task Exposure by Job Outlook Rating](../questions/economic_footprint/job_structure/figures/outlook_exposure_violin.png)

### Skills and Technology: What Kind of Work Is Exposed

Of 120 O*NET SKA elements, AI leads on 23 — all in knowledge or skills domains, none in physical or sensorimotor abilities. Top AI advantages: Sales and Marketing (+4.6), History and Archeology (+4.4), Philosophy and Theology (+3.3), Foreign Language (+3.3). Human advantages are concentrated in physical and perceptual abilities: Sound Localization (-7.9), Reaction Time (-7.8), Peripheral Vision (-7.7). Most cognitive skills are near parity or slight AI advantage.

The technology footprint tells the same story from a different angle. Weighted by task exposure × employment, the highest-footprint technology categories are database user interface software, ERP, and CRM software — the information infrastructure of the knowledge economy.

![Elements Where AI Leads](../questions/economic_footprint/skills_landscape/figures/ska_leads_ai.png)

![Elements Where Humans Lead](../questions/economic_footprint/skills_landscape/figures/ska_leads_human.png)

### Agentic vs. Conversational AI

Three configs capture the mode split: Human Conversation confirmed (54.1M workers), Agentic Confirmed (31.1M), Agentic Ceiling (60.4M). The agentic ceiling already exceeds conversational confirmed — the potential of agentic AI exceeds current conversational AI deployment. The 29.3M-worker gap between agentic confirmed and ceiling is an organizational deployment lag, not a capability limitation.

97.7% of workers in AI-affected occupations are in roles with meaningful AI augmentation potential (auto-aug score ≥ 2). The data supports an augmentation frame — AI can meaningfully assist almost every affected worker — even as the disruption from productivity change plays out.

![Agentic vs. Conversational by Sector](../questions/economic_footprint/ai_modes/figures/agentic_vs_conversational.png)

### How We Got Here: The Trend

The All Confirmed estimate roughly doubled from September 2024 to February 2026. Sector-level gains over the full series, ranked by percentage-point change:

1. Legal Occupations: +25.5pp (22.8% → 48.3%)
2. Educational Instruction and Library: +24.8pp (28.8% → 53.6%)
3. Sales and Related: +22.8pp (36.8% → 59.5%)
4. Computer and Mathematical: +22.3pp (43.4% → 65.7%)
5. Business and Financial Operations: +19.4pp (31.4% → 50.7%)

At the bottom: Farming (+1.9pp), Transportation (+2.3pp), Production (+2.6pp). The physical frontier hasn't moved.

Both confirmed and ceiling trajectories are expanding — they're not converging. The frontier is still advancing faster than the validation process can consolidate. New capabilities keep being proposed before old proposals fully harden into confirmed status.

![Aggregate Worker Count Trend Over Time](../questions/economic_footprint/trends/figures/aggregate_trend.png)

![Major Sector Exposure Growth](../questions/economic_footprint/trends/figures/major_growth_bar.png)

### Work Activities: The Mechanism Layer

The highest-penetration General Work Activities (GWAs) under All Confirmed: Updating and Using Relevant Knowledge (72.0%), Interpreting the Meaning of Information for Others (70.0%), Communicating with People Outside the Organization (69.6%), Working with Computers (69.3%). These are the activities that constitute information work. The robust end is entirely physical: Operating Vehicles (1.4%), Performing General Physical Activities (12.2%).

At the IWA level: "Respond to customer problems or inquiries" (75.2% exposure, 2.2M workers) and "Explain technical details of products or services" (81.9%, 1.3M workers) — customer-facing information work is among the most deeply affected activity types in the economy.

![GWA Task Penetration](../questions/economic_footprint/work_activities/figures/gwa_pct.png)

![Agentic vs. Conversational at GWA Level](../questions/economic_footprint/work_activities/figures/gwa_mode_butterfly.png)

### Geography: Five Clusters, No High-Exposure States

Every state has essentially the same average AI task exposure (~36.1%). This isn't a data error. Task exposure is computed at the occupation level using national datasets — a software developer in Utah has the same exposure as a software developer in Massachusetts. What varies across states is sector composition, which clusters into five recognizable economic types.

**Cluster 1 — Tech and Sun Belt metros** (AZ, CA, CO, FL, GA, MD, NC, TX, UT, VA, WA): highest Computer/Math and Sales shares.

**Cluster 2 — Diversified industrial and northeastern states** (NY, IL, OH, PA, MI, MA, and others): highest healthcare shares, most balanced sector mix.

**Cluster 3 — DC alone**: Business/Finance at 24.8%, Computer/Math at 21.2% — the federal contractor economy is its own category.

**Cluster 4 — Rural and inland states** (IA, KS, AL, MS, ID, ND, and others): highest Office/Admin, Food Prep, and Production shares.

**Cluster 5 — Tourism and service economies** (NV, HI, NM, GU, PR, VI): hospitality, tourism, and services; highest administrative share.

There are no "high-exposure states" versus "low-exposure states." State-level policy should be calibrated to sector composition.

![State Economic Cluster Map](../questions/economic_footprint/state_profiles/figures/state_cluster_map.png)

![Sector Composition by Cluster](../questions/economic_footprint/state_profiles/figures/cluster_heatmap.png)

---

## 2. Time Trends

*Full detail: [time_trends/time_trends_report.md](../questions/time_trends/time_trends_report.md)*

*Primary config: All Confirmed series (Sep 2024–Feb 2026) | Ceiling: All Sources series*

### The High-Exposure Tier Was Created During the Window

In September 2024, zero occupations had 60% or more of their tasks covered by confirmed AI usage. By February 2026, 145 did. The entire high-exposure tier didn't exist at the start of the measurement window — it was built during it.

41% of all occupations (381 of 923) changed exposure tier over the period. The Restructuring tier (20–39%) was the most dynamic: 433 occupations were there in September 2024, and more than half moved upward by February 2026. 212 occupations crossed the 33% risk gate — the threshold below which the risk model treats exposure as insufficient to classify an occupation as high-risk. Any risk tier assignment from September 2024 would misclassify a fifth of the occupational landscape.

![Exposure Tier Counts Over Time](../questions/time_trends/tier_churn/figures/tier_counts_over_time.png)

![New High-Tier Entrants by Sector](../questions/time_trends/tier_churn/figures/new_high_tier_by_sector.png)

### How Occupations Grew: Six Trajectory Types

44% of occupations — 406 of 923 — are laggards: less than 5 percentage points of total gain over 16 months. These are overwhelmingly physical and operational occupations. The expansion was concentrated in a 222-occupation "steady grower" cohort that moved from an average of 29% to 60% confirmed exposure over the period. The sectors driving the steady growers: Educational Instruction (44 occupations), Management (26), Healthcare Practitioners (23) — not Computer and Mathematical, which dominated the "early mover" category of occupations that were already high-exposure in September 2024 and added little since.

![Trajectory Type Mix by Sector](../questions/time_trends/trajectory_shapes/figures/trajectory_type_by_sector.png)

![Trajectory Scatter](../questions/time_trends/trajectory_shapes/figures/trajectory_scatter.png)

### The "Obvious" AI Occupations Are Flat

Software Developers, Data Scientists, and Accountants show identical confirmed values at every one of the six dataset dates — not approximately equal, identical to the hundredth of a percentage point. Their confirmed exposure profile was fully established by September 2024 and hasn't changed since.

Meanwhile, HR Specialists gained 53.5pp (22.4% → 75.8%), with 34.1pp of that in a single March 2025 update. Market Research Analysts: +49.7pp to 89.5%. Customer Service Representatives: +39.0pp to 84.1%. The occupations with the largest gains are not the headline-grabbing AI-disruption targets.

Registered Nurses crossed from 9.3% to 33.4%, crossing the 33% risk gate only in the final period (the August 2025 update added 22.1pp at once).

![All Named Occupations Over Time](../questions/time_trends/occs_timeline/figures/all_occs_confirmed.png)

![Total Gain Bar Chart](../questions/time_trends/occs_timeline/figures/occs_total_gain.png)

### Confirmed vs. Ceiling: The Gap Opened in August 2025

Before April 2025, there was no confirmed/ceiling gap — MCP hadn't been incorporated into the ceiling measurement yet. When MCP data was added in the August 2025 dataset, the ceiling jumped to 47.8% while confirmed was at 37.0%, creating a ~10pp gap. Since then, confirmed has grown slightly faster than ceiling, but both are growing and the absolute gap has barely moved.

The sector-level breakdown shows where MCP adds the most above what conversational AI confirms: Transportation (59% confirmed/ceiling ratio) and Production (68%) have the largest MCP-specific gaps. Legal and Education (both ~88%) have the smallest — MCP adds little in those domains beyond what conversational AI already covers.

![National Confirmed vs. Ceiling](../questions/time_trends/confirmed_ceiling_convergence/figures/national_confirmed_vs_ceiling.png)

![Sector Confirmed/Ceiling Ratio](../questions/time_trends/confirmed_ceiling_convergence/figures/sector_ratio_delta.png)

### Work Activity Tipping Points: What's Next

At the IWA level: zero activities were at ≥66% confirmed in September 2024; 52 are by February 2026. The fastest-growing IWA — "Evaluate scholarly work" — went from 11.3% to 88.0% (+76.7pp). Three of the top five fastest-growing IWAs are education-adjacent. "Research laws, precedents, or other legal data" sits at 92.5% — the highest final level of any fast grower.

Two dataset updates drove most threshold crossings: March 2025 and August 2025. The pattern isn't smooth accumulation — it's discrete jumps as new capabilities get confirmed across clusters of related activities simultaneously.

72 IWAs are currently in the active expansion zone (10–33%, growing): "Prepare financial documents" (30.2%), "Negotiate contracts" (30.1%), "Collect information about patients or clients" (29.1%), "Record information about legal matters" (26.5%). These are the activities most likely to cross the 33% threshold in the next 12–18 months at current growth rates.

![Top 20 Fastest-Growing IWAs](../questions/time_trends/wa_tipping_points/figures/top20_iwa_growth.png)

![IWAs Approaching 33%](../questions/time_trends/wa_tipping_points/figures/iwa_approaching_33pct.png)

---

## 3. Job Exposure

*Full detail: [job_exposure/job_exposure_report.md](../questions/job_exposure/job_exposure_report.md)*

*Primary config: All Confirmed | Five configs compared for robustness*

### Current Exposure State

Under confirmed usage, 145 occupations employing 31.4 million workers have 60% or more of their tasks exposed to AI. Another 219 occupations (41.8M workers) sit in the moderate band (40–60%). That's 364 occupations and 73.2 million workers where AI is already performing a substantial share of the task load — not theoretically, but based on confirmed usage patterns.

The gap to ceiling is uneven. Adding MCP capability data pushes the high tier from 145 to 249 occupations. Some occupations barely move — Technical Writers go from 85.8% to 85.9%. Others jump dramatically: Cashiers from 46.9% to 68.2%, General and Operations Managers from 27.9% to 52.3%, Software Developers from 45.2% to 64.7%. These are the occupations where agentic AI tooling has demonstrated capability that confirmed human usage hasn't yet reflected.

![Exposure Across Configs](../questions/job_exposure/exposure_state/figures/config_comparison.png)

![Exposure Tier Distribution by Major Category](../questions/job_exposure/exposure_state/figures/tier_stacked_by_major.png)

### Risk Scoring: Exposure ≠ Risk

A 90% task exposure score means something very different depending on the occupation's structural context. The seven-factor composite risk model addresses this directly:

**Direct exposure signals (weight 2 each):** task exposure above median, AI skill-capability gap above median, rising exposure trend, rising capability-gap trend.

**Structural vulnerability factors (weight 1 each):** job zone 1-3, poor labor market outlook, above-median software tool density.

An exposure gate at 33% prevents structurally vulnerable but low-exposure occupations from being classified as high-risk.

**195 occupations (50.7M workers) score as high-risk** — where both exposure and structural context converge. 224 occupations (20.1M workers) are low risk. 504 occupations (82.5M workers) sit at moderate.

The flag composition shows the logic. Score-4 occupations (141 of them, avg exposure 17.2%) are almost entirely structural: 89% have the job zone flag, 87% have poor outlook, but only 6% have the exposure flag. Vulnerable but not yet reached. Score-11 occupations (28 of them, avg exposure 64.7%) have every flag active — the "perfect storm" jobs.

272 occupations change risk tier depending on which AI capability source is used, which identifies which jobs' risk profile depends on which AI modality gets deployed.

![Risk Score vs. Task Exposure Scatter](../questions/job_exposure/job_risk_scoring/figures/risk_vs_pct_scatter.png)

![Flag Breakdown by Risk Score](../questions/job_exposure/job_risk_scoring/figures/flag_breakdown_by_score.png)

### Worker Resilience: What to Invest In

The SKA gap analysis produces a clean three-way split across domains:

**Abilities** — overwhelmingly human-advantaged. Roughly 285 ability elements favor humans versus 65 that favor AI. The top 15 human-advantage elements are all abilities: Sound Localization (-7.89), Reaction Time (-7.85), Peripheral Vision (-7.69), and on down. The only non-ability in the top 15 is Building and Construction knowledge.

**Knowledge** — the opposite. Roughly 285 knowledge elements favor AI versus just 15 where humans lead. AI's top advantages: Sales and Marketing (+4.64), History and Archeology (+4.44), Philosophy and Theology (+3.28), Foreign Language (+3.28). If your job's value comes primarily from knowing things, AI already exceeds the typical occupational need.

**Skills** — the contested middle. About 212 favor humans, 185 favor AI. This is where the actionable guidance lives: skills are trainable, and the human-advantage skills (service orientation, active listening, coordination) can be deliberately developed.

AI capability gaps are growing across all configs. The median SKA gap delta was +5.33 for confirmed usage and +6.52 for ceiling. The frontier is moving.

![Top Human-Advantage Elements](../questions/job_exposure/worker_resilience/figures/human_advantage_bar.png)

![Top AI-Advantage Elements](../questions/job_exposure/worker_resilience/figures/ai_advantage_bar.png)

### Reskilling Cost and the AI Paradox

Pivot cost — the total skill and knowledge gap between high-risk and low-risk occupations within the same job zone — varies from 55.7 (Zone 1) to 303.8 (Zone 3). Zone 3 is the crisis point: mid-level office and clerical workers face the longest pivot distance because low-risk occupations in their zone require technical knowledge they don't have — Mechanical (24.0 gap), Physics (16.4), Building and Construction (15.8).

The hopeful finding: across all job zones, the majority of pivot-cost elements are ones where AI capability already exceeds the at-risk worker's current level. In Zone 2, 99.5% of the reskilling cost is in AI-advantaged elements. AI can be deployed as a learning accelerator for the very skills workers need to acquire to move out of at-risk occupations.

![Pivot Cost by Job Zone](../questions/job_exposure/pivot_distance/figures/pivot_cost_by_zone.png)

![AI-Assisted Reskilling Breakdown](../questions/job_exposure/pivot_distance/figures/ai_assisted_reskilling.png)

### Hidden At-Risk Occupations

Using a projection method — which captures both direction and magnitude of skill-profile overlap with AI capabilities — 150 occupations emerge as hidden at-risk: low current confirmed exposure but high projection onto the AI capabilities vector. Healthcare dominates this list: Preventive Medicine Physicians, Urologists, Nurse Anesthetists, General Internal Medicine Physicians, and Physical Medicine/Rehabilitation Physicians all appear in the top 10.

53% of these hidden at-risk occupations are already seeing rising exposure in the confirmed config. The window for proactive intervention is not just open — it's actively closing.

![Hidden At-Risk: Projection vs. Exposure](../questions/job_exposure/audience_framing/figures/hidden_at_risk_scatter.png)

---

## 4. Potential Growth

*Full detail: [potential_growth/potential_growth_report.md](../questions/potential_growth/potential_growth_report.md)*

*Primary config: All Confirmed | Ceiling: All Sources*

### The $980B Adoption Gap

The gap between confirmed (61.3M workers, $3.99T wages) and ceiling (77.1M, $4.97T) is 15.8M workers and $980B in annual wages. This isn't future capability — it's tools that already work, not broadly deployed.

The sector-level distribution: Office and Administrative Support leads by raw worker gap (2.6M, from 51% to 68% confirmed-to-ceiling). Transportation leads by percentage-point gap (12.3pp, confirmed 17.6% to ceiling 29.9%). Management carries the largest wage gap because the occupations are high-paying. General and Operations Managers alone accounts for $90.2B in the gap — a single occupation category.

At the work activity level, "Documenting/Recording Information" (GWA) has the largest absolute gap: 37% → 67%, +4.4M workers. Documentation tools are mature and widely used in high-end settings. They're not deployed at the bulk of jobs where the task exists.

The trend: confirmed grew from 39.5M to 61.3M workers over 16 months (+55%). The gap persists because the ceiling also grew. Adoption is real but not at ceiling pace.

![Confirmed vs. Ceiling Gap by Major Sector](../questions/potential_growth/adoption_gap/figures/occ_gap_major.png)

![Top IWAs by Worker Gap](../questions/potential_growth/adoption_gap/figures/wa_gap_iwa.png)

![Confirmed Growth vs. Ceiling](../questions/potential_growth/adoption_gap/figures/gap_trend.png)

### Wage Potential: Where the Dollar Value Lives

$980B per year in wages sits in demonstrated-but-undeployed capability. For every $4 that AI tools currently reach in wages, there's another dollar in demonstrated-but-not-deployed capability.

The wage gap is concentrated at the top of the wage distribution. Management carries the largest sector wage gap because management occupations are both high-wage and have a large adoption gap. At the IWA level, "Maintain operational records" carries $144B in the wage gap — more economic value in its adoption gap than many entire industry sectors.

The hotspot analysis (59 occupations in the top quartile on both median wage and adoption gap): Software QA Analysts ($114K median, 25.6pp gap), Software Developers ($114K, 19.5pp), Medical and Health Services Managers ($118K, 17.8pp). These are roles where closing the gap produces the most per-worker economic value.

![Wage Gap by Major Sector](../questions/potential_growth/wage_potential/figures/wage_gap_major.png)

![Wage Hotspot: High-Wage + Large-Gap Occupations](../questions/potential_growth/wage_potential/figures/wage_hotspot_scatter.png)

### Automation Opportunity: Where Capability, Gap, and Risk Converge

248 occupations fall in the automation opportunity quadrant: AI capability already exceeds occupational skill need AND the adoption gap is large. This is where the economic opportunity is most legible — tools exist, humans are capable, the gap is deployment.

102 of those 248 also carry a high risk tier from the job risk scoring model. These are the transformation signal occupations — where capability, deployment gap, and structural vulnerability all converge. The list is dominated by Office/Admin and Sales: Cashiers (+3.56 SKA gap, 21pp adoption gap, high risk), Retail Salespersons, Bookkeeping Clerks, Office Clerks, Billing Clerks, Executive Secretaries.

The remaining 146 Q1 occupations (without high risk tier) are more purely opportunity-framed: Software QA Analysts, Project Management Specialists, Medical Secretaries (moderate risk). For these, the story is augmentation and productivity, not displacement pressure.

![Automation Opportunity Scatter](../questions/potential_growth/automation_opportunity/figures/opportunity_scatter.png)

![Transformation Signal Occupations](../questions/potential_growth/automation_opportunity/figures/transformation_signal.png)

---

## 5. Agentic Usage

*Full detail: [agentic_usage/agentic_usage_report.md](../questions/agentic_usage/agentic_usage_report.md)*

*Primary configs: AEI API 2026-02-12 (Agentic Confirmed) | MCP Cumul. v4 | MCP + API 2026-02-18 (Agentic Ceiling)*

### The Four Exposure Scenarios

| Scenario | Workers | % Employment | Wages |
|---|---|---|---|
| Agentic Confirmed (AEI API) | 31.1M | 20.3% | $2.16T |
| MCP Only | 46.5M | 30.4% | $2.97T |
| Agentic Ceiling (MCP+API) | 60.4M | 39.4% | $3.97T |
| Conversational Baseline | 61.3M | 40.0% | $3.99T |

The agentic ceiling nearly matches the conversational confirmed baseline. At 156 high-tier (≥60%) occupations under the ceiling vs. just 36 under confirmed, the gap represents 120 occupations and ~26M workers where deployment is plausible but not yet documented.

![Agentic Exposure State Comparison](../questions/agentic_usage/exposure_state/figures/exposure_state_comparison.png)

### Sector Footprint

Five major categories account for the bulk of agentic ceiling exposure: Office and Administrative Support (12.9M workers, 62.1%), Sales (9.2M, 68.5%), Business and Financial Operations (5.6M, 52.6%), Management (5.5M, 41.7%), Computer and Mathematical (3.8M, 75.0%).

The agentic delta (ceiling minus conversational baseline) shows which sectors specifically benefit from tool-calling AI: Office/Admin (+11.0pp), Computer/Math (+9.3pp), Sales (+8.9pp). The negative deltas — Food Prep (-14.7pp), Community/Social Services (-11.9pp), Education (-11.7pp) — are sectors where conversational AI already covers the relevant tasks and agentic capabilities add little.

![Agentic vs. Conversational Delta by Sector](../questions/agentic_usage/sector_footprint/figures/agentic_vs_conv_delta.png)

### What Agentic AI Uniquely Touches

The biggest IWA gains when moving from conversational to agentic ceiling: "Record information about environmental conditions" (+57.8pp), "Maintain operational records" (+51.1pp), "Prepare schedules for services or facilities" (+50.7pp). Agentic AI's marginal contribution over conversational AI is in automating the operational backbone — scheduling, documentation, records management — not the creative or analytical work that gets attention.

MCP's signature occupations — Telemarketers (90%), Online Merchants (87%), Web Developers (85%) — are roles with high digital system interaction. Where MCP leads AEI API most: Data Scientists (+72pp), Sales service reps (+71pp), Penetration Testers (+61pp). Where AEI API leads MCP: Patient Representatives (-53pp), Actors (-48pp), Industrial-Organizational Psychologists (-44pp). The pattern is clean: MCP measures AI-system interaction capability; AEI API measures AI-human workflow deployment.

![Top IWAs Under Agentic Ceiling](../questions/agentic_usage/work_activities/figures/top_iwas_agentic_ceiling.png)

![IWA Delta: Agentic vs. Conversational](../questions/agentic_usage/work_activities/figures/iwa_delta_agentic_vs_conv.png)

![MCP vs. AEI API by Sector](../questions/agentic_usage/mcp_profile/figures/mcp_vs_aei_delta_major.png)

### Growth Trajectory

The agentic ceiling grew from 33.4M workers (April 2025) to 60.4M (February 2026) — 81% growth in under a year. Growth was front-loaded: the August 2025 update added 9.4M workers in a single step. The pace slowed substantially in late 2025 and early 2026, with the last two updates adding a combined 1.0M workers.

AEI API grew more steadily: 23.4M (Aug 2025) to 31.1M (Feb 2026), tracking real enterprise deployment rather than benchmark capability expansion.

The measurement framework (eco_2025 task taxonomy matched to MCP benchmarks) is approaching saturation. The real agentic exposure number may already exceed what current metrics can capture.

![Agentic Ceiling Trend](../questions/agentic_usage/trends/figures/agentic_ceiling_trend.png)

![AEI API and MCP Trends](../questions/agentic_usage/trends/figures/aei_api_mcp_trend.png)

---

## 6. Source Agreement

*Full detail: [source_agreement/source_agreement_report.md](../questions/source_agreement/source_agreement_report.md)*

*Four sources: Human Conv. (AEI Conv + Micro) | Agentic (AEI API) | Microsoft | MCP Cumul. v4*

### Agreement Degrades with Granularity

Spearman rank correlations between sources: major category (mean rho = 0.875), minor (0.807), broad (0.732), occupation (0.676). This is the expected pattern: broad sector agreement, specific occupation disagreement.

Six major categories achieve unanimous high-confidence consensus (all four sources agree): Arts/Design/Entertainment, Business/Financial Operations, Computer/Mathematical, Life/Physical/Social Science, Office/Admin Support, and Sales. Ten major categories are effectively single-source or no-source — Construction, Farming, Food Prep, both Healthcare groups, Installation/Maintenance, Personal Care, Production, Protective Service, Transportation. These sectors are consistently rated as low AI-exposure by every source, which is informative in itself.

91% of occupations have zero cross-source consensus in the top-30 most exposed. The sources identify almost entirely different specific occupations as most affected, even within sectors they agree on.

![Correlation Matrix by Aggregation Level](../questions/source_agreement/ranking_agreement/figures/correlation_matrix_by_level.png)

![Confidence Tiers by Level](../questions/source_agreement/ranking_agreement/figures/confidence_tiers.png)

### Score Distributions: Very Different Shapes

The four sources produce dramatically different distributions. Human Conv. is most aggressive (mean 32.1%, 81 occupations in high tier). AEI API is most conservative (median 8.6%, 626 occupations below 20%). Microsoft is compressed with a hard ceiling near 58% and **zero high-tier occupations**. MCP spreads more than Microsoft but has a large low-tier cohort.

Tier breakdown across 923 occupations:

| Source | <20% | 20–40% | 40–60% | ≥60% |
|---|---|---|---|---|
| Human Conv. | 280 | 342 | 220 | 81 |
| Agentic (AEI API) | 626 | 158 | 103 | 36 |
| Microsoft | 369 | 433 | 121 | **0** |
| MCP | 445 | 304 | 120 | 54 |

The highest-variance occupations — Data Scientists (std=30.0), Penetration Testers (std=27.6), Actors (std=28.0) — show the most cross-source disagreement. Policy targeting these roles based on one source may be wrong by a factor of 3.

![Score Distribution by Source](../questions/source_agreement/score_distributions/figures/pct_distribution_by_source.png)

![Tier Distribution by Source](../questions/source_agreement/score_distributions/figures/tier_distribution.png)

### What Each Source Uniquely Sees

Human Conv. uniquely emphasizes tutoring, creative work, and lab-science roles. AEI API's distinctive hits are healthcare education, media production, and adult literacy instruction. Microsoft has no clearly distinctive occupations — it's the most generic rater. MCP uniquely flags GIS technicians, infrastructure operators, and technical coordination roles — the system-interaction side of AI.

The GWA-level portrait confirms the theme: Human Conv. leads on information-processing GWAs; MCP spikes on scheduling and planning GWAs; Microsoft maintains consistent but moderate coverage.

![Distinctive Human Conv. Occupations](../questions/source_agreement/source_portraits/figures/distinctive_human_conv.png)

![Distinctive MCP Occupations](../questions/source_agreement/source_portraits/figures/distinctive_mcp.png)

### Marginal Contributions: What Each Layer Adds

Adding the API layer (Human Conv. → All Confirmed): 64 occupations upgrade to High tier, concentrated in tech-adjacent and analytical roles. Adding MCP (All Confirmed → All Ceiling): 104 occupations upgrade to High; broader sweep — Office/Admin (+17.3pp), Management (+15.7pp), Sales (+15.0pp) at the major-category level. 42 IWAs cross the 33% threshold from the MCP addition, vs. 10 from the API addition.

Neither addition causes occupations to lose exposure. The signals are additive.

![Tier Transition: MCP Addition](../questions/source_agreement/marginal_contributions/figures/tier_shift_mcp.png)

![Major Category Gain from MCP Addition](../questions/source_agreement/marginal_contributions/figures/major_delta_mcp.png)

---

## 7. State Clusters

*Full detail: [state_clusters/state_clusters_report.md](../questions/state_clusters/state_clusters_report.md)*

*Builds on economic_footprint/state_profiles sector-composition baseline*

### Five Lenses, Five Different Groupings

The economic_footprint/state_profiles analysis established that average pct_tasks_affected is ~36% everywhere and that meaningful variation is in sector composition. This bucket runs four additional clusterings — risk tier distribution, work activity signature, agentic intensity, and adoption gap — and asks whether the same state groupings emerge.

They don't. All pairwise Adjusted Rand Index values between schemes are ≤ 0.26. The maximum is sector composition × activity signature (0.26) — both capture "what type of work" states do, just from different angles. Agentic intensity × adoption gap is 0.03 — essentially random. The five lenses are measuring genuinely different things about state economies.

![ARI Heatmap Between All 5 Clusterings](../questions/state_clusters/cluster_convergence/figures/ari_heatmap.png)

### Risk Profile: Puerto Rico and Virginia Are Not the Same

Clustering states by employment-weighted risk tier distribution shows significant variation: pct_high workers ranges from 35.9% (Massachusetts) to 48.9% (Puerto Rico/U.S. Virgin Islands). Tourism/service economies (PR, VI) concentrate structural vulnerability because their workforces have lower job zones and below-average outlooks. Massachusetts and other large northeastern states have high exposure but not the structural vulnerability flags — high exposure in well-buffered professional roles.

DC is risk-middle-of-the-road despite being an outlier on sector composition: its government and contractor workforce is highly exposed but high-zone, well-compensated, and mostly in stable positions.

![Risk Tier Distribution by State](../questions/state_clusters/risk_profile/figures/risk_tier_bars.png)

### Activity Signature: DC Is Five Standard Deviations from Everyone Else

Clustering by GWA share of AI-exposed employment shows how small differences between non-DC states are. The gap between any two non-DC clusters on any GWA is less than 1 percentage point. AI exposure is pre-selected for cognitive and administrative tasks, so the activity fingerprint converges across very different state economies.

DC is the massive outlier: +3.89pp more "Thinking Creatively" and +2.83pp more "Analyzing Data" than the national average — nothing else comes close. Its knowledge-worker concentration is genuinely different in kind, not just degree.

![GWA Heatmap by State and Cluster](../questions/state_clusters/activity_signature/figures/gwa_heatmap.png)

### Agentic Intensity and Adoption Gap: Uniform Everywhere

The national average agentic intensity (agentic/confirmed workers) is 0.507; the state range is 0.474 (Guam) to 0.571 (DC). The adoption gap averages 0.243, range 0.216–0.277. These two dimensions are essentially uniform — and nearly orthogonal to everything else (ARI ≤ 0.13 vs. all other schemes).

Policy focused on "which states are most exposed to agentic AI" or "which states have the most room for AI to spread" gets roughly the same answer for every state: all of them, to the same degree.

![Agentic Intensity by State](../questions/state_clusters/agentic_profile/figures/overall_agentic_bar.png)

![Adoption Gap by State](../questions/state_clusters/adoption_gap/figures/overall_gap_bar.png)

### State Stability: Who's Consistently Typical, Who's Consistently Anomalous

DC has the lowest stability score (0.07): consistently anomalous under every lens, but in different ways each time. The most stable states — WV, ME, WI, MO, KS — consistently co-cluster with each other across multiple schemes. They're "typical" by multiple dimensions at once. Their challenges may be less likely to be recognized as distinctive precisely because the data doesn't flag them as unusual from any angle.

![State Stability Scores](../questions/state_clusters/cluster_convergence/figures/stability_bar.png)

---

## 8. Field Benchmarks

*Full detail: [field_benchmarks/field_benchmarks_report.md](../questions/field_benchmarks/field_benchmarks_report.md)*

*External sources: Project Iceberg | Seampoint LLC (Utah) | AEI (Humlum & Vestergaard) | ChatGPT usage | Microsoft Copilot*

### The Measurement Spectrum

Our 40% confirmed exposure estimate isn't a high outlier — it sits within the range of what every major AI-and-work study has found, once you understand what each is measuring. The apparent contradictions between studies mostly dissolve when you map each source to its position in the measurement spectrum:

- **Confirmed real-world usage** (our data, AEI, ChatGPT): 20–40%
- **Deployment-constrained readiness** (Seampoint): 20–51%
- **Technical capability ceiling** (Iceberg): 2–12%

These aren't competing estimates of the same thing. They're different experiments answering different questions about what AI is doing, can do under governance constraints, or could technically substitute.

![Three-Layer Measurement Spectrum](../questions/field_benchmarks/automation_share/figures/layer_chart.png)

![Full Methodology Map](../questions/field_benchmarks/platform_landscape/figures/methodology_map.png)

### The 20.3% = 20% Cross-Validation

Our agentic_confirmed rate (20.3%) matches Seampoint's governance-constrained takeover rate (20%) to within a rounding error. These two numbers were produced by entirely different methodologies, from different data sources, asking related but distinct versions of the same question.

Seampoint: "What fraction of Utah work hours can AI fully take over under current governance constraints?"

Our agentic_confirmed: "What fraction of national employment is in occupations where confirmed agentic (tool-use) AI usage has been documented?"

Both arrive at 20%. This is the most meaningful external cross-validation in the field for our framework.

The ceiling comparison is equally clean: our all_ceiling (50.3%) and Seampoint's augment estimate (51%) — the upper bound for near-term AI task coverage — also converge. Both analyses point to ~50% as the natural near-term ceiling of AI task coverage.

### Project Iceberg: Not a Contradiction

Project Iceberg (Chopra et al., 2025) produces a "Full Index" of 11.7%. This is below our confirmed 40%, which sounds like a contradiction until you understand the unit difference. Iceberg is measuring the fraction of skill-wage value that AI can substitute — a narrow, conservative concept that requires the AI to replace not just the task but the underlying economic value of the skill. We're measuring breadth of task involvement, which includes augmentative uses where AI assists but doesn't substitute.

An AI system touching 40% of a worker's tasks doesn't mean it's substituting 40% of their skill value. Most of those interactions are augmentative. Both numbers are defensible; they're measuring different things.

### Cross-Platform Sector and Activity Consensus

Five independent sources — our dashboard, Copilot enterprise data, AEI task-attempt analysis, ChatGPT work sessions, and Microsoft's assessment — all identify the same high-exposure cluster: Computer/Math, Office/Admin, Sales, Business/Finance. The sector ranking is robust across every source that measures at the sector level.

At the activity level, three GWAs dominate every platform's distribution: Documenting/Recording Information, Getting Information, and Processing Information. This convergence across independent platforms and methodologies is one of the strongest validation signals in the field.

AEI's 57% augmentative / 43% automative split — where augmentative means AI working alongside humans rather than replacing them — is consistent with our auto-augmentation framework finding that most AI task involvement extends human judgment rather than replacing it outright.

![Cross-Source Sector Rankings](../questions/field_benchmarks/sector_breakdown/figures/cross_source_sectors.png)

![Platform GWA Alignment](../questions/field_benchmarks/work_activity_comparison/figures/platform_gwa_alignment.png)

### Utah: $62.6B in Confirmed AI Task Scope

Utah's all_confirmed rate: 41.9% — slightly above the 40.0% national rate, reflecting Utah's professional-services-heavy workforce composition. In dollar terms, $62.6B of Utah wages are in confirmed AI task scope, against a $104B total Utah wage base.

Seampoint pegs $21B to tasks AI can fully take over and $36B total in Utah. Our $62.6B is higher because we're measuring all AI-touched tasks, not just governance-ready full-handoff tasks. When normalized to the same measurement framework, the numbers are consistent with the 20%/40%/50% spectrum observed nationally.

![Utah Task Exposure vs. Seampoint](../questions/field_benchmarks/utah_benchmarks/figures/utah_pct_comparison.png)

---

## Cross-Cutting Findings

**The preparation paradox.** Zone 4 workers are the most AI-exposed. This complicates any policy frame focused exclusively on low-education workers — by task exposure, the people most often assumed to be safe are facing the most pressure. At the same time, Zone 4 workers have the most economic cushion to absorb or adapt to change.

**Exposure ≠ risk, and the difference matters for targeting.** The seven-factor risk model with an exposure gate correctly identifies 195 occupations (50.7M workers) as genuinely high-risk. Sorting by exposure alone would produce a different and less useful population. "High risk" in this framework reliably means both significant task penetration AND structural vulnerability.

**The deployment gap is organizational, not technological.** The agentic ceiling (60.4M workers) already exceeds conversational confirmed (54.1M). $980B in wages sits in demonstrated-but-undeployed capability. The tools exist. The bottleneck is enterprise deployment infrastructure and organizational adoption, not further AI capability development.

**AI is the best reskilling tool for the displacement it causes.** Across all job zones, the majority of pivot-cost elements are ones where AI capability exceeds the at-risk worker's current level. In Zone 2, 99.5% of the reskilling cost is AI-advantaged. Policy that ignores this leaves significant leverage on the table.

**The "obvious" AI occupations plateaued early; the unexpected ones grew.** Software Developers, Data Scientists, and Accountants: zero confirmed growth over 16 months. HR Specialists, Market Research Analysts, Customer Service Representatives: 39–54pp gains. Risk assessments that rely on intuition about which jobs "seem" AI-prone will consistently miss the occupations that are actually changing.

**Sector-level findings are robust; occupation-level findings are source-dependent.** Major-level source correlation = 0.875. Occupation-level = 0.676. 91% of occupations have zero cross-source consensus in the top-30. Sector policy can proceed with confidence; occupation-specific interventions require source-specific justification and should be treated as provisional.

**External cross-validation is unusually clean.** Our agentic_confirmed (20.3%) matches Seampoint's takeover estimate (20%). Our ceiling (50.3%) matches Seampoint's augment ceiling (51%). Both convergences were arrived at independently. The framework is measuring something real.

---

## Sub-Report Index

| Bucket | Report | Core Question |
|---|---|---|
| Economic Footprint | [economic_footprint_report.md](../questions/economic_footprint/economic_footprint_report.md) | Total scale, sectors, work activities, geography, trends |
| Time Trends | [time_trends_report.md](../questions/time_trends/time_trends_report.md) | How AI exposure evolved over 16 months |
| Job Exposure | [job_exposure_report.md](../questions/job_exposure/job_exposure_report.md) | Which workers are most at risk and what they can do |
| Potential Growth | [potential_growth_report.md](../questions/potential_growth/potential_growth_report.md) | The $980B adoption gap and where it lives |
| Agentic Usage | [agentic_usage_report.md](../questions/agentic_usage/agentic_usage_report.md) | The full agentic AI footprint and growth trajectory |
| Source Agreement | [source_agreement_report.md](../questions/source_agreement/source_agreement_report.md) | What the four sources agree and disagree on |
| State Clusters | [state_clusters_report.md](../questions/state_clusters/state_clusters_report.md) | State variation across five analytical dimensions |
| Field Benchmarks | [field_benchmarks_report.md](../questions/field_benchmarks/field_benchmarks_report.md) | How our numbers compare to the broader research landscape |

---

## Config Reference

| Config Key | Dataset | Role |
|---|---|---|
| `all_confirmed` | AEI Both + Micro 2026-02-12 | **PRIMARY** — all confirmed usage |
| `all_ceiling` | All 2026-02-18 | Upper bound — includes MCP |
| `human_conversation` | AEI Conv + Micro 2026-02-12 | Confirmed human conversational use only |
| `agentic_confirmed` | AEI API 2026-02-12 | Confirmed agentic tool-use (AEI API only) |
| `agentic_ceiling` | MCP + API 2026-02-18 | Agentic ceiling — MCP + AEI API |

*All analyses use freq method, auto-aug ON, national geography unless explicitly noted.*
