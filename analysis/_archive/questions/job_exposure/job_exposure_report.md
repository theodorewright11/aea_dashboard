# Job Exposure: AI's Impact on the Labor Market

*Primary config: All Confirmed | 923 occupations | National | Method: freq | Auto-aug ON*

---

The short version: confirmed AI usage already reaches a meaningful share of the task load in 364 occupations covering 73.2 million workers. The ceiling — what AI *could* do if fully deployed — pushes that to 508 occupations and 101.5 million workers. Risk isn't just about exposure: an eight-factor weighted model (max score 10) that gates on actual task penetration identifies 115 occupations (34.4M workers) as genuinely high-risk under a more conservative four-tier framework. Workers' durable advantage is physical, not cognitive — AI has reached just 9–34% of the typical occupation's requirement for physical abilities, versus 109–131% for knowledge domains. And the next wave of disruption — 150 occupations with high AI-capability overlap but low current exposure — is already showing rising trends.

---

## 1. Current State of Exposure

*Full detail: [exposure_state/exposure_state_report.md](exposure_state/exposure_state_report.md)*

Under confirmed usage (all_confirmed — conversation + API + Microsoft, no MCP ceiling data), 145 occupations employing 31.4 million workers have 60% or more of their tasks exposed to AI. Another 219 occupations (41.8M workers) sit in the moderate band (40–60%). That's 364 occupations and 73.2 million workers where AI is already demonstrably performing a substantial share of the task load — not theoretically, but based on confirmed usage patterns extrapolated to the full occupational structure.

The gap to ceiling is real but uneven. Adding MCP capability data pushes the high tier from 145 to 249 occupations, picking up an additional 22.8 million workers. Some occupations barely move — Market Research Analysts go from 89.5% to 92.7%, Technical Writers from 85.8% to 85.9%. Others jump dramatically: Cashiers from 46.9% to 68.2%, General and Operations Managers from 27.9% to 52.3%, Software Developers from 45.2% to 64.7%. These are the occupations where agentic AI tooling has capability that confirmed human conversation usage hasn't yet reflected.

Trends are pointing one direction. 612 of 923 occupations saw positive exposure growth in the confirmed config over the tracking period, with a median gain of 5.7 percentage points and total workers affected growing by 21.8 million. Under ceiling, 887 of 923 grew.

Some surprises in the hierarchy. Training and Development Managers sit at 85.7% exposure within a Management major category that averages 36.3%. Pharmacists hit 64.9% in a Healthcare category averaging 29.7%. Supervisors of Construction and Extraction Workers show 47.2% in a major category averaging just 14.4%. The category average masks significant within-group variation.

![Config Comparison](exposure_state/figures/config_comparison.png)

---

## 2. Which Jobs Are Most at Risk?

*Full detail: [job_risk_scoring/job_risk_scoring_report.md](job_risk_scoring/job_risk_scoring_report.md)*

High exposure alone doesn't tell you whether a job is at risk of being fundamentally restructured. A 90% task exposure score for Market Research Analysts means something different than 90% for a low-zone clerical job with poor labor market outlook. The eight-factor composite risk score (max 10) addresses this by weighting exposure depth (task percentage > 50%, SKA overall_pct > median) at 2x each, and velocity, auto-augmentability, and structural vulnerability at 1x each. An exposure gate at 33% prevents structurally vulnerable but low-exposure jobs from being labeled high-risk.

The result under the new four-tier framework: 115 occupations (34.4M workers) score 8–10 as high risk, with an average task exposure of 65.4%. This is more conservative than the old three-tier model (which found 195 high-risk occupations) because the 50% absolute threshold on flag 1 and the tighter tier boundaries mean "high risk" now requires deep, not just above-median, exposure. 356 occupations (64.6M workers) sit at mod-high risk (score 5–7), 214 (31.0M workers) at mod-low (score 3–4), and 238 (23.3M workers) at low. The gate downgraded 2 occupations that would have otherwise scored high.

The flag composition tells the real story. Score 3 occupations (108, avg pct 27.5%) are structural-plus-trend: 54% have the job zone flag, 56% have poor outlook, but just 2% have the pct flag. Score 7 occupations (55, avg pct 40.0%) have the SKA flag at 87% and SKA trend at 100%, but flag 1 (pct > 50%) at only 20% — deep capability alignment without crossing the task coverage threshold. Score 10 — the 24 "all flags active" occupations averaging 68.0% exposure — have every single flag triggered.

306 occupations change risk tier depending on which AI capability source you use (more common under 4 tiers). 149 make jumps of 3+ tiers. Writers and Authors swing from mod-low under Human Conversation to high under Agentic. The instability is useful information — it tells you which jobs' risk profile depends on which AI modality actually gets deployed.

![Risk vs Pct Scatter](job_risk_scoring/figures/risk_vs_pct_scatter.png)

---

## 3. What Can Workers Do?

*Full detail: [worker_resilience/worker_resilience_report.md](worker_resilience/worker_resilience_report.md)*

The SKA analysis — now expressed as AI capability as a percentage of what each occupation needs (100% = AI matches the job's requirement) — reveals a clean three-way split. Abilities are overwhelmingly human territory: the top human-advantage elements are all physical, with AI reaching just 9% (Sound Localization), 21% (Night Vision), 24% (Peripheral Vision), and 25% (Speed of Limb Movement) of typical occupational requirements.

Knowledge domains tell the opposite story. AI's top advantages: Sales and Marketing (131% of occ need), History and Archeology (125%), Philosophy and Theology (121%), Foreign Language (118%). The practical translation: if your job's value comes primarily from knowing things, AI already exceeds the typical occupational need.

Skills sit in the middle — a genuine contest. Instructing (115%), Learning Strategies (112%), and Programming (108%) favor AI. Operation and Control (41%), Installation (46%), and Equipment Selection (48%) favor humans. This is where the actionable guidance lives: skills are trainable, and the human-advantage skills can be deliberately developed.

AI capability percentages are growing across all configs. The median overall_pct delta was +37.8pp for confirmed usage and +46.5pp for ceiling. AI isn't standing still.

The tips-and-tricks analysis for three occupations makes this concrete. Secretaries should invest in administrative judgment and service orientation (deep human advantages) while letting AI handle calendars, scheduling, and information lookup (auto_aug 4.5–5.0). Registered Nurses' deepest moat is Psychology and Problem Sensitivity — the clinical judgment that AI can't replicate — while documentation and protocol tasks are prime AI candidates. Construction Laborers are the physical-work safe harbor: their top advantages are all physical abilities where AI sits at 9–34% of need.

![Human Advantage Elements](worker_resilience/figures/human_advantage_bar.png)

---

## 4. Where Is Reskilling Cheapest?

*Full detail: [pivot_distance/pivot_distance_report.md](pivot_distance/pivot_distance_report.md)*

Pivot cost — the total skill and knowledge gap (L1 rectified distance) between high-risk and low-risk occupations within the same job zone — varies from 58.6 in Zone 1 (43% new ground) to 359.2 in Zone 3 (64% new ground). Zone 3 is the crisis point: mid-level office and clerical workers face the longest pivot distance because low-risk occupations in their zone require technical knowledge they don't have. Zone 2 is notable at 181.1 (91% new ground), meaning almost the entire destination skill profile is unfamiliar territory. For scale: the median occupation's total skill+knowledge mass is 296, so a pivot cost of 359 represents more than a full occupation's worth of learning.

The actionable finding: across all zones, AI can help close the reskilling gap for the majority of cost-driving elements. Per-zone breakdowns now show the specific top-10 skills and knowledge elements that drive the cost, plus the top-5 elements that would be "left behind" in the pivot. See [zone_breakdowns/](pivot_distance/zone_breakdowns/) for the full per-zone detail.

![Pivot Cost by Zone](pivot_distance/figures/pivot_cost_by_zone.png)

---

## 5. Where Is Policy Intervention Most Urgent?

*Full detail: [audience_framing/audience_framing_report.md](audience_framing/audience_framing_report.md)*

Using a projection method (which captures both direction and magnitude of skill-profile overlap with AI capabilities, unlike cosine similarity which only captures direction), 150 occupations emerge as hidden at-risk. These have low current confirmed exposure but high projection onto the AI capabilities vector — meaning AI already has the technical ability to reach their skill demands, even though confirmed usage hasn't gotten there yet.

Healthcare dominates this list. Preventive Medicine Physicians, Urologists, Nurse Anesthetists, General Internal Medicine Physicians, and Physical Medicine/Rehabilitation Physicians all appear in the top 10. Education Administrators K–12 (22.4% current, 38.2% ceiling) and Nuclear Engineers (16.7% current, 26.8% ceiling) show significant ceiling gaps, suggesting the deployment pathway is already opening.

53% of these hidden at-risk occupations are seeing rising exposure in the confirmed config. The window for proactive intervention is not just open — it's actively closing.

Among the worst-case occupations (high exposure AND poor outlook), the dominant skill domains are knowledge-heavy: Foreign Language (18.74), History and Archeology (18.36), Customer and Personal Service (18.35). Skills don't crack the top 15 even though we now include them. This is consistent with the worker resilience finding that knowledge domains are AI's strongest suit. But it's also encouraging: these knowledge foundations are broad and transferable. Workers in worst-case occupations aren't trapped in narrow specializations.

---

## 6. How Do Findings Land for Specific Jobs?

*Full detail: [occs_of_interest/occs_of_interest_report.md](occs_of_interest/occs_of_interest_report.md)*

Across 27 matched occupations, confirmed exposure ranges from 12.0% (Construction Laborers) to 89.5% (Market Research Analysts). The weighted risk scoring (now 8 flags, max 10, 4 tiers) properly separates exposure from risk: Market Research Analysts at 89.5% score mod-high because they're zone 4 with good outlook, while Customer Service Representatives at 84.1% and Secretaries at 75.1% both score 10 (high risk) because every flag converges.

The ceiling delta shows where MCP/agentic AI would hit hardest if deployed. Cashiers would jump from 46.9% to 68.2% (+21.3pp). General and Operations Managers from 27.9% to 52.3% (+24.4pp). Software Developers from 45.2% to 64.7% (+19.5pp). But some occupations barely change: Technical Writers go from 85.8% to 85.9% — conversational AI already covers almost their entire task load.

Registered Nurses (33.4% confirmed, mod-high risk) are worth watching. They're not in crisis today, but their skill profile projects strongly onto the AI capabilities vector, and the ceiling pushes them to 40.2%. General and Operations Managers and Accountants both carry hidden-at-risk flags.

---

## 7. Cross-Cutting Findings

**Exposure does not equal risk, and the four-tier scoring reflects that.** The eight-flag model with an exposure gate ensures that "high risk" means deep task penetration (>50%), AI capability exceeding the job's skill needs, AND typically structural vulnerability. Market Research Analysts are the poster child: 89.5% exposure, mod-high risk. The new four-tier system separates mod-high from mod-low, resolving the old three-tier model's problem of lumping score-3 and score-7 occupations together under a single "moderate" label.

**The three-layer framing matters.** Confirmed usage (all_confirmed) is what AI is doing today. The ceiling (all_ceiling) is where it could reach. The gap between them — 104 additional high-tier occupations and 22.8M more workers — is the deployment opportunity. For some occupations (Technical Writers, Market Research Analysts), the gap is nearly closed. For others (Cashiers, General Managers, Software Developers), the agentic frontier would significantly change the picture.

**The reskilling bottleneck is technical knowledge, not soft skills.** The pivot distance analysis shows that the costliest elements to close are Mechanical, Building and Construction, Physics, and Engineering. Meanwhile, the worker resilience analysis shows that human advantages are concentrated in physical abilities. Effective workforce development should combine physical-task career pathways with technical certification — not generic professional development courses.

**AI is both the cause of and the best tool for reskilling.** Across all job zones, the majority of pivot-cost-driving elements are ones where AI capability exceeds the at-risk worker's current level. AI can be deployed as a learning accelerator for the very skills workers need to acquire to move out of at-risk occupations.

**Everything is trending in the same direction.** 612 of 923 occupations grew in confirmed exposure. AI capability as a percentage of occupational requirements (SKA overall_pct) is climbing across all configs, with median gains between +13.7 and +46.5 percentage points. This is an economy-wide trajectory, not an isolated disruption.

---

## 8. Key Takeaways

1. **73.2 million workers** are in occupations where confirmed AI usage affects 40%+ of their tasks. Under ceiling, that rises to 101.5 million.

2. **115 occupations (34.4M workers)** score high risk under the eight-flag model (max 10) with exposure gate. "High risk" now requires deep exposure (>50% of tasks) plus convergence of capability and structural signals. Another 356 occupations (64.6M workers) sit at mod-high.

3. **Workers' durable advantage is physical, not cognitive.** AI sits at 9–34% of occupational need for top physical abilities, but 109–131% for top knowledge domains. Workers should leverage AI for knowledge tasks and invest in the judgment, coordination, and physical skills that remain human.

4. **150 occupations are hidden at-risk** — their skill profiles project strongly onto AI capabilities but confirmed usage hasn't reached them. Healthcare specialties dominate. 53% already show rising exposure.

5. **AI is the best reskilling tool available** for the displacement it causes. In Zone 2, 99.5% of pivot cost is in elements where AI capability exceeds the at-risk worker's current level.

6. **Zone 3 workers face the highest reskilling cost** (359.2 total, 64% new ground). Mid-level office/clerical workers pivoting to low-risk occupations need technical knowledge that generic training programs don't address. For context, the median occupation's total skill+knowledge mass is 296, so a Zone 3 pivot cost of 359 represents more than a full occupation's worth of learning.

---

## Sub-Report Index

| Sub-Analysis | Report | What It Answers |
|---|---|---|
| Exposure State | [exposure_state_report.md](exposure_state/exposure_state_report.md) | How exposed is the economy, and how is that changing? |
| Job Risk Scoring | [job_risk_scoring_report.md](job_risk_scoring/job_risk_scoring_report.md) | Which occupations face genuine replacement risk? |
| Worker Resilience | [worker_resilience_report.md](worker_resilience/worker_resilience_report.md) | Where do humans lead, and what should workers train? |
| Pivot Distance | [pivot_distance_report.md](pivot_distance/pivot_distance_report.md) | How expensive is reskilling, and can AI help? |
| Audience Framing | [audience_framing_report.md](audience_framing/audience_framing_report.md) | Which jobs are next, and where is intervention most urgent? |
| Occupations of Interest | [occs_of_interest_report.md](occs_of_interest/occs_of_interest_report.md) | How do findings land for 29 named occupations? |

## Config Reference

| Config Key | Dataset | Role |
|---|---|---|
| `all_confirmed` | AEI Both + Micro 2026-02-12 | **Primary** — all confirmed usage |
| `all_ceiling` | All 2026-02-18 | Comparison — includes MCP ceiling |
| `human_conversation` | AEI Conv + Micro 2026-02-12 | Confirmed human conversation only |
| `agentic_confirmed` | AEI API 2026-02-12 | Confirmed agentic tool-use (AEI API only) |
| `agentic_ceiling` | MCP + API 2026-02-18 | Agentic ceiling |
