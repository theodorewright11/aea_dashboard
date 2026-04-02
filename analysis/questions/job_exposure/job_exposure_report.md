# Job Exposure: AI's Impact on the Labor Market

*Five analysis configs | 923 occupations | National | Method: freq | Auto-aug ON*

---

## Overview

This report synthesizes six sub-analyses that together answer a single overarching question: **how exposed is the U.S. labor market to AI, which workers are most at risk, what can they do about it, and where is the policy intervention most urgent?**

Each sub-analysis is fully documented in its own report. This document draws the through-line.

---

## 1. Current State of Exposure

*Full detail: [exposure_state/exposure_state_report.md](exposure_state/exposure_state_report.md)*

Under the all_ceiling configuration, 249 occupations employing 54.2 million workers already have 60% or more of their tasks exposed to AI. Another 259 occupations (47.3M workers) sit in the moderate band (40--60%). Combined, more than 101 million workers are in occupations where AI can demonstrably perform at least 40% of their task load. Sales and Related occupations lead exposure by sector, with 99.8% of employment in the high tier, followed by Computer and Mathematical (99.1%) and Office and Administrative Support (89.8%).

The gap between ceiling and confirmed usage is substantial: only 81 occupations are in the high tier under confirmed human-conversation AI usage, compared to 249 under ceiling. This 36.7 million-worker gap represents deployment opportunity -- places where AI capability exists but adoption hasn't yet arrived. The trend is closing fast: 887 of 923 occupations saw positive exposure growth, with a median increase of 16.7 percentage points.

![Config Comparison](exposure_state/figures/config_comparison.png)

---

## 2. Which Jobs Are Most at Risk of Replacement?

*Full detail: [job_risk_scoring/job_risk_scoring_report.md](job_risk_scoring/job_risk_scoring_report.md)*

High exposure alone does not predict replacement. Our seven-factor composite risk score layers in SKA gap trends, job zone, labor market outlook, and software tool density. The result: 233 occupations (59.9M workers) score in the high-risk tier (5--7 flags triggered), while 461 occupations (77.8M workers) are moderate and 229 (15.5M) are low-risk.

The disconnect between exposure and risk is one of this analysis's most important findings. Market Research Analysts face 92.7% task exposure but only moderate risk, protected by a job zone of 4 (considerable preparation). Registered Nurses sit at 40% exposure and score low-risk. Meanwhile, occupations like Waiters and Waitresses have modest 45% exposure but land in the high-risk tier because every structural flag -- low job zone, poor outlook, high software density -- converges against them. Insurance Claims Processing Clerks trigger all seven flags for a perfect risk score of 7.

![Risk Tier Distribution](job_risk_scoring/figures/risk_tier_distribution.png)

---

## 3. What Can Workers Do?

*Full detail: [worker_resilience/worker_resilience_report.md](worker_resilience/worker_resilience_report.md)*

The element-level SKA gap analysis reveals a clean divide. Human advantages are concentrated entirely in physical and perceptual abilities: Speed of Limb Movement (-7.49 gap), Sound Localization (-7.33), Dynamic Flexibility (-6.47), Reaction Time (-6.43). These are areas where AI capability falls far short of what occupations require.

AI advantages cluster in knowledge domains: Foreign Language (+6.05), Sales and Marketing (+5.38), History and Archeology (+4.58), Philosophy and Theology (+4.23). The practical implication is clear -- workers whose jobs depend on physical presence, dexterity, or real-time sensory judgment retain a durable edge. Workers whose jobs center on knowledge recall or subject expertise should shift toward leveraging AI for those elements rather than competing against it. The one skill (not ability or knowledge) where AI leads is Instructing (+2.87), signaling that even the delivery of expertise is becoming AI-accessible.

![Human Advantage Elements](worker_resilience/figures/human_advantage_bar.png)

---

## 4. Where Is Reskilling Cheapest?

*Full detail: [pivot_distance/pivot_distance_report.md](pivot_distance/pivot_distance_report.md)*

The cost of pivoting from a high-risk to a low-risk occupation varies dramatically by job zone. Zone 1 workers (entry-level, little preparation) face the lowest pivot cost at 133.8 total skill gap units -- the move from positions like Baristas and Door-to-Door Sales to Farmworkers and Logging Equipment Operators is relatively short. Zone 3 (medium preparation) is the most expensive at 322.1, where office and clerical workers must acquire entirely new technical knowledge to reach the low-risk occupations in their zone.

The cost drivers are almost entirely specialized technical knowledge -- Building and Construction (71.0), Mechanical (64.4), Engineering and Technology (52.6). This means retraining programs that focus on general "soft skills" development miss the actual bottleneck. Effective reskilling for high-risk workers requires targeted technical certification, not generic professional development.

![Pivot Cost by Zone](pivot_distance/figures/pivot_cost_by_zone.png)

---

## 5. Where Is Policy Intervention Most Urgent?

*Full detail: [audience_framing/audience_framing_report.md](audience_framing/audience_framing_report.md)*

134 occupations are hidden at-risk: their skill and knowledge profiles nearly match those of heavily exposed jobs, but AI adoption hasn't reached them yet. Education and management roles dominate this list -- Education Administrators K--12 (similarity 0.92), Special Education Teachers (0.92), and Loss Prevention Managers (0.90) sit in the top ranks. These are the "next wave" occupations where the window for proactive intervention is still open.

Among the worst-case occupations (high exposure AND poor labor market outlook), the dominant skill domains are broad and transferable: Philosophy and Theology, Customer and Personal Service, Foreign Language, History. This is encouraging for reskilling -- these workers aren't trapped in narrow specializations. Their knowledge foundations transfer readily; the challenge is redirecting them toward occupations with better outlook and lower AI exposure before the transition becomes forced.

![Hidden At-Risk Scatter](audience_framing/figures/hidden_at_risk_scatter.png)

---

## 6. How Do Findings Land for Specific Jobs?

*Full detail: [occs_of_interest/occs_of_interest_report.md](occs_of_interest/occs_of_interest_report.md)*

Across 27 matched occupations, exposure ranges from 12.6% (Construction Laborers) to 92.7% (Market Research Analysts). Ten of 27 land in the high-risk tier, including Secretaries and Admin Assistants (90.9% exposure), Web Developers (90.8%), Interpreters and Translators (87.7%), and Graphic Designers (87.3%). These are roles people interact with daily, and the scale of at-risk employment is substantial.

The most striking individual finding: Registered Nurses score low-risk today (40.2% exposure, protected by job zone and strong outlook) but are flagged as hidden at-risk -- the only one of the 27 named occupations to carry that flag. Their skill profile is a 0.92 match to the high-exposure average. If AI adoption follows the path that skill similarity predicts, nursing will shift from the low-risk tier to something far more exposed. For a workforce of over 3 million, this is a finding that warrants attention now, while the reskilling window is still open.

![Exposure Ranked Bar](occs_of_interest/figures/exposure_ranked_bar.png)

---

## 7. Cross-Cutting Findings

- **Exposure does not equal risk.** The seven-factor risk model separates the 249 high-exposure occupations into meaningfully different tiers. Job zone and labor market outlook serve as protective buffers -- Software Developers and Market Research Analysts are highly exposed but structurally protected, while Waiters and Cashiers face convergent risk from every direction.

- **The reskilling bottleneck is technical knowledge, not soft skills.** The pivot distance analysis shows that the costliest elements to close are Building and Construction, Mechanical, and Engineering -- all specialized technical domains. Meanwhile, the worker resilience analysis shows that human advantages are concentrated in physical abilities. These two findings converge: effective workforce development should combine physical-task careers with technical certification pathways, not generic skills courses.

- **The hidden at-risk quadrant is dominated by education roles.** Education Administrators, Special Education Teachers, and related occupations cluster at the top of the hidden at-risk list. Their skill profiles nearly match heavily exposed office and knowledge-worker occupations. If AI penetration follows skill-profile similarity, the education sector is next -- and that sector is large, publicly funded, and policy-responsive.

- **Knowledge domains are AI's strongest suit and the worst-case workers' strongest asset.** The same knowledge areas where AI already exceeds occupational need (Foreign Language, Education and Training, Philosophy) are also the dominant elements in the high-exposure/low-outlook group. Workers in these worst-case occupations aren't trapped -- their knowledge is broad and transferable -- but they need directed pathways to occupations where that knowledge is valued and AI exposure is lower.

- **Nearly every occupation is moving in the same direction.** 887 of 923 occupations grew in exposure across the tracking period. Zero declined. This is not a story about a few disrupted industries -- it is an economy-wide trajectory. The question is no longer whether AI will reach a given occupation, but when and how fast.

---

## 8. Key Takeaways

1. **More than 100 million U.S. workers** are in occupations where AI can demonstrably perform at least 40% of their tasks. Under the ceiling configuration, 54.2 million are at 60% or above.

2. **Risk is concentrated but not where exposure is highest.** 233 occupations (59.9M workers) score high-risk when structural factors like job zone, outlook, and software density are layered in. High exposure alone is a necessary but insufficient condition.

3. **Workers' durable advantage is physical, not cognitive.** The top 10 human-advantage elements are all physical and perceptual abilities. Knowledge recall is AI's strongest domain. Workers should leverage AI for knowledge tasks and invest in the judgment, coordination, and physical skills that remain distinctly human.

4. **134 occupations are hidden at-risk** -- their skill profiles match high-exposure jobs but AI hasn't reached them yet. Education roles dominate this list. The policy window for proactive intervention is open now and closing.

5. **Registered Nurses are the single most important hidden-risk finding.** Low risk today but flagged as hidden at-risk across 3M+ workers. Their skill profile is a near-perfect match to heavily exposed occupations. If AI follows the path that skill similarity predicts, nursing will be the next major sector to feel the impact.

---

## Sub-Report Index

| Sub-Analysis | Report | What It Answers |
|---|---|---|
| Exposure State | [exposure_state_report.md](exposure_state/exposure_state_report.md) | How exposed is the economy today, and how is that changing? |
| Job Risk Scoring | [job_risk_scoring_report.md](job_risk_scoring/job_risk_scoring_report.md) | Which occupations face replacement, not just transformation? |
| Worker Resilience | [worker_resilience_report.md](worker_resilience/worker_resilience_report.md) | Where do humans still have an advantage, and what should workers train? |
| Pivot Distance | [pivot_distance_report.md](pivot_distance/pivot_distance_report.md) | How expensive is it to reskill, and where is it cheapest? |
| Audience Framing | [audience_framing_report.md](audience_framing/audience_framing_report.md) | Which jobs are next, and where is retraining investment most urgent? |
| Occupations of Interest | [occs_of_interest_report.md](occs_of_interest/occs_of_interest_report.md) | How do all findings land for 29 specific named occupations? |

## Config Reference

| Config Key | Dataset |
|---|---|
| `all_ceiling` | All 2026-02-18 (primary) |
| `human_conversation` | AEI Conv + Micro 2026-02-12 |
| `agentic_confirmed` | MCP + API 2026-02-12 |
| `all_confirmed` | AEI Both + Micro 2026-02-12 |
| `agentic_ceiling` | MCP + API 2026-02-18 |
