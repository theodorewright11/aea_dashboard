# Work Activity Exposure: Which Types of Work Are Most Affected by AI?

*Primary config: All Confirmed | 332 IWAs | National | Method: freq | Auto-aug ON*

---

The activity-level picture of AI exposure is more useful for education and workforce planning than the occupation-level picture. At the IWA level, 52 activities are fragile (≥66% AI exposure), 116 are moderate (33–66%), and 164 are robust (<33%). The robust activities are almost entirely physical, caregiving, and operational work — everything requiring presence in a physical environment, situational judgment in real time, or direct care for people and systems. 82% of affected workers are doing moderate-or-fragile activities. AI's footprint is expanding: 284 of 332 IWAs grew in exposure over 15 months. The education system's core work — evaluating students, developing materials, assessing capabilities — is growing fastest.

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

![Top IWAs by % Tasks Affected (All Confirmed)](../questions/work_activity_exposure/exposure_state/figures/top_iwas_pct.png)

![GWA Exposure Across All Five Configs](../questions/work_activity_exposure/exposure_state/figures/gwa_config_comparison.png)

![Top IWAs by Workers Affected](../questions/work_activity_exposure/exposure_state/figures/top_iwas_workers.png)

![Confirmed vs Ceiling Exposure — All IWAs](../questions/work_activity_exposure/exposure_state/figures/iwa_confirmed_vs_ceiling.png)

---

## 2. Robustness: What's Resistant, and What's Next

*Full detail: [activity_robustness/activity_robustness_report.md](activity_robustness/activity_robustness_report.md)*

The tier distribution across all 332 IWAs: 52 fragile (≥66% confirmed), 116 moderate (33–66%), 164 robust (<33%). Half the universe is below the meaningful-change threshold — but the worker distribution is very different from the activity count, because robust activities tend to be physical and operational work with different employment concentrations than information work.

Ten IWAs are fragile in every one of the five configs. These are the activities where confirmed usage, ceiling capability, conversational AI, and agentic AI all agree: legal research (92.5%), historical research (89.1%), scholarly evaluation (88.0%), marketing content (85.2%), writing (81.3%), editing (77.9%), market analysis (76.5%), explaining technical details (81.9%), customer inquiry response (75.2%), and software design (73.8%). You can change the dataset, the methodology, or the time period — these activities stay fragile.

122 IWAs are robust in all five configs. The common thread: activities requiring physical presence, real-time environmental awareness, or direct care and oversight of people and physical systems. Direct organizational operations (21%), assisting individuals with special needs (7.5%), food and beverage services (18.8%), personnel supervision (18.7%), health condition monitoring (19.1%), equipment inspection (11%), and compliance monitoring (22.8%) are the durable tier. These aren't unimportant activities — they're things that happen in a specific place at a specific time with a specific person.

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

![IWA Robustness Tier Distribution](../questions/work_activity_exposure/activity_robustness/figures/iwa_robustness_tiers.png)

![GWA Robustness Overview](../questions/work_activity_exposure/activity_robustness/figures/gwa_robustness.png)

![Next Wave — Confirmed-to-Ceiling Gaps](../questions/work_activity_exposure/activity_robustness/figures/next_wave_gaps.png)

![Cross-Config Stability per IWA](../questions/work_activity_exposure/activity_robustness/figures/cross_config_stability.png)

---

## 3. What This Means for Education and Workforce Development

*Full detail: [education_lens/education_lens_report.md](education_lens/education_lens_report.md)*

18% of affected workers are in robust activities. 82% — 64.5M out of 78.6M — are doing activities with at least 33% AI exposure. This isn't a story about a small group of tech-adjacent workers. The moderate tier alone (40.8M workers) is where the restructuring will happen for the majority of the U.S. workforce.

| Tier | IWAs | Workers Affected | Share of Total |
|------|------|-----------------|----------------|
| Fragile (≥ 66%) | 52 | 23.6M | 30% |
| Moderate (33–66%) | 116 | 40.8M | 52% |
| Robust (< 33%) | 164 | 14.1M | 18% |

The domain breakdown confirms where exposure concentrates:

| Domain | GWAs | Avg % Exposed |
|--------|------|--------------|
| Cognitive/Technical | 9 | 53.3% |
| Information/Documentation | 3 | 49.6% |
| Interpersonal | 9 | 47.3% |
| Management/Coordination | 4 | 32.7% |
| Physical/Operational | 6 | 13.1% |

The gap between 53% (Cognitive/Technical) and 13% (Physical/Operational) is the distance between what AI can do and what a person has to be physically present to do. Management/Coordination at 33% is interesting — managing work, coordinating activities, and staffing are already 30%+ AI-exposed on confirmed usage, and the agentic configs push coordination work substantially higher.

Is AI a fad? The quantitative answer: no. 284 of 332 IWAs grew in exposure between September 2024 and February 2026. 72 IWAs crossed the 10% threshold for the first time — going from essentially unaffected to meaningfully AI-touched in roughly 15 months. The fastest-growing:

| IWA | Sept 2024 | Feb 2026 | Growth |
|-----|-----------|----------|--------|
| Evaluate scholarly work | 11.3% | 88.0% | +76.7pp |
| Assess student capabilities | 13.9% | 67.5% | +53.6pp |
| Set up classrooms or educational materials | 0.0% | 49.7% | +49.7pp |
| Implement security measures for computer systems | 23.1% | 72.8% | +49.7pp |
| Monitor financial data or activities | 3.6% | 52.2% | +48.6pp |

The educational activities deserve attention. Evaluating student work went from 11% to 88% in 15 months. The activities that define instructional work — evaluating student submissions, developing lesson materials, assessing capabilities — are exactly where AI adoption is growing fastest. The education system's resistance to change is happening as the work that defines education gets increasingly AI-exposed.

What should training programs actually build? The durable activities are robustly AI-resistant AND have large workforces: direct organizational operations (1.15M workers, 20.7% exposure), assisting individuals with special needs (549K, 7.5%), food and beverage services (521K, 18.8%), personnel supervision (496K, 18.7%), health condition monitoring (303K, 19.1%), equipment inspection (244K, 11%), compliance monitoring (239K, 22.8%). These share two characteristics: they happen in physical environments, and they require situational judgment in real time.

A note on "prompting" as a training target: operating computer systems (77%) and working with computers (69%) are both in the fragile zone. Prompting AI is itself an AI-reached skill. Teaching people to prompt is valuable today; calling it the durable skill set is not supported by this data. What is supported: teaching the layer above prompting — judgment about when AI is wrong, evaluation of AI-generated output, physical and operational competencies that provide the context AI assists with but doesn't replace.

![Workforce by Exposure Tier](../questions/work_activity_exposure/education_lens/figures/workforce_by_tier.png)

![Durable Training Targets — Robust Across All Configs](../questions/work_activity_exposure/education_lens/figures/durable_training_targets.png)

![AI Exposure by Work Domain](../questions/work_activity_exposure/education_lens/figures/domain_exposure.png)

![Is AI's Footprint Expanding? Top-Climbing Activity Types](../questions/work_activity_exposure/education_lens/figures/exposure_growth_trend.png)

---

## 4. How Findings Translate for Each Audience

*Full detail: [audience_framing/audience_framing_report.md](audience_framing/audience_framing_report.md)*

The same data looks different depending on who's reading it. The sub-report frames findings specifically for policymakers, workforce developers and educators, researchers, and laypeople.

**For policymakers:** the investment question is where workforce development funding has the highest return. The 23.6M workers in fragile activities (≥66% exposure) are the immediate policy targets: customer service, legal documentation, marketing, software design, data analysis, instructional design. The 40.8M in moderate activities (33–66%) are likely to see restructuring rather than elimination. Training dollars should flow toward the durable activities — physical supervision, caregiving, inspection, compliance monitoring. But the ceiling data is the forward indicator: "Scheduling Work and Activities" is 45% confirmed but 85% ceiling; "Documenting/Recording Information" is 37% confirmed but 67% ceiling. Programs built around administrative efficiency should be time-limited with clear transition pathways. The most important policy signal: the education system's core activities are growing fastest. Policy intervention in how schools are adapting to AI shouldn't wait for educators to self-report.

**For workforce developers and educators:** build training programs around the robustly AI-resistant activities with large workforces. Stop building programs centered on activities with confirmed exposure ≥66% and a strong trend line — legal research (93%), marketing content (85%), data analysis (79%), customer inquiry response (75%), technical explanation (82%) are activities training people for work that's already heavily AI-reached. The question isn't whether to include AI tools in the curriculum; it's what human contribution these roles need after AI handles the baseline.

**For researchers:** mapping AI exposure at the IWA level rather than occupation level reveals within-occupation variation that occupation-level analysis misses. A registered nurse's task set spans activities from "monitor health conditions" (19% — robust) to "respond to customer inquiries" (75% — fragile). Occupation-level analysis averages over that variation. The widest cross-config disagreements at the GWA level — Scheduling (45% confirmed vs. 85% ceiling), Coaching and Developing Others (52% conversational vs. 10% agentic), Documentation (37% confirmed vs. 67% ceiling) — are architecturally specific: they reflect which AI interface is being used, not uncertainty about whether AI can do the work.

**For laypeople:** 86% of activity types grew in exposure in 15 months. Software design is 74% AI-exposed — specific programming tasks are highly AI-reachable. The durable activities requiring physical presence, situational judgment in real time, and direct care for people are what the data says is hard to replace. Kids who will be hardest to replace can do physical work, care for people, supervise operations in real environments, and evaluate AI output rather than just generate it. Prompting and spreadsheets are inside the exposed zone, not outside it.

![Workers at Risk by Activity Category](../questions/work_activity_exposure/audience_framing/figures/policy_gwa_workers.png)

![Training Sweet Spot — Large Workforce, AI-Resistant](../questions/work_activity_exposure/audience_framing/figures/workforce_training_targets.png)

![Config Agreement at GWA Level](../questions/work_activity_exposure/audience_framing/figures/researcher_config_comparison.png)

![AI Exposure Over Time — Is It Growing?](../questions/work_activity_exposure/audience_framing/figures/layperson_ai_trend.png)

---

## 5. Cross-Cutting Findings

**The physical/cognitive boundary is the defining line.** Every robust GWA is a physical-operations category. Every fragile GWA is information and communication. That boundary has been stable across all five configs, over time, and at every level of the hierarchy from GWA down to DWA. It's not an artifact of one data source or methodology.

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
| Stably fragile (all 5 configs) | 10 |
| Stably robust (all 5 configs) | 122 |
| Next wave (robust confirmed, ceiling ≥33%) | 42 |
| Workers in fragile activities | 23.6M (30%) |
| Workers in moderate activities | 40.8M (52%) |
| Workers in robust activities | 14.1M (18%) |
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
