# ANALYSIS_CLAUDE.md — Analysis Agent Instructions

Rules specific to working in the `analysis/` folder. Read this alongside the project-level `CLAUDE.md` — this supplements, does not replace it.

---

## Writing Style

When writing reports, narratives, or any prose deliverables, follow the writing style reference in `analysis/writing_style_reference.md`. The key points: conversational-analytical register, loose form but rigorous logic, no hedging filler, no bureaucratic framing, no AI-sounding connectors. Don't force it — the goal is to sound like a sharp person reasoning through data, not to match a template. Keep things as concise as they should be; don't pad sections.

---

## Before Starting Any Analysis Task

1. Read project-level `CLAUDE.md` and `PRD.md`.
2. Read `ANALYSIS_PRD.md` (what the analysis system does, question catalog, five configs).
3. Read `ANALYSIS_ARCHITECTURE.md` (folder structure, compute access, SKA formula, output standards).
4. If the task touches SKA computation, re-read the SKA formula section in `ANALYSIS_ARCHITECTURE.md` before writing any code.
5. This very important - If the task is ambiguous about scope, which sub-question it belongs to, or how a metric should be computed — **ask before implementing**.

---

## Question Workflow

- A question prompt produces outputs for **its own sub-folder only**. It does not touch `report/report.md`. The aggregate report is updated by a separate dedicated prompt.
- Each sub-question has: `README.md`, `<name>_report.md`, `run.py`, `results/` (gitignored), `figures/` (committed key figures so the report loads on github).
- Top-level question folders (e.g., `job_exposure/`) additionally have a `README.md` and a `job_exposure_report.md` that synthesizes all sub-questions.
- Run scripts from project root: `venv/Scripts/python -m analysis.questions.job_exposure.<sub_question>.run`

## Syncing to question_findings/

Whenever a `*_report.md` is created or updated, copy it to `analysis/question_findings/` and rewrite its image paths to resolve from that folder.

**Naming convention:**
- Bucket-level reports (`questions/{bucket}/{bucket}_report.md`) → `question_findings/{bucket}_report.md`
- Sub-question reports (`questions/{bucket}/{sub}/{sub}_report.md`) → `question_findings/{bucket}__{sub}_report.md`

**Image path rewriting:** All `![caption](path)` image references must be updated to point back to the original `figures/` directory:
- Bucket reports: prepend `../questions/{bucket}/` to each image path
- Sub-question reports: prepend `../questions/{bucket}/{sub}/` to each image path

Do not rewrite link-only syntax `[text](url)` or any path beginning with `http`.

## Aggregate Report Format

Top-level `<bucket>_report.md` files follow a specific structure. Use `job_exposure/job_exposure_report.md` as the canonical reference. Requirements:

- **Header line**: config summary on the first line — `*Primary config: ... | ... | ...*`
- **Opening paragraph**: 4–6 sentence summary of the full bucket's through-line (not an abstract — more like "here's the punchline before the reasoning").
- **Numbered sections, one per sub-question**: each section opens with `*Full detail: [<name>_report.md](<sub-folder>/<name>_report.md)*` on its own line, then provides a narrative synthesis of that sub-question's findings — not a copy of the sub-report, but a distillation that stands on its own.
- **Embedded figures**: key figures from each sub-folder's committed `figures/` dir, referenced with relative paths from the aggregate report (e.g., `sector_footprint/figures/aggregate_totals.png`). Every section should have at least one figure. Use `![Caption](relative/path)` format.
- **Cross-Cutting Findings section**: 4–6 findings that span multiple sub-questions and couldn't appear in any single sub-report. Bold the finding name, then one paragraph of reasoning.
- **Key Takeaways section**: numbered list, 5–7 items, each starting with a **bolded key number or fact** followed by one sentence of context.
- **Sub-Report Index**: a table with columns Sub-Analysis | Report | What It Answers. Link the report filename.
- **Config Reference**: a table with columns Config Key | Dataset | Role. Match the five ANALYSIS_CONFIGS exactly.

## Rolling Aggregate Reports (report/ folder)

The `analysis/report/` folder contains two documents that roll up findings across all active question buckets. These are the primary deliverables for stakeholders and paper authors. They are NOT auto-generated — they require a dedicated update pass when significant new results exist.

**Two-document structure:**

### `report_brief.md` — Highlighted Stories (3–8 findings)

The short-form report. Tells the 3–8 most compelling stories across all analysis buckets. Intended audience: policymakers, paper reviewers, anyone who wants the main takeaways in one place.

Format requirements:
- **Opening paragraph** (1–2 sentences): scope and primary config.
- **One overview figure** showing aggregate scale (e.g., five-config totals). This is the first figure in the document.
- **One section per story** (3–8 total). Each section has:
  - A header that states the finding, not the topic — skimming the headers alone should convey the paper's thesis. Example: "Zero to 145: The High-Exposure Tier Was Created During the Study Window", not "Temporal Analysis".
  - Narrative prose in the conversational-analytical voice (see `writing_style_reference.md`). Walk through the reasoning, not just the conclusion.
  - 1–2 figures from the relevant bucket's committed `figures/` dir. Figure paths use `../questions/{bucket}/...` relative to `report/`.
  - A `*Full analysis: [...](...)*` link to the relevant bucket report.
- **"Where to Go Next" section** at the end: links to `report.md` and to all eight bucket reports.
- **Config reference footer** (one line).

How to pick stories (in priority order):
1. Findings that are counterintuitive or gap-filling relative to existing literature.
2. Findings where the data produces a number or pattern that would change how a policymaker acts.
3. Findings that are cross-validated by multiple independent sources or methods.
4. Findings that are methodological contributions (not just results).
5. Personal preference / editorial judgment.
Cap at 8 stories. Past 8 becomes unwieldy for a "highlights" format. Below 3 feels thin.

### `report.md` — Full Comprehensive Report

The long-form report. Covers all active analysis buckets with depth. Intended audience: researchers, paper co-authors, anyone who wants the full picture with all supporting figures.

Format requirements:
- **Opening paragraph**: 3–5 sentences on scope, primary config, and what's new since the last version.
- **Table of contents**: one entry per chapter, with anchor links.
- **One chapter per active analysis bucket** (currently 8 buckets). Each chapter:
  - Opens with `*Full detail: [bucket_report.md](...)*` link.
  - Has a `*Primary config: ...*` line.
  - Covers the key findings from that bucket with sub-sections. Section headers state findings, not topics.
  - Embeds key figures (1–3 per sub-section) using `../questions/{bucket}/...` paths.
  - Does NOT reproduce the full bucket report verbatim — synthesizes and distills, with forward-links for depth.
- **Cross-Cutting Findings section**: 5–8 findings that span multiple buckets.
- **Sub-Report Index table**: one row per bucket with columns Bucket | Report | Core Question.
- **Config Reference table**: five configs.

### Updating the Reports

When new sub-question results are produced or an existing bucket report is updated:

1. Identify which chapter of `report.md` covers that bucket and update the relevant sub-sections. Update numbers, figures, and narrative to reflect the new results.
2. Assess whether any of the 8 stories in `report_brief.md` need updating. If a story's key numbers changed, update the narrative and figures. If a new result is more compelling than an existing story, consider swapping.
3. If a new bucket is added (new top-level question folder), add a chapter to `report.md` and assess whether any finding from it warrants a story slot in `report_brief.md`.
4. Do NOT update `report.md` or `report_brief.md` as part of a question-specific prompt. These are updated only by a dedicated report-update prompt.

Figure path convention from `report/`: `../questions/{bucket}/{sub-folder}/figures/{filename}.png`

## Reference-Only Scripts

The following question scripts are kept for reference but are **broken** due to dataset renames in the backend (e.g., old names like `"AEI Cumul. (Both) v4"` no longer exist). Do not attempt to run or fix them unless explicitly asked:
- `questions/economic_footprint/run.py`
- `questions/job_exposure/run.py` (old flat version, superseded by sub-folders)

---

## Data and Compute Rules

- **SKA is real-time.** Never pre-save SKA outputs as static CSVs and load them later. Always call `compute_ska(pct, ska_data)` fresh from `analysis.data.compute_ska`. The five configs in `ANALYSIS_CONFIGS` produce different pct inputs → different AI capability scores.
- **Use `get_pct_tasks_affected()` from `analysis.config`** to get pct for a single dataset. Do not build the config dict by hand in question scripts.
- **Use `ANALYSIS_CONFIGS` and `ANALYSIS_CONFIG_SERIES`** from `analysis.config` for the canonical five configs. Do not hardcode dataset names in question scripts.
- **`analysis/data/tech_skills_simple.csv`** is the static n_software lookup. It is generated by `analysis/data/compute_tech_skills.py` and committed. Do not regenerate it unless `technology_skills_v30.1.csv` is updated.
- **Trend analysis** uses `ANALYSIS_CONFIG_SERIES` for the time series per config. For SKA gap trends, recompute at first and last date only (not all intermediate dates).

## Code Quality (analysis-specific)

Follow project `CLAUDE.md` Python rules, plus:
- All `run.py` scripts must be runnable as `python -m analysis.questions.job_exposure.<sub>.run` from project root.
- Use `ensure_results_dir()` from `analysis.config` to create `results/` and `results/figures/`.
- Use `COLORS`, `FONT_FAMILY`, `CATEGORY_PALETTE` from `analysis.utils` for all charts. Never hardcode colors in question scripts.
- Every `run.py` must copy key figures to a committed `figures/` dir and call `generate_pdf()` at the end.

## Charts and Dashboard Reproduction

**`analysis/charts.md`** is the single consolidated reference for all committed analysis figures and how to reproduce them (or not) on the live dashboard. It covers every sub-question across all nine active buckets.

When adding a new figure to a `run.py`:
- Add an entry in `analysis/charts.md` under the appropriate bucket/sub-question section.
- Specify the chart type, what it shows, and either the dashboard reproduction steps or "Not reproducible" with the reason.

**Chart formatting rules:**
- Horizontal bar charts using `make_horizontal_bar` must pass the DataFrame sorted `ascending=False` (largest first). `make_horizontal_bar` uses `autorange="reversed"` on the y-axis — passing ascending=True will render smallest at top.
- For raw `go.Figure` horizontal bars (without `make_horizontal_bar`), sort `ascending=True` (smallest first) so the largest value renders at the top of the chart.
- Reports use opening paragraphs (no `## TLDR` heading and no `**TLDR:**` prefix). Just a plain paragraph immediately after the config line and `---` divider.
- State/geo labels should be uppercase in all bar charts.

## Pitfalls

- `pct_tasks_affected` from `get_pct_tasks_affected()` is already a ratio-of-totals (0-100). Never average it across occupations to get a group pct — re-derive from task_comps.
- SKA importance filter (≥ 3) must be applied **per occupation row**, not globally. An element that is unimportant in one occupation is still valid in others.
- O*NET `title` in v30.1 files matches `title_current` in eco_2025. If match rate < 90%, log a warning and investigate.
- For pivot distance: if a job zone has fewer than 10 high-risk or low-risk occupations, use whatever is available (`min(10, n)`).
