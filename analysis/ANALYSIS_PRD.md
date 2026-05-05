# ANALYSIS_PRD.md — Analysis System Product Requirements

What the `analysis/` system produces and who it's for. Does not repeat information in the main `PRD.md`.

---

## Purpose

A structured system for answering research questions using the AEA Dashboard's compute pipeline. Each question lives in its own folder, produces reproducible outputs (CSVs, figures, PDF narrative), and feeds into a rolling report.

---

## Audiences

| Audience | What they want |
|----------|---------------|
| **Researchers (Alice, Zach, people who'd cite this)** | "Is the methodology sound? What's novel? What claims are actually supported?" |
| **Policymakers (OAIP, state workforce boards, legislators)** | Clear takeaways. "What should we do? Where should money go? What's coming?" |
| **Practitioners (workforce development people, educators, HR, people running programs)** | "Which skills matter? Which training programs should we build? What does this mean for my sector?" |

---

## Five Analysis Configs

All analyses use one or more of these five canonical dataset configurations. Each is a single pre-combined dataset — no combine_method toggle needed. All use `method="freq"` (time-weighted), `use_auto_aug=True`, `geo="nat"` unless a script specifies otherwise.

**Primary config is `all_confirmed`.** The three-layer framing:
1. **Confirmed usage** (`all_confirmed`) — base lens. "AI is doing these things."
2. **Ceiling** (`all_ceiling`) — comparison. "Here's where AI could be doing more than confirmed usage suggests." Includes MCP capability data which is less robust.
3. **Actual adoption** — acknowledged gap; we don't have data on how many workplaces are actually using AI for these tasks yet.

| Key | Dataset | What it measures |
|-----|---------|-----------------|
| `all_confirmed` | `final_all_confirmed_usage_2026-02-12` | **PRIMARY** — All confirmed usage (conv + API + Microsoft, no MCP) |
| `all_ceiling` | `final_all_usage_2026-02-18` | Upper bound — everything AI can reach (AEI + MCP + Microsoft) |
| `human_conversation` | `final_confirmed_human_usage_2026-02-12` | Confirmed human conversational AI use (AEI Conv + Microsoft Copilot; same chat-session interaction mode, no API/agentic) |
| `agentic_confirmed` | `final_aei_agentic_usage_2026-02-12` | Confirmed agentic tool-use (AEI API) |
| `agentic_ceiling` | `final_all_agentic_usage_2026-02-18` | Agentic Ceiling tool-use (MCP + AEI API) |

The agentic configs show how much architectural investment would be needed to deploy AI for a given set of tasks, and what agentic AI covers vs. browser/conversational AI.

---

## Question Catalog

### Active: Job Exposure (`questions/job_exposure/`)

**Overarching question:** Where is work being transformed, who is most at risk of displacement, and what can workers and policymakers do about it?

| Sub-folder | Question |
|------------|----------|
| `exposure_state/` | What is the current state of AI task exposure? (national, time-weighted, all five configs, trend over time) |
| `job_risk_scoring/` | What is the probability that a job gets replaced rather than just changed? (7-factor composite risk score) |
| `worker_resilience/` | What can a worker do to make their job more resilient? (SKA gap: where human advantage is largest vs. where AI leads) — includes `ska_deep_dive/` sub-report covering element trends, cross-config comparison, category breakdown, and most AI-subsumed occupations |
| `pivot_distance/` | Where is it cheap to pivot, and where is it expensive? (average reskill cost from high-risk to low-risk by job zone) |
| `audience_framing/` | How do findings translate across audiences? (skill profile overlaps, dominant domains in high-risk/low-outlook jobs) |
| `occs_of_interest/` | How do findings land for the named occupation list? |

**Risk scoring factors** (job_risk_scoring) — 8 binary flags with weighted scoring + exposure gate:
- **Flags 1–2 (strongest exposure signals, weight = 2 each):**
  1. `pct_tasks_affected > 50%` (absolute threshold)
  2. `SKA percentage > median` (AI capability as % of job need)
- **Flags 3–8 (supporting signals, weight = 1 each):**
  3. `pct trend: positive AND above-median growth` (median of ALL growth, not just positive)
  4. `SKA gap trend: positive AND above-median growth`
  5. `job_zone ∈ {1, 2, 3}`
  6. `outlook ∈ {2, 3}` (below-average; note: 1 = good outlook but low wages)
  7. `n_software > median`
  8. `auto_avg_with_vals > median`
- **Exposure gate:** occupations with `pct_tasks_affected < 33%` cannot be classified as high risk regardless of score (downgrades to Mod-High).
- **Tiers:** max score = 10. `8–10 = high`, `5–7 = mod-high`, `3–4 = mod-low`, `0–2 = low`.

**SKA formula** — see `ANALYSIS_ARCHITECTURE.md` for the locked-in spec.

### Active: Work Activity Exposure (`questions/work_activity_exposure/`)

**Overarching question:** Which types of work are most affected by AI, and what does that mean for where education and workforce development should focus?

Organized around IWA (Intermediate Work Activity) level as primary lens. No SKA or risk-scoring (occupation-level metrics); instead focuses on robustness tiers, confirmed-to-ceiling gaps, trend expansion, and audience-specific framing.

| Sub-folder | Question |
|------------|----------|
| `exposure_state/` | What is the current state of AI task exposure across work activities? (IWA/GWA/DWA rankings, five configs, confirmed vs ceiling, trends) |
| `activity_robustness/` | Which activities are AI-resistant, and which are in the next wave? (robustness tiers <33% / 33–66% / ≥66%, stable-robust IWAs, ceiling gaps) |
| `education_lens/` | What does this mean for what we teach and train? (durable targets, workforce by tier, domain exposure, growth trends, is-AI-a-fad question) |
| `audience_framing/` | How do findings translate for each audience? (policy, workforce/educators, researchers, laypeople) |

**Key findings:**
- 164 robust / 116 moderate / 52 fragile IWAs (out of 332 total)
- 82% of affected workers in activities with ≥33% exposure (64.5M out of 78.6M)
- 275/332 IWAs grew in exposure over 11 months (Mar 2025 → Feb 2026); 27 newly above 10%
- Fastest-growing IWAs are educational: evaluate scholarly work (+77pp), assess student capabilities (+54pp)
- Robust activities are almost entirely physical/operational; fragile ones are informational/cognitive

**Note:** Four of the five ANALYSIS_CONFIGS use pre-combined datasets (is_aei=False) → eco_2025 baseline for WA analysis. `agentic_confirmed` uses `AEI API 2026-02-12` (is_aei=True) → eco_2015 baseline for WA analysis (routed through aei_group). WA scripts that use `result.get("mcp_group") or result.get("aei_group")` handle this correctly.

### Active: Economic Footprint (`questions/economic_footprint/`)

**Overarching question:** What is the total economic scale of AI exposure — across sectors, wages, work activities, job structure, and geography — and how has it changed over time?

| Sub-folder | Question |
|------------|----------|
| `sector_footprint/` | Which sectors carry the most workers and wages in scope? How do the five configs compare? |
| `skills_landscape/` | What skills does AI lead vs. humans? Which technology categories are most exposed? |
| `job_structure/` | How does exposure distribute across job zones (preparation level) and job outlook ratings? |
| `ai_modes/` | How much more does agentic AI expose vs. conversational? What is the auto-augmentability distribution? |
| `trends/` | How have workers affected, wages affected, and task penetration changed over time across all five config series? |
| `state_profiles/` | What types of state economies have the most exposed workforces, clustered by sector composition? |
| `work_activities/` | What is the GWA/IWA-level footprint? How do agentic vs. conversational modes differ at the activity level? |

**Key findings (All Confirmed primary config):**
- 61.3M workers affected, $3.99T wages in scope, 40.0% of total employment
- Ceiling estimate: 77.1M workers, $4.97T wages, 50.3% of employment
- Top sectors by workers: Office/Admin (11.2M, 51.1%), Sales (7.6M, 59.5%), Business/Finance (5.5M, 50.7%)
- Confirmed agentic (AEI API only) reaches 31.1M workers, $2.16T wages, 20.3% of employment; agentic ceiling (MCP + AEI API) reaches 60.4M workers
- Sales (+18.6 pp) and Computer/Math (+16.0 pp) saw the largest task penetration gains over the dataset window (Mar 2025 → Feb 2026)
- Zone 4 (considerable prep) has the highest average AI exposure (~50.9%); Zone 1 the lowest (~26.9%)
- 5 state clusters by sector composition; pct_tasks_affected is uniform (~36.1%) across all states
- 97.7% of affected workers are in occupations with meaningful AI augmentation potential (auto-aug score >= 2)

**Note:** `work_activities/` covers economic footprint angles only. For deeper WA exposure profiling see `questions/work_activity_exposure/`.

### Active: Potential Growth (`questions/potential_growth/`)

**Overarching question:** Where is current AI usage far below demonstrated capability, and what is the economic opportunity in that gap?

| Sub-folder | Question |
|------------|----------|
| `adoption_gap/` | Where is confirmed usage furthest below the ceiling, across occupations and work activities? |
| `wage_potential/` | Which occupations and sectors have the highest economic value locked in the gap? |
| `automation_opportunity/` | Where does AI already lead on SKA AND the adoption gap is large? Where is the transformation signal? |
| `audience_framing/` | How do these findings translate for policy, workforce practitioners, researchers, and laypeople? |

**Key findings (all_confirmed primary config, all_ceiling as ceiling):**
- Adoption gap: 15.8M workers (61.3M confirmed → 77.1M ceiling)
- Wage gap: $980B/year ($3.99T confirmed → $4.97T ceiling)
- Largest sector gaps by workers: Office/Admin (2.6M), Transportation (2.4M), Sales (2.1M), Management (1.8M)
- Largest activity gap by workers: Documenting/Recording Information (GWA, +4.4M workers, +30pp)
- Largest IWA wage gap: Maintain operational records ($144B)
- 248 occupations in Q1 (AI leads on SKA AND large adoption gap); 102 also carry high risk tier (transformation signal)
- Wage hotspots: 59 occupations in top quartile on both median wage (≥$90,845) and adoption gap (≥12.6pp)
- General and Operations Managers alone: $90.2B wage gap from a single occupation category
- Confirmed growth: +14.7M workers in 11 months (Mar 2025 → Feb 2026); ceiling also grew

**Note:** `ai_transformative_potential/` (old folder) has been replaced by this analysis. Do not reference it.

### Active: Source Agreement (`questions/source_agreement/`)

**Overarching question:** How robust are the dashboard's findings across its four independent data sources, and what does each source uniquely contribute?

**Four sources compared:** Human Conv. (AEI Conv + Micro 2026-02-12) | Agentic (AEI API 2026-02-12) | Microsoft | MCP Cumul. v4

| Sub-folder | Question |
|------------|----------|
| `ranking_agreement/` | Where do the four sources agree/disagree on which occupations are most AI-exposed? (Spearman correlations, confidence tiers at all aggregation levels) |
| `score_distributions/` | How are auto-aug scores distributed within each source, and where is cross-source variance highest? |
| `source_portraits/` | What is each source's distinctive signature — what does each one uniquely see? |
| `marginal_contributions/` | What does each source layer add to the combined picture? (layer-by-layer tier shifts) |

**Key findings:**
- Source agreement degrades with granularity: major mean Spearman rho = 0.875, occupation rho = 0.676; 91% of occupations have zero cross-source consensus in top-30
- Six bedrock major categories (all four sources agree): Computer/Math, Office/Admin, Sales, Business/Finance, Arts/Design/Media, Life/Physical/Social Science
- Strongest source pair: Human Conv. vs Microsoft (rho 0.93 major, 0.86 occ); weakest: Agentic vs Microsoft (rho 0.80 major, 0.55 occ)
- MCP addition upgrades 104 occupations to High tier (>=60%); API addition upgrades 64
- MCP distinctively exposes system-interaction and administrative automation work; Human Conv. distinctively exposes education, legal, and social service work

### Active: Agentic Usage (`questions/agentic_usage/`)

**Overarching question:** What is the full picture of agentic AI's footprint on U.S. work — which sectors, which work activities, how fast is it growing?

**Primary datasets:** AEI API 2026-02-12 (Agentic Confirmed) | MCP Cumul. v4 (MCP Only) | MCP + API 2026-02-18 (Agentic Ceiling)

| Sub-folder | Question |
|------------|----------|
| `exposure_state/` | Current agentic footprint: headline numbers, tier distributions, confirmed vs. ceiling |
| `sector_footprint/` | Which sectors carry the most workers and wages in agentic scope? |
| `work_activities/` | Which work activities does agentic AI specifically illuminate? |
| `mcp_profile/` | What does MCP specifically reveal about tool-use AI exposure? |
| `trends/` | How has the agentic frontier grown over time? |

**Key findings:**
- Agentic Confirmed (AEI API): 31.1M workers, 20.3% of employment; Agentic Ceiling (MCP+API): 60.4M workers, 39.4%
- Conversational baseline (all_confirmed): 61.3M workers, 40.0% — agentic ceiling nearly matches conversational coverage
- MCP distinctively exposes office/admin, data work, and system-interaction occupations; Computer/Math sector shows largest MCP-over-AEI-API delta
- Agentic ceiling grew 81% from April 2025 to February 2026, but the last two dataset versions added only ~1.0M workers combined — growth is asymptoting
- AEI API and MCP work activity profiles differ: AEI API (eco_2015 baseline) reflects agentic workflow integration; MCP (eco_2025) captures tool-use across information-processing and administrative activities

### Active: Field Benchmarks (`questions/field_benchmarks/`)

**Overarching question:** How do the AEA Dashboard's findings compare to other major AI-and-work research, and where does our confirmed usage sit in the broader measurement landscape?

**External sources:** Project Iceberg (Chopra et al., 2025) | Seampoint LLC (Utah, 2026 preliminary) | AEI (Humlum & Vestergaard, 2024) | ChatGPT usage (Weidinger et al., 2025) | Microsoft Copilot (2025)

| Sub-folder | Question |
|------------|----------|
| `automation_share/` | How does our task exposure rate compare to Iceberg and Seampoint? |
| `wage_impact/` | How do our wages_affected compare to Seampoint's Utah dollar estimates? |
| `utah_benchmarks/` | Utah-specific: our pct_tasks_affected for Utah workers vs. Seampoint 20%/51% |
| `theoretical_vs_confirmed/` | Where does confirmed usage sit relative to deployment readiness and technical capability? |
| `sector_breakdown/` | Which sectors rank highest across our analysis, Copilot, AEI, and ChatGPT? |
| `work_activity_comparison/` | Which GWA-level activity types appear across all confirmed-usage platforms? |
| `platform_landscape/` | Full methodology comparison — all six sources side by side |

**Key findings:**
- Our agentic_confirmed (20.3%) matches Seampoint's governance-constrained takeover rate (20%) — the strongest external cross-validation signal for our framework
- Our all_ceiling (50.3%) matches Seampoint's augment estimate (51%) — both frameworks converge on ~50% as the near-term AI task coverage ceiling
- Iceberg's 11.7% Full Index is not a contradiction: it measures skill-wage substitutability, not task-level usage breadth — different question, not a disagreement
- Utah all_confirmed: $62.6B wages in scope (60.2% of $104B total), vs. Seampoint's $21B takeover / $36B total
- Cross-platform sector consensus: Computer/Math, Office/Admin, Sales, Business/Finance rank highest in every source that measures sector-level AI exposure
- GWA convergence: Documenting/Recording, Getting Information, Processing Information are the top activity categories across our data, ChatGPT sessions, and Copilot enterprise logs

**Three measurement layers:**
- Layer 1 — Confirmed real-world usage (our data, AEI, ChatGPT): what AI is actually doing
- Layer 2 — Deployment-constrained readiness (Seampoint): what orgs can deploy now under governance
- Layer 3 — Technical capability ceiling (Iceberg): what AI tools can technically substitute

### Active: State Clusters (`questions/state_clusters/`)

**Overarching question:** When you examine U.S. states through the lenses established in the other analyses — risk landscape, work activity fingerprint, agentic exposure, adoption gap — do the same state groupings emerge each time, or does each lens reveal different fault lines?

**Builds on:** `economic_footprint/state_profiles` sector-composition clustering (k=5, used as reference baseline throughout).

**Primary datasets:** AEI Both + Micro 2026-02-12 (all_confirmed) | All 2026-02-18 (all_ceiling) | AEI API 2026-02-12 (agentic_confirmed)

| Sub-folder | Question |
|------------|----------|
| `risk_profile/` | Which states have the most high-risk workers? (employment-weighted risk tier clustering) |
| `activity_signature/` | What types of work is AI touching in each state's exposed workforce? (GWA share clustering) |
| `agentic_profile/` | How agentic vs. conversational is each state's AI exposure? (agentic intensity per sector) |
| `adoption_gap/` | Where is there the most room for AI to spread further? (ceiling vs. confirmed gap per sector) |
| `cluster_convergence/` | Do all five schemes agree on state groupings? (ARI matrix, state stability scores) |

**Key findings:**
- All pairwise ARI values between clustering schemes are ≤ 0.26 — the five lenses are measuring genuinely different things
- Risk varies significantly (35.9%–48.9% pct_high workers): Puerto Rico/USVI have the most high-risk workers; Massachusetts has the least; DC is mid-tier despite uniquely high exposure
- Activity signature differences between non-DC states are sub-1pp on any GWA; DC is an outlier at +3–4pp on analytical/creative GWAs
- Agentic intensity barely varies nationally (0.474–0.571 range); DC is the only strong outlier at 0.571
- Adoption gap is nearly uniform (avg 0.243, range 0.216–0.277); Kentucky highest, DC lowest
- DC has the lowest stability score (0.07) — consistently anomalous but in different ways under each lens
- Most stable states: WV, ME, WI, MO, KS — consistently "typical" across all dimensions

### Active: Time Trends (`questions/time_trends/`)

**Overarching question:** What does the temporal dimension reveal that static snapshots miss — how did AI exposure evolve, which occupations followed which growth patterns, and what's the trajectory of the confirmed/ceiling gap?

Primary lens: `all_confirmed` series (AEI Both + Micro, Mar 2025 – Feb 2026, 4 dates). Ceiling comparison uses `all_ceiling` series (8 dates).

| Sub-folder | Question |
|------------|----------|
| `trajectory_shapes/` | How did individual occupations grow? Six trajectory type classifications across all 923 occupations |
| `tier_churn/` | How stable are exposure tiers? Tier transitions, new high-tier entrants, sector stability rates |
| `confirmed_ceiling_convergence/` | Is deployment catching up to capability? National and sector-level confirmed/ceiling ratio trends |
| `wa_tipping_points/` | Which IWAs crossed meaningful thresholds (10%, 33%, 66%), which are approaching them? |
| `occs_timeline/` | Full time-series for the 29 named occupations of interest |

**Key findings:**
- 12 occupations at >=60% confirmed in Mar 2025; 145 by Feb 2026 — 133 new high-tier entrants in 11 months
- 51% of occupations (468) are "laggards" with <5pp total gain — AI expansion is concentrated, not universal
- August 2025 is the dominant inflection-point dataset date within this window; confirmed exposure advances in discrete jumps
- Confirmed/ceiling gap opened in Aug 2025 (MCP incorporation), sitting at ~10pp nationally; confirmed growing slightly faster than ceiling (ratio improved 77% → 80%)
- Software Developers and Data Scientists: zero confirmed growth across all 4 dates; Customer Service Representatives +35.0pp, Technical Writers +30.6pp, Network Admins +26.8pp
- 60 IWAs in active expansion zone (10–33%, growing); financial/legal/healthcare documentation IWAs approaching 33% threshold

### Active: Workforce Meeting (`questions/workforce_meeting/`)

**Overarching question:** What are the key charts a workforce meeting audience (business and education leaders) needs to see to understand AI's impact on Utah's workforce and make decisions about reskilling, durable skills, and AI adoption?

Not a research bucket — a presentation deliverable. 14 charts designed for slide decks, ordered by "lose 10% of audience per slide" logic. All charts use Utah employment, All Confirmed config, freq method, auto-aug ON.

### Active: Workforce Meeting v2 (`questions/workforce_meeting_v2/`)

**Overarching question:** Same as workforce_meeting. V2 is a restyled, non-technical variant for audiences with no research background (e.g. Nandeeni).

### Active: Workforce Sig Meeting (`questions/workforce_sig_meeting/`)

Not a research bucket — a presentation deliverable. The report opens with a "How Each Number Is Generated" methodology table on Chief Executives (6 of 31 sample tasks shown; footer math uses all 31 tasks: Σ(freq × auto-aug/5) ÷ Σ freq → 50.7% task completions affected → 87,400 workers affected → $18.0B wages affected, exactly matching `get_pct_tasks_affected("AEI Both + Micro 2026-02-12")["Chief Executives"]`). Then it embeds key paper figures: `temporal_trend` from part_1; all five part_2 charts (`phys_info_divide`, `job_zone_violin`, `ska_levels`, `gwa_exposure`, `major_categories`); `tech_commodities` from part_3. Finally two custom charts produced locally: `gap_to_ceiling_wages.png` (top sectors by all_confirmed → all_ceiling wage gap, stacked confirmed-+-extension on a wages-affected x-axis, sorted by wage gap) and `conv_allconfirmed_ceiling.png` (three bars per major: Conversational → All Confirmed → Ceiling).

V2 changes: charts only (no narrative text), 11 charts (headline/pivot cost/auto-aug dropped), larger fonts throughout, primary values as large white text inside bars, no config subheadings, x-axis scale visible, "%" not "pp" for deltas, chart 07 reframed as conversational vs. agentic overlay, SKA reference line explicitly labelled.

| Chart | What It Shows |
|-------|--------------|
| `01_utah_headline` | Utah workers with AI-exposed tasks (stacked proportion bar) |
| `02_sector_scope` | Top 7 sectors by workers affected (+ %tasks, wages) |
| `03_gwa_scope` | Top 7 GWAs by % tasks affected (+ workers, wages) |
| `04_sector_trend` | Top 7 sector growers: Δworkers Mar 2025 → Feb 2026 |
| `05_gwa_trend` | Top 7 GWA growers: Δ% tasks Mar 2025 → Feb 2026 |
| `06_sector_adoption_gap` | Top 7 sectors: confirmed→ceiling worker gap |
| `07_gwa_adoption_gap` | Top 7 GWAs: confirmed→ceiling %tasks gap |
| `08_ai_modes_gap` | Top 7 sectors: conversational→agentic worker drop |
| `09_autoaug_by_sector` | Top 7 sectors by avg auto-aug score |
| `10_pivot_cost` | Reskilling cost by job zone |
| `11–14_ska_*` | Human vs AI advantage in skills and knowledge (4 charts) |

**Key numbers (Utah, All Confirmed):**
- 921K workers affected (54% of Utah workforce), $62.6B wages in scope
- Top sectors by workers: Office/Admin (146K), Business/Finance (109K), Management (87K)
- Top GWAs by % tasks: Updating Knowledge (72%), Interpreting Information (70%), External Communication (70%)
- Zone 3 workers face the most expensive reskilling path (359 L1 distance)

### Planned (future sessions)

| Bucket | Core question |
|--------|--------------|
| (none remaining) | |

---

## Paper

The `analysis/paper/` folder contains infrastructure for the AEA research paper. The paper is assembled from `.md` files — one per section — which will be stitched together once all parts are complete. **Target length: 15–20 pages of prose (excluding appendices).**

A working paper outline is at `paper/working_paper_outline.md`. It is **not final and may contain outdated information** — use it only as a general structure reference and to gauge section length targets. The outline covers: Abstract, Introduction, Background, Data Sources, Methodology, Results (Parts 1–3), Discussion, Limitations, Future Work, and Appendices.

### Structure

```
paper/
├── paper_config.py              — PAPER_PALETTE, chart formatting, style_paper_figure()
├── writing_style_source.md      — ~30 pages of source writing for style calibration
├── paper_writing_style.md       — Condensed dos and don'ts for paper writing
├── working_paper_outline.md     — Draft structure reference only (not final, may be outdated)
├── results/                     — Results section
│   ├── results.md               — Assembled Results section (Parts 1–3)
│   ├── part_1/                  — Scale, Convergence, Growth — FIRST DRAFT COMPLETE
│   ├── part_2/                  — Characterization — FIRST DRAFT COMPLETE
│   └── part_3/                  — Action — FIGURES + SCAFFOLDING (no prose yet)
```

### Writing Style

Paper writing uses `paper/writing_style_source.md` (style calibration) and `paper/paper_writing_style.md` (condensed rules). Question reports use a separate reference: `questions/writing_style_reference.md`.

### Part 1 — Scale, Convergence, Growth ("This is real")

The credibility argument. Four chart groups:
1. **Overview**: Five-config aggregate footprint — workers and wages as % of national totals
2. **Convergence (internal)**: Spearman rank correlation heatmaps (lower triangle) across four independent sources (Claude Browser, Claude API, Copilot, MCP) at four aggregation levels
3. **Convergence (external)**: 2×2 grid of rectangular 4×4 heatmaps — our four sources (rows) vs. four external academic benchmarks (Eloundou GPT-4 β, Eloundou Human β, AIOE 10-app mean, AIOE Reading Comprehension) at the same four aggregation levels. External benchmarks rolled up to SOC group level by unweighted mean across matched occupations.
4. **Temporal**: % of employment with AI-exposed tasks over time (All Confirmed vs All Ceiling), plus per-date delta tables

Narrative arc: scale → internal multi-source convergence → convergence with independent academic work → growth trajectory. Does not characterize which sectors are most exposed (Part 2) or recommend actions (Part 3). Benchmark comparisons (Seampoint, Iceberg) are woven in briefly alongside the Eloundou/AIOE convergence chart as external validation evidence.

### Part 2 — Characterization: Where AI Exposure Falls ("Here's what it is")

Five chart groups characterizing the structural distribution of AI exposure:
1. **Physical/Informational Divide**: Box plots of % tasks affected by occupation group (Non-physical / Mixed / Physical, classified by proportion of physical tasks)
2. **Job Zone**: Violin plots of % tasks affected by O*NET job zone (1–5), showing AI exposure peaks at Zone 4–5 (considerable/extensive prep)
3. **SKA Levels**: AI Maximum of imp×lv vs. workforce benchmarks for every Skills, Abilities, and Knowledge element (3 subplots with workforce max, P95, top-10, mean markers)
4. **Work Activities**: All GWAs ranked by % tasks affected, bar color intensity = workers affected, annotated with workers and wages
5. **Major Categories**: All 22 major occupational categories in 3 side-by-side panels (% Tasks Affected, Workers Affected, Wages Affected)

Narrative arc: physical/informational structure → preparation level gradient → element-level capability profile → work activity rankings → sector-level view. Uses All Confirmed config throughout.

### Part 3 — Action: What To Do About It ("Here's what to do about it")

In the middle of a content revamp. The previous draft (eight charts in three audience sections — Organizations, Policy, Individuals — plus a property-biplot framing chart and an augmentation-regime caveat) has been pared back. Currently three charts; audience scaffolding will be rebuilt as more charts come in.

1. **Tech commodities top-25** by depth × breadth composite (reused from `economic_footprint/skills_landscape`).
2. **Conv → Confirmed → Ceiling reach by major sector** — all 22 major occ categories on a stacked bar with three segments: Conversational confirmed base + Conv → Confirmed gap (focal, colored by workers added) + Confirmed → Ceiling extension. Sorted by Conv → Confirmed % tasks gap. Right-side annotations show pp / workers / wages deltas for both gaps.
3. **AI intensity vs. median-rank anchor (full eco_2025 denominator)** — chart 15 from `exploratory/pct_norm_vs_eco/run_v3.py`. Major occ categories ranked by Σ pct (rated, equal 3-source bias-corrected) / Σ (freq × emp) over the full eco_2025 universe, anchored on Educational Instruction = 1.00×, with a dashed median line. Bars shaded by `pct_tasks_affected`. Imports v3 compute at function level — skips with a warning if the gitignored exploratory folder is absent.

---

## Occupations of Interest

29 named occupations across three groups — see `OCCS_OF_INTEREST` in `analysis/config.py` for the exact list. Matched against `title_current` in eco_2025 with fuzzy matching where needed.

Groups: High-profile/high-employment · AI-controversial/interesting · Utah-relevant

---

## Exploratory Folder

`analysis/exploratory/` is gitignored and outside the question system. It holds one-off charts that are interesting but don't belong in a formal question bucket. Nothing from here feeds into `question_findings/` or `report/`.

Each exploratory sub-folder must have:
- `run.py` — script that produces all figures
- `README.md` — folder metadata: what it produces, config used, run command
- `<name>_report.md` — findings writeup with inline figures and narrative (e.g., `zone_pivot_anatomy_report.md`)
- `results/` — auto-created on run; figures saved to `results/figures/`; gitignored

The `<name>_report.md` is the primary deliverable. It should read like a short analysis memo — not a bullet list of what the charts show, but a narrative that answers the question that motivated the analysis.

| Sub-folder | What it makes |
|------------|--------------|
| `ska_levels/` | AI imp×lv vs. workforce benchmarks (eco mean, top-10, p95) for every SKA element across three AI variants |
| `zone_pivot_anatomy/` | Why zone 3 peaks on pivot cost; SKA overlap structure, sector composition, and scatter of at-risk occupations by zone |
| `physical_informational_divide/` | Physical vs. informational occupation split (<33%/>67% thresholds); structural task distributions (GWA/IWA/DWA); AI exposure: pct distribution, IWA workers concentration, auto-aug breakdown by task type × coverage × dataset (Confirmed/Ceiling), GWA concentration curve, auto-aug vs. pct scatter |
| `aioe_comparison/` | Felten/Raj/Seamans AIOE 52×10 matrix vs. our pct_tasks_affected. Per-occ AIOE score = sum(imp×lv×ability_cap)/sum(imp×lv) on imp≥3 rows, 3 variants (mean-10, Language Modeling only, Reading Comprehension only). 18 charts: occ-level scatter, SOC-level convergence (focused + all-sources), 4-aggregate-panel ability ranking (sorted by mean/RC/LM), per-ability SKA aggregates vs AIOE, per-AI-app ρ breakdown at 3 SKA aggregates |
| `pct_norm_vs_eco/` | AI usage distribution (Σ `pct_normalized`) vs. economic baseline, renormalized to 100%. Overhauled: 2 configs (`all_confirmed`, `aei_all_usage`) × 7 levels (major/minor/broad/occ/gwa/iwa/dwa) × 2 eco scopes (config-scoped vs. full eco_2025) × 5 bias variants (`no_bias`, `equal` 3-source consensus, `chatgpt_2x/5x/10x`). Bias correction: `bias_ratio[gwa] = claude_share / consensus_share` using fixed AEI/Copilot/ChatGPT GWA distributions; each task's pct divided by its GWA's ratio (averaged across GWAs for multi-mapped tasks). Coverage: GWA + major get all bias × both configs × both eco; other levels are `all_confirmed` + equal bias + both eco. 100 PNGs. V2 (`run_v2.py` + v2 report) replaces delta framing with 20 **AI-intensity-ranking** charts: per-cat ratio = Σ pct (bias-corrected) / Σ (freq×emp), renormalized to 100%; 8 base levels (major/minor/broad/occ/gwa/iwa/dwa/task, rated-task denominator), +2 ChatGPT-5× variants on major + gwa, +2 full-eco variants on major + gwa, +4 auto_aug-weighted variants on major + gwa × both eco scopes (pct × auto_aug_mean/5 applied per row), +4 smoothing variants (sqrt and additive α=median(den)). Plus `major_diagnostics.csv` and `major_raw_numerator.png` for per-major task counts, eco coverage, and raw Σ pct with/without auto_aug. V3 (`run_v3.py` + v3 report) holds metric and level fixed (intensity ratio at major occ category) and varies the source dataset and bias correction across 11 charts: 5 dataset-driven no-bias variants (`all_confirmed`, `microsoft_only`, `aei_all`, `aei_conv` from `final_aei_human_usage_2026-02-12.csv`, `aei_api` from `final_aei_agentic_usage_2026-02-12.csv`), 4 of those same datasets with equal 3-source bias correction (all_confirmed, aei_all, aei_conv, aei_api), plus 2 synthetic-from-prior charts where Copilot's / ChatGPT's published GWA share is split evenly across unique eco_2025 tasks per GWA (full eco_2025 denominator). Headlines: Computer/Math is the most volatile cell (3.2% under Microsoft to 41.7% under AEI API); Life/Physical/Social Science is the most stable top entry (top in 9 of 11 charts); bias correction's effect concentrates on Computer/Math (always loses share) and Arts/Design (always gains). Charts 12–17 reanchor chart 06 on Educational Instruction (the higher of the two median-rank majors out of 22, lands at 1.00×) with a dashed median-line annotation. 12 = basic ratio; 13 = sqrt-den smoothing; 14 = additive smoothing (den + median(den)); 15 = same numerator as 12 but full-eco denominator; 16 / 17 = chart 12 / 15 with auto-aug weighting on the numerator (Σ pct × (auto_aug/5) / Σ ew). Life Sciences sits at 25.5× / 5.8× / 4.7× / 20.4× / 27.7× / 22.2× across the six; Computer/Math at 8.5× / 4.8× / 5.7× / 10.2× / 9.0× / 10.7×. Charts 12, 15, 16, 17 bars are color-shaded by pct_tasks_affected (darker = higher), computed at major level on all_confirmed via the standard dashboard formula. Under additive smoothing Computer/Math passes Life Sciences, showing the basic ratio's Life-Sciences lead is partly a small-denominator artifact; under chart 15 (full eco denominator) Computer/Math also rises relative to chart 12, indicating the dataset rates a higher share of Computer/Math tasks than the average sector. Auto-aug weighting (16 / 17) bumps the top-3 majors up by roughly 5–10% in lift terms but doesn't flip the ranking. |
| `schaal_substitution/` | Replicates the chart types from `paper/results/part_1` + `part_2` (minus correlations and temporal) using Schaal 2025's per-task scores from `merged_tasks_full.csv` in the position normally occupied by our pipeline's `auto_aug_mean`. Schaal score normalized as `score / 2` to match the original `auto_aug_mean / 5` 0–1 multiplier mechanic. Two versions per chart: **economy** (Schaal applied to every eco_2025 task that has a score) and **confirmed** (Schaal applied only to task-occ pairs that ALSO appear in the all_confirmed dataset). **Five score variants** run through the full pipeline: `auto_avg` (Schaal Overall = eq. 1: `0.25 × (PV + DA + TK + AG)`), `pv_avg` (Performance Variance / Moravec proxy), `da_avg` (Data Abundance), `tk_avg` (Tacit Knowledge — high = MINIMAL TK required = MORE automatable, system-prompt convention), `ag_avg` (Algorithmic Efficiency Gap). Six chart types per variant (overview, phys/info, job zone, GWA, major categories, SKA via compute_ska piped with Schaal-derived pct) × 11 PNGs each, plus one cross-variant comparison chart = **56 PNGs total** in `results/figures/{auto,pv,da,tk,ag,_comparison}/`. Headline: each subhypothesis paints a structurally different occupational gradient — DA is closest to our observed-usage data (Computer/Math + Office/Admin top), TK is the cleanest Schaal-Moravec test (high-skill expert work consistently at the bottom — supports Schaal's seniority-biased technological change argument), PV is counterintuitive (Arts/Education on top because performance variance is highest there), AG is essentially a phys/info cut. No single subhypothesis reproduces Schaal Overall — the four-factor average is doing real work. |
| `external_indices_correlation/` | (3) **Group-level auto_aug vs Schaal heatmap** (`group_auto_aug_vs_schaal.png`) — two stacked 4×5 heatmaps. Rows: SOC levels (major/minor/broad/occ). Cols: Schaal's 5 score columns from `merged_tasks_full.csv` (auto_avg + 4 subhypotheses). Cells: Spearman ρ between group-level avg `auto_aug_mean` (from all_confirmed) and group-level avg Schaal score. Two methods applied symmetrically: **Method A — Zero-fill** (avg over ALL eco task-occ pairs in group; missing scores = 0) and **Method B — Rated-only** (only pairs with both ratings). Headline: Schaal DA is the strongest predictor (ρ ≈ 0.83 at major under Method A), Schaal TK runs negative (~−0.33) because observed Claude usage concentrates in high-tacit-knowledge fields where Schaal predicts protection — cross-validates the seniority-biased technological change argument from a different angle. Method A correlations are 1.5–3× stronger than Method B because zero-fill captures coverage signal, which Method B strips. |
| `external_indices_correlation/` | (1) **SOC convergence heatmap** — Spearman ρ of our 4 internal sources + 5 ANALYSIS_CONFIGS (9 rows) against all 16 external AI/automation exposure indices in `Comparison of Indices.csv` from Schaal 2025 (Cambridge ERA AI Governance) — Schaal's own theory-based Moravec index (overall `auto_w` + 4 subhypotheses PV/DA/TK*/AG; TK is inverted-coded), Eloundou α/β/γ, Webb software/robot/ai, SML, AIOE base, Frey-Osborne, Autor routine cog/manual. Four SOC levels (major/minor/broad/occupation), pairwise dropna per cell, diverging color scale (negative ρ matters — Webb Robot, Routine Manual, Frey-Osborne anti-correlate strongly with our LLM-era measures, matching Schaal's own Figure 4 paradigm-shift finding), significance asterisks (`*` p<.05, `**` p<.01, `***` p<.001). (2) **Task-level scatter** (`tasks_overall.png` + `tasks_subhypotheses.png`) — Schaal's per-task `auto_avg` from `merged_tasks_full.csv` vs our `auto_aug_mean` per (task_normalized, soc_code_2019_full). 5-panel one-per-config + 4-panel subhypothesis breakdown. Joins on normalized task text + 2019 SOC; AEI-only datasets bridged from 2010 SOC via the AEI Both + Micro crosswalk; GWA/IWA/DWA expansion deduped. Task-level ρ (0.07–0.30) is much weaker than occ-level ρ (0.5–0.6) — agreement is a between-occupation phenomenon, not within. Three PNGs + 4 CSVs (occ-level long-form + summary, task-level overall + subhypothesis summaries). |
| `claude_lab/` | Claude's autonomous research workspace on the AEA Dashboard data. Operates independently of the rest of the analysis system — Claude picks threads, runs investigations, and documents findings as a researcher would, without being directed toward specific paper chapters. Has its own `CLAUDE.md` agent spec, `research_log.md` rolling synthesis (single shareable artifact, updated every session), `INVENTORY.md` meta log, `lib/` for shared helpers, and one named sub-folder per research thread. Each thread follows the standard pattern (`run.py`, `results/`, `notes.md`, optional `<topic>_report.md`). Findings that feel paper-relevant are flagged in `research_log.md`; promotion to `paper/` is gated by the user, not by Claude. Folder used to be called `action_levers/` (its seed run); the seed sub-folder `initial_action_charts/` retains that name and produces six charts on what to do about widespread exposure (complementarity quadrant, sectoral velocity, wage cliff matrix, resilience differential, trade-up corridors, bottleneck activity atlas). |
| `task_properties_correlation/` | Correlates 12 LLM-rated task properties (`m, d, s, r, h, e, t, tf, df, de, nt, ac`) from `data/final_eco_2025_with_task_properties.csv` against our 4 internal sources + 6 configs (5 ANALYSIS_CONFIGS + new `all_confirmed_conservative` from `final_all_confirmed_usage_ms_nonphysical_2026-02-12.csv`, registered in backend as `"AEI Both + Micro Conservative 2026-02-12"`) at major/minor/broad/occupation levels. Now includes a 46-formula × 3-weighting × 4-level × 2-target systematic search (`formula_search.py`, 1,104 cells) over the 7 properties used in Composite A & B (d, m, s, h, r, tf, df). Targets: (1) mean pct_tasks_affected across the 4 paper sources, (2) intensity ratio_pct from `analysis/exploratory/pct_norm_vs_eco/results/v2/0X.csv` (Σ pct / Σ freq×emp, renormalized to 100% — per-capacity AI usage rather than absolute coverage). Headline winner: **`(d × s) × (6−r) × (6−df)` weighted by `t`** — against `all_confirmed` directly: ρ +0.949 at major, +0.855 minor, +0.775 broad, +0.711 occ. Against `all_confirmed_conservative` (MS non-physical): +0.915 major, +0.857 minor, +0.793 broad, +0.746 occ. Beats raw `s` alone (+0.83 baseline) at every level. (Note: an earlier draft of this entry reported numbers averaged across 4 paper sources, which inflated ρ via noise reduction; the single-target numbers above are the honest read.) At broad/occupation levels against the conservative target, `(d × s) / r` × t slightly edges the inverted-multiply winner (+0.809 / +0.765 vs +0.793 / +0.746) — division wins where enough occupations absorb per-task variance. Three structural fixes vs. original Composite A: (i) drop `m`, `h`, `tf` (redundant or noisy), (ii) **invert frictions as bounded multipliers `(6−x)` instead of dividing** (division causes per-task variance explosion; inverted-multiply doesn't), (iii) weight by `t`. Original `(d·m·s·h)/(r·tf·df)` ranks ~#25 of 46 formulas. For the intensity target, the additive net score `s − (r + df)` weighted by freq is most robust (ρ ≈ +0.50 across minor/broad/occ; +0.75 at major) — different targets reward different operations: multiplicative for absolute coverage, additive for per-capacity intensity. Two methodologies side-by-side: **Method A** — group-mean of (property × weight) with weight ∈ {raw, freq_mean, t}; **Method B** — composite-as-auto-aug, where the composite is min-max scaled to [0,1] and plugged into the dashboard's pct pipeline as a stand-in for `auto_aug_mean / 5`, producing a synth_pct correlated against real source pct. Two composite formulas tested: Composite A = `(d·m·s·h)/(r·tf·df)` (friction in denominator); Composite B = `d·m·s` (slim variant). Each runs full-eco and confirmed-only (parallel of Schaal Method B filter — restricted to (task, occ) pairs in all_confirmed). Plus paper convergence rerun: reproduces `paper/results/part_1/convergence.png` (4 sources × 4 sources internal) and `convergence_external.png` (4 sources × 4 external benchmarks: Eloundou GPT-4 β, Eloundou Human β, AIOE mean, AIOE RC) with both freq and t weighting side by side, adding Composite-A-as-auto-aug as a 5th source row. Outputs: 6 PNGs (per-property + composite full eco; same confirmed-only; Method B; major property averages; paper internal convergence freq/t; paper external convergence freq/t) + 6 CSVs. **Headlines:** (1) **Raw `s` (algorithmic similarity) ranks SOC majors at ρ = +0.84** against our pct, raw `d` at +0.80 — the property signal was just being buried by freq weighting; (2) **Composite B (`d·m·s`) outperforms Composite A at every weighting** (raw +0.66 vs +0.32; ×t +0.71 vs +0.53; Method B ×freq +0.67 vs +0.39) — adding the friction denominator hurts because friction terms have wide per-task variance that gets amplified multiplicatively; (3) freq weighting still flips per-property correlations negative (same finding as first pass); (4) confirmed-only filter decreases the strongest predictors because restricting to tasks AI sees removes the discriminative tail in `s` and `d`; (5) paper convergence with t weighting ≈ freq weighting (internal 0.65 vs 0.66; external 0.69 vs 0.71) — the cross-source ranking story is robust to per-task weight choice; (6) `all_confirmed_conservative` correlates almost identically to `all_confirmed`. The slim composite (Method A, `d·m·s`, × t, full eco) hits ρ +0.71 at major as the headline single number. |
| `crashing_waves_vs_rising_tides/` | Empirical comparison to Mertens et al. (2026), "Crashing Waves vs. Rising Tides" (arXiv 2604.01363). The paper distinguishes two AI-progress patterns — narrow concentrated waves vs. broad parallel-shift tides — and concludes capability is tide-shaped overall, with six job families showing statistically significant steeper logistic slope (β). We can't replicate their per-task duration test (no task-duration estimates in our data), so we run a complementary cross-occupation cut. **Part A** (tide vs. wave): distribution shape of Δpct_tasks_affected across 923 occupations between snapshot dates — histograms, Gini, kurtosis, Lorenz-style concentration curves, lift profile by initial-exposure decile, rank stability over time, per-period violins, growth-by-major sorted by paper β. Run for both `all_confirmed` (4 dates Mar 2025 → Feb 2026) and `all_ceiling` (8 dates over the same window). Headline split: capability (ceiling) is tide-shaped (Gini 0.39, smooth lift profile), adoption (confirmed) is wave-shaped (Gini 0.65, growth concentrated in already-exposed occupations). **Part B** (forward risk via paper β): encodes Mertens Table 1 betas onto our 22 majors; computes three forward-risk scores per occupation restricted to the six sig-β majors — `already_score = pct_last × |β|`, `headroom_score = (100−pct_last) × |β|`, `combined_score = p(1−p)|β|·100` (logistic-derivative weighting, peaks at p=0.5). The "already" cut surfaces the most diverse front-of-the-wave list (Electronics Engineers, Investment Fund Managers, Architects, Graphic Designers, Public Relations Specialists, Concierges); the "headroom" cut is dominated by Personal Care/Service because |β|=0.93 there is roughly double the next steepest. 13 PNGs total + 11 CSVs. |
| `onet_economy_baseline/` | Pure structural look at the U.S. occupational economy from O*NET + BLS only — **no AI data**. 62 figures across 8 numbered families: (1) overall makeup distributions (emp/wage histograms, zone/outlook/phys class bars), (2) makeup by SOC level (major all-22, top-30 minor + broad — emp / wages / avg zone / avg wage), (3) phys-class split (avg zone, avg wage, composition-by-major stacked, phys × zone heatmap, phys × outlook heatmap), (4) job zone deep dive (avg wage by zone, avg pct phys by zone, major × zone emp + wage heatmaps), (5) SKA levels at imp ≥ 3 using O*NET native subgroupings — Cognitive / Psychomotor / Physical / Sensory abilities; Content / Process / Social / Complex Problem Solving / Technical / Systems / Resource Management skills; 10 knowledge domains — including subgroup × major heatmaps for each of the three SKA types, (6) physical-vs-non-physical SKA share per occupation (Psychomotor + Physical Abilities + manual subset of Technical Skills counted as physical; Sensory tracked separately and rolled into non-physical for the binary cut) by major / zone / phys class / wage quartile + scatter, (7) work activities GWA / IWA / DWA — emp + wages + avg zone for GWAs, top-30 IWAs and DWAs, GWA × phys class / GWA × zone / GWA × major heatmaps (employment allocated equally across each occupation's tasks), (8) cross-cuts — wage × zone violins, wage × phys class violins, wage × pct_physical scatter, avg SKA × wage scatter, SKA × zone violins, emp × major × phys class stacked. Figures filename-prefixed by family number for easy browsing. |
| `risk_score_audit/` | Diagnostic on the `job_exposure/job_risk_scoring` 8-flag composite, framing the question of whether to import it into Part 3 of the paper. Two methodological overrides applied locally (not in `compute_ska.py` or the question script): (i) SKA AI capability uses top-10 mean instead of p95 — stricter "what AI demonstrably can do" floor matching the dashboard's per-row reference; (ii) flag 6 fires on `emp_change_pct_2024_2034 < 0` (BLS 2024–2034 employment projection from eco_2025) instead of DWS outlook in {2,3} — direct employment-trajectory signal replacing the 2-axis outlook+wages tradeoff. 248 of 923 occs have negative projected change. Four sections: (1) flag-validity diagnostics — eta² of each flag against pct_physical, job_zone, and major shows F5 (zone in 1–3) is tautological with job_zone (η² = 1.00), F7 (software > median) is heavily structural (η² ≈ 0.42 across all three cuts), F1 moderate (η² 0.12 zone, 0.36 major), F6 (emp proj < 0) much less structural than the old DWS version (η² 0.05 phys / 0.11 zone / 0.29 major vs prior 0.13/0.20/0.30 — the swap reduces structural contamination of flag 6), F2/F3/F4/F8 mostly independent; (2) SKA mechanicalness (top-10 mean) — OLS R²(ska_pct ~ pct_physical) = 0.03 (negligible), R²(ska_pct ~ job_zone) = 0.19, combined 0.22; direction on zone reversed from the upstream intuition (lower-zone occs have HIGHER SKA pct because their requirement floor is lower); (3) level-vs-trend independence — eight 2×2 contingencies: pct level × pct trend has 21% off-diag at median (φ = 0.57) / 11% at p75 (φ = 0.72); SKA × SKA tighter under top-10 mean (10% / 6% off-diag, φ = 0.80 / 0.83); cross pairings at φ ≈ 0; (4) flagging variants — nine "high-exposure" definitions. A (`pct > 50%`), B (`pct > p75`), D (`pct > 50% + trend top half`) essentially identical (Jaccard 0.94–0.98, ~230 occs each); C (`pct > 50% + emp proj < 0`) drops to 59 occs (was 83 with DWS); E (trimmed 4-flag composite) is 200 occs with 87% Jaccard with A; F (full 8-flag) is 109 occs with 46% Jaccard with A and 61% zone 1–3 (vs 30% baseline) / 44% emp proj < 0 (vs 25%). Three quad-intersect variants (pct + SKA>med + pct trend>med + emp proj < 0): G (`pct>50%`) → 43 occs, H (`pct>median`) → 62 occs, I (`pct>p75`) → 41 occs. G ≈ I (Jaccard 0.95). H is the only quad-intersect with distinct content (admits 19 mid-exposure occs in trajectory). All three force emp proj < 0 by construction and run 76–84% zone 1–3. Recommendation in the report: four defensible options in increasing strictness — A (raw pct cut), E (trimmed composite), C (pct ∩ emp proj decline), H (pct>med + 3-condition watch list). Avoid F (too structural), B/D (≈ A), G/I (≈ each other). Side-deliverable: `ska_below_100_top10.csv` lists the 250 occs with SKA top-10 mean < 100% (vs 735 under p95), with a clean physical-vs-cognitive-ceiling split in the bottom 50. 6 PNGs + 8 CSVs. |

---

## What Each Question Delivers

Each sub-question produces:
- `<name>_report.md` — full narrative (also converted to PDF in `results/`)
- `results/*.csv` — all data tables
- `results/figures/*.png` — full figure set (gitignored)
- `figures/*.png` — key figures committed to git, embedded in the report

Each top-level question bucket additionally produces `<bucket>_report.md` synthesizing all sub-question findings. This aggregate report follows a specific format: numbered sections (one per sub-question) with `*Full detail:*` links, embedded figures from each sub-folder's committed `figures/` dir, a Cross-Cutting Findings section, a Key Takeaways section, a Sub-Report Index table, and a Config Reference table. See `ANALYSIS_CLAUDE.md` for the full spec and `job_exposure/job_exposure_report.md` as the canonical reference.
