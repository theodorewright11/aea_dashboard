# Work Activity Exposure

**Overarching question:** Which types of work are most affected by AI, and what does that mean for where education and workforce development should focus?

**TLDR:** The activity-level picture of AI exposure is more useful for education and workforce planning than the occupation-level picture. At the IWA level, 52 activities are fragile (≥66% AI exposure), 116 are moderate (33–66%), and 164 are robust (<33%). The robust activities are almost entirely physical, caregiving, and operational work. 82% of affected workers are doing moderate-or-fragile activities. AI's footprint is expanding — 284 of 332 IWAs grew in exposure over 15 months. The education system's core work (evaluating students, developing materials, assessing capabilities) is growing the fastest.

---

## Sub-Questions

### [exposure_state/](exposure_state/exposure_state_report.md) — What is the current state of activity exposure?

332 IWAs in the O*NET universe. Confirmed exposure ranges from 0.07% to 92.5%. The top exposed activities are information-processing and communication tasks: legal research, scholarly evaluation, marketing content, scientific data analysis, software design. Four GWA categories are fragile (≥66%): Working with Computers, Interpreting Information for Others, Communicating Outside the Organization, Updating and Using Relevant Knowledge. Five GWA categories are robust (<33%), and they're all physical.

The ceiling (all-source maximum) consistently exceeds the confirmed average, with the largest gaps in scheduling, documentation, and operational record-keeping. The confirmed-to-ceiling gap is a deployment gap, not a capability gap — the AI can do this work; the question is whether and how fast it gets deployed.

### [activity_robustness/](activity_robustness/activity_robustness_report.md) — Which activities are AI-resistant?

10 IWAs are fragile in all five configs. 122 IWAs are robust in all five configs. The "next wave" is 42 IWAs currently below 33% confirmed but already ≥33% ceiling. The next wave is driven by agentic AI: scheduling, operational record-keeping, and work assignment are where MCP + API capability far exceeds conversational AI usage. The confirmed-to-ceiling gap in these categories (often 40–50pp) is the distance between what AI can do in a well-deployed agentic system vs. what shows up in average conversational usage data.

### [education_lens/](education_lens/education_lens_report.md) — What does this mean for what we teach?

18% of the affected workforce is doing robust activities. 82% is in moderate or fragile territory. The Cognitive/Technical domain is the most exposed at 53% avg, Physical/Operational the least at 13%. 284/332 IWAs grew in exposure over 15 months; 72 crossed the 10% threshold for the first time. The fastest-growing activity types are educational: evaluating scholarly work (+77pp), assessing student capabilities (+54pp), setting up educational materials (+50pp). The education system's own work is in the fast lane.

Durable training targets: physical supervision, caregiving, inspection, compliance monitoring. 122 IWAs meet the stable-robust threshold with substantial workforce coverage. These are activities requiring physical presence, situational judgment in real environments, and direct care for people and systems.

### [audience_framing/](audience_framing/audience_framing_report.md) — How do findings translate for each audience?

- **Policy**: 64.5M workers in activities with ≥33% exposure. Invest in physical/caregiving training tracks with long-term value; time-limit programs built around administrative efficiency. The education sector needs specific attention — fastest-growing exposure, likely slowest-changing institution.
- **Workforce**: Build training around the durable activities (direct organizational operations, special needs assistance, physical inspection, compliance monitoring). Don't pivot to "prompting" as the durable skill — it's inside the exposed zone.
- **Researchers**: Activity-level analysis reveals within-occupation variation that occupation-level analysis misses. Config disagreement is architecturally specific: scheduling/documentation diverge because agentic vs. conversational AI have different deployment patterns.
- **Laypersons**: AI is not a fad — 86% of activity types grew in exposure in 15 months. The kids who will be hardest to replace are the ones who can do physical work, care for people, supervise operations, and evaluate AI output rather than just generate it.

---

## Key Numbers

| Metric | Value |
|--------|-------|
| Total IWAs analyzed | 332 |
| Fragile IWAs (≥66% confirmed) | 52 |
| Moderate IWAs (33–66%) | 116 |
| Robust IWAs (<33%) | 164 |
| Stably fragile (all 5 configs) | 10 |
| Stably robust (all 5 configs) | 122 |
| Next wave (robust confirmed, ceiling ≥33%) | 42 |
| Workers in fragile activities | 23.6M (30%) |
| Workers in moderate activities | 40.8M (52%) |
| Workers in robust activities | 14.1M (18%) |
| IWAs that grew in exposure (15 mo.) | 284 / 332 (86%) |
| IWAs newly above 10% exposure | 72 |

---

## How to Run

```bash
venv/Scripts/python -m analysis.questions.work_activity_exposure.exposure_state.run
venv/Scripts/python -m analysis.questions.work_activity_exposure.activity_robustness.run
venv/Scripts/python -m analysis.questions.work_activity_exposure.education_lens.run
venv/Scripts/python -m analysis.questions.work_activity_exposure.audience_framing.run
```

Sub-questions are independent.
