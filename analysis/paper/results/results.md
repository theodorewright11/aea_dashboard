# Results

---

## Part 1 — Scale, Convergence, Growth

### The Overview

![Aggregate AI Economic Footprint](part_1/figures/overview.png)

At the latest dataset version (February 2026), our primary configuration — confirmed AI usage across conversational and API activity — puts 61.3 million workers in scope, representing 40.0% of U.S. employment and $3.99 trillion in annual wages. The ceiling estimate, which adds MCP tool-use capability specifications to the confirmed usage data, reaches 77.1 million workers, 50.3% of employment, and $4.97 trillion in wages. These are not projections of how much AI will eventually affect work — they're what we observe in AI system logs now, cross-walked to occupational task data.

The five configurations in the overview chart show a deliberate spread across measurement philosophies. The narrowest view — agentic confirmed at 20.3% — captures only confirmed tool-use AI activity: API-driven, workflow-integrated, typically requiring more infrastructure to deploy than a browser session. Human conversational at 35.3% captures the dominant current form of AI at work: knowledge workers using Claude, ChatGPT, and Copilot for communication, research, and documentation tasks. The combined confirmed view (40.0%) adds Microsoft's occupational task assessment, derived from Copilot usage patterns, which provides an independent anchor. The agentic ceiling at 39.4% arrives at roughly the same number as all confirmed despite being computed via an entirely different pathway — tool-use capability mapping rather than usage logs — which is itself a convergence signal. And the all-ceiling at 50.3% is the union: every confirmed source plus MCP, representing the full demonstrated capability frontier.

The alignment at the top of that range with Seampoint's independent estimate — 51% of worker hours could be AI-augmented under governance-constrained deployment conditions — is not coincidental. Two measurement frameworks built on entirely different data and methodology arrive at essentially the same number for how far AI's current reach extends. The agentic-confirmed figure (20.3%) similarly matches Seampoint's more conservative takeover rate (20%) — the fraction of tasks AI could handle entirely without human collaboration. These alignments suggest both frameworks are capturing the same underlying deployment reality, measured from different directions.

---

### The Convergence Argument

![Spearman ρ on % Tasks Affected](part_1/figures/convergence.png)

Scale numbers matter, but they're only compelling if they hold up across different ways of approaching the same underlying question. The convergence chart is making a different argument than the scale chart: not *how much*, but *how confident*.

Four data sources enter the correlation analysis — Claude browser usage (AEI conversational), Claude API usage (AEI agentic), Microsoft Copilot task assessment, and MCP tool-use capability mapping. These measure related but genuinely distinct things: revealed user behavior across conversational AI sessions, developer-driven agentic workflows, enterprise productivity tool usage, and the functional specification of thousands of AI tool integrations. At the major occupational category level, the Spearman rank correlations between all six source pairs range from 0.79 to 0.98, with a mean of 0.85. That's strong agreement across sources measuring from fundamentally different angles.

The correlation structure has an interpretable shape. The two Claude-based sources — browser and API — track each other most closely (0.98), which isn't surprising: they share model architecture and, to some extent, user population, even though one captures conversational usage and the other captures tool-calling patterns. The weakest major-level pair is Copilot vs. Claude browser at 0.79. That 0.79 is still a strong correlation — it means that when you rank the 22 major occupational categories by AI exposure in Microsoft's enterprise productivity data versus Claude's conversational usage data, those rankings align closely despite coming from entirely different platforms, methodologies, and user populations.

The agreement degrades predictably as you zoom in. At the occupation level (923 categories), the mean correlation falls to 0.64, and the weakest pairs sit around 0.55. More directly: zero percent of individual occupations achieve top-30 placement across all four sources simultaneously. This isn't a data quality problem — it's structural. Each source captures a real dimension of AI exposure, and those dimensions aren't equivalent at the occupation level even when they're equivalent at the sector level. The practical implication is that sector-level findings carry high confidence, while occupation-level claims need source attribution.

The qualitative structure of the consensus is worth stating once, clearly. Six major occupational categories are placed in the high-exposure tier by all four sources: Computer and Mathematical, Office and Administrative Support, Sales, Business and Financial Operations, Arts and Design, and Life/Physical/Social Science. Ten major categories show consistently low exposure across every source: construction, farming, food prep, both healthcare groups, installation and maintenance, personal care, production, protective service, and transportation. The sources agree as strongly on what AI doesn't do as on what it does — and that double consensus, high-exposure and low-exposure both confirmed across independent methods, is the clearest signal that the measurement approach is tracking something structurally real.

---

### The Temporal Argument

![% of Employment with AI-Exposed Tasks Over Time](part_1/figures/temporal_trend.png)

The March 2025 all-confirmed estimate sat at 30.4% of employment — 46.6 million workers. By February 2026, it sits at 40.0%, 61.3 million workers. That's 14.7 million additional workers added to the confirmed-exposure count in eleven months, driven not by labor market changes but by expanding observed AI activity across occupational tasks. The same jobs are there; AI keeps finding new footholds in them.

The growth isn't smooth. In the confirmed series, the August 2025 dataset is the dominant event: +10.1 million workers, +6.6 percentage points in a single snapshot. November 2025 adds 3.4 million more. February 2026 adds 1.2 million. Each increment is smaller than the last — a deceleration consistent with an asymptote forming, either because most readily AI-exposed cognitive work is now captured in confirmed usage, or because the dataset window hasn't yet seen a new adoption wave. Both interpretations are consistent with the data.

![All Confirmed](part_1/figures/temporal_table_all_confirmed.png)

The ceiling series follows a different growth path. Its earliest jump — April 2025, +12.6 million workers, +8.2 percentage points — came from the first MCP dataset incorporation, not from AI adoption growth per se. MCP added a large tranche of task coverage at once because it's a capability specification dataset rather than a usage log. Subsequent ceiling increments have been smaller and more gradual. The ceiling ends the window at 50.3% while confirmed sits at 40.0% — a roughly 10-percentage-point gap representing demonstrated-but-not-yet-confirmed frontier.

![All Sources (Ceiling)](part_1/figures/temporal_table_all_ceiling.png)

The confirmed-to-ceiling ratio has been narrowing: 77% in August 2025, 80% by February 2026. Confirmed usage is growing slightly faster than the ceiling, meaning deployment is slowly catching up to demonstrated capability. The open question is whether that convergence continues, and what it looks like when it does — whether confirmed exposure approaches the current ceiling, whether the ceiling itself keeps expanding as new AI tools emerge, or both simultaneously. The next sections turn to what's driving the shape of both numbers and what it means for workers, sectors, and policy.

---

## Part 2 — [TBD: Characterization]

*Content pending.*

---

## Part 3 — [TBD: Action]

*Content pending.*
