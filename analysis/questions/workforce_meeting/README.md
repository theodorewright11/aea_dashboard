# Workforce Meeting — Presentation Charts

14 presentation-quality charts for a Utah workforce meeting with business and education leaders. Charts are designed for slide decks: bar-chart-only, minimal text, consistent styling, numbered in suggested presentation order.

## Audience

Business and education leaders making decisions about reskilling investment, durable skills identification, and pro-AI workforce initiatives. Non-technical. Executive summary vibe.

## Config

All charts use `all_confirmed` (AEI Both + Micro 2026-02-12) | freq | auto-aug ON | **Utah** unless noted otherwise.

- **Trends**: AEI Both + Micro 2025-03-06 → 2026-02-12
- **Adoption gap**: all_confirmed vs all_ceiling (both Utah)
- **AI modes**: human_conversation vs agentic_confirmed (both Utah)
- **SKA elements**: national scope (occupation-level metric, geo-invariant)
- **Auto-aug**: national scope (task-level metric, geo-invariant)
- **Pivot cost**: national scope (loaded from existing job_exposure/pivot_distance results)

## Charts

| # | File | What It Shows |
|---|------|--------------|
| 01 | `utah_headline` | Utah workers with AI-exposed tasks — headline stat |
| 02 | `sector_scope` | Top 7 sectors by workers affected (+ %tasks, wages) |
| 03 | `gwa_scope` | Top 7 work activities by % tasks affected (+ workers, wages) |
| 04 | `sector_trend` | Top 7 sector growers in workers (Mar 2025 → Feb 2026) |
| 05 | `gwa_trend` | Top 7 GWA growers in % tasks (Mar 2025 → Feb 2026) |
| 06 | `sector_adoption_gap` | Top 7 sectors: confirmed → ceiling gap (workers) |
| 07 | `gwa_adoption_gap` | Top 7 GWAs: confirmed → ceiling gap (% tasks) |
| 08 | `ai_modes_gap` | Top 7 sectors: conversational → agentic drop (workers) |
| 09 | `autoaug_by_sector` | Top 7 sectors by avg auto-aug score (tasks with AI score) |
| 10 | `pivot_cost` | Reskilling cost by job zone (all 5 zones) |
| 11 | `ska_human_skills` | Top 7 skills where humans still lead AI |
| 12 | `ska_human_knowledge` | Top 7 knowledge domains where humans still lead AI |
| 13 | `ska_ai_skills` | Top 7 skills where AI has overtaken humans |
| 14 | `ska_ai_knowledge` | Top 7 knowledge domains where AI has overtaken humans |

## Run

```bash
venv/Scripts/python -m analysis.questions.workforce_meeting.run
```
