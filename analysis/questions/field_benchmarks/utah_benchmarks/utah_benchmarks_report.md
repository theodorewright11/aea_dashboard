*Config: All five configs | Method: Freq | Auto-aug ON | Utah (geo="ut")*

Utah is where we have the richest external comparison point — Seampoint's governance-constrained deployment analysis gives us both a dollar figure (handled in `wage_impact/`) and a percentage of work hours estimate, which is what this sub-analysis focuses on. The question is: for Utah workers specifically, what fraction of their tasks does our confirmed usage suggest AI is touching, and how does that compare to Seampoint's 20% takeover / 51% augment framework?

*Full detail: [utah_benchmarks_report.md](utah_benchmarks_report.md)*

## Utah Task Exposure vs. Seampoint

![Utah pct_tasks_affected across 5 configs vs Seampoint 20% and 51%](figures/utah_pct_comparison.png)

Our all_confirmed Utah figure is 41.9% — double Seampoint's 20% takeover estimate and approaching Seampoint's 51% augment threshold. The agentic_confirmed config at 27.2% lands between the two Seampoint benchmarks, which makes intuitive sense: agentic, tool-use AI is closer to the "governance-constrained takeover" concept than the broader conversational + API usage we capture in all_confirmed.

The alignment between our ceiling (50.5%) and Seampoint's augment estimate (51%) is striking. It suggests that when AI is operating at full current capability — including MCP tool use and all agentic pathways — it's reaching roughly the same scope as Seampoint projects for governance-constrained augmentation deployment in Utah.

## Top Utah Occupations

![Top 20 Utah occupations by pct_tasks_affected](figures/utah_top_occs.png)

The top Utah occupations by exposure are consistent with the national picture: high-information-density, administrative, and professional services roles dominate. These also tend to be the roles Seampoint identifies as prime deployment candidates in their governance-constrained framework.

## Utah vs. National

Utah's exposure rate (41.9% confirmed) is slightly higher than the national rate (40.0%), which reflects Utah's workforce composition — somewhat heavier on professional services and tech-adjacent sectors, lighter on physical trades. The differences are modest enough that Utah is a reasonable proxy for national dynamics rather than an outlier.

## Key numbers

| Config | Utah pct_agg | Utah workers | Utah wages |
|--------|-------------|--------------|------------|
| All Confirmed | 41.9% | 921K | $62.6B |
| All Ceiling | 50.5% | 1,142K | $77.0B |
| Human Conversation | 36.5% | 803K | $53.7B |
| Agentic Confirmed | 27.2% | 481K | $34.0B |
| Agentic Ceiling | 40.0% | 902K | $61.8B |
| Seampoint: Take Over | 20.0% | — | $21.0B |
| Seampoint: Augment | 51.0% | — | $15.0B |

## Config

| Setting | Value |
|---------|-------|
| Primary dataset | `AEI Both + Micro 2026-02-12` |
| Method | freq (time-weighted) |
| use_auto_aug | True |
| Geography | Utah (geo="ut") |

## Files

| File | Description |
|------|-------------|
| `figures/utah_pct_comparison.png` | Our 5 configs Utah pct_agg vs Seampoint |
| `figures/utah_top_occs.png` | Top 20 Utah occupations by exposure |
| `results/utah_pct_agg.csv` | pct_agg, workers, wages by config |
| `results/utah_top_occs_confirmed.csv` | All Utah occupations ranked |
