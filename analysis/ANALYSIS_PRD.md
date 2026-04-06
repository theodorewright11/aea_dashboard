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

**Note:** All five ANALYSIS_CONFIGS use pre-combined datasets (is_aei=False) → eco_2025 baseline for WA analysis. Consistent across all configs. No family separation needed.

### Planned (future sessions)

| Bucket | Core question |
|--------|--------------|
| Economic Footprint | General results: sectors, wages, trends, state profiles |
| Potential Growth | Where is current usage far below capability? Where is the economic opportunity? |
| Source Agreement | Where do sources agree/disagree? What does MCP uniquely add? |
| Time Trends | Anything not covered in the above |
| State Clusters | State groupings beyond what Utah vs. National covers |

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

Each top-level question bucket additionally produces `<bucket>_report.md` synthesizing all sub-question findings.
