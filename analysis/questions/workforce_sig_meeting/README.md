# workforce_sig_meeting

Presentation deliverable — charts compiled for a workforce significance
meeting. The report (`workforce_sig_meeting_report.md`) opens with a
"how the numbers are generated" methodology table on Chief Executives,
then embeds existing paper figures and two custom charts produced here.

This is a presentation bucket, not a research bucket. It does not have
sub-questions and it does not feed into `question_findings/` or `report/`.
Same pattern as `workforce_meeting/` and `workforce_meeting_v2/`.

## Run

```
venv/Scripts/python -m analysis.questions.workforce_sig_meeting.run
```

Generates:
- `figures/conv_allconfirmed_ceiling.png` — committed
- `figures/gap_to_ceiling_wages.png` — committed
- `results/figures/*.png` — same files, gitignored
- `results/conv_allconfirmed_ceiling.csv` — backing data
- `results/gap_to_ceiling_wages.csv` — backing data
- `results/methodology_chief_executives_full.csv` — all 31 Chief Executives
  tasks with freq_mean, auto_aug_mean, ai_affected, AI weight, baseline
  weight (gitignored — the report quotes the rolled-up summary)
- `results/methodology_chief_executives_summary.csv` — summary numbers
  used in the report's footer math

## Charts

- **Methodology table** (top of report) — Chief Executives, 6 of 31 sample
  tasks shown. Footer math uses all 31 tasks: Σ(freq × auto-aug/5) ÷ Σ freq
  → % task completions AI affected → workers affected → wages affected.
  Sources: `data/final_eco_2025.csv` for tasks/freq/employment/wage,
  `data/final_all_confirmed_usage_2026-02-12.csv` for `auto_aug_mean`.
  The methodology table mirrors the formula the dashboard uses with
  `method=freq, use_auto_aug=True`; pct lands at 50.7%, identical to
  `get_pct_tasks_affected("AEI Both + Micro 2026-02-12")["Chief Executives"]`.
- **Reused from `paper/results/part_1`**: `temporal_trend.png`
- **Reused from `paper/results/part_2`**: `phys_info_divide.png`,
  `job_zone_violin.png`, `ska_levels.png`, `gwa_exposure.png`,
  `major_categories.png`
- **Reused from `paper/results/part_3`**: `tech_commodities.png`
- **`gap_to_ceiling_wages.png`** — wages variant of part_3's
  `gap_to_ceiling.png`. Same stacked confirmed-+-extension structure but
  x-axis is wages affected (USD/yr) instead of workers affected, and the
  sectors are sorted by wage gap instead of worker gap.
- **`conv_allconfirmed_ceiling.png`** — variant of part_3's
  `conv_vs_agentic.png` where the middle bar is "All Confirmed" (instead
  of "Agentic Confirmed") and the right bar is "Ceiling". Three bars per
  major: Conversational → All Confirmed → Ceiling.

## Config

- All charts: National, freq method, auto-aug ON.
- Custom chart datasets: `human_conversation` (AEI Conv + Microsoft),
  `all_confirmed` (AEI Conv + API + Microsoft), `all_ceiling` (AEI + MCP
  + Microsoft), all at 2026-02-12 / 2026-02-18 snapshots.
- Methodology table dataset: `all_confirmed` (`AEI Both + Micro 2026-02-12`).

## Files

| Path | What |
|------|------|
| `workforce_sig_meeting_report.md` | The deliverable — methodology table + figures |
| `run.py` | Builds custom figures + methodology breakdown |
| `figures/conv_allconfirmed_ceiling.png` | Custom chart (committed) |
| `figures/gap_to_ceiling_wages.png` | Custom chart (committed) |
| `results/*.csv` | Backing data (gitignored) |
