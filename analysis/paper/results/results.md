# Results

---

## Part 1 — AI Is In The Workforce

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

### External Convergence

![Spearman ρ — Our Sources vs. External Benchmarks](part_1/figures/convergence_external.png)

Internal agreement is one check. A more stringent test is whether our ranking of occupations lines up with independent academic work built on entirely different methodology. Two well-known exposure indices fit that description. Eloundou, Manning, Mishkin, and Rock (2023, "GPTs are GPTs") scored every O*NET occupation on a 0–1 LLM-exposure rubric, once by GPT-4 and once by a human panel; we use the β variant (E1 + 0.5·E2), which their paper treats as the primary measurement. Felten, Raj, and Seamans' AIOE is an older, ability-based index: it scores occupations by how overlapping their O*NET abilities are with a set of AI applications from a 2018 MTurk survey. We use the 10-application row mean (original AIOE framing) and the Reading Comprehension column alone (the one most closely aligned to modern LLMs). Neither index was built with the same task data, the same scoring model, or the same time window as ours. If our rankings agreed with these, it would be because all four approaches were picking up on the same underlying structure, not because of shared inputs.

The rankings do agree. At the major category level, the sixteen cells (four internal sources × four external benchmarks) have a mean Spearman ρ of 0.83, with a range of 0.67 to 0.93. That's essentially the same agreement strength we saw for our four sources against each other (mean 0.85). The degradation-with-granularity pattern holds here too: at the occupation level (n ≈ 900), the mean drops to 0.64 across the sixteen cells, range 0.52 to 0.77. Same shape as the internal chart, same magnitudes.

The strongest row is MCP, which agrees most closely with Eloundou's ratings (0.92 with GPT-4 β, 0.93 with Human β at major; 0.77 and 0.73 at occupation). This makes sense given what each thing measures: MCP captures what AI tools can functionally do (tool integration specs), and the Eloundou rubric scores capability overlap with LLMs. Both are assessments of potential exposure, not observed usage. The weakest row is Copilot, which runs 0.67–0.78 at major and drops to 0.52–0.64 at occupation. That's the row where Microsoft's enterprise assessment disagrees most with the academic benchmarks. It still correlates strongly in an absolute sense, but Copilot's signal comes from inside Microsoft's own productivity-software lens, and that lens weights differently from either the Eloundou rubric or the AIOE ability profile. It's also worth noting that AIOE Reading Comprehension correlates with our sources about as well as AIOE mean does, sometimes slightly better. For modern LLM-era exposure ranking, the single reading-comprehension column carries more of the signal than an average that includes nine older AI applications.

The upshot: two research groups using completely different scoring frameworks (GPT-4 and human judgment on exposure rubrics; ability-to-AI-application overlap) arrived at rankings that look like ours. Our framework is reproducing a structural pattern that independent academic work has already found, not an artifact of the specific data sources or methodology we used.

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

## Part 2 — Where Is AI In The Workforce

### The Physical/Informational Divide

![Physical/Informational Divide](part_2/figures/phys_info_divide.png)

The most basic structural question about AI exposure is whether it respects the divide between physical and informational work. It does, and it's not subtle. Occupations where fewer than a third of tasks are physical (393 occupations, roughly 43% of the total) have a median AI task exposure of 48.1%. Occupations where more than two-thirds of tasks are physical (310 occupations) sit at 17.2% median. Mixed occupations (220, those in the 33-67% physical range) land at 33.0%. The interquartile ranges barely overlap: non-physical occupations' Q1 (33.6%) is above the physical group's Q3 (26.7%).

This isn't a finding about AI preferring white-collar work in some vague sense. It's a measurement of where current AI systems are actually being used. The data comes from confirmed conversation logs, API usage, and enterprise assessment, not from theoretical capability scoring. When real people and real systems interact with AI to accomplish work tasks, the tasks they're accomplishing are overwhelmingly informational. The physical occupations that do show up with moderate exposure (the outliers reaching 50-60% in the box plot) tend to be ones where the informational component of the job is substantial despite the physical classification (think supervisory roles in construction or equipment inspection).

---

### Job Zone and Preparation Level

![Job Zone Violin](part_2/figures/job_zone_violin.png)

Job zone is O*NET's classification of how much preparation an occupation requires: Zone 1 is little or no preparation, Zone 5 is extensive (think physicians, lawyers, senior engineers). The relationship between preparation level and AI exposure is not linear, and the shape matters.

Zone 1 (33 occupations) sits at a median of 13.3%. Zone 2 (298 occupations) at 20.0%. Zone 3 (213) at 30.4%. Then the curve flattens: Zone 4 (225 occupations, considerable preparation) hits 47.0% median, and Zone 5 (154, extensive preparation) also sits at 47.0%. The means tell a slightly different story (Zone 5 at 49.1% vs Zone 4 at 47.4%) because Zone 5 has a heavier right tail, with more occupations pushed above 60%.

The finding worth sitting with is that AI exposure peaks in the occupations that require the most education and training, not the least. This runs counter to the popular framing of AI as a threat primarily to low-skill work. The occupations most affected are the ones where workers have invested the most in specialized preparation. Whether that exposure represents augmentation or substitution risk depends on factors this data doesn't resolve, but the structural pattern is clear: current AI capability overlaps most heavily with the tasks performed by the most educated workers.

---

### SKA Levels: AI Capability vs. Workforce Requirements

![SKA Levels](part_2/figures/ska_levels.png)

The SKA (Skills, Knowledge, Abilities) chart asks a different question than the exposure metrics. Instead of "what percentage of tasks does AI touch," it asks "for each specific skill, knowledge domain, or ability that occupations require, how does AI's demonstrated capability compare to what the workforce actually needs?"

The answer depends heavily on which domain you're looking at. In knowledge (33 elements), AI's maximum demonstrated capability exceeds the economy-wide average requirement for 88% of elements. Education and Training leads at 86% of workforce max, followed by Computers and Electronics (80%) and Engineering and Technology (83%). The bottom of the knowledge chart is exclusively physical-world domains: Food Production, Production and Processing, Mechanical. AI knows a lot about a lot of things, but its knowledge advantage is concentrated in informational and analytical domains.

Skills (35 elements) show a more mixed picture: 71% of elements have AI max above economy mean. Writing leads (87% of workforce max), followed by Mathematics (71%) and Learning Strategies (83%). The bottom cluster is entirely hands-on: Installation (27%), Repairing (32%), Equipment Selection (58%). The physical/informational divide from the first chart shows up again here at the element level.

Abilities (52 elements) are where AI's reach is most limited. Only 44% of ability elements have AI max above the economy mean. Mathematical Reasoning leads (71% of workforce max), but most physical and perceptual abilities (Sound Localization at 9%, Night Vision at 15%, Peripheral Vision at 16%) are near zero. This makes sense: abilities represent the underlying capacities that make tasks possible, and many of those capacities are fundamentally embodied.

The workforce reference markers (P95 ticks, top-10 diamonds, economy mean circles) provide the context that makes these numbers interpretable. An AI capability at 70% of workforce max sounds high until you see that the P95 marker (what the top practitioners in the economy actually need) is at 85%. The gap between AI capability and what the most demanding occupations require remains substantial across most elements, even where AI clearly exceeds the typical requirement.

---

### Work Activity Exposure

![GWA Exposure](part_2/figures/gwa_exposure.png)

The General Work Activity classification breaks down all occupational work into 41 categories (technically 37 with non-zero values in the data). This chart shows what kinds of work AI is touching, ranked by % tasks affected. The color gradient maps to workers affected, so darker bars represent activities where AI exposure is both deep (high percentage) and wide (many workers).

The top cluster is informational and communicative: Updating and Using Relevant Knowledge (72.0%), Interpreting the Meaning of Information for Others (70.0%), Communicating with People Outside the Organization (69.6%), Working with Computers (69.3%). These are activities where AI has found the deepest footholds. The bottom cluster is physical and mechanical: Operating Vehicles (1.4%), Performing General Physical Activities (12.2%), Controlling Machines and Processes (12.7%).

But exposure percentage is only half the story, which is why the worker and wage annotations matter. Performing Administrative Activities ranks 8th by % tasks affected (58.7%) but reaches 3.8 million workers and $170B in wages. Making Decisions and Solving Problems sits at 52.8% but touches 3.6 million workers and $262B. These are activities embedded across nearly every occupation, so even moderate percentage exposure translates to massive economic scale.

The darkest bars (most workers) aren't always at the top. Handling and Moving Objects is only at 18.1% but represents 4.7 million workers, because so many occupations involve at least some material handling. The chart's color gradient makes these pockets visible in a way that a pure percentage ranking would miss.

---

### Major Occupational Categories

![Major Categories](part_2/figures/major_categories.png)

The three-panel view of all 22 major occupational categories shows the three metrics side by side: percentage of tasks affected, total workers in scope, and total wages in scope. Each panel tells a different part of the story, and the categories that lead on one metric don't necessarily lead on the others.

Computer and Mathematical occupations lead on % tasks affected at 65.7%, but rank 8th in workers (3.3M) and 5th in wages ($331B) because the sector is relatively small. Sales occupations rank 2nd on % tasks affected (59.5%) and jump to 2nd in workers (7.6M) because the sector is large. Office and Administrative Support ranks 4th on % tasks (51.1%) but 1st in workers (11.2M) and 2nd in wages ($533B) because it's the largest major category in the economy.

Management Occupations present an interesting case. At 35.5% task exposure, they rank 12th on percentage, below the median. But because management positions carry high wages, they rank 1st in wages affected ($614B) and 5th in workers (4.8M). AI exposure in management roles represents a relatively small share of the work but an outsized share of the economic value.

The bottom of all three panels converges: Farming, Fishing, and Forestry (13.7%, 41K workers, $1.7B wages) and Construction and Extraction (13.9%, 1.3M workers, $85.6B) consistently rank at or near the bottom. These are sectors where the work is fundamentally physical, and current AI systems have minimal demonstrated overlap with their task profiles.

---

## Part 3 — Action: What To Do About It

### The 12 Properties Collapse to ~2 Dimensions

![Property Biplot](part_3/figures/property_biplot.png)

*Prose pending.*

---

### For Organizations

#### Tech Commodities Where AI Has Reach

![Tech Commodities](part_3/figures/tech_commodities.png)

*Prose pending.*

#### Conversational vs. Agentic Footprint

![Conversational vs Agentic](part_3/figures/conv_vs_agentic.png)

*Prose pending.*

#### The Gap Between Confirmed Use and Demonstrated Capability

![Gap to Ceiling](part_3/figures/gap_to_ceiling.png)

*Prose pending.*

---

### For Policy

#### Risk × Recovery (Option A — 8-Flag Risk vs. SKA Gap)

![Risk x SKA](part_3/figures/risk_x_ska.png)

*Prose pending.*

#### Risk × Recovery (Option B — Exposure vs. Offset Properties)

![Pct x nt+de](part_3/figures/pct_x_nt_de.png)

*Prose pending.*

#### Frictions Discriminate Within Non-Physical Work

![Phys/Info + Frictions](part_3/figures/phys_info_frictions.png)

*Prose pending.*

---

### For Individuals

#### Where Humans Still Lead: Tacit Knowledge and Task Duration

![Tacit Knowledge x Duration](part_3/figures/tacit_duration_safe.png)

*Prose pending.*

---

### The Augmentation-Regime Caveat

*Prose pending. Note: t and freq_mean are inversely related (Spearman ρ ≈ −0.32); long-duration tasks happen less frequently. This affects how × t weighting compares to × freq weighting and is a methodological footnote on the charts above.*
