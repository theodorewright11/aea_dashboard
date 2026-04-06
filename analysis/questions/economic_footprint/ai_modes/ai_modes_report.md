# Economic Footprint: AI Modes

**TLDR:** Agentic AI exposes 5.3 million more workers than conversational AI under confirmed estimates (59.4M vs 54.1M). The gap reflects a genuine structural difference in what agentic systems can do — not just chat, but take multi-step actions, use tools, and complete workflows. Auto-augmentability scores are uniformly high: 97.7% of workers are in occupations with meaningful AI augmentation potential (score >= 2 on a 5-point scale), with a weighted mean of 2.82 across the full workforce.

---

## Conversational vs. Agentic: The Size of the Difference

Three configs capture the mode split:

- **All Confirmed**: 61.3M workers, $3.99T wages
- **Human Conversation (confirmed)**: 54.1M workers, $3.47T wages
- **Agentic Confirmed**: 59.4M workers, $3.92T wages

The conversational number is the lower bound for non-physical AI interaction — it's asking how many workers have tasks that AI can handle in a back-and-forth exchange. Agentic is asking how many workers have tasks that AI can handle when given tools, memory, and the ability to take multi-step actions.

The 5.3M worker gap between agentic confirmed and conversational confirmed represents occupations where the defining limitation was scope, not capability. These are jobs where AI can do the task, but only if it can act — access databases, write and execute code, browse the web, send emails, interact with APIs — not just respond to prompts. As agentic systems become standard rather than experimental, these 5.3 million workers move from "not yet affected" to "directly in scope."

The wage implication is significant: $3.92T for agentic vs. $3.47T for conversational — a $450 billion gap in wages of affected workers. That's a rough measure of the value pool that agentic capability unlocks beyond what conversational AI already touches.

---

## What Changes Between Modes

The GWA-level data shows where the modes diverge most sharply.

Working with Computers is high-exposure under all modes (69.3% all_confirmed, 62.6% conversational, 83.7% agentic confirmed). The agentic score is dramatically higher because "working with computers" encompasses tasks that require persistent actions — running scripts, managing files, interacting with software — not just answering questions about them.

Documenting/Recording Information: 37.3% (all_confirmed), 29.6% (conversational), 62.2% (agentic). A huge gap. Documentation tasks are often multi-step workflows — pulling information from various sources, structuring it, saving it — that require agentic capability to complete end-to-end.

Scheduling Work and Activities: 44.9% (all_confirmed), 27.7% (conversational), 84.5% (agentic). Scheduling is almost entirely an action-sequencing task. Conversational AI can discuss schedules; agentic AI can actually manage them.

Performing Administrative Activities: 58.7% (all_confirmed), 55.0% (conversational), 67.6% (agentic). Here the gap is smaller — administrative tasks have a high conversational component (drafting, answering, composing) alongside the action-taking component.

The pattern: tasks that are primarily communicative or analytical remain at roughly similar levels across modes. Tasks that require action-taking — accessing systems, managing workflows, completing multi-step processes — jump substantially in the agentic configuration.

---

## Auto-Augmentability

Auto-augmentability is a different angle. Rather than asking "can AI do this task," it asks "how well can AI assist a worker doing this task" — a measure of collaboration potential rather than replacement risk.

The score is on a 1-5 scale, where 1 means minimal augmentation potential and 5 means AI can substantially amplify the worker's output. Across the full affected workforce:

- **Weighted mean auto-augmentability**: 2.82 / 5.0
- **Workers in occupations with score >= 2**: 97.7%

97.7% is a striking number. Almost every worker in an AI-affected occupation is in a role where AI can meaningfully assist them — not just marginally, but genuinely augment their output. The distribution is overwhelmingly concentrated in the 2-3 range rather than at the extremes, which suggests a broad middle tier of "AI can help but isn't going to replace" across the economy's affected occupations.

A score of 2.82 out of 5 means we're at roughly mid-range augmentation potential across the board. There's substantial room to move up the scale as AI systems improve — particularly for the tasks currently at the boundary between "AI can assist" and "AI can complete autonomously." That boundary has been moving toward the latter for the past two years.

The by-major-sector breakdown of auto-augmentability scores generally tracks the task penetration findings: Computer/Mathematical and Business/Financial show the highest augmentability scores; physically-grounded sectors like Transportation and Construction show lower scores. But the within-sector variance is worth noting — even in sectors with lower average exposure, there are high-augmentability occupations. The administrative and information-processing layer of every sector carries higher augmentability than the hands-on layer.

---

## Reading the Mode Gap as a Forward Indicator

The 5.3M gap between agentic and conversational confirmed exposure is essentially a measure of latent impact — workers whose tasks AI can complete in principle, but only with the kind of agentic infrastructure that's just now becoming standard.

Agentic AI systems — models equipped with tools, long-horizon planning, and the ability to interact with real-world systems — have moved from research concept to production deployment in roughly the past 18 months. As enterprise adoption scales, the occupations that were in the "agentic only" exposure zone will increasingly face real workflow automation, not just AI-assisted drafting.

The implication: the 54M conversational number is roughly what AI is capable of disrupting right now with current deployment patterns. The 59M agentic number is what's possible as agentic deployment matures. The ceiling config puts the outer bound at 77M workers. The path from 54M to 59M is probably measured in months, not decades. The path from 59M to 77M depends on what AI systems can demonstrate capability on next.

This is why the mode comparison matters beyond just counting workers. It's a forward-looking decomposition of where the growth in AI impact will come from.
