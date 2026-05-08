# Audience Framing: The Potential Growth Findings for Different Readers

*Pulls findings from adoption_gap, wage_potential, and automation_opportunity | Method: freq | Auto-aug ON | National*

---

## Overview

The potential growth analysis answers a specific question: where is confirmed AI usage far below what AI can demonstrably do, and what does that gap mean in economic terms? The findings are the same regardless of who you're talking to. The framing, emphasis, and appropriate caveats are different for each audience.

This section doesn't repeat the full analysis — see the sub-question reports for the detailed numbers. It translates.

---

## For Policy

![Policy Investment Priorities — Wage Gap + Workers Gap](../questions/potential_growth/audience_framing/figures/policy_investment_priorities.png)

The macro case is relatively clean: $980 billion in annual wages sit in AI capabilities that have been demonstrated to work but aren't broadly deployed. The ceiling isn't theoretical — it's what at least some organizations are already doing with existing tools. The gap is an organizational and adoption problem, not a technological one.

**Where to direct AI adoption programs:** The sectors with the largest combined wage-gap and workers-gap — Office/Admin, Management, Sales, and Transportation/Material Moving — are the highest-priority targets. These aren't sectors that need new AI tools developed for them. The tools exist. The gap is in deployment, training, and organizational integration.

**The workforce development angle:** 248 occupations fall into Q1 — AI leads AND adoption is lagging. Within that group, 102 carry high job-risk signals (structural vulnerability, poor outlook, low job zone). Policy that supports AI tool adoption in those occupations without also supporting workforce transition is missing half the picture. The $980B opportunity and the 102 transformation-signal occupations are two sides of the same coin.

**What this isn't:** This analysis doesn't produce a job-loss count or a displacement forecast. High-risk occupations in Q1 are under pressure; they're not necessarily shrinking. The policy case isn't "act now to stop displacement" — it's "act now to shape how the adoption gap closes, because it will close one way or another."

**State-level relevance:** The gap analysis is national, but the economic footprint analysis shows that pct_tasks_affected is relatively uniform across states (~36% nationally). The economic opportunity from closing the gap is also roughly proportional to a state's sector composition. States with heavy office/admin and sales employment (most large states) have proportionally larger wage gaps.

---

## For Workforce Practitioners and Educators

![Workforce Training Targets — Q1 and Q3 by Employment × Wage](../questions/potential_growth/audience_framing/figures/workforce_training_targets.png)

The chart shows two types of occupations sorted by economic relevance (employment × median wage):

**Orange (Q1: AI leads, big gap):** AI tools are already more capable than what these jobs typically need, AND those tools aren't being widely deployed. For workers in these roles, learning to use the tools that exist today is likely to be more durable than waiting for AI to catch up to human capability — AI already has.

**Blue (Q3: Humans still lead, but gap exists):** Human skills still have an advantage in these occupations, but there's a meaningful adoption gap. These are tool-familiarity plays rather than capability plays. The AI tools exist and work for specific tasks; workers who know how to use them well will be more effective than those who don't, even though the fundamental skill advantage still lies with the humans.

These are directional signals, not prescriptions. We don't know exactly what AI adoption will look like in any specific occupation — that depends on what tools organizations purchase, how they redesign workflows, and which specific tasks get automated versus augmented. What we can say is:

- Occupations in Q1 have high AI capability and a deployment gap. Workers in those roles are more likely to encounter AI tools in their workflows in the next few years than workers in Q4.
- Occupations in Q3 have a tool-familiarity opportunity. The ceiling says AI can do more; the confirmed data says it's not happening yet; the SKA says humans still hold an edge. Learning the existing tools well is likely to extend that edge rather than replace it.

**Specific high-relevance targets from the workforce perspective:**
- Medical Secretaries: 42pp adoption gap, AI clearly capable — healthcare organizations are very likely to push AI tools into this role
- Cashiers and Retail Salespersons: High risk, high AI advantage, very large workforce — these roles face the most structural change pressure in the near term
- Software QA Analysts: 25pp gap, high wages — AI augmentation tools in testing are mature and the deployment gap is likely to close in tech organizations rapidly

A note on what we don't know: saying an occupation has a large adoption gap doesn't mean the workers in it need to retrain for a different occupation. In most cases it means they need to learn to use AI tools as part of their existing job. The distinction between "your job is changing" and "your job is disappearing" matters enormously for workforce program design, and this analysis cannot make that distinction definitively for any given role.

---

## For Researchers

![Config Sensitivity](../questions/potential_growth/audience_framing/figures/researcher_config_sensitivity.png)

The adoption gap is measured as the difference between `all_confirmed` and `all_ceiling`. Both endpoints are pre-combined datasets, so the gap is sensitive to the choice of what counts as "confirmed" and what counts as "ceiling." Here's what's robust and what isn't:

**Robust:**
- The sector ranking (which major categories have the largest gaps) is consistent across all five configs. Office/Admin and Management are always at the top; Construction and Healthcare Practitioners are always low.
- The IWA-level pattern (documentation, record-keeping, scheduling as the highest-gap activity types) is stable.
- The macro dollar figure ($980B gap from `all_confirmed` to `all_ceiling`) is a point estimate that would move significantly if you used `human_conversation` as the baseline ($1.51T gap) or `agentic_ceiling` as the ceiling ($1.00T gap). The confirmed-vs-ceiling framing should be understood as a range, not a single number.

**Config-sensitive:**
- Education sector: appears much higher under human conversational AI configs than under agentic. The ceiling for Education is conversational, not tool-use.
- Transportation: gains heavily from MCP/agentic ceiling. The gap in Transportation is mostly driven by the ceiling rising with agentic capability, not by confirmed being particularly low.
- The transformation signal (Q1 + high risk) is based on all_confirmed for both adoption gap and SKA computation. Using a different config would shift the specific occupations but not the general pattern.

**Methodological notes:**
- SKA gap is computed at the 95th percentile of ai_capability across all occupations (per element), then compared to each occupation's specific occ_score. This means SKA gap is relative — positive means this occupation is below the 95th percentile capability frontier, not that AI will do the job.
- The adoption gap is in percentage points of pct_tasks_affected, which is a ratio-of-totals computation. Small differences at the occupation level can compound significantly at the aggregate.
- Matching on `title_current` between occupation data and SKA O*NET elements loses some occupations (~30 of 923 had no SKA match). Those occupations are excluded from the automation_opportunity analysis.

---

## For a General Audience

![Where We Are vs Where We Could Be](../questions/potential_growth/audience_framing/figures/layperson_opportunity.png)

Here's the simple version: AI tools that exist today can demonstrably help with a broader set of tasks than are currently using them. The blue bars show how many workers are in jobs where AI tools are actively being used right now. The orange bars show how many more workers are in jobs where the tools exist and work, but aren't widely deployed yet.

That orange bar isn't a prediction that those workers will lose their jobs. It's a statement about tools: the capability is there, the deployment isn't. Whether and how that gap closes depends on decisions made by organizations, not just by AI development.

A few concrete examples:
- **Medical Secretaries**: AI tools can demonstrably handle much of the documentation and scheduling work in this role. Confirmed usage is at 31% of tasks; the tools suggest 73% is reachable. That 42pp gap is AI capability sitting on the shelf.
- **General and Operations Managers**: These are experienced people running businesses. Confirmed usage is at 28% of their tasks. The ceiling — what AI tools have been shown to help with — is 52%. That 24pp gap includes things like decision-support analysis, documentation, and project coordination.
- **Stockers and Order Fillers**: Confirmed exposure is only 23%. The ceiling says 45% is reachable. Most of that gap is in record-keeping and inventory management, not physical material moving.

What does "the ceiling is reachable" actually mean for someone in these jobs? Honestly, it depends. If your organization adopts AI tools for inventory tracking and you're a stocker, your workflow will change — but you probably won't become a software engineer. If you're a medical secretary and your hospital system rolls out AI documentation tools, you'll use different tools for the same underlying job. The gap closing doesn't mean the jobs go away; it means they change.

The 102 occupations in the "transformation signal" category — where AI already leads, the adoption gap is large, AND the job has structural risk factors — are more uncertain. These are the roles where the combination of AI capability and organizational pressure is most likely to produce significant structural change over the next few years. Cashiers, billing clerks, data entry workers, certain administrative roles. Not certain displacement, but higher pressure.

For most workers, the practical meaning of the adoption gap is simpler: AI tools related to your work exist right now and probably do things you'd find useful. The question isn't whether they'll be relevant to your job — they already are. The question is when, and in what form, your organization will start using them.

---

## Files

| File | Contents |
|------|----------|
| `results/policy_priorities.csv` | Sectors ranked by combined wage + workers gap |
| `results/workforce_targets.csv` | Q1 + Q3 occupations by employment × median wage |
| `results/researcher_sensitivity.csv` | Pct tasks affected by sector and config |
