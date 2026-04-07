*Config: All Confirmed (primary) + All Ceiling | Method: Freq | Auto-aug ON | National | Major sectors*

Across every source — our dashboard, Copilot enterprise data, AEI task-attempt analysis, and ChatGPT work sessions — three sector clusters keep coming up: information-heavy professional services (Computer/Math, Business/Finance), administrative coordination work (Office/Admin), and customer-facing roles (Sales). The convergence isn't accidental: these are the sectors where work is predominantly verbal, written, informational, and non-physical. The fact that five independent measurement approaches all point to them is strong cross-validation.

*Full detail: [sector_breakdown_report.md](sector_breakdown_report.md)*

## Our Sector Rankings

![Top 10 sectors by workers affected (all_confirmed)](../questions/field_benchmarks/sector_breakdown/figures/our_sector_rankings.png)

Our primary config (all_confirmed) puts Office and Administrative Support at the top by raw worker count (11.2M, 51.1% exposure), followed by Sales (7.6M, 59.5% — highest rate of any large sector), then Business/Finance (5.5M, 50.7%) and Food Prep (4.9M, 35.6%). Food Prep's presence reflects the number of workers, not high individual exposure — many food service tasks are physical. The rate-weighted view is where the alignment with external sources becomes clearest.

## AEA Dashboard vs. Copilot

![Cross-source sector comparison: our pct vs Copilot applicability](../questions/field_benchmarks/sector_breakdown/figures/cross_source_sectors.png)

Copilot's enterprise analysis identifies the same top three sectors — Sales (~52% applicability), Computer/Math (~50%), Office/Admin (~49%) — with nearly identical rank order to our pct_tasks_affected rates for those sectors. Our all_confirmed rates for these sectors are 59.5% (Sales), ~67% (Computer/Math), and 51.1% (Office/Admin). Our rates are slightly higher on average, consistent with confirmed usage breadth being wider than Copilot's task-applicability framing (which focuses on whether Copilot can meaningfully assist with a task, not all AI touchpoints).

## AEI and ChatGPT Task Categories

![External sources: AEI task categories and ChatGPT work-use types](../questions/field_benchmarks/sector_breakdown/figures/external_task_breakdown.png)

AEI's task-attempt data shows that Computer & Mathematical work (technical problem-solving) dominates Claude conversation usage at ~37% of task-attempts — this maps directly to our Computer/Math sector having the highest pct_tasks_affected rate. Writing tasks at ~22% map to Office/Admin and cross-sector administrative work. ChatGPT's work-session data shows Writing at 40% and Practical Guidance at 24%, which maps to the same informational-professional cluster. The underlying activity types — document production, analysis, information retrieval — are consistent across all sources.

## What Diverges

Food Preparation is in our top 10 by worker count (4.9M) but absent from Copilot's applicability rankings, because exposure-by-worker-count and sector applicability are different questions. Copilot is measuring how applicable its tools are in a given sector; we're showing how many workers in each sector have AI touching their tasks. A sector with many workers and moderate exposure will rank high on the worker-count view even if the per-worker rate is modest.

Healthcare and Community/Social Services also show moderate exposure in our data that doesn't appear prominently in other sources — likely because those sources focus on software-tool usage, while our confirmed data captures AI usage in care coordination, documentation, and administrative healthcare tasks.

## Key numbers

| Sector | Our pct (confirmed) | Copilot applicability |
|--------|--------------------|-----------------------|
| Sales | 59.5% | ~52% |
| Computer & Math | ~67% | ~50% |
| Office/Admin | 51.1% | ~49% |
| Business/Finance | 50.7% | ~44% |
| Management | 35.5% | ~41% |

## Config

| Setting | Value |
|---------|-------|
| Primary dataset | `AEI Both + Micro 2026-02-12` |
| Method | freq (time-weighted) |
| use_auto_aug | True |
| Geography | National |
| agg_level | major |

## Files

| File | Description |
|------|-------------|
| `figures/our_sector_rankings.png` | Top 10 sectors by workers_affected |
| `figures/cross_source_sectors.png` | Our pct vs Copilot applicability |
| `figures/external_task_breakdown.png` | AEI and ChatGPT task-type distributions |
| `results/sector_confirmed.csv` | Our sector data |
| `results/copilot_sector_data.csv` | Copilot applicability rates |
| `results/aei_task_categories.csv` | AEI task distribution |
| `results/chatgpt_work_categories.csv` | ChatGPT work use types |
