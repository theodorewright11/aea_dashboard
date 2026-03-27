# Question: What Is AI's Total Economic Footprint Across the US Economy?

How many workers, how many wage dollars, and what share of the total US economy does AI exposure represent — and how does the answer change depending on which data source, AI mode, and methodology you use?

This analysis runs the dashboard's compute pipeline across five distinct data source perspectives and four methodology toggles to produce a comprehensive picture of AI's economic reach. Rather than picking a single number, we show the **range** — because the gap between estimates is itself a finding.

---

## 1. The Range of Estimates: Between 26% and 35% of the US Workforce

The total economic footprint of AI depends on which data you trust. We compute three source perspectives:

| Source | Datasets | Workers Affected | % of Employment | Wages Affected | % of Wage Bill |
|--------|----------|-----------------|-----------------|---------------|---------------|
| **Current Usage** (floor) | AEI Cumul. (Both) v4 + Microsoft | 39.3M | 25.7% | $2,570B | 27.3% |
| **Capability Ceiling** (max) | AEI Cumul. (Both) v4 + MCP Cumul. v4 + Microsoft | 53.3M | 34.8% | $3,398B | 36.0% |
| **Combined** (best estimate) | Same three sources, averaged | 41.7M | 27.2% | $2,703B | 28.7% |

The floor (what AI is actually being used for today) says one in four workers. The ceiling (the maximum exposure any single source identifies per task, across all three data sources) says more than one in three. The 9.1 percentage-point gap between floor and ceiling — representing 14.0 million workers and $828 billion in wages — is the **unrealized adoption gap**: the difference between where AI is being used and the maximum exposure any source detects.

Our combined best estimate: **41.7 million workers (27.2% of US employment) perform work that overlaps with current AI capability, representing $2.7 trillion in annual wages (28.7% of the total wage bill).**

![Economy Overview](figures/economy_overview.png)

Note that the wage-weighted percentages (27.3–36.0%) slightly exceed the worker-weighted percentages (25.7–34.8%) across all sources, indicating that AI-exposed occupations tend to be somewhat higher-paid than average.

---

## 2. Where the Money Is: $2.7 Trillion in AI-Exposed Wages

The AI footprint is not evenly distributed. Three major categories alone account for over 40% of all AI-exposed wages:

| Rank | Major Category | Workers Affected | Wages Affected | % Tasks Affected |
|------|---------------|-----------------|---------------|-----------------|
| 1 | Management | 3.3M | $407B | 25.5% |
| 2 | Office and Administrative Support | 8.6M | $405B | 40.6% |
| 3 | Business and Financial Operations | 4.0M | $327B | 36.6% |
| 4 | Sales and Related | 5.7M | $272B | 44.7% |
| 5 | Computer and Mathematical | 2.7M | $269B | 52.2% |
| 6 | Healthcare Practitioners | 1.8M | $174B | 16.4% |
| 7 | Educational Instruction | 2.5M | $158B | 32.3% |

Management tops the wage impact ($407B) despite having a lower % tasks affected (25.5%) — the sheer size and high salaries of the management workforce make it the largest dollar-value exposure category. Office/Admin comes in second for wages but first for workers (8.6M), reflecting a massive workforce with moderate salaries and high task overlap with AI.

Computer and Mathematical occupations have the **highest task exposure rate** (52.2%) — more than half of all weighted task work in this sector overlaps with AI capability. But with 2.7M workers, it's only the 6th largest by absolute worker count.

![Treemap of Wages by Category](figures/treemap_wages.png)

The treemap shows this concentration visually: Management and Office/Admin dominate the wage picture, while Computer/Math is deeply colored (high % exposure) despite being a smaller box. Food Preparation, Transportation, and Healthcare Practitioners have large workforces but lighter coloring — AI reaches into these sectors but touches a smaller share of their tasks.

![Impact Scatter](figures/impact_scatter.png)

The impact scatter plot reveals the strategic landscape: the **upper-right quadrant** (high % tasks AND many workers) is where AI's economic impact concentrates. Office/Admin, Sales, and Business/Financial sit here — large workforces with substantial task overlap. Computer/Math is far right (highest % tasks) but lower (smaller workforce). Food Preparation and Transportation are high on workers but low on % tasks — large sectors where AI touches only a slice of the work.

---

## 3. The Uncertainty Range by Sector

For each major category, the gap between current usage (floor) and capability (ceiling) varies dramatically:

![Dumbbell Range Chart](figures/range_workers_major.png)

**Key patterns:**

- **Office/Admin** has the widest absolute range: 7.1M workers (usage) to over 11M (ceiling), a multi-million-worker gap. AI tools can reach deep into this sector but adoption hasn't caught up.
- **Sales** also shows a wide range, with the ceiling (max across all sources) extending well beyond current usage.
- **Computer/Math** shows a narrower range — sources broadly agree this sector is heavily AI-exposed, though the max ceiling still extends meaningfully beyond the combined estimate.
- **Education** has an unusual pattern where current usage approaches the ceiling more closely than most sectors, driven by strong conversational AI adoption (tutoring, writing assistance).
- **Construction, Farming, and Building Maintenance** show uniformly low exposure across all sources, with narrow ranges — these sectors are consistently insulated from AI.

---

## 4. Two Modes of AI: Agentic vs Conversational

We split the AI footprint by mode using cleanly separated data sources:

| AI Mode | Datasets | Workers Affected | % of Employment | Wages Affected | % of Wage Bill |
|---------|----------|-----------------|-----------------|---------------|---------------|
| **Agentic / Tool-use** | AEI API Cumul. v4 + MCP Cumul. v4 | 37.8M | 24.7% | $2,493B | 26.4% |
| **Conversational / Copilot** | AEI Cumul. Conv. v4 + Microsoft | 34.6M | 22.6% | $2,241B | 23.8% |

Agentic AI (tool-using, API-calling, autonomous AI) now slightly exceeds conversational AI (chatbots, copilots, writing assistants) — 37.8M vs 34.6M workers, a gap of 3.2M. This uses the cleanest possible data separation: the AEI cumulative API-only dataset captures tool-use conversations exclusively, while the AEI cumulative conversation-only dataset captures dialogue-based interactions with no API overlap.

The result is striking: **agentic AI's economic reach is larger than conversational AI's.** This challenges the assumption that chatbots and copilots are the dominant mode of AI impact. Tool-use and API-based AI — systems that take actions, access databases, and manipulate external resources — are touching a larger share of the workforce.

![Butterfly: Agentic vs Conversational](figures/agentic_vs_conversational.png)

The butterfly chart reveals the sector-by-sector picture:

- **Agentic AI leads** in Office/Admin, Sales, Computer/Math, Healthcare, Food Preparation, and Transportation — sectors where AI tools automate structured workflows, data processing, and operational tasks.
- **Conversational AI leads** in Education, Management, and Arts/Design/Entertainment — sectors where AI assists primarily through dialogue (tutoring, writing, creative brainstorming, advisory work).
- The split is close in Business/Financial Operations, where both modes contribute substantially.

The agentic vs conversational distinction matters for policy: agentic AI implies deeper integration into business processes (APIs, tool chains, automated workflows), while conversational AI is more surface-level (a person talking to a chatbot). Agentic adoption may be harder to reverse once embedded.

**Note:** The agentic and conversational datasets are now cleanly separated (API-only vs conversation-only AEI cumulative data), but they do not sum to the combined total because the combined group uses the full AEI Cumul. (Both) v4 dataset alongside MCP and Microsoft.

---

## 5. Source Agreement Across Sectors

The heatmap shows where data sources agree and disagree on AI exposure levels:

![Heatmap: Source Agreement](figures/heatmap_sources.png)

**Areas of strong agreement (dark across all columns):**
- **Computer/Math** (39–65% across sources): every data source sees high AI exposure here. Agentic (54%) is especially strong.
- **Office/Admin** (29–54%): consistently the most-exposed large sector by worker count.
- **Sales** (33–54%): broad agreement on substantial exposure, with agentic (46%) leading.

**Areas of disagreement:**
- **Education**: Current Usage shows 37% and Conversational reaches 34%, but Agentic only 37% — conversational AI (tutoring, writing help) is the primary driver here, though agentic tools have caught up more than expected.
- **Food Preparation**: Agentic (12%) is notably lower than conversational (21%) — tool-based AI has limited application in this sector.
- **Healthcare**: Moderate across sources (13–18%), with agentic (13%) and conversational (15%) both present — tools are slowly penetrating clinical workflows.

---

## 6. Physical vs Non-Physical Work

Excluding physical tasks dramatically changes the picture:

| Physical Mode | Workers Affected | % of Economy | Ratio to All Tasks |
|--------------|-----------------|-------------|-------------------|
| All Tasks | 41.7M | 27.2% | 1.0× |
| Non-Physical Only | 50.8M | 33.2% | 1.22× |
| Physical Only | 30.1M | 19.7% | 0.72× |

![Physical Comparison](figures/physical_comparison.png)

When we remove physical tasks from the calculation, AI exposure jumps to **33.2%** — one-third of the economy. Non-physical (cognitive, informational, communicative) work is **1.7× more AI-exposed** than physical work (33.2% vs 19.7%).

This matters for policy: occupations that are primarily cognitive face meaningfully higher AI overlap. The 27.2% "all tasks" number blends physical and non-physical work together, masking the intensity of exposure for desk workers, knowledge workers, and service workers in non-physical roles.

---

## 7. Methodology Sensitivity: How Much Does the Approach Matter?

The auto-aug toggle is the single biggest methodological lever:

| Config | Workers Affected | % of Economy |
|--------|-----------------|-------------|
| Primary (Time, Auto-aug ON) | 41.7M | 27.2% |
| Value Method (Auto-aug ON) | 42.7M | 27.9% |
| Auto-aug OFF | 69.8M | 45.5% |
| Max Exposure (Value, Aug OFF) | 70.9M | 46.2% |

![Toggle Sensitivity](figures/toggle_sensitivity.png)

**The auto-aug toggle nearly doubles the footprint.** With auto-aug ON (the primary config), each task's contribution is scaled by how automatable AI rates it (0–5 scale, divided by 5). Turning it off treats every AI-flagged task as fully automatable — the "maximum possible exposure" scenario. This jumps from 27.2% to 45.5%, adding 28.1M workers.

The interpretation: **27.2% is the quality-adjusted footprint** (tasks weighted by how well AI can actually handle them), while **45.5–46.2% is the raw coverage** (every task AI has touched, regardless of quality). The gap between these — 18.3 percentage points, 28M workers — represents work where AI has some capability but limited practical impact.

**Time vs Value method barely matters** (27.2% vs 27.9%). Whether you weight tasks by frequency alone or by frequency × relevance × importance, the total footprint changes by less than 1 percentage point. This is reassuring: the findings aren't an artifact of the weighting methodology.

**Robustness: All 10 top major categories are stable across all 4 toggle combinations.** The same sectors dominate AI exposure regardless of how you slice the methodology. This is the strongest robustness result possible.

---

## 8. How Automatable Is American Work?

The employment-weighted average auto-aug score across all occupations is **2.08 out of 5** — moderate automatability. More than half of American workers (56.1%) are in occupations with an average score of 2.0 or higher.

![Auto-aug Distribution](figures/autoaug_distribution.png)

The distribution is roughly bell-shaped with a peak in the 2.0–2.5 range (34.8M workers). This means the largest single group of workers is in occupations with **moderate AI automatability** — not trivially automatable, not immune, but squarely in the zone where AI can assist meaningfully.

The tails are informative:
- **Low automatability (0–1.0)**: 22.8M workers in occupations where AI capability is minimal. These are the most insulated from AI disruption.
- **High automatability (3.0–5.0)**: 27.4M workers in occupations where AI scores indicate strong capability. These are where restructuring pressure will be highest.

---

## 9. Task Coverage Across the Economy

Of the 17,507 unique tasks in the O*NET 2025 taxonomy, **12,261 (70.0%) have been rated by at least one AI source.** This means AI data sources have assessed the automatability of 70% of all distinct work activities in the US economy. The remaining 30% have no AI rating — either because AI hasn't been applied to those tasks or because the tasks don't appear in the AI conversation/tool logs.

---

## 10. National vs Utah

Utah's AI exposure profile is essentially identical to the national average:

| Geography | Workers Affected | % of Employment |
|-----------|-----------------|-----------------|
| National | 41.7M | 27.2% |
| Utah | 628K | 27.4% |

The 0.2 percentage-point difference is negligible. Utah's occupational mix is similar enough to the national average that AI exposure doesn't meaningfully differ. This is relevant for Utah OAIP: national findings can be applied to the Utah context with high confidence.

---

## 11. Key Takeaways

1. **Between 26% and 35% of the US workforce is AI-exposed** depending on whether you measure current usage (floor) or the maximum across all sources (ceiling). Our best combined estimate is **27.2% — 41.7 million workers and $2.7 trillion in wages.**

2. **The $828B gap between floor and ceiling** (14.0M workers) represents the range between confirmed AI usage and the maximum exposure any source detects.

3. **Three sectors account for 42% of all AI-exposed wages**: Management ($407B), Office/Admin ($405B), and Business/Financial ($327B). Computer/Math has the highest intensity (52% of tasks) but a smaller workforce.

4. **Agentic AI now slightly exceeds conversational AI** in total reach (37.8M vs 34.6M workers). With cleanly separated data, tool-use and API-based AI touches more of the workforce than chat-based AI — a finding that challenges common assumptions about how AI impacts work.

5. **Non-physical work is 1.7× more AI-exposed** than physical work. The true exposure for cognitive workers is 33.2%, not 27.2%.

6. **The auto-aug toggle is the biggest methodology lever** — turning it off nearly doubles exposure from 27% to 46%. This separates "quality-adjusted" exposure from "raw AI coverage."

7. **The top 10 major categories are perfectly stable** across all methodology toggles. The story doesn't change with the approach.

8. **The average American worker's tasks score 2.08/5 on automatability.** 56% of workers are in occupations scoring >= 2.0.

9. **70% of all O*NET tasks** have been assessed by at least one AI source.

10. **Utah ≈ National** — exposure profiles are nearly identical.

---

## Config

Primary: AEI Cumul. (Both) v4 + MCP Cumul. v4 + Microsoft | Average | Time | Auto-aug ON | National | All tasks | Major category. Ceiling uses Max. Agentic: AEI API Cumul. v4 + MCP Cumul. v4. Conversational: AEI Cumul. Conv. v4 + Microsoft. Sensitivity: Auto-aug OFF, Value method, Physical split, Utah geography.

## Files

| File | Description |
|------|-------------|
| `economy_totals.csv` | Headline numbers per source group |
| `major_combined.csv` | Major category breakdown (combined sources) |
| `major_current_usage.csv` | Major category breakdown (usage floor) |
| `major_capability_ceiling.csv` | Major category breakdown (capability ceiling) |
| `major_agentic.csv` | Major category breakdown (agentic AI) |
| `major_conversational.csv` | Major category breakdown (conversational AI) |
| `physical_comparison.csv` | All vs non-physical vs physical-only totals |
| `toggle_sensitivity.csv` | Exposure under 4 toggle combinations |
| `nat_vs_utah.csv` | National vs Utah comparison |
| `autoaug_summary.csv` | Auto-aug economy-wide metrics |
| `task_coverage.csv` | O*NET task coverage by AI sources |
