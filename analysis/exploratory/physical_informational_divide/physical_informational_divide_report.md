# Physical vs. Informational: The Structural AI Divide

*Config: All Confirmed (AEI Both + Micro 2026-02-12) | O*NET 2025 task structure | National*

---

The core question in AI workforce policy isn't whether AI affects work — it's whether AI affects *your* work in a way that changes what you need to do. That distinction maps, pretty cleanly, onto a structural split that runs through the occupational landscape: jobs where most of the work is physical, and jobs where most of it isn't.

This analysis operationalizes that split using O*NET's task-level physical flag. Each task in the dataset is marked physical or not. For each occupation, we compute the share of tasks that are physical, then classify: less than 33% physical = non-physical occupation, 33–67% = mixed, more than 67% = physical. That gives us 461 non-physical occupations, 267 mixed, and 187 physical.

The 33/67 thresholds aren't arbitrary — they're where the intuition holds up under inspection. Pharmacists and Registered Nurses land in non-physical (29–39%), which is right: most of their work is cognitive and informational even though they handle physical things. Paramedics and Truck Drivers land in physical (62–65%), also right. The mixed band captures the genuinely hybrid occupations — Physical Therapists, Police Officers, Clinical Lab Technologists — where neither label quite fits.

## The Structural Constraint

The clearest result is in the raw task counts.

Physical occupations (187 of them) carry 1,565 physical tasks and only 312 non-physical tasks. That's a 5-to-1 ratio. Their entire informational layer — the surface that AI can plausibly engage with — is 312 tasks across the full group. Non-physical occupations carry 7,529 non-physical tasks and 864 physical ones (which tend to be quasi-physical: monitoring, judging quality, inspecting rather than lifting or building).

That number — 312 vs. 7,529 — is the whole argument in two numbers. Physical jobs are structurally constrained in how much of their task surface AI can reach.

![GWA task distribution — 3×2 panel showing top GWAs by task count for each occupation group × task type](results/figures/gwa_task_distribution.png)

The GWA breakdown makes the content of that constraint concrete. Physical occupations' physical tasks are concentrated in Handling and Moving Objects (546 tasks), Inspecting Equipment (145), Estimating Quantifiable Characteristics (141), Performing General Physical Activities (127), and Repairing/Maintaining Mechanical Equipment (88). AI doesn't pick up boxes or tighten bolts. These tasks are outside its reach not because the work is complex, but because it's embodied.

The non-physical tasks within physical occupations — that thin informational layer — cluster in Getting Information (68), Communicating with Supervisors (42), Making Decisions and Solving Problems (33), Documenting/Recording Information (30), and Training and Teaching Others (26). This is where AI shows up in physical jobs: helping workers look things up, log results, communicate status, and learn new procedures. Narrow, useful, but not transformative.

Non-physical occupations tell a different story. Their non-physical task surface spans Documenting/Recording Information (727 tasks), Thinking Creatively (700), Providing Consultation and Advice (672), Getting Information (540), and Communicating with Supervisors (477) — and that's just the top five. The full IWA and DWA charts show the spread more clearly.

![IWA task distribution — top 12 IWAs per combination](results/figures/iwa_task_distribution.png)

![DWA task distribution — top 10 DWAs per combination](results/figures/dwa_task_distribution.png)

## What This Means for AI's Role in Physical Work

The paper's framing around physical jobs isn't "AI doesn't apply" — it's "AI applies to a specific slice." In a physical occupation, AI helps with the informational support layer: getting instructions, recording outcomes, monitoring for issues, communicating across the team. Process optimization on the cognitive side of a physically-dominated job. That's genuinely useful, but it doesn't change what the job fundamentally is, because the core work — the physical execution — stays human.

This is why physical jobs face a different policy question than informational ones. The risk isn't displacement or transformation of the job itself. It's displacement of specific informational support roles that currently sit inside or adjacent to physical jobs (schedulers, dispatchers, quality-logging functions). The physical work stays; the informational scaffolding around it gets thinner.

## The Informational Trilemma

Non-physical jobs are where the harder question lives. When AI can potentially engage with most of a job's task surface — and the data shows that's the case across creative, analytical, advisory, and documentation-heavy work — the outcome isn't predetermined. Three things can happen:

A job gets overtaken. The tasks AI can do are the job, and there's no residual human function that justifies the role. Reskilling is the response — either toward work that complements AI (judgment, relationship, oversight) or toward AI-less domains where human presence still matters.

A job changes. AI takes over a portion of the task load, but the human still owns the parts that require judgment, context, or physical presence. The job doesn't disappear; it upgrades. Training for this looks like building the skills to extract more value from AI — knowing when to trust it, how to direct it, how to verify its outputs.

A job stays the same. Either AI exposure is low enough that nothing changes, or the work is resistant enough (specialized expertise, regulatory requirements, relational trust) that displacement doesn't happen on any near-term horizon. No intervention needed.

The auto-aug scores point in the right direction on this. Non-physical occupations average 3.49 on the auto-aug scale (0–5), mixed occupations 3.11, physical occupations 2.97. Higher auto-aug means more room for AI to assist — but also more surface area for substitution. Physical jobs have structurally lower augmentation potential, which matches the task structure: there's less there for AI to grab.

![Average auto-augmentability score by occupation group](results/figures/auto_aug_by_occ_group.png)

## On the Terminology

"Informational" is probably the right framing for the paper's audience, even though it's not fully precise. The technical distinction is cognitive/non-physical vs. physical/embodied, and the actual O*NET categories are more granular than that. But "informational" captures the essential idea — jobs organized around processing, producing, and communicating information — in a way that a general audience will immediately understand. It's accurate enough and accessible enough that it earns its keep.

The alternative terms ("cognitive," "knowledge-based," "white-collar") all have baggage or miss part of the picture. "Informational" is clean.

## What to Build From Here

This framing — physical vs. informational, with mixed as the genuine gray zone — is a structural scaffold for the rest of the paper's policy argument. The physical/informational divide maps cleanly onto the trilemma: physical jobs mostly skip it, mixed jobs face a partial version, and informational jobs are squarely in the middle of it.

The natural next step is sector-level data: which sectors are dominated by physical vs. informational occupations, and how does that map onto the policy landscape (reskilling programs, workforce development priorities, economic development strategy). The data's all here; it's a matter of running the aggregation.

---

## Config and Files

| Item | Detail |
|------|--------|
| Dataset | `final_all_confirmed_usage_2026-02-12.csv` |
| Task classification | O*NET 2025 `physical` flag |
| Thresholds | <33% physical tasks = Non-physical, 33–67% = Mixed, >67% = Physical |
| Occupation counts | Non-physical: 461, Mixed: 267, Physical: 187 |
| Method | Task counts (structural, no AI scoring) |

| File | Contents |
|------|---------|
| `results/occ_classification.csv` | Per-occupation: pct_physical, occ_group, auto_aug |
| `results/auto_aug_summary.csv` | Mean/median auto-aug by occ group |
| `results/gwa_counts.csv` | Task counts by occ_group × task_type × GWA |
| `results/iwa_counts.csv` | Task counts by occ_group × task_type × IWA |
| `results/dwa_counts.csv` | Task counts by occ_group × task_type × DWA |
| `figures/gwa_task_distribution.png` | GWA 3×2 panel chart |
| `figures/iwa_task_distribution.png` | IWA 3×2 panel chart |
| `figures/dwa_task_distribution.png` | DWA 3×2 panel chart |
| `figures/auto_aug_by_occ_group.png` | Auto-aug comparison |
