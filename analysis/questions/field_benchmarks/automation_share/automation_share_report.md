*Config: All Confirmed (primary) | Method: Freq | Auto-aug ON | National | All 5 configs compared*

The automation share comparison is where this benchmarking exercise gets philosophically interesting. Three sources, three numbers — 40%, 20%, 11.7% — and they look like they can't all be right. They can, because they're not measuring the same thing. Our 40% confirmed figure captures how many of the average worker's tasks have been touched by AI in observed usage. Seampoint's 20% takeover estimate is asking what an organization could actually deploy right now if governance allowed it, in a specific state, under current oversight constraints. Project Iceberg's 11.7% Full Index is measuring the fraction of skill-wage value that existing AI tools can technically substitute. These are three different questions, and the fact that confirmed usage is higher than a technical capability estimate isn't a paradox — it means the capability framing (skill substitution) is narrower than usage reality.

*Full detail: [automation_share_report.md](automation_share_report.md)*

## Rate Comparison

![Rate comparison: our 5 configs vs external benchmarks](figures/rate_comparison.png)

The horizontal layout makes the spread visible. Our five configs span 20%–50%: agentic_confirmed at 20.3% (tool-use only, narrowest definition), human_conversation at 35.3%, all_confirmed at 40.0% (primary), agentic_ceiling at 39.4%, and all_ceiling at 50.3% (everything AI can reach including MCP). Seampoint's 51% augment estimate essentially matches our ceiling — which is actually a meaningful alignment signal, since Seampoint is asking what governance-constrained deployment could reach and we're asking what's technically in scope with current tools. Seampoint's 20% takeover figure precisely matches our agentic_confirmed rate, which makes sense: agentic AI doing full tasks without human collaboration is the definitional match for "AI can take over."

The Iceberg numbers look small by comparison, but that's the unit difference at work. Iceberg measures skill-wage substitutability — if a worker spends 11.7% of their earnings on skills AI tools can technically replicate, that's not the same as 11.7% of their tasks being affected by AI. Tasks involve more than just the application of specific skills.

## Layer Chart

![Layer chart: measurement spectrum from agentic confirmed to Seampoint augment](figures/layer_chart.png)

Reading left to right: agentic_confirmed (20%) → all_confirmed (40%) → all_ceiling (50%) → Iceberg Full (11.7%) → Seampoint takeover (20%) → Seampoint augment (51%). The Iceberg numbers sit lower not because AI is doing less than we observe, but because they're measuring technical skill overlap, not real usage breadth.

## Key numbers

| Source | Metric | Value |
|--------|--------|-------|
| AEA Dashboard: All Confirmed | emp-weighted mean pct_tasks_affected | 40.0% |
| AEA Dashboard: Ceiling | same, with MCP | 50.3% |
| AEA Dashboard: Agentic Confirmed | tool-use only | 20.3% |
| Project Iceberg: Full Index | % of skill wage value (all sectors) | 11.7% |
| Project Iceberg: Surface Index | % of skill wage value (tech sector) | 2.2% |
| Seampoint Utah: AI Can Take Over | % of work hours, governance-constrained | 20.0% |
| Seampoint Utah: AI Can Augment | % of work hours, AI extends human judgment | 51.0% |

## Config

| Setting | Value |
|---------|-------|
| Primary dataset | `AEI Both + Micro 2026-02-12` |
| Method | freq (time-weighted) |
| use_auto_aug | True |
| Geography | National |
| agg_level | occupation |

## Files

| File | Description |
|------|-------------|
| `figures/rate_comparison.png` | All 5 configs vs external benchmarks |
| `figures/layer_chart.png` | Dot plot spectrum |
| `results/automation_share_ours.csv` | Our 5 configs pct_agg |
| `results/external_benchmarks.csv` | External source values |
