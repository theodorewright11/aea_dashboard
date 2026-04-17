# Results

---

## Part 1 — Scale, Convergence, Growth

### The Overview

![Aggregate AI Economic Footprint](part_1/figures/overview.png)

As of February 2026, our primary configuration (confirmed AI usage across conversational and API channels, no MCP) puts 61.3 million workers in scope. That's 40.0% of U.S. employment and $3.99 trillion in annual wages. The ceiling, which extends confirmed data with MCP tool-use capability mapping, reaches 77.1 million workers, 50.3% of employment, $4.97 trillion. These aren't projections of future AI impact. They're measurements of what we observe in AI system logs right now, matched to standard occupational task records.

The five configurations are designed to ask the same question from different angles. The narrowest, agentic confirmed at 20.3%, captures only confirmed tool-use AI: the kind that requires workflow integration and API access rather than a chat session. Human conversational at 35.3% combines two independent chat-based sources: Anthropic's AEI conversational data (Claude sessions) and Microsoft's Copilot data (Bing Copilot sessions). Different products, different user populations, same interaction mode. A human typing to a chatbot, not code calling an API. The combined confirmed view (40.0%) adds AEI API-based usage on top of that conversational baseline: the agentic layer where AI operates programmatically rather than in conversation. The agentic ceiling at 39.4% gets to roughly the same number through a completely different route (tool-use capability mapping rather than usage logs). And the all-ceiling at 50.3% adds MCP on top of everything, capturing the full frontier of what current AI tools can demonstrably do.

That our ceiling (50.3%) lands right on top of Seampoint's independent estimate (51% of worker hours could be AI-augmented under governance constraints) is probably not a coincidence. Two frameworks built on entirely different data and methodology, both arriving at essentially the same number. The agentic-confirmed figure (20.3%) also matches Seampoint's takeover rate (20%), which is the fraction of tasks AI could handle without human involvement at all. When two independent approaches converge like that, it suggests they're both picking up on something real.

---

### The Convergence Argument

![Spearman ρ on % Tasks Affected](part_1/figures/convergence.png)

Big numbers are one thing. The more important question is whether they hold up when you measure the same phenomenon from genuinely different directions. The convergence chart makes a different argument than the scale chart: not *how much*, but *how confident*.

Four data sources go into the correlation analysis: Claude browser usage (AEI conversational), Claude API usage (AEI agentic), Microsoft Copilot task assessment, and MCP tool-use capability mapping. They're measuring related but genuinely different things. What people actually do in chat sessions, what developers build into API workflows, how an enterprise productivity tool assesses task overlap, and what thousands of AI tool integrations are functionally specified to do. At the major occupational category level, Spearman rank correlations (which measure whether two sources put occupations in the same order; 1.0 means identical ranking, 0 means no relationship) range from 0.79 to 0.98 across all six source pairs, mean of 0.85. That's strong agreement from sources that have no methodological reason to agree.

The two Claude-based sources (browser and API) track most closely at 0.98. Not surprising: same model architecture, overlapping user base, even though one measures chat and the other tool-calling. The weakest major-level pair is Copilot vs. Claude browser at 0.79. That's still a strong correlation. It means that when you rank the 22 major occupational categories by AI exposure in Microsoft's enterprise data versus Anthropic's conversational usage data, the rankings align closely despite entirely different platforms, methods, and user populations.

The agreement degrades as you zoom in. At the occupation level (923 categories), the mean falls to 0.64, the weakest pairs sit around 0.55. Zero occupations appear in the top 30 of all four sources simultaneously. This isn't a data quality problem. It's structural. Each source measures a different dimension of AI exposure, and those dimensions don't map to the same occupations even when they map to the same sectors. Sector-level findings carry high confidence. Occupation-level claims need source attribution.

Six major categories land in the high-exposure tier across all four sources: Computer and Mathematical, Office and Administrative Support, Sales, Business and Financial Operations, Arts and Design, and Life/Physical/Social Science. Ten major categories show consistently low exposure across every source: construction, farming, food prep, both healthcare groups, installation and maintenance, personal care, production, protective service, and transportation. The sources agree as strongly on what AI doesn't touch as on what it does, and that double consensus is the clearest signal the framework is tracking something real about which kinds of work current AI engages with.

---

### The Temporal Argument

![% of Employment with AI-Exposed Tasks Over Time](part_1/figures/temporal_trend.png)

In March 2025, the all-confirmed estimate put 46.6 million workers in scope, 30.4% of employment. By February 2026, it sits at 61.3 million workers and 40.0%. That's 14.7 million additional workers in eleven months. The jobs themselves haven't changed. AI has found more footholds in existing tasks.

The growth isn't smooth. In the confirmed series, the August 2025 dataset accounts for the biggest single jump: +10.1 million workers, +6.6 percentage points. November 2025 adds 3.4 million more. February 2026 adds 1.2 million. Each step is smaller than the last. Whether that's a genuine slowdown or just that this particular window hasn't caught the next wave of adoption, we can't tell from the data alone.

![All Confirmed](part_1/figures/temporal_table_all_confirmed.png)

The ceiling series follows a different path. Its earliest jump (April 2025, +12.6 million workers, +8.2 percentage points) came from the first MCP dataset being incorporated, not from adoption growth. MCP added a large tranche of task coverage all at once because it measures what AI tools can do, not what people are actually doing with them. Subsequent ceiling increments have been smaller. By the end of the window, the ceiling sits at 50.3% while confirmed sits at 40.0%: a roughly 10-percentage-point gap representing work that AI can demonstrably do but that hasn't shown up in confirmed usage yet.

![All Sources (Ceiling)](part_1/figures/temporal_table_all_ceiling.png)

The confirmed-to-ceiling ratio has been narrowing: 77% in August 2025, 80% by February 2026. Confirmed usage is growing slightly faster than the ceiling, meaning deployment is slowly catching up to demonstrated capability. Whether that gap continues to close, and how fast, depends on factors this data doesn't resolve: how much of the ceiling represents capability organizations will eventually deploy versus capability that stays theoretical.

---

## Part 2 — [TBD: Characterization]

*Content pending.*

---

## Part 3 — [TBD: Action]

*Content pending.*
