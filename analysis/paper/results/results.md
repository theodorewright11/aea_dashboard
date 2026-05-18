# Results

---

## Part 1 — AI Is In The Workforce

### External Benchmark Comparison — by AI Source

![External Benchmark Comparison — Source-level, Major](part_1/figures/convergence_major.png)

![External Benchmark Comparison — Source-level, Occupation](part_1/figures/convergence_occ.png)

*Prose pending update for new chart.*

---

### External Benchmark Comparison — by Data Configuration

![External Benchmark Comparison — Config-level, Major](part_1/figures/convergence_configs_major.png)

![External Benchmark Comparison — Config-level, Occupation](part_1/figures/convergence_configs_occ.png)

*Prose pending.*

---

### AI Economic Exposure Across Data Configurations

![AI Economic Exposure Across Data Configurations](part_1/figures/overview.png)

As of February 2026, our primary configuration (confirmed AI usage across conversational and API channels, no MCP) puts 61.3 million workers in scope. That's 40.0% of U.S. employment and $3.99 trillion in annual wages. The ceiling, which extends confirmed data with MCP tool-use capability mapping, reaches 77.1 million workers, 50.3% of employment, $4.97 trillion. These aren't projections of future AI impact. They're measurements of what we observe in AI system logs right now, matched to standard occupational task records.

The five configurations are designed to ask the same question from different angles. The narrowest, agentic confirmed at 20.3%, captures only confirmed tool-use AI: the kind that requires workflow integration and API access rather than a chat session. Human conversational at 35.3% combines two independent chat-based sources: Anthropic's AEI conversational data (Claude sessions) and Microsoft's Copilot data (Bing Copilot sessions). Different products, different user populations, same interaction mode. A human typing to a chatbot, not code calling an API. The combined confirmed view (40.0%) adds AEI API-based usage on top of that conversational baseline: the agentic layer where AI operates programmatically rather than in conversation. The agentic ceiling at 39.4% gets to roughly the same number through a completely different route (tool-use capability mapping rather than usage logs). And the all-ceiling at 50.3% adds MCP on top of everything, capturing the full frontier of what current AI tools can demonstrably do.

That our ceiling (50.3%) lands right on top of Seampoint's independent estimate (51% of worker hours could be AI-augmented under governance constraints) is probably not a coincidence. Two frameworks built on entirely different data and methodology, both arriving at essentially the same number. The agentic-confirmed figure (20.3%) also matches Seampoint's takeover rate (20%), which is the fraction of tasks AI could handle without human involvement at all. When two independent approaches converge like that, it suggests they're both picking up on something real.

---

### All Confirmed vs All Sources (Ceiling) Over Time

![All Confirmed vs All Sources (Ceiling) Over Time](part_1/figures/temporal_trend.png)

In March 2025, the all-confirmed estimate put 46.6 million workers in scope, 30.4% of employment. By February 2026, it sits at 61.3 million workers and 40.0%. That's 14.7 million additional workers in eleven months. The jobs themselves haven't changed. AI has found more footholds in existing tasks. *Prose pending refresh against the new tasks/workers/wages panels.*

![Tasks rated and AI capability over time](part_1/figures/temporal_tables.png)

---

## Part 2 — Where Is AI In The Workforce

### Major Occupational Categories (with Physical / Non-Physical Structural Lens)

![Major Categories — Variants A, B, All Confirmed](part_2/figures/major_categories.png)

Part 2 opens at major-cat granularity rather than the old occupation-bucket box plot, with the physical / non-physical structural cut threaded directly into the chart. The five panels read left to right as: **Variant A** — the naive non-physical task share per major (no AI signal at all, just a freq-weighted ratio of how much of a major's task time is non-physical); **Variant B** — % tasks exposed restricted to non-physical tasks on both sides of the calculation; then the **All Confirmed** trio of % tasks / workers / wages. The major-by-major n_occs by physical-bucket counts appear in the subtitle so the underlying distribution stays in view.

Reading across the panels surfaces the structural-vs-discriminatory split: a major where Variant A and All Confirmed sit close together (Computer/Math, Business/Finance) is one where the AI exposure reading basically tracks the structural cognitive share. A major where Variant B and All Confirmed are similar but Variant A is much lower (Healthcare Support, Building & Grounds Cleaning) is one where AI exposure on the small cognitive sub-economy of the major is high, even though the major as a whole is dominated by physical work.

---

### Major Occupational Categories — 2-Year Trend Projection

![Major Categories Trend](part_2/figures/major_categories_trend.png)

Per-metric top 10 movers ranked by absolute observed change first → final snapshot. Solid bar = current Feb 2026 value; faint hatched extension = 2-year linear OLS projection. The projection is a "if recent rate continues" thought experiment, not a forecast; the 4-snapshot input series doesn't support richer growth models at this horizon.

---

### Job Zone and Preparation Level

![Job Zone Violin](part_2/figures/job_zone_violin.png)

The right-side stacked bar shows the share of each zone's occupations that are Physical / Mixed / Non-Physical, making the structural composition of each zone visible alongside its exposure distribution.

![Job Zone Violin — Non-Physical Occupations Only](part_2/figures/job_zone_violin_nonphys.png)

Restricting the same chart to occupations with `pct_physical < 33%` tests whether the zone signal is just a phys/non-phys proxy. The zone ordering broadly survives the restriction.

Job zone is O*NET's classification of how much preparation an occupation requires: Zone 1 is little or no preparation, Zone 5 is extensive (think physicians, lawyers, senior engineers). The relationship between preparation level and AI exposure is not linear, and the shape matters.

Zone 1 (33 occupations) sits at a median of 13.3%. Zone 2 (298 occupations) at 20.0%. Zone 3 (213) at 30.4%. Then the curve flattens: Zone 4 (225 occupations, considerable preparation) hits 47.0% median, and Zone 5 (154, extensive preparation) also sits at 47.0%. The means tell a slightly different story (Zone 5 at 49.1% vs Zone 4 at 47.4%) because Zone 5 has a heavier right tail, with more occupations pushed above 60%.

The finding worth sitting with is that AI exposure peaks in the occupations that require the most education and training, not the least. This runs counter to the popular framing of AI as a threat primarily to low-skill work. The occupations most affected are the ones where workers have invested the most in specialized preparation. Whether that exposure represents augmentation or substitution risk depends on factors this data doesn't resolve, but the structural pattern is clear: current AI capability overlaps most heavily with the tasks performed by the most educated workers.

---

### SKA Levels: AI Capability vs. Workforce Requirements

![SKA Skills](part_2/figures/ska_skills.png)

![SKA Knowledge and Abilities](part_2/figures/ska_knowledge_abilities.png)

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


## Part 3 — Action: What To Do About It

### Conv → Confirmed → Ceiling Reach by Major Sector

![Conv → Confirmed → Ceiling](part_3/figures/conv_confirmed_ceiling_gap.png)

*Prose pending.*

---

### Tech Commodities Where AI Has Reach

![Tech Commodities](part_3/figures/tech_commodities.png)

*Prose pending.*

---

### Occupations Most At Risk Of Displacement

![Risk Score 5f — SKA-gated focused 43](part_3/figures/risk_score_5f.png)

*Prose pending.*

---

### State Exposure vs. Most-At-Risk Concentration

![State exposure vs. most-at-risk concentration](part_3/figures/state_exposure_at_risk.png)

*Prose pending.*

---

### AI Usage Intensity by Sector

![AI Intensity Anchor](part_3/figures/intensity_anchor_fulleco.png)

*Prose pending.*
