# Work Activity Exposure: Which Types of Work Are Most Affected by AI?

*Primary config: All Confirmed | 332 IWAs | National | Method: freq | Auto-aug ON*

---

The activity-level picture of AI exposure is more useful for education and workforce planning than the occupation-level picture. At the IWA level, 52 activities are fragile (≥66% AI exposure), 116 are moderate (33–66%), and 164 are robust (<33%). The robust activities are almost entirely physical, caregiving, and operational work — everything requiring presence in a physical environment, situational judgment in real time, or direct care for people and systems. 82% of affected workers are doing moderate-or-fragile activities. AI's footprint is expanding: 284 of 332 IWAs grew in exposure over 15 months. The education system's core work — evaluating students, developing materials, assessing capabilities — is growing fastest. A three-category training framework maps this into actionable investment targets: Durable (robust + educationally relevant), AI × Human pair (moderate tier), and Delegation/Oversight (fragile + next-wave).

---

## 1. Current State of Activity Exposure

*Full detail: [exposure_state/exposure_state_report.md](exposure_state/exposure_state_report.md)*

332 Intermediate Work Activities. Confirmed exposure ranges from 0.07% ("Test sites for environmental hazards") to 92.5% ("Research laws, precedents, or other legal data"). That's nearly the full range of possible values. AI is genuinely transforming some types of work while barely touching others — and the split isn't about which industries are lucky or unlucky. It's about what the work requires.

The top confirmed IWAs cluster coherently: legal research, historical analysis, scholarly evaluation, marketing content, technical explanation, writing, market analysis, software design. These are information retrieval, synthesis, communication, and judgment based on structured knowledge — exactly what large language models are trained to do. The near-zero gap between confirmed and ceiling for many of them (legal research: 92.5% vs. 92.5%; language interpretation: 82.8% vs. 82.8%) tells you this isn't emergent capability that hasn't been deployed yet. People are already using AI for these things at near-maximal reach.

At the GWA level, four categories have crossed into fragile territory (≥66% confirmed):

| GWA | Confirmed % | Ceiling % | Workers |
|-----|------------|-----------|---------|
| Updating and Using Relevant Knowledge | 72.0% | 73.1% | 1.0M |
| Interpreting the Meaning of Information for Others | 70.0% | 72.9% | 2.6M |
| Communicating with People Outside the Organization | 69.6% | 77.2% | 3.5M |
| Working with Computers | 69.3% | 84.8% | 1.9M |

"Working with Computers" at 69% confirmed is striking, but the more revealing number is the ceiling: 84.8%. Computer-based work is where agentic AI capability is highest. The 15pp gap between confirmed and ceiling is the deployment gap — the technology is already there.

The robust end of the GWA spectrum is entirely physical: Operating Vehicles (1.4%), Performing General Physical Activities (12.2%), Controlling Machines (12.7%), Repairing Mechanical Equipment (13.5%), Handling and Moving Objects (18.1%). There's not a single interpersonal, cognitive, or communication GWA in the robust tier.

There's also an interesting config split on "Scheduling Work and Activities": 44.9% confirmed, 85.3% ceiling. The agentic ceiling (MCP + API) drives most of that difference — agentic AI is very capable at structured scheduling, even though conversational AI isn't being used for it much. Scheduling is the clearest case where the gap between confirmed and ceiling is architecturally specific: it's about which AI interface is being deployed, not whether AI can do the work.

![Top IWAs by % Tasks Affected (All Confirmed)](exposure_state/figures/top_iwas_pct.png)

![GWA Exposure Across All Five Configs](exposure_state/figures/gwa_config_comparison.png)

![Top IWAs by Workers Affected](exposure_state/figures/top_iwas_workers.png)

![Confirmed vs Ceiling Exposure — All IWAs](exposure_state/figures/iwa_confirmed_vs_ceiling.png)

---

## 2. Robustness: What's Resistant, and What's Next

*Full detail: [activity_robustness/activity_robustness_report.md](activity_robustness/activity_robustness_report.md)*

The tier distribution across all 332 IWAs: 52 fragile (≥66% confirmed), 116 moderate (33–66%), 164 robust (<33%). Half the universe is below the meaningful-change threshold — but the worker distribution is very different from the activity count, because robust activities tend to be physical and operational work with different employment concentrations than information work.

**Only 4 IWAs are fragile in every one of the five configs.** These are the activities where confirmed usage, ceiling capability, conversational AI, and agentic AI all agree: legal research (92.5%), editing (77.9%), explaining technical details (81.9%), and market analysis (76.5%). The more demanding criterion here is that all five configs include the agentic_confirmed config (AEI API only), which typically shows lower percentages than combined usage configs. For an activity to be fragile in all five, it needs to be deeply AI-reached even in tool-use and API patterns, not just conversational AI. Many activities are fragile in 3–4 configs; these four are the most robust signal.

122 IWAs are robust in all five configs. The common thread: activities requiring physical presence, real-time environmental awareness, or direct care and oversight of people and physical systems. Direct organizational operations (21%), assisting individuals with special needs (7.5%), personnel supervision (18.7%), health condition monitoring (19.1%), equipment inspection (11%), and compliance monitoring (22.8%) are the durable tier. These aren't unimportant activities — they're things that happen in a specific place at a specific time with a specific person.

The "next wave" is 42 IWAs currently below 33% confirmed but where the ceiling already puts them at or above 33%. The top cases by confirmed-to-ceiling gap:

| IWA | Confirmed % | Ceiling % | Gap |
|-----|------------|-----------|-----|
| Record information about environmental conditions | 14.4% | 72.3% | +57.8pp |
| Maintain operational records | 21.2% | 73.0% | +51.7pp |
| Prepare schedules for services or facilities | 31.2% | 82.1% | +50.9pp |
| Assign work to others | 27.8% | 75.3% | +47.5pp |
| Maintain sales or financial records | 28.1% | 75.2% | +47.1pp |
| Schedule operational activities | 26.1% | 66.9% | +40.9pp |

These are operational activities — record-keeping, scheduling, assignment — not creative or analytical ones. The reason the ceiling is so much higher is that agentic AI (MCP + API) is very capable at structured data entry, scheduling, and record management, even though conversational AI usage doesn't show up strongly in these categories. The next wave is agentic, not conversational.

This reveals something important about what "confirmed usage" captures vs. what it misses. Conversational AI shows up in analytical and communication work. Agentic AI shows up in operational and systems work. Activities where these two patterns diverge sharply are where the deployment gap is largest — and where the risk is least visible in the current data.

The cross-config stability chart filters to IWAs where configs disagree by more than 3pp (roughly two-thirds of all IWAs pass this threshold). Activities with wide spread — particularly "Scheduling Work and Activities" (45% confirmed vs. 85% ceiling) and "Coaching and Developing Others" (52% conversational vs. 10% agentic) — are where the answer depends on which AI deployment model you're measuring. These disagreements are architecturally specific, not random noise.

![GWA Robustness Overview](activity_robustness/figures/gwa_robustness.png)

![Next Wave — Confirmed-to-Ceiling Gaps](activity_robustness/figures/next_wave_gaps.png)

![Cross-Config Stability — IWAs with Meaningful Uncertainty](activity_robustness/figures/cross_config_stability.png)

---

## 3. What This Means for Education and Workforce Development

*Full detail: [education_lens/education_lens_report.md](education_lens/education_lens_report.md)*

18% of affected workers are in robust activities. 82% — 64.5M out of 78.6M — are doing activities with at least 33% AI exposure. This isn't a story about a small group of tech-adjacent workers. The moderate tier alone (40.8M workers) is where the restructuring will happen for the majority of the U.S. workforce.

| Tier | IWAs | Workers Affected | Share of Total |
|------|------|-----------------|----------------|
| Fragile (≥ 66%) | 52 | 23.6M | 30% |
| Moderate (33–66%) | 116 | 40.8M | 52% |
| Robust (< 33%) | 164 | 14.1M | 18% |

### Three-Category Training Framework

The tier structure provides the foundation, but the training implications differ within tiers. A practical planning framework:

**Category 1 — Durable: Train Directly.** Robust activities (<33%) in all five configs AND associated with occupations requiring meaningful education or training (mean job zone ≥2.5). 68 IWAs, 5.2M workers. These activities will hold value as AI reshapes adjacent work — healthcare work, supervisory and management activities, compliance and safety inspection, financial examination. The right investment is in the activity itself, not primarily in AI tools.

**Category 2 — AI × Human Pair: Train for Collaboration.** The moderate tier (33–66%), 116 IWAs, 40.9M workers. Human judgment combined with AI is still better than AI alone. This category splits by trend:
- *Stable moderate* (slow-growing, <15pp since Sept 2024): 84 IWAs, 32.7M workers. Likely to remain AI-human partnership for the medium term.
- *Rising moderate* (fast-growing, ≥15pp): 32 IWAs, 8.2M workers. Moving toward the delegation category — "analyze data to improve operations" (+31pp to 41%), "maintain health or medical records" (+27pp to 33%), "develop educational programs" (+29pp to 37%). Prioritize oversight skills now.

**Category 3 — Delegate/Oversight: Train for Direction and Review.** Fragile activities (≥66%, 52 IWAs, 23.6M workers) plus next-wave activities (confirmed <33% but ceiling ≥33%, 42 IWAs, 7.0M workers). The human role here is increasingly setup, quality review, exception handling, and accountability — not execution.

| Category | Sub-type | IWAs | Workers |
|----------|----------|------|---------|
| 1 — Durable | — | 68 | 5.2M |
| 2 — AI × Human | Stable moderate | 84 | 32.7M |
| 2 — AI × Human | Rising moderate | 32 | 8.2M |
| 3 — Delegate/Oversight | Fragile | 52 | 23.6M |
| 3 — Delegate/Oversight | Next wave | 42 | 7.0M |

**Uncertainty caveat:** this is a directional map, not a fixed one. Activities move across categories as AI capabilities and usage expand. The framework needs regular updating as datasets refresh.

### Is AI a Fad?

The quantitative answer: no. 284 of 332 IWAs grew in exposure between September 2024 and February 2026. 72 IWAs crossed the 10% threshold for the first time. The fastest-growing:

| IWA | Sept 2024 | Feb 2026 | Growth |
|-----|-----------|----------|--------|
| Evaluate scholarly work | 11.3% | 88.0% | +76.7pp |
| Assess student capabilities | 13.9% | 67.5% | +53.6pp |
| Set up classrooms or educational materials | 0.0% | 49.7% | +49.7pp |
| Implement security measures for computer systems | 23.1% | 72.8% | +49.7pp |
| Monitor financial data or activities | 3.6% | 52.2% | +48.6pp |

The educational activities deserve attention. Evaluating student work went from 11% to 88% in 15 months. The activities that define instructional work — evaluating student submissions, developing lesson materials, assessing capabilities — are exactly where AI adoption is growing fastest.

The domain breakdown confirms where exposure concentrates:

| Domain | GWAs | Avg % Exposed |
|--------|------|--------------|
| Cognitive/Technical | 9 | 53.3% |
| Information/Documentation | 3 | 49.6% |
| Interpersonal | 9 | 47.3% |
| Management/Coordination | 4 | 32.7% |
| Physical/Operational | 6 | 13.1% |

The gap between 53% (Cognitive/Technical) and 13% (Physical/Operational) is the distance between what AI can do and what a person has to be physically present to do.

![Workforce by Exposure Tier](education_lens/figures/workforce_by_tier.png)

![Three-Category Training Framework](education_lens/figures/training_framework.png)

![Durable Training Targets — Educationally Relevant](education_lens/figures/durable_training_targets.png)

![AI Exposure by Work Domain](education_lens/figures/domain_exposure.png)

![Is AI's Footprint Expanding? Top-Climbing Activity Types](education_lens/figures/exposure_growth_trend.png)

---

## 4. How Findings Translate for Each Audience

*Full detail: [audience_framing/audience_framing_report.md](audience_framing/audience_framing_report.md)*

The same data looks different depending on who's reading it. The sub-report frames findings specifically for policymakers, workforce developers and educators, researchers, and laypeople. The three-category framework (Durable / AI × Human / Delegation) runs through all four framings as the unifying structure.

**For policymakers:** the investment question is where workforce development funding has the highest return. The three-category framework maps directly onto three types of policy investment: fund toward the 68 durable IWAs (healthcare, supervision, compliance, financial examination — 5.2M workers, mean job zone 3+); support AI × human pair transitions for the 40.9M workers in the moderate tier, with special urgency for the 32 rising-moderate IWAs (8.2M workers) whose activities are trending toward delegation; prepare for disruption in the 52 fragile IWAs (23.6M workers) and 42 next-wave IWAs (7.0M workers). The ceiling data is the forward indicator: "Scheduling Work and Activities" is 45% confirmed but 85% ceiling; "Documenting/Recording Information" is 37% confirmed but 67% ceiling. Programs built around administrative efficiency should include transition pathways from the start. The most important policy signal: the education system's own core activities (evaluating student work, developing lesson materials, assessing capabilities) are growing fastest.

**For workforce developers and educators:** the three-category framework is the practical planning tool. Build training around the 68 durable IWAs where training dollars hold their value. Teach AI collaboration for the moderate tier — not how to do the activity, but how to direct AI doing the activity, evaluate its outputs, and maintain the contextual judgment AI lacks. For delegation-category activities (customer service, legal documentation, marketing, data analysis, technical explanation), train toward what the human role looks like after AI handles the baseline execution: setting context, validating outputs, handling exceptions, maintaining accountability. A note on prompting: "Working with Computers" (69%) and "Operate computer systems" (77%) are both fragile. Prompting is a useful skill today, but it's in the delegation category — the durable investment is in the judgment layer above prompting.

**For researchers:** mapping AI exposure at the IWA level rather than occupation level reveals within-occupation variation that occupation-level analysis misses. A registered nurse's task set spans activities from "monitor health conditions" (19% — robust) to "respond to customer inquiries" (75% — fragile). The widest cross-config disagreements at the GWA level — Scheduling (45% confirmed vs. 85% ceiling), Coaching and Developing Others (52% conversational vs. 10% agentic), Documentation (37% confirmed vs. 67% ceiling) — are architecturally specific: they reflect which AI interface is being used, not uncertainty about whether AI can do the work.

The eco_2015 vs. eco_2025 baseline comparison shows what changes when you switch from raw AEI data (eco_2015 baseline) to pre-combined datasets (eco_2025 baseline). Key caveat: the comparison is directional, not calibrated — the two baselines use different O*NET task inventories, and eco_2025 adds Microsoft Copilot scores. The largest eco_2025 > eco_2015 gaps: "Organizing, Planning, and Prioritizing Work" (+35.9pp), "Estimating Quantifiable Characteristics" (+33.6pp), "Performing Administrative Activities" (+26.8pp). Two GWAs where eco_2015 ≥ eco_2025: "Resolving Conflicts and Negotiating" (-5.2pp), "Documenting/Recording Information" (-3.1pp). The large upward shift in organizational/administrative GWAs primarily reflects Microsoft Copilot coverage.

**For laypeople:** 86% of activity types grew in exposure in 15 months. The three-category frame translates directly: Is your job primarily in physical, care, or oversight activities (Category 1)? Train toward the activity itself. Primarily in activities where human + AI collaboration is the current norm (Category 2)? Build AI fluency alongside substantive skills. Primarily in high-exposure activities like customer service, legal documentation, or data analysis (Category 3)? The investment is in the judgment and oversight layer — knowing what AI got wrong, setting it up correctly, maintaining accountability. Kids don't need to be programmers; they need to be able to evaluate what the AI produced.

![Workers at Risk by Activity Category](audience_framing/figures/policy_gwa_workers.png)

![Workforce by Training Category](audience_framing/figures/workforce_training_targets.png)

![Config Agreement at GWA Level](audience_framing/figures/researcher_config_comparison.png)

![GWA Exposure: eco_2015 vs eco_2025 Baseline](audience_framing/figures/researcher_eco_baseline_comparison.png)

![AI Exposure Over Time — Is It Growing?](audience_framing/figures/layperson_ai_trend.png)

---

## 5. Cross-Cutting Findings

**The physical/cognitive boundary is the defining line.** Every robust GWA is a physical-operations category. Every fragile GWA is information and communication. That boundary has been stable across all five configs, over time, and at every level of the hierarchy from GWA down to DWA. It's not an artifact of one data source or methodology.

**The three-category framework is the unifying structure.** Durable (robust + educationally relevant), AI × Human pair (moderate, split by trend rate), and Delegation/Oversight (fragile + next-wave) — these categories map onto distinct training strategies, policy investments, and research questions. The framework is directional, not deterministic: activities move across categories as AI capabilities expand.

**Config disagreements are architecturally specific, not random.** The activities with the widest spread across configs are the ones where conversational and agentic AI have fundamentally different deployment patterns: scheduling (agentic leads), coaching (conversational leads), documentation (narrow now, wide ceiling). Where configs agree tightly — legal, writing, market analysis, scholarly work — the exposure signal is robust to data source.

**The next wave is operational, not cognitive.** The 42 next-wave IWAs (confirmed <33%, ceiling ≥33%) are dominated by record-keeping, scheduling, assignment, and operational record management. These aren't the analytical activities already known to be AI-exposed — they're the workflow and administrative infrastructure of every organization. When agentic AI deployment scales, these will move from the robust tier to the fragile tier without any new capability being required.

**82% is not a marginal story.** 82% of workers in AI-affected occupations are doing activities with at least 33% exposure. The moderate tier (40.8M workers) is where the most consequential restructuring will happen — not through wholesale job elimination, but through significant changes to what the job actually involves day to day. That's harder to see and harder to prepare for than the headline fragile cases.

**The education system's own work is in the fast lane.** Evaluating student work (+77pp), assessing student capabilities (+54pp), setting up educational materials (+50pp) — the instructional activities that define the education sector are among the fastest-growing in AI exposure. The institutions most positioned to shape how people respond to AI disruption are themselves facing the steepest exposure curve.

---

## 6. Key Numbers

| Metric | Value |
|--------|-------|
| Total IWAs analyzed | 332 |
| Fragile IWAs (≥66% confirmed) | 52 |
| Moderate IWAs (33–66%) | 116 |
| Robust IWAs (<33%) | 164 |
| Stably fragile (all 5 configs) | 4 |
| Stably robust (all 5 configs) | 122 |
| Next wave (robust confirmed, ceiling ≥33%) | 42 |
| Workers in fragile activities | 23.6M (30%) |
| Workers in moderate activities | 40.8M (52%) |
| Workers in robust activities | 14.1M (18%) |
| Cat 1 durable IWAs (educationally relevant) | 68 (5.2M workers) |
| Cat 2 AI × Human IWAs | 116 (40.9M workers) |
| Cat 3 Delegate/Oversight IWAs | 94 (30.6M workers) |
| IWAs that grew in exposure (15 mo.) | 284 / 332 (86%) |
| IWAs newly above 10% exposure | 72 |
| Highest-penetration IWA | Research laws/legal data (92.5%) |
| Fastest-growing IWA | Evaluate scholarly work (+76.7pp) |

---

## Sub-Report Index

| Sub-Analysis | Report | What It Answers |
|---|---|---|
| Exposure State | [exposure_state_report.md](exposure_state/exposure_state_report.md) | What is the current state of AI task exposure across work activities? |
| Activity Robustness | [activity_robustness_report.md](activity_robustness/activity_robustness_report.md) | Which activities are AI-resistant, and which are in the next wave? |
| Education Lens | [education_lens_report.md](education_lens/education_lens_report.md) | What does this mean for what we teach and train? |
| Audience Framing | [audience_framing_report.md](audience_framing/audience_framing_report.md) | How do findings translate across audiences — policy, workforce, research, public? |

## Config Reference

| Config Key | Dataset | Role |
|---|---|---|
| `all_confirmed` | AEI Both + Micro 2026-02-12 | **Primary** — all confirmed usage |
| `all_ceiling` | All 2026-02-18 | Comparison — includes MCP ceiling |
| `human_conversation` | AEI Conv + Micro 2026-02-12 | Confirmed human conversation only |
| `agentic_confirmed` | AEI API 2026-02-12 | Confirmed agentic tool-use (AEI API only) |
| `agentic_ceiling` | MCP + API 2026-02-18 | Agentic ceiling |
