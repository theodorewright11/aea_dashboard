# Analysis Charts — Dashboard Reproduction Guide

How to reproduce key analysis figures using the live AEA Dashboard, or why certain charts require custom computation. One section per analysis bucket; one entry per committed figure.

---

## Dataset Mapping

The five ANALYSIS_CONFIGS correspond to these dashboard dataset selections:

| Config Key | Dashboard Datasets | Combine |
|---|---|---|
| `all_confirmed` | AEI Cumul. (Both) v4 + Microsoft | Average |
| `all_ceiling` | AEI Cumul. (Both) v4 + MCP Cumul. v4 + Microsoft | Max |
| `human_conversation` | AEI Cumul. Conv. v4 + Microsoft | Average |
| `agentic_confirmed` | AEI API Cumul. v4 (alone) | Average |
| `agentic_ceiling` | AEI API Cumul. v4 + MCP Cumul. v4 | Average |

All dashboard reproductions use: Method = Time, Physical = All, Auto-aug = ON, Geo = National unless noted.

---

## 1. Economic Footprint

### 1.1 Sector Footprint (`economic_footprint/sector_footprint/`)

**`aggregate_totals.png`** — Vertical bar: one bar per config showing workers affected (M), annotated with % of national employment. Each bar is a distinct color.
- Not directly reproducible. The dashboard shows bar charts per category, not aggregate economy totals. Use tooltips in Occupation Categories to read individual sector totals.

**`major_workers.png`** — Horizontal bar: top major occupational categories by workers affected (all_confirmed).
- **Page:** Occupation Categories
- **Group A:** Datasets = AEI Cumul. (Both) v4 + Microsoft | Combine = Average | Agg = Major Category | Sort = Workers Affected | Top N = 23

**`major_wages.png`** — Horizontal bar: top major categories by wages affected (all_confirmed).
- **Page:** Occupation Categories
- **Group A:** same as above but Sort = Wages Affected

**`major_pct.png`** — Horizontal bar: top major categories by % tasks affected (all_confirmed).
- **Page:** Occupation Categories
- **Group A:** same but Sort = % Tasks Affected

**`floor_ceiling_range.png`** — Dumbbell: confirmed vs ceiling % tasks affected per major category.
- **Page:** Occupation Categories (two groups)
- **Group A:** AEI Cumul. (Both) v4 + Microsoft | Average | Sort = % Tasks Affected
- **Group B:** AEI Cumul. (Both) v4 + MCP Cumul. v4 + Microsoft | Max | Sort = % Tasks Affected
- Note: Tooltips show delta between groups. The dumbbell format is analysis-only; dashboard shows side-by-side bars.

**`config_heatmap.png`** — Heatmap: major category × five configs, % tasks affected.
- Not reproducible. The dashboard cannot display multi-config comparisons in a single heatmap view.

**`treemap_wages.png`** — Treemap: sector block sizes = wages affected, color = % tasks affected.
- Not reproducible. The dashboard only produces bar charts.

### 1.2 Skills Landscape (`economic_footprint/skills_landscape/`)

**`ska_leads_ai.png`** — Horizontal bar: top 20 SKA elements where AI capability exceeds human occupational need.
- Not reproducible. SKA gap computation is analysis-only; not available in the dashboard.

**`ska_leads_human.png`** — Horizontal bar: top 20 elements where humans lead AI.
- Not reproducible. Same reason.

**`ska_major_heatmap.png`** — Heatmap: major occupational category × config, average overall SKA gap.
- Not reproducible.

**`tech_top_economy.png`** — Horizontal bar: top 25 O*NET technology categories by exposure-weighted presence.
- Not reproducible. Technology skill category analysis is not in the dashboard.

**`tech_major_heatmap.png`** — Heatmap: major sector × top tech categories (normalized counts).
- Not reproducible.

### 1.3 Job Structure (`economic_footprint/job_structure/`)

**`job_zone_bar.png`** (or similar) — Workers/wages/pct by job zone (1–5).
- Not directly reproducible. The dashboard can filter by threshold values but doesn't aggregate by job zone.

**`outlook_bar.png`** — Exposure by job outlook rating.
- Not reproducible. Job outlook (DWS star rating) is a column in the Explorer but not a grouping dimension on the chart pages.

### 1.4 AI Modes (`economic_footprint/ai_modes/`)

**`agentic_vs_conv_scatter.png`** / agentic comparison charts — Scatter/bar comparing agentic vs. conversational exposure.
- **Page:** Occupation Categories (two groups)
- **Group A:** AEI Cumul. Conv. v4 + Microsoft | Average | Agg = Major | Sort = Workers Affected
- **Group B:** AEI API Cumul. v4 + MCP Cumul. v4 | Average | Agg = Major | Sort = Workers Affected
- Note: Dashboard shows side-by-side bars; analysis produces scatter and butterfly charts.

**Auto-aug distribution charts** — Not reproducible. Score distribution histograms are analysis-only.

### 1.5 Trends (`economic_footprint/trends/`)

**Trend line charts** — Workers/wages/pct over time for all_confirmed series.
- **Page:** Trends → Occupation Categories tab
- **Datasets:** Select all AEI Cumul. (Both) versions + Microsoft versions
- **Metric:** Workers Affected (or Wages / % Tasks)
- **Line mode:** Average
- Note: The dashboard Trends page covers similar territory. Use "All" dataset versions to approximate config series.

### 1.6 State Profiles (`economic_footprint/state_profiles/`)

**`state_cluster_map.png`** — US map showing 5 state clusters by sector composition.
- Not reproducible. The dashboard has a geography dropdown but no map visualization.

**`cluster_profiles.png`** — Grouped bar: sector composition share per cluster.
- Not reproducible. Cluster computation is analysis-only.

**`state_sector_heatmap.png`** — Heatmap: state × sector, share of AI-exposed workforce.
- Not reproducible.

### 1.7 Work Activities (`economic_footprint/work_activities/`)

**`gwa_workers.png`** — Horizontal bar: general work activities by workers affected (all_confirmed).
- **Page:** Work Activities
- **Group A:** AEI Cumul. (Both) v4 + Microsoft | Average | Activity Level = GWA | Sort = Workers Affected | Top N = 20

**`gwa_pct.png`** — Horizontal bar: GWAs by % tasks affected.
- **Page:** Work Activities
- **Group A:** same as above | Sort = % Tasks Affected

**`gwa_config_heatmap.png`** — Heatmap: GWA × five configs, % tasks affected.
- Not reproducible. Multi-config heatmap is analysis-only.

**`gwa_mode_butterfly.png`** — Butterfly: conversational vs. agentic workers by GWA.
- **Page:** Work Activities (two groups)
- **Group A:** AEI Cumul. Conv. v4 + Microsoft | Average | GWA | Sort = Workers Affected
- **Group B:** AEI API Cumul. v4 + MCP Cumul. v4 | Average | GWA | Sort = Workers Affected
- Note: Butterfly layout is analysis-only; dashboard shows side-by-side bars.

**`gwa_trend.png`** — Line chart: top GWAs by pct trend over time.
- **Page:** Trends → Work Activities tab
- **Datasets:** Select all AEI Cumul. (Both) versions
- **Activity Level:** GWA | **Metric:** % Tasks Affected

---

## 2. Job Exposure

### 2.1 Exposure State (`job_exposure/exposure_state/`)

**`scatter_exposure_vs_emp_confirmed.png`** — Scatter: pct_tasks_affected vs. employment per occupation (all_confirmed).
- Not reproducible. The dashboard does not produce scatter plots.

**`tier_distribution_bar.png`** — Stacked/grouped bar: occupation counts by exposure tier (High/Moderate/Restructuring/Low).
- Not reproducible. Tier thresholds are analysis-defined.

**`top_occ_workers.png`** — Horizontal bar: top occupations by workers affected.
- **Page:** Occupation Categories
- **Group A:** AEI Cumul. (Both) v4 + Microsoft | Average | Agg = Occupation | Sort = Workers Affected | Top N = 30

**`config_comparison_pct.png`** — Multi-config comparison chart.
- Not reproducible. Multi-config comparison at occupation level is analysis-only.

### 2.2 Job Risk Scoring (`job_exposure/job_risk_scoring/`)

**`risk_tier_distribution.png`** — Bar: count of high/moderate/low risk occupations.
- Not reproducible. Risk scoring is analysis-only (7-factor weighted model).

**`risk_score_scatter.png`** — Scatter: risk score vs. exposure.
- Not reproducible.

**`top_high_risk_occs.png`** — Horizontal bar: top high-risk occupations by employment.
- Approximate: **Page:** Occupation Categories | Agg = Occupation | Sort = Workers Affected | then filter by % Tasks Affected ≥ 33% via Explorer threshold filters.

**`tier_shift_heatmap.png`** — Heatmap: usage tier vs. ceiling tier for each occupation.
- Not reproducible.

### 2.3 Worker Resilience (`job_exposure/worker_resilience/`)

All figures (SKA gap distributions, top human-advantage elements, top AI-advantage elements) require SKA computation and are not reproducible on the dashboard.

### 2.4 Pivot Distance (`job_exposure/pivot_distance/`)

All figures (reskill cost distributions, job zone transition maps) require multi-occupational SKA distance computation and are not reproducible on the dashboard.

### 2.5 Audience Framing (`job_exposure/audience_framing/`)

Charts showing policy-framing GWA views and education skill profiles.
- **`policy_gwa_chart.png`** — Top GWAs for policy audience.
  - **Page:** Work Activities | GWA | Sort = Workers Affected | Top N = 15
- Other framing charts are analysis-only (skill domain breakdowns, audience-specific narratives).

### 2.6 Occupations of Interest (`job_exposure/occs_of_interest/`)

**`occs_of_interest_exposure.png`** — Horizontal bar: the 29 named occupations by pct_tasks_affected.
- **Page:** Occupation Explorer (Advanced)
  - Search for individual occupation names to find their metrics.
  - No single dashboard view shows all 29 at once; use the Explorer table with threshold filters.

---

## 3. Work Activity Exposure

### 3.1 Exposure State (`work_activity_exposure/exposure_state/`)

**`top_iwas_pct.png`** — Horizontal bar: top 20 IWAs by % tasks affected (all_confirmed).
- **Page:** Work Activities
- **Group A:** AEI Cumul. (Both) v4 + Microsoft | Average | Activity Level = IWA | Sort = % Tasks Affected | Top N = 20

**`top_iwas_workers.png`** — Horizontal bar: top 20 IWAs by workers affected.
- **Page:** Work Activities
- **Group A:** same as above | Sort = Workers Affected

**`gwa_config_comparison.png`** — Grouped vertical bar: GWA exposure across all 5 configs.
- Not reproducible. Multi-config comparison is analysis-only.

**`iwa_trends.png`** — Line chart: top IWA pct trends over time.
- **Page:** Trends → Work Activities tab
- **Datasets:** All AEI Cumul. (Both) versions | **Activity Level:** IWA | **Metric:** % Tasks Affected | **Line mode:** Individual or Average

**`iwa_confirmed_vs_ceiling.png`** — Scatter: confirmed vs. ceiling pct per IWA.
- Not reproducible. The dashboard doesn't produce scatter plots.

### 3.2 Activity Robustness (`work_activity_exposure/activity_robustness/`)

**`robustness_tier_bar.png`** — Bar: IWA count per robustness tier (Robust/Moderate/Fragile).
- Not reproducible. Tier classification is analysis-defined (<33%, 33-66%, ≥66%).

**`next_wave_iwas.png`** — Horizontal bar: IWAs currently robust but ceiling puts them at ≥33%.
- Not reproducible. Requires confirmed vs. ceiling comparison with tier thresholds.

**`gwa_robustness_summary.png`** — GWA-level robustness overview.
- **Page:** Work Activities (two groups for confirmed vs. ceiling)
- **Group A:** AEI Cumul. (Both) v4 + Microsoft | Average | GWA | Sort = % Tasks Affected
- **Group B:** AEI Cumul. (Both) v4 + MCP Cumul. v4 + Microsoft | Max | GWA | Sort = % Tasks Affected
- Note: Use tooltips to compare rates. The robustness tier classification itself is analysis-only.

### 3.3 Education Lens (`work_activity_exposure/education_lens/`)

**`durable_targets_bar.png`** — Horizontal bar: IWAs that are durable training targets (robust + growing slowly or stable).
- Not reproducible. Durability classification is analysis-only.

**`workforce_by_tier.png`** — Workers in each robustness tier across all IWAs.
- Not reproducible.

**`domain_exposure_bar.png`** — Domain-level exposure breakdown (cognitive/social/physical/technical).
- Not reproducible. Domain classification is analysis-only.

### 3.4 Audience Framing (`work_activity_exposure/audience_framing/`)

**`policy_gwa_chart.png`** — Top GWAs for policy-relevant messaging.
- **Page:** Work Activities | GWA | Sort = Workers Affected | Top N = 15

Other audience-framing charts are analysis-only.

---

## 4. Potential Growth

### 4.1 Adoption Gap (`potential_growth/adoption_gap/`)

**`confirmed_vs_ceiling_scatter.png`** — Scatter: confirmed vs. ceiling % per occupation.
- Not reproducible.

**`occ_gap_major.png`** — Dumbbell: confirmed vs. ceiling per major category (workers affected gap).
- **Page:** Occupation Categories (two groups)
- **Group A:** AEI Cumul. (Both) v4 + Microsoft | Average | Agg = Major | Sort = Workers Affected
- **Group B:** AEI Cumul. (Both) v4 + MCP Cumul. v4 + Microsoft | Max | Agg = Major | Sort = Workers Affected
- Note: Tooltip deltas approximate the gap. Dumbbell format is analysis-only.

**`occ_gap_minor.png`** — Top 20 minor categories by workers_affected gap (ceiling − confirmed).
- Not directly reproducible. Requires subtracting two runs.

**`occ_gap_occupation.png`** — Top 30 occupations by workers gap.
- Not directly reproducible.

**`wa_gap_gwa.png`** — GWA-level dumbbell: confirmed vs. ceiling.
- **Page:** Work Activities (two groups, same dataset pair as above, Activity Level = GWA)

**`wa_gap_iwa.png`** — Top 20 IWAs by workers gap.
- Not directly reproducible.

**`gap_trend.png`** — Line chart: confirmed workers growth vs. ceiling baseline over time.
- **Page:** Trends → Occupation Categories
- **Datasets:** All AEI Cumul. (Both) + Microsoft versions (for confirmed) and All versions (for ceiling)
- **Metric:** Workers Affected | **Line mode:** Average

**`config_robustness.png`** — Heatmap: major-level pct across all 5 configs.
- Not reproducible.

### 4.2 Wage Potential (`potential_growth/wage_potential/`)

**`wage_gap_major.png`** — Wages gap (ceiling − confirmed) by major category.
- **Page:** Occupation Categories (two groups)
- **Group A:** all_confirmed config | Sort = Wages Affected
- **Group B:** all_ceiling config | Sort = Wages Affected
- Note: Use tooltips to see delta. Direct subtraction is analysis-only.

**`wage_gap_occupation.png`** — Top occupations by wage gap.
- Not reproducible. Requires custom subtraction computation.

**`hotspot_scatter.png`** — Scatter: median wage vs. adoption gap, colored by sector.
- Not reproducible.

### 4.3 Automation Opportunity (`potential_growth/automation_opportunity/`)

**`ska_gap_scatter.png`** / **`q1_occupations_bar.png`** — SKA gap vs. adoption gap; Q1 occupations.
- Not reproducible. SKA computation is analysis-only.

### 4.4 Audience Framing (`potential_growth/audience_framing/`)

Audience-specific charts for policy, workforce practitioners, researchers. All are analysis-only (custom SKA + gap combinations).

---

## 5. Source Agreement

### 5.1 Ranking Agreement (`source_agreement/ranking_agreement/`)

**`spearman_heatmap.png`** — Heatmap: pairwise Spearman rank correlation between sources at each aggregation level.
- Not reproducible. Cross-source correlation is analysis-only.

**`top30_overlap.png`** — Bar/tile: how many occupations share top-30 status across sources.
- Not reproducible.

**`confidence_tier_distribution.png`** — Distribution of occupations by cross-source confidence tier.
- Not reproducible.

### 5.2 Score Distributions (`source_agreement/score_distributions/`)

**`auto_aug_distributions.png`** — Violin/histogram: auto-aug score distribution per source.
- Not reproducible. Score distribution charts are analysis-only.

**`cross_source_variance.png`** — Occupation-level cross-source variance.
- Not reproducible.

### 5.3 Source Portraits (`source_agreement/source_portraits/`)

**`source_distinctive_sectors.png`** — What each source uniquely sees by sector.
- Not reproducible. Source-specific distinctiveness requires comparing all four sources simultaneously.

### 5.4 Marginal Contributions (`source_agreement/marginal_contributions/`)

**`layer_tier_shifts.png`** — Bar: how many occupations shift tiers when each source is added.
- Not reproducible. Requires running analysis with each source layer-by-layer.

---

## 6. Agentic Usage

### 6.1 Exposure State (`agentic_usage/exposure_state/`)

**Headline numbers chart** — Agentic confirmed vs. ceiling vs. conversational comparison.
- **Page:** Occupation Categories (three-group comparison not directly supported; use two groups)
- **Group A:** AEI API Cumul. v4 (alone) | Agg = Major | Sort = Workers Affected (agentic confirmed)
- **Group B:** AEI API Cumul. v4 + MCP Cumul. v4 | Average | Agg = Major | Sort = Workers Affected (agentic ceiling)

**Tier distribution (agentic)** — Not reproducible. Tier thresholds are analysis-defined.

### 6.2 Sector Footprint (`agentic_usage/sector_footprint/`)

**`major_workers_agentic_ceiling.png`** — Horizontal bar: workers by major sector (agentic ceiling).
- **Page:** Occupation Categories
- **Group A:** AEI API Cumul. v4 + MCP Cumul. v4 | Average | Agg = Major | Sort = Workers Affected | Top N = 23

**`major_pct_agentic_ceiling.png`** — Horizontal bar: % tasks affected by sector (agentic ceiling).
- **Page:** Occupation Categories
- **Group A:** same as above | Sort = % Tasks Affected

**`delta_agentic_vs_conv.png`** — Diverging bar: agentic ceiling pct − conversational baseline pct by sector.
- **Page:** Occupation Categories (two groups)
- **Group A:** AEI Cumul. Conv. v4 + Microsoft | Average | Agg = Major
- **Group B:** AEI API Cumul. v4 + MCP Cumul. v4 | Average | Agg = Major
- Note: Tooltip deltas show the gap. Diverging bar format is analysis-only.

### 6.3 Work Activities (`agentic_usage/work_activities/`)

**`top_iwas_agentic_ceiling.png`** — Top 20 IWAs by % tasks affected (agentic ceiling).
- **Page:** Work Activities
- **Group A:** AEI API Cumul. v4 + MCP Cumul. v4 | Average | Activity Level = IWA | Sort = % Tasks Affected | Top N = 20

**`iwa_delta_agentic_vs_conv.png`** — Top 20 IWAs gaining most from agentic AI.
- Not directly reproducible. Requires subtracting two separate runs.

**`gwa_comparison_eco2025.png`** — Grouped bar: GWA pct across agentic ceiling, MCP only, conv baseline.
- **Page:** Work Activities (two groups)
- **Group A:** AEI Cumul. Conv. v4 + Microsoft | Average | GWA
- **Group B:** AEI API Cumul. v4 + MCP Cumul. v4 | Average | GWA
- Note: Three-source comparison requires two dashboard groups; the MCP-only series is not individually selectable.

**`top_iwas_aei_api.png`** — Top 20 IWAs (AEI API / eco_2015 baseline).
- **Page:** Work Activities
- **Group A:** AEI API Cumul. v4 (alone) | Average | IWA | Sort = % Tasks Affected | Top N = 20
- Note: Uses eco_2015 baseline — not directly comparable to eco_2025 results.

### 6.4 MCP Profile (`agentic_usage/mcp_profile/`)

**`mcp_top_occupations.png`** — Top 30 occupations by MCP exposure (pct_tasks_affected).
- **Page:** Occupation Categories
- **Group A:** MCP Cumul. v4 (alone) | Average | Agg = Occupation | Sort = % Tasks Affected | Top N = 30

**`mcp_vs_aei_delta_major.png`** — Diverging bar: MCP pct − AEI API pct by major category.
- **Page:** Occupation Categories (two groups)
- **Group A:** AEI API Cumul. v4 (alone) | Agg = Major
- **Group B:** MCP Cumul. v4 (alone) | Agg = Major
- Note: Diverging format is analysis-only; use tooltip deltas on dashboard.

**`mcp_signature_iwas.png`** — Top 20 IWAs by MCP exposure.
- **Page:** Work Activities
- **Group A:** MCP Cumul. v4 (alone) | IWA | Sort = % Tasks Affected | Top N = 20

**`mcp_vs_conv_major.png`** — Grouped bar: MCP vs. conversational by major category.
- **Page:** Occupation Categories (two groups)
- **Group A:** AEI Cumul. Conv. v4 + Microsoft | Average | Agg = Major
- **Group B:** MCP Cumul. v4 (alone) | Agg = Major

### 6.5 Trends (`agentic_usage/trends/`)

**Agentic ceiling growth line chart** — Workers affected over time (MCP + API series).
- **Page:** Trends → Occupation Categories
- **Datasets:** Select all MCP Cumul. versions + AEI API Cumul. versions
- **Metric:** Workers Affected | **Line mode:** Average or Max

**Sector growth bar** — Which sectors grew most in agentic exposure.
- Not directly reproducible. Requires computing growth between two dataset dates.

---

## 7. Field Benchmarks

### 7.1 Automation Share (`field_benchmarks/automation_share/`)

**`rate_comparison.png`** — Grouped bar: our 5 configs vs. Iceberg and Seampoint benchmark rates.
- Not reproducible. Comparison requires external benchmark data not in the dashboard.

**`layer_chart.png`** — Dot/bar plot: full measurement spectrum (all sources on one axis).
- Not reproducible. Hardcoded external benchmark values.

### 7.2 Wage Impact (`field_benchmarks/wage_impact/`)

**`utah_wage_comparison.png`** — Bar: our Utah wages vs. Seampoint $21B/$36B benchmarks.
- Approximate: **Page:** Occupation Categories
  - **Group A:** AEI Cumul. (Both) v4 + Microsoft | Average | Agg = Major | Geo = Utah | Sort = Wages Affected
  - Then sum wages from tooltips. Seampoint benchmark line is analysis-only.

**`national_wage_totals.png`** — Bar: national wages across 5 configs.
- Not reproducible. Aggregate totals are analysis-only.

### 7.3 Utah Benchmarks (`field_benchmarks/utah_benchmarks/`)

**`utah_pct_comparison.png`** — Bar: Utah pct_tasks_affected for our 5 configs vs. Seampoint 20%/51%.
- Approximate: **Page:** Occupation Categories | Geo = Utah | Agg = Major | Sort = % Tasks Affected. Seampoint reference lines are analysis-only.

**`utah_top_occs.png`** — Top 20 Utah occupations by AI task exposure.
- **Page:** Occupation Categories | Geo = Utah | Agg = Occupation | Sort = % Tasks Affected | Top N = 20

### 7.4 Theoretical vs. Confirmed (`field_benchmarks/theoretical_vs_confirmed/`)

**`measurement_spectrum.png`** and **`layer_breakdown.png`** — All sources mapped by measurement type with reference lines.
- Not reproducible. Uses hardcoded external benchmark data.

### 7.5 Sector Breakdown (`field_benchmarks/sector_breakdown/`)

**`our_sector_rankings.png`** — Top 10 sectors by workers affected (all_confirmed).
- **Page:** Occupation Categories
- **Group A:** AEI Cumul. (Both) v4 + Microsoft | Average | Agg = Major | Sort = Workers Affected | Top N = 10

**`cross_source_sectors.png`** — Grouped bar: our pct vs. Copilot applicability for overlapping sectors.
- Not reproducible. Copilot data is hardcoded external benchmark.

**`external_task_breakdown.png`** — Two-panel: AEI task categories and ChatGPT work-use categories.
- Not reproducible. External benchmark data only.

### 7.6 Work Activity Comparison (`field_benchmarks/work_activity_comparison/`)

**`our_gwa_rankings.png`** — Top 15 GWAs by workers affected.
- **Page:** Work Activities | GWA | Sort = Workers Affected | Top N = 15

**`augment_vs_automate.png`** — AEI's augmentative vs. automative split bar.
- Not reproducible. External AEI breakdown data.

**`platform_gwa_alignment.png`** — ChatGPT vs. Copilot GWA distributions.
- Not reproducible. External platform data.

### 7.7 Platform Landscape (`field_benchmarks/platform_landscape/`)

**`headline_comparison.png`** and **`methodology_map.png`** — All sources on one chart, methodology scatter.
- Not reproducible. Full external benchmark synthesis.

---

## 8. State Clusters

### 8.1 Risk Profile (`state_clusters/risk_profile/`)

**`risk_tier_bars.png`** — Stacked horizontal bar: states sorted by % high-risk workers, stacked by tier.
- Not reproducible. State-level risk tier distributions require the analysis risk scoring model applied per state.

**`cluster_profiles.png`** — Grouped bar: avg risk tier distribution per cluster.
- Not reproducible.

**`vs_sector_comp.png`** — Heatmap: sector cluster vs. risk cluster cross-tabulation.
- Not reproducible.

### 8.2 Activity Signature (`state_clusters/activity_signature/`)

**`gwa_heatmap.png`** — Heatmap: state × GWA share of AI-exposed employment.
- Not reproducible. State × GWA breakdown is analysis-only.

### 8.3 Agentic Profile (`state_clusters/agentic_profile/`)

**`overall_agentic_bar.png`** — Bar: agentic intensity (agentic/confirmed ratio) by state.
- Not reproducible. Requires computing the ratio of two dataset runs per state.

### 8.4 Adoption Gap (`state_clusters/adoption_gap/`)

**`overall_gap_bar.png`** — Bar: adoption gap ratio by state.
- Not reproducible. State-level gap requires two-dataset comparison.

### 8.5 Cluster Convergence (`state_clusters/cluster_convergence/`)

**`ari_heatmap.png`** — Heatmap: ARI between all 5 clustering schemes.
- Not reproducible. Cluster comparison is analysis-only.

**`stability_bar.png`** — Bar: state stability scores across clustering schemes.
- Not reproducible.

---

## 9. Time Trends

### 9.1 Trajectory Shapes (`time_trends/trajectory_shapes/`)

**`trajectory_type_bar.png`** — Bar: occupation count per trajectory type (6 types).
- Not reproducible. Trajectory classification is analysis-only.

**`trajectory_examples.png`** — Line chart: example occupations per trajectory type.
- Approximate: **Page:** Trends → Occupation Categories | Agg = Occupation | search for specific occupations.

### 9.2 Tier Churn (`time_trends/tier_churn/`)

**`tier_transition_sankey.png`** / **`tier_transition_heatmap.png`** — How occupations moved between tiers.
- Not reproducible. Tier transition tracking is analysis-only.

**`new_high_tier_entrants.png`** — Bar: sectors with most new high-tier entrants.
- Not reproducible.

**`sector_tier_stability.png`** — Bar: sector stability rates across the window.
- Not reproducible.

### 9.3 Confirmed/Ceiling Convergence (`time_trends/confirmed_ceiling_convergence/`)

**`national_convergence.png`** — Line: confirmed and ceiling workers over time, with gap.
- **Page:** Trends → Occupation Categories
- **Datasets:** All AEI Cumul. (Both) + Microsoft versions + All (ceiling) versions
- **Metric:** Workers Affected | **Line mode:** Average
- Note: Dashboard shows separate lines; gap computation is analysis-only.

**`sector_convergence.png`** — Line: confirmed/ceiling ratio trend by sector.
- Not reproducible. Ratio computation requires custom analysis.

### 9.4 WA Tipping Points (`time_trends/wa_tipping_points/`)

**`threshold_crossings.png`** — Timeline showing which IWAs crossed 10%, 33%, 66% thresholds.
- Not reproducible. Threshold-crossing detection is analysis-only.

**`approaching_33pct.png`** — Bar: IWAs currently below 33% but above 10% and growing.
- **Page:** Work Activities | IWA | Sort = % Tasks Affected — then use tooltips to identify those in the 10–33% range. Full filter is analysis-only.

### 9.5 Occupations Timeline (`time_trends/occs_timeline/`)

**`occs_timeline.png`** — Multi-line: time series for all 29 named occupations.
- **Page:** Trends → Occupation Categories | Agg = Occupation | search for individual occupations
- Note: The dashboard can show individual occupation lines; the committed figure overlays all 29 at once which requires the analysis script.

---

## 10. Workforce Meeting (`workforce_meeting/`)

14 presentation-quality charts for a Utah workforce meeting. All use Utah geo, All Confirmed, freq, auto-aug ON unless noted.

**`01_utah_headline.png`** — Stacked bar: Utah workers with AI-exposed tasks (921K, 54%) vs rest.
- **Page:** Occupation Categories | Agg = Major | Geo = Utah | then sum Workers Affected across all categories. The stacked-bar proportion visual is analysis-only.

**`02_sector_scope.png`** — Horizontal bar: top 7 Utah sectors by workers affected, labels include % tasks + wages.
- **Page:** Occupation Categories | Agg = Major | Geo = Utah | Sort = Workers Affected | Top N = 7. Compound labels are analysis-only.

**`03_gwa_scope.png`** — Horizontal bar: top 7 GWAs by % tasks affected (Utah), labels include workers + wages.
- **Page:** Work Activities | GWA | Geo = Utah | Sort = % Tasks Affected | Top N = 7. Compound labels are analysis-only.

**`04_sector_trend.png`** — Horizontal bar: top 7 sector delta workers (Mar 2025 → Feb 2026).
- Not reproducible. Dashboard Trends page shows time-series lines, not delta bars.

**`05_gwa_trend.png`** — Horizontal bar: top 7 GWA delta % tasks (Mar 2025 → Feb 2026).
- Not reproducible. Same reason as 04.

**`06_sector_adoption_gap.png`** — Horizontal bar: top 7 sector confirmed→ceiling gap (workers).
- **Page:** Occupation Categories | Group A = All Confirmed, Group B = All Sources | Geo = Utah. Use tooltip deltas. Ranked gap view is analysis-only.

**`07_gwa_adoption_gap.png`** — Horizontal bar: top 7 GWA confirmed→ceiling gap (% tasks).
- Same approach as 06 but on Work Activities page. Ranked gap view is analysis-only.

**`08_ai_modes_gap.png`** — Horizontal bar: top 7 sector conversational→agentic worker drop.
- **Page:** Occupation Categories | Group A = Human Conversation, Group B = Agentic Confirmed | Geo = Utah. Use tooltip deltas. Ranked view is analysis-only.

**`09_autoaug_by_sector.png`** — Horizontal bar: top 7 sectors by avg auto-aug (tasks with value).
- Not reproducible. Auto-aug averaging requires task-level computation from raw dataset files.

**`10_pivot_cost.png`** — Vertical bar: reskilling cost (L1 distance) by job zone.
- Not reproducible. Pivot cost computation is analysis-only (loaded from job_exposure/pivot_distance results).

**`11_ska_human_skills.png`** — Horizontal bar: top 7 skills where humans lead AI, with 100% parity line.
- Not reproducible. SKA gap computation is analysis-only.

**`12_ska_human_knowledge.png`** — Same as 11 for knowledge domains.
- Not reproducible.

**`13_ska_ai_skills.png`** — Horizontal bar: top 7 skills where AI leads, with 100% parity line.
- Not reproducible.

**`14_ska_ai_knowledge.png`** — Same as 13 for knowledge domains.
- Not reproducible.

---

## Charts Not Reproducible on Dashboard (Summary)

The following chart types produced by the analysis scripts have no dashboard equivalent:
- **Scatter plots** — exposure vs. employment, confirmed vs. ceiling per occupation/IWA
- **SKA gap charts** — require the skills/abilities/knowledge gap computation pipeline
- **Risk scoring charts** — require the 7-factor weighted risk model
- **Heatmaps (multi-config or multi-source)** — dashboard shows one configuration at a time
- **Treemaps** — dashboard only produces bar charts
- **State maps** — dashboard has no geographic map visualization
- **Cluster analysis** — k-means clustering is analysis-only
- **Trajectory classification** — temporal growth pattern classification is analysis-only
- **Tier transition / sankey** — multi-date tier tracking is analysis-only
- **External benchmark comparisons** — Seampoint, Iceberg, AEI (Humlum), ChatGPT data are hardcoded in analysis scripts and not in the dashboard
