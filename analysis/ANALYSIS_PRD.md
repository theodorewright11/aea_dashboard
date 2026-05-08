# ANALYSIS_PRD.md — What the Analysis Folder Is For

What lives in `analysis/`, who it serves, and what it produces.

For *how to navigate* the folder (folder map, compute APIs, formulas), see `ANALYSIS_ARCHITECTURE.md`. For *how to work in it* (rules, conventions), see `ANALYSIS_CLAUDE.md`.

---

## Purpose

The `analysis/` folder is the research arm of the AEA Dashboard project. The dashboard ships interactive metrics; this folder produces the underlying research — the paper, the methodology audits, the comparisons against external indices, and the per-question deep dives that motivated the metrics.

---

## Audiences

| Audience | What they want from this folder |
|----------|--------------------------------|
| **Researchers (Alice, Zach, paper reviewers, citations)** | "Is the methodology sound? What's novel? What claims are actually supported?" |
| **Policymakers (OAIP, state workforce boards, legislators)** | Clear takeaways. "What should we do? Where should money go? What's coming?" |
| **Practitioners (workforce dev, educators, HR)** | "Which skills matter? Which training programs should we build? What does this mean for my sector?" |

---

## The Five Analysis Configs

All analyses use one or more of these five canonical dataset configurations. Each is a single pre-combined dataset — no `combine_method` toggle needed. All use `method="freq"` (time-weighted), `use_auto_aug=True`, `geo="nat"` unless a script specifies otherwise.

**Primary config: `all_confirmed`.** The three-layer framing:
1. **Confirmed usage** (`all_confirmed`) — base lens. "AI is doing these things."
2. **Ceiling** (`all_ceiling`) — comparison. "Here's where AI could be doing more than confirmed usage suggests." Includes MCP capability data which is less robust.
3. **Actual adoption** — acknowledged gap; we don't have data on how many workplaces are actually using AI for these tasks yet.

| Key | Dataset | What it measures |
|-----|---------|-----------------|
| `all_confirmed` | `final_all_confirmed_usage_2026-02-12` | **PRIMARY** — All confirmed usage (conv + API + Microsoft, no MCP) |
| `all_ceiling` | `final_all_usage_2026-02-18` | Upper bound — everything AI can reach (AEI + MCP + Microsoft) |
| `human_conversation` | `final_confirmed_human_usage_2026-02-12` | Confirmed human conversational AI use (AEI Conv + Microsoft Copilot) |
| `agentic_confirmed` | `final_aei_agentic_usage_2026-02-12` | Confirmed agentic tool-use (AEI API) |
| `agentic_ceiling` | `final_all_agentic_usage_2026-02-18` | Agentic ceiling tool-use (MCP + AEI API) |

The agentic configs show how much architectural investment would be needed to deploy AI for a given set of tasks, and what agentic AI covers vs. browser/conversational AI.

`config.py` exports these as `ANALYSIS_CONFIGS`, with display labels in `ANALYSIS_CONFIG_LABELS` and time series for trend analysis in `ANALYSIS_CONFIG_SERIES`.

---

## Deliverables

Three live deliverable types and one archived one.

### 1. The paper (`analysis/paper/`)

The primary current deliverable. Three parts:

- **Part 1 — Scale, Convergence, Growth** (first draft complete). Establishes the magnitude of AI exposure, shows that independent measurement sources converge on similar rankings, and traces how confirmed usage has grown.
- **Part 2 — Characterization: Where AI Exposure Falls** (in progress). The shape of exposure — physical/informational divide, job zones, SKA breakdown, work activities, major occupational categories.
- **Part 3 — Action: What To Do About It** (in progress). Adoption gap, technology commodity exposure, the focused-set risk score, sector-level intensity anchoring.

Each part has its own `run.py`, `README.md`, and committed `figures/` directory. The assembled prose lives in `paper/results/results.md`. Paper writing follows a separate style reference (`paper/writing_style_source.md` + `paper/paper_writing_style.md`).

### 2. Exploratory analyses (`analysis/exploratory/`)

One-off deep dives motivated by paper drafting or open methodology questions. Each sub-folder is self-contained: `run.py`, `README.md`, a narrative `<name>_report.md`, and a gitignored `results/`. Naming convention is `<bucket>_<topic>` so `ls` groups them:

- `paperinfra_*` — mirrors and variants of paper figures
- `extcompare_*` — comparisons against external AI exposure indices (Schaal, Eloundou, Mertens, AIOE, etc.)
- `audit_*` — methodology audits (task properties, risk score, physical filter, weighting, etc.)
- `deepdive_*` — per-element / structural deep dives

Two folders are committed via gitignore exception (`paperinfra_all_charts/`, `paperinfra_appendix/`); the rest are local-only.

`claude_lab/` is a separate autonomous-research workspace that operates by its own conventions.

### 3. Reusable computation modules (`analysis/data/`, `analysis/config.py`, `analysis/utils.py`)

The SKA gap computation, the canonical configs, the chart styling, and the PDF generation helpers. All live exploratory and paper scripts depend on these.

### 4. (Archived) Question-bucket reports (`analysis/_archive/`)

The earlier era of this project — 11 question buckets (job_exposure, economic_footprint, work_activity_exposure, potential_growth, source_agreement, agentic_usage, field_benchmarks, state_clusters, time_trends, plus three workforce-meeting deliverables). Each bucket asked an overarching question with sub-folders for sub-questions, produced a per-bucket `<bucket>_report.md`, and rolled up into `report/report.md` and `report/report_brief.md`.

The question system is **frozen**. No new buckets get added; existing reports are read-only. Patterns developed there (the SKA formula, the 8-flag risk score) remain live and are documented in `ANALYSIS_ARCHITECTURE.md`. The paper draws from question findings but supersedes them as the canonical research output.

The archived reports remain readable on GitHub — image paths inside `_archive/report/` and `_archive/question_findings/` use `../questions/...` which still resolves correctly because all three folders moved together.

---

## What This Folder Is *Not*

- **Not the dashboard codebase.** The interactive product lives in `backend/` and `frontend/`. The analysis folder consumes the same compute engine (`backend/compute.py`) but produces static reports and figures, not API endpoints.
- **Not a place for ad-hoc throwaway code.** Every exploratory sub-folder must have a README and a narrative report. If something doesn't justify that overhead, it doesn't belong here.
- **Not where new question buckets get added.** That system is archived. New analysis goes under `exploratory/` or feeds into a paper section.
