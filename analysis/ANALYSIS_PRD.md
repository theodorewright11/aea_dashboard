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
| `worker_resilience/` | What can a worker do to make their job more resilient? (SKA gap: where human advantage is largest vs. where AI leads) |
| `pivot_distance/` | Where is it cheap to pivot, and where is it expensive? (average reskill cost from high-risk to low-risk by job zone) |
| `audience_framing/` | How do findings translate across audiences? (skill profile overlaps, dominant domains in high-risk/low-outlook jobs) |
| `occs_of_interest/` | How do findings land for the named occupation list? |

**Risk scoring factors** (job_risk_scoring) — 7 binary flags with weighted scoring + exposure gate:
- **Flags 1–4 (exposure signal, weight = 2 each):**
  1. `pct_tasks_affected > median`
  2. `SKA gap > median` (AI capability exceeds typical job need)
  3. `pct trend: positive AND above-median growth` (median of ALL growth, not just positive)
  4. `SKA gap trend: positive AND above-median growth`
- **Flags 5–7 (structural vulnerability, weight = 1 each):**
  5. `job_zone ∈ {1, 2, 3}`
  6. `outlook ∈ {2, 3}` (below-average; note: 1 = good outlook but low wages)
  7. `n_software > median`
- **Exposure gate:** occupations with `pct_tasks_affected < 33%` cannot be classified as high risk regardless of score.
- **Tiers:** max score = 11. `8–11 = high risk`, `4–7 = moderate`, `0–3 = low`.

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

### Planned (future sessions)

| Bucket | Core question |
|--------|--------------|
| Source Agreement | Where do sources agree/disagree? What does MCP uniquely add? |

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
