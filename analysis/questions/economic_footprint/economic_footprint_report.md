# What Is AI's Total Economic Footprint Across the US Economy?

**TLDR:** Under our primary configuration (All Confirmed), AI exposure now reaches 61.3 million workers — 40% of total US employment — representing $4.0 trillion in annual wages. The ceiling estimate puts it at 77.1 million workers and $5.0 trillion. The footprint has roughly doubled since late 2024. It is concentrated in knowledge work, heaviest in Zone 4 (credentialed professional jobs). Conversational AI (54.1M workers) currently has broader confirmed reach than agentic API usage (31.1M), but the agentic ceiling (60.4M) shows the potential is there once agentic deployment matures.

---

## The Scale

61.3 million workers. $3.99 trillion in wages. 40% of total US employment.

That's the confirmed estimate — requiring AI capability claims to be validated across multiple sources before a task counts as affected. The ceiling, which includes all AI capability claims regardless of cross-source confirmation, is 77.1 million workers and $4.97 trillion in wages, representing 50.3% of employment.

The gap between confirmed and ceiling — 15.8 million workers, roughly $980 billion in wages — is not noise. It's a real methodological divide: tasks where some AI systems have demonstrated capability but the evidence hasn't consolidated into confirmed status. That gap is also a forward indicator. As AI capabilities continue to be confirmed across additional sources, some portion of those 15.8 million workers will shift from "ceiling only" to "confirmed."

The five-config picture in full:

| Config | Workers | Wages | % Employment |
|--------|---------|-------|-------------|
| All Confirmed (primary) | 61.3M | $3.99T | 40.0% |
| All Sources (ceiling) | 77.1M | $4.97T | 50.3% |
| Human Conversation | 54.1M | $3.47T | 35.3% |
| Agentic Confirmed (AEI API only) | 31.1M | $2.16T | 20.3% |
| Agentic Ceiling (MCP + AEI API) | 60.4M | $3.97T | 39.4% |

---

## Where the Workers Are

The concentration of AI-exposed work follows the concentration of information-processing employment. The three largest sectors by workers affected under All Confirmed:

- **Office and Administrative Support**: 11.2M workers, 51.1% tasks affected, $532.7B wages. The largest sector by raw worker count. These jobs were the focus of automation discussions long before LLMs — data entry, correspondence, scheduling, record-keeping — and the current data confirms their exposure is both wide and deep.
- **Sales and Related**: 7.6M workers, 59.5% tasks affected, $363.0B wages. High worker count and one of the highest task penetration rates in the economy. Sales work is built around information-gathering, communication, and documentation — a natural fit for current AI capability.
- **Business and Financial Operations**: 5.5M workers, 50.7% tasks affected, $443.7B wages. Analysts, accountants, consultants. The knowledge-worker core of the professional economy.

The highest-intensity sectors by task penetration rate tell a slightly different story:

- **Computer and Mathematical**: 65.7% — the most deeply task-penetrated major sector, with 3.3M workers and $331.3B in wages. These workers are also most likely to use AI as a productivity tool rather than face direct displacement; the distinction matters.
- **Sales**: 59.5%
- **Educational Instruction and Library**: 53.6% — higher than most people expect. The tasks embedded in educational work — content preparation, explanation, feedback, administrative documentation — are all areas of genuine AI strength.

At the other end: Farming/Forestry (13.7%), Construction and Extraction (13.9%), and Transportation and Material Moving (17.6%). Physical, equipment-dependent work where AI's current reach is limited.

The wage picture is dominated by Management ($613.9B in wages affected) despite only moderate task penetration (35.5%) — a function of the sector's massive payroll per worker. This is worth keeping in mind for policy discussions: the workers most exposed by task percentage and the sector with the most wages at stake are not the same thing.

---

## How We Got Here: The Trend

The All Confirmed estimate has roughly doubled since the first available dataset date (late September 2024). The ceiling configuration went from 39.5M workers to 77.1M over the same 18-month window. That kind of growth in assessed exposure isn't primarily a labor market story — the occupational mix hasn't changed that much. What changed is how much of existing work AI can demonstrably do.

The sector-level trend data makes this concrete. Ranked by absolute percentage-point gain in task exposure over the full dataset window:

1. **Legal Occupations**: +25.5 pp (22.8% → 48.3%)
2. **Educational Instruction and Library**: +24.8 pp (28.8% → 53.6%)
3. **Sales and Related**: +22.8 pp (36.8% → 59.5%)
4. **Computer and Mathematical**: +22.3 pp (43.4% → 65.7%)
5. **Business and Financial Operations**: +19.4 pp (31.4% → 50.7%)

Legal's near-doubling from 22.8% to 48.3% reflects AI systems' growing capability in legal reasoning, document analysis, and research — capabilities that have advanced rapidly and that legal work is unusually well-suited for (large volumes of structured text, well-defined task boundaries, strong retrieval demands). Education's jump tracks the emergence of capable writing, tutoring, and content-generation systems.

At the bottom: Farming (+1.9 pp), Transportation (+2.3 pp), Production (+2.6 pp). The physical frontier hasn't moved.

---

## What Kind of Work Is Exposed

The skills data gives the sharpest picture of *why* these sectors are exposed. Across 120 O*NET skills, knowledge, and abilities elements, AI currently leads on 23 — all in knowledge or skills domains, none in physical or sensorimotor abilities. The top AI-leading elements: Sales and Marketing (+4.6 advantage over economy average), History and Archeology (+4.4), Foreign Language (+3.3). The pattern is clear: knowledge that can be encoded, retrieved, and synthesized from text — exactly what large language models are trained to do.

Human advantages are concentrated in physical and perceptual abilities. Sound Localization, Reaction Time, Peripheral Vision — AI scores near zero on all of them, not because humans score exceptionally high but because these are capabilities AI simply doesn't have in any embodied sense. The deeper point: most *cognitive* skills — written comprehension, reading comprehension, mathematical reasoning — show near-parity or slight AI advantage. The cognitive frontier has moved further than most people realize.

At the work activity level, the highest-penetration GWAs under All Confirmed:
- **Interpreting the Meaning of Information for Others**: 70.0%
- **Communicating with People Outside the Organization**: 69.6%
- **Working with Computers**: 69.3%
- **Updating and Using Relevant Knowledge**: 72.0%

These are the activities that constitute the core of information work. The high-worker-count GWAs (Documenting/Recording at 5.9M, Handling and Moving Objects at 4.7M) tell you where the people are; the high-penetration GWAs tell you where AI is most deeply capable.

At the IWA level, the clearest signals: "Respond to customer problems or inquiries" (2.2M workers, 75.2% tasks affected) and "Explain technical details of products or services" (1.3M workers, 81.9% tasks affected) — customer-facing information work is among the most deeply affected activity categories in the economy.

---

## Job Structure: The Preparation Paradox

The relationship between job preparation level and AI exposure runs counter to the standard automation narrative. Average task exposure by O*NET job zone:

- Zone 1 (little prep): ~26.9%
- Zone 2 (some prep): ~30.6%
- Zone 3 (medium prep): ~35.0%
- **Zone 4 (considerable prep, bachelor's + experience): ~50.9%** ← peak
- Zone 5 (extensive prep, advanced degree): ~45.9%

The most credentialed jobs — managers, accountants, engineers, analysts, healthcare practitioners — carry the highest average AI exposure. This is not a claim that Zone 4 workers will be replaced wholesale. It's a claim that a larger share of what they do on a given day is AI-capable than for someone in Zone 1.

Zone 5 shows slightly lower exposure than Zone 4 because the most elite professional work — original research, clinical judgment, legal strategy — still has meaningful AI-resistant components. The Zone 4 peak is where the combination of structured knowledge work and high task volume creates the greatest overlap with current AI capability.

From the job outlook data: Rating 3 occupations (below-average / declining) carry higher average exposure (39.2%) than Rating 1 (bright outlook, 29.8%). Jobs the labor market already views as precarious tend to be more AI-exposed. Whether AI exposure is causing the poor outlook or just correlated with it varies by occupation — some are declining *because* of automation; others are AI-exposed and the market hasn't fully repriced them yet.

---

## Agentic vs. Conversational

Confirmed agentic tool-use (AEI API only) reaches 31.1M workers, compared to 54.1M for conversational AI. Confirmed agentic is currently narrower — API-based agentic deployment is concentrated in higher-complexity technical contexts rather than broadly across the information economy. But the agentic ceiling (MCP + AEI API, 60.4M workers) already exceeds conversational, which shows the potential is there; the gap between ceiling and confirmed (29.3M workers) is organizational deployment lag, not technical limitation.

The mode-level data shows how confirmed agentic and conversational differ at the activity level. Administrative tasks (55.0% conversational vs. 25.1% agentic), information retrieval (48.8% vs. 29.7%), and data analysis (50.5% vs. 34.8%) are all higher under conversational — these are the activities where broad chatbot-style deployment is most mature. Where confirmed agentic modestly leads: scheduling (27.7% vs. 37.9%) and a handful of multi-step workflow activities where tool-using systems have been specifically deployed. The agentic ceiling data shows that scheduling, administrative, and documenting activities would all rise dramatically if MCP-based tooling were as widely deployed as conversational AI.

The three-layer framing: confirmed agentic (31.1M) is what we've measured in production AEI API deployments. The agentic ceiling (60.4M) is what's possible with today's demonstrated capability. The gap between them — 29.3M workers — is the latent impact zone. As agentic infrastructure becomes standard enterprise practice, that gap closes.

Auto-augmentability reinforces the picture from a different angle: 97.7% of workers in AI-affected occupations are in roles with meaningful AI augmentation potential (score >= 2 on a 5-point scale), with a weighted mean of 2.82. Almost every worker in an AI-affected occupation can be meaningfully assisted by AI — not just marginally.

---

## Geography

Every state has essentially the same average AI task exposure: approximately 36.1%. This isn't surprising once you understand how the measure works — task exposure is computed at the occupation level using national datasets, so geography doesn't enter the calculation directly. What varies across states is sector composition, and that variation clusters into five recognizable economic types:

- **Cluster 1 — Tech/Sun Belt metros** (CA, TX, WA, CO, AZ, FL, VA, etc.): highest Computer/Math and Sales shares
- **Cluster 2 — Diversified industrial/northeastern** (NY, IL, OH, PA, MI, MA, etc.): highest healthcare shares, most balanced
- **Cluster 3 — DC alone**: Business/Finance at 24.8%, Computer/Math at 21.2% — the federal contractor economy, in its own category
- **Cluster 4 — Rural/agricultural/inland** (IA, KS, AL, MS, ID, ND, etc.): highest Office/Admin, Food Prep, and Production shares
- **Cluster 5 — Tourism/service economies** (NV, HI, NM, GU, PR, VI): highest hospitality and service shares

The state-uniform exposure finding has direct policy implications. There are no "high-exposure states" versus "low-exposure states" — the challenge is distributed. State-level responses should be calibrated to sector composition, not to some notion that certain geographies face more risk than others.

---

## What This Adds Up To

40% of US employment, $4 trillion in wages, an exposure rate that has roughly doubled in 18 months. The sectors carrying the most workers are the same ones that have seen the fastest growth in exposure. The workers most deeply exposed by task percentage are credentialed Zone 4 professionals, not low-skill workers. The agentic gap is growing, and 97.7% of affected workers are in occupations where AI can meaningfully amplify their output.

The honest reading of these numbers has two parts. First, the scale is large enough that the economic disruption question is not "if" but "how" — through productivity gains, headcount reductions, wage compression, or some mix. Second, the data captures capability and exposure, not actual deployment. A substantial lag exists between what AI can demonstrably do and what firms are actually using it for at scale. That gap is probably closing faster in some sectors (legal, software, customer service) than others (healthcare, education, construction).

The trend data — 18 months of roughly doubling confirmed exposure — suggests the capability side of the ledger is not plateauing. The question now is whether economic and organizational reality keeps pace.

---

*Analysis based on `final_all_confirmed_usage_2026-02-12` as primary config. Full sub-question breakdowns, figures, and CSVs in `sector_footprint/`, `skills_landscape/`, `job_structure/`, `ai_modes/`, `trends/`, `state_profiles/`, and `work_activities/` sub-folders.*
