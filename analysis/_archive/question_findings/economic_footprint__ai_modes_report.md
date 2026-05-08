# Economic Footprint: AI Modes

Confirmed agentic tool-use (AEI API only) reaches 31.1 million workers — narrower than the 54.1 million reached by conversational AI. The gap reflects a real difference in deployment patterns: API-based agentic usage is currently more specialized than broad conversational AI adoption. But the agentic ceiling — adding MCP server capability data — pushes the count to 60.4 million, which exceeds conversational. The gap between confirmed agentic (31.1M) and ceiling agentic (60.4M) is where the next wave lives. Auto-augmentability scores are uniformly high: 97.7% of workers are in occupations with meaningful AI augmentation potential (score >= 2 on a 5-point scale), with a weighted mean of 2.82 across the full workforce.

---

## Conversational vs. Agentic: The Size of the Difference

Three configs capture the mode split:

- **All Confirmed**: 61.3M workers, $3.99T wages
- **Human Conversation (confirmed)**: 54.1M workers, $3.47T wages
- **Agentic Confirmed (AEI API only)**: 31.1M workers, $2.16T wages

The conversational number reflects what AI is doing when people interact with it directly — asking questions, getting help drafting, analyzing documents. Agentic confirmed (AEI API) is what AI is doing when it's given tools and takes autonomous actions — calling APIs, running code, managing workflows. These are different deployment patterns, and the numbers show they reach different jobs.

The 23M worker gap between conversational and confirmed agentic reflects the structure of current deployment: agentic tool-use via API is concentrated in higher-skill, higher-complexity occupations, while conversational AI is already embedded broadly across the information economy. This isn't a capability story — it's a deployment story. Agentic systems are capable of reaching more; they just haven't been deployed that broadly yet.

The agentic ceiling (MCP + AEI API combined) at 60.4M workers shows what agentic AI could reach if MCP-based tooling were as widely deployed as conversational tools. That number exceeds conversational (54.1M), which means the potential of agentic AI is already above the current conversational baseline — the gap is organizational deployment, not technical limitation.

The wage gap between agentic confirmed and conversational is substantial: $2.16T vs. $3.47T, a $1.3T difference in wages of workers reached. That gap is almost entirely in occupations where conversational AI has broad reach but agentic deployment hasn't followed.

---

## What Changes Between Modes

The GWA-level data shows where the modes diverge most sharply.

**Documenting/Recording Information**: 29.6% (conversational) vs. 31.3% (agentic). These are nearly identical. Documentation tasks appear in the AEI API workflow data at roughly the same rate as in conversational usage — the difference is where it shows up, not how much.

**Performing Administrative Activities**: 55.0% (conversational) vs. 25.1% (agentic). Administrative tasks are actually higher under conversational AI — drafting, composing, responding, and organizing are primarily communicative activities that conversational AI covers well. API-based agentic usage captures the action layer but doesn't dominate the drafting layer.

**Scheduling Work and Activities**: 27.7% (conversational) vs. 37.9% (agentic). Scheduling ticks up under agentic — multi-step calendar management is more naturally agentic than conversational — but the difference is modest.

**Getting Information**: 48.8% (conversational) vs. 29.7% (agentic). Getting information is substantially higher under conversational. Information retrieval through natural-language conversation is where AI is most confirmed and most broadly deployed. Agentic API usage for "getting information" is more specialized — querying structured systems, not answering questions.

**Analyzing Data or Information**: 50.5% (conversational) vs. 34.8% (agentic). Similar pattern to Getting Information — analytical work is heavily conversational-first in current deployment.

The broad pattern: activities that are communicative, interpretive, and analytical are currently higher under conversational AI. Activities requiring multi-step workflows or direct system access (scheduling, some documentation) are where agentic modestly leads. The confirmation data from AEI API reflects where agentic has been specifically deployed — high-complexity technical contexts — not the full breadth of what agentic could reach.

![Agentic vs. Conversational Worker Counts by Sector](figures/agentic_vs_conversational.png)

---

## Where the Deployment Gap Is Largest

The drop in workers affected from conversational to agentic — ranked by sector — shows where agentic deployment most lags conversational reach. Sectors with the largest drops are where conversational AI is broadly embedded but agentic tool-use hasn't followed.

![Worker Reach Drop: Conversational to Agentic](figures/agentic_workers_drop.png)

The same pattern through the lens of task penetration: the drop in pct_tasks_affected from conversational to agentic shows which sectors lose the most task coverage when moving to tool-use-only.

![Task Penetration Drop: Conversational to Agentic](figures/agentic_pct_drop.png)

---

## Auto-Augmentability

Auto-augmentability is a different angle. Rather than asking "can AI do this task," it asks "how well can AI assist a worker doing this task" — a measure of collaboration potential rather than replacement risk.

The score is on a 1-5 scale, where 1 means minimal augmentation potential and 5 means AI can substantially amplify the worker's output. Across the full affected workforce:

- **Weighted mean auto-augmentability**: 2.82 / 5.0
- **Workers in occupations with score >= 2**: 97.7%

97.7% is a striking number. Almost every worker in an AI-affected occupation is in a role where AI can meaningfully assist them — not just marginally, but genuinely augment their output. The distribution is overwhelmingly concentrated in the 2-3 range rather than at the extremes, which suggests a broad middle tier of "AI can help but isn't going to replace" across the economy's affected occupations.

A score of 2.82 out of 5 means we're at roughly mid-range augmentation potential across the board. There's substantial room to move up the scale as AI systems improve — particularly for the tasks currently at the boundary between "AI can assist" and "AI can complete autonomously." That boundary has been moving toward the latter for the past two years.

The by-major-sector breakdown of auto-augmentability scores generally tracks the task penetration findings: Computer/Mathematical and Business/Financial show the highest augmentability scores; physically-grounded sectors like Transportation and Construction show lower scores. But the within-sector variance is worth noting — even in sectors with lower average exposure, there are high-augmentability occupations. The administrative and information-processing layer of every sector carries higher augmentability than the hands-on layer.

![Auto-Augmentability Distribution Across Affected Workforce](figures/autoaug_distribution.png)

![Avg Auto-Aug Score by Sector — All Confirmed](figures/autoaug_by_major.png)

### Auto-Aug Across Dataset Configs

Two ways to look at auto-augmentability across configs:

**Tasks with AI score**: average auto_aug_mean across unique tasks that appear in the AI dataset and have a score. This shows how automatable the tasks AI has actually assessed are.

**Over all eco tasks**: average auto_aug_mean across all unique tasks in the eco baseline (eco_2025 for most configs; eco_2015 for Agentic Confirmed, which uses the AEI baseline). Tasks not in the AI dataset count as 0. This shows AI's coverage footprint — a sector with many tasks untouched by AI will score lower here even if its assessed tasks are highly automatable.

![Avg Auto-Aug by Sector × Config — Tasks With AI Score](figures/autoaug_by_config_with_vals.png)

![Avg Auto-Aug by Sector × Config — Over All Eco Tasks](figures/autoaug_by_config_all.png)

---

## Reading the Mode Gap as a Forward Indicator

The 23M worker gap between conversational confirmed (54.1M) and agentic confirmed (31.1M) is not primarily a capability gap — it's a deployment gap. The agentic ceiling at 60.4M demonstrates that agentic AI has already demonstrated capability across a broader set of tasks than current AEI API usage reflects.

The confirmed agentic number (AEI API) captures deployments where agentic tooling is actually in use — production environments, developer workflows, complex automation pipelines. These are higher-complexity use cases than the broad conversational AI baseline. As agentic infrastructure matures and enterprise deployments scale, the occupational coverage of confirmed agentic usage will expand toward the ceiling.

The gap between agentic ceiling (60.4M) and agentic confirmed (31.1M) is 29.3M workers — occupations where agentic capability has been demonstrated but confirmed deployment hasn't reached them. By comparison, the conversational confirmed/ceiling gap is smaller, because conversational AI deployment is more mature. Agentic AI is at an earlier point on the adoption curve: high ceiling, lower confirmed floor, with a wide deployment gap that organizational decisions will close over time.

The implication: the next major wave of measured AI impact will likely come from the agentic layer expanding its confirmed footprint. As agentic tools become standard deployment rather than specialized infrastructure, the AEI API numbers will grow toward the ceiling. That's a path from 31M to 60M workers — roughly doubling — without any new AI capability being required.
