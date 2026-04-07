# Field Benchmarks

**Question:** How do the AEA Dashboard's findings compare to other major AI-and-work research?

This bucket benchmarks our confirmed-usage numbers against six external sources spanning
real-world platform data, enterprise deployment analysis, governance-constrained readiness
estimates, and skill-based technical capability assessments.

## Sub-analyses

| Sub-folder | Question |
|------------|----------|
| `automation_share/` | How does our task exposure rate compare to Project Iceberg and Seampoint? |
| `wage_impact/` | How do our dollar wages-affected compare to Seampoint's Utah figures? |
| `utah_benchmarks/` | Utah-specific: our pct_tasks_affected for Utah workers vs. Seampoint's 20%/51% |
| `theoretical_vs_confirmed/` | Where does confirmed usage sit relative to deployment readiness and technical capability? |
| `sector_breakdown/` | Which sectors rank highest across our analysis, Copilot, AEI, and ChatGPT data? |
| `work_activity_comparison/` | Which GWA-level activity types appear across all confirmed-usage platforms? |
| `platform_landscape/` | Full methodology comparison — all sources side by side |

## External sources

| Source | What it measures |
|--------|-----------------|
| Project Iceberg (Chopra et al., 2025) | % of skill wage value AI tools can technically perform |
| Seampoint LLC (Utah, 2026 prelim.) | % of work hours AI can take over / augment (governance-constrained) |
| AEI (Humlum & Vestergaard, 2024) | Occupational task coverage from Claude API conversation logs |
| ChatGPT usage (Weidinger et al., 2025) | Work-session distribution from ChatGPT logs |
| Microsoft Copilot (2025) | Task applicability rates from enterprise Copilot deployment |

## Run order

```bash
venv/Scripts/python -m analysis.questions.field_benchmarks.automation_share.run
venv/Scripts/python -m analysis.questions.field_benchmarks.wage_impact.run
venv/Scripts/python -m analysis.questions.field_benchmarks.utah_benchmarks.run
venv/Scripts/python -m analysis.questions.field_benchmarks.theoretical_vs_confirmed.run
venv/Scripts/python -m analysis.questions.field_benchmarks.sector_breakdown.run
venv/Scripts/python -m analysis.questions.field_benchmarks.work_activity_comparison.run
venv/Scripts/python -m analysis.questions.field_benchmarks.platform_landscape.run
```
