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
| `human_conversation` | `final_confirmed_human_usage_2026-02-12` | Confirmed human conversational AI use only |
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
- 284/332 IWAs grew in exposure over 15 months (Sept 2024 → Feb 2026); 72 newly above 10%
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
- Legal (+25.5 pp) and Education (+24.8 pp) saw the largest task penetration gains over the dataset window
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
- Confirmed growth: +21.8M workers in 16 months (Sep 2024 → Feb 2026); ceiling also grew

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

Primary lens: `all_confirmed` series (AEI Both + Micro, Sep 2024 – Feb 2026). Ceiling comparison uses `all_ceiling` series.

| Sub-folder | Question |
|------------|----------|
| `trajectory_shapes/` | How did individual occupations grow? Six trajectory type classifications across all 923 occupations |
| `tier_churn/` | How stable are exposure tiers? Tier transitions, new high-tier entrants, sector stability rates |
| `confirmed_ceiling_convergence/` | Is deployment catching up to capability? National and sector-level confirmed/ceiling ratio trends |
| `wa_tipping_points/` | Which IWAs crossed meaningful thresholds (10%, 33%, 66%), which are approaching them? |
| `occs_timeline/` | Full time-series for the 29 named occupations of interest |

**Key findings:**
- Zero occupations at >=60% confirmed in Sep 2024; 145 by Feb 2026 — the entire high-exposure tier was created during the window
- 44% of occupations (406) are "laggards" with <5pp total gain — AI expansion is concentrated, not universal
- March 2025 and August 2025 are the two inflection-point dataset dates; confirmed exposure advances in discrete jumps
- Confirmed/ceiling gap opened in Aug 2025 (MCP incorporation), sitting at ~10pp nationally; confirmed growing slightly faster than ceiling
- Software Developers and Data Scientists: literally zero confirmed growth across all 6 dates; HR Specialists and Market Research Analysts: +53pp and +50pp respectively
- 72 IWAs in active expansion zone (10–33%, growing); financial/legal/healthcare documentation IWAs approaching 33% threshold

### Planned (future sessions)

| Bucket | Core question |
|--------|--------------|
| (none remaining) | |

---

## Occupations of Interest

29 named occupations across three groups — see `OCCS_OF_INTEREST` in `analysis/config.py` for the exact list. Matched against `title_current` in eco_2025 with fuzzy matching where needed.

Groups: High-profile/high-employment · AI-controversial/interesting · Utah-relevant

---

## What Each Question Delivers

Each sub-question produces:
- `<name>_report.md` — full narrative (also converted to PDF in `results/`)
- `results/*.csv` — all data tables
- `results/figures/*.png` — full figure set (gitignored)
- `figures/*.png` — key figures committed to git, embedded in the report

Each top-level question bucket additionally produces `<bucket>_report.md` synthesizing all sub-question findings. This aggregate report follows a specific format: numbered sections (one per sub-question) with `*Full detail:*` links, embedded figures from each sub-folder's committed `figures/` dir, a Cross-Cutting Findings section, a Key Takeaways section, a Sub-Report Index table, and a Config Reference table. See `ANALYSIS_CLAUDE.md` for the full spec and `job_exposure/job_exposure_report.md` as the canonical reference.
