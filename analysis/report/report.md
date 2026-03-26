# AEA Dashboard Analysis Report

Automation Exposure Analysis — Findings from the AEA Dashboard data pipeline.

Built for Utah's Office of Artificial Intelligence Policy (OAIP).

---

## Executive Summary

The gap between AI tool capability and actual AI usage reveals where AI has the greatest unrealized transformative potential. Transportation and Material Moving occupations have the largest absolute worker gap (2.5M), driven by a massive workforce where AI tools can reach 18% of tasks but real adoption covers only 5.5%. Office/Admin and Sales follow with 2.4M and 2.1M worker gaps respectively. At the occupation level, Cashiers (1.2M gap), Sales Reps of Services (842K, zero current usage), and General/Operations Managers (805K) top the list. Education is the notable exception: AI is already used more than tools can automate, suggesting conversational AI (tutoring, writing help) has outpaced structured tool capability.

When we narrow the lens to job elimination risk — occupations where AI is already being used for most of the job's task value — 9 occupations cross the 60% usage-confirmed threshold, representing 1.5M workers. The largest are Market Research Analysts (431K workers, 63%), Search Marketing Strategists (431K, 66%), and Instructional Coordinators (211K, 61%). Another 146 occupations (35.9M workers) sit in the moderate risk tier (40-60%), where restructuring is more likely than elimination. Capability data (MCP v4) shows 59 occupations would be high-risk if AI were fully deployed — the gap of 54 "emerging risk" occupations, including Cashiers (3.1M), Customer Service Reps (2.7M), and Office Clerks (2.5M), represents the next wave of risk as AI adoption spreads. These findings are stable across both Time and Value weighting methods.

---

## Table of Contents

- [AI Transformative Potential](#ai-transformative-potential) — Where the gap between AI capability and adoption is largest
- [Job Elimination Risk](#job-elimination-risk) — Which occupations are most at risk of being lost to AI

---

## AI Transformative Potential

**Question:** Where are the jobs and sectors with the greatest potential for AI to be transformative?

**Method:** Compare MCP v4 (AI tool capability ceiling) against AEI Cumul. v4 (current real-world AI usage from Claude conversations). The gap represents unrealized potential. Tested across 4 config variants: Time/Value method x auto-aug ON/OFF.

### Key findings

**1. Transportation and Material Moving has the largest unrealized potential by workers.**

MCP v4 rates 18.0% of tasks as AI-capable, but AEI shows only 5.5% current usage. With 18.8M workers in this sector, that 12.5 percentage-point gap translates to 2.5M workers worth of untapped potential. These are warehouse, shipping, and logistics roles where AI scheduling, routing, and inventory tools exist but haven't been broadly adopted.

**2. Office/Admin and Sales have the most potential in absolute terms after accounting for their already-high adoption.**

Office/Admin: 54.4% MCP capability vs 32.8% current usage = 21.6pp gap, 2.4M workers.
Sales: 54.2% MCP vs 43.2% current = 11.0pp gap, 2.1M workers.

These sectors are already the most AI-affected by raw worker count, and there's still substantial room to grow.

**3. Education is the inverse — AI usage exceeds tool capability.**

AEI shows 45.2% of educational tasks involved in real AI conversations, but MCP tools only cover 22.9%. This is the largest negative gap (-22.3pp, -1.76M workers). Education's AI usage is happening through conversational interaction (tutoring, writing feedback, explanation) rather than through structured tool automation. This is the only major category where adoption has clearly outpaced measured capability.

**4. Several specific occupations have zero current AI usage but significant tool capability.**

Sales Reps of Services (70.8% MCP, 0% AEI), Project Management Specialists (49.3% MCP, 0% AEI), Industrial Truck Operators (29.3% MCP, 0% AEI), Substitute Teachers (29.7% MCP, 0% AEI). These represent completely untapped potential.

**5. The auto-aug toggle reveals a second layer of potential.**

When auto-aug is turned off (treating all AI-flagged tasks as maximally automatable), the gaps expand dramatically. Management jumps from +886K to +5.3M workers gap. This means many Management tasks are flagged as AI-capable but currently have moderate automation quality scores. If AI tools improve for these tasks, Management could see the single largest increase in AI impact.

**6. The Time vs Value method toggle barely changes the story.**

Rankings are nearly identical between Time (frequency-only weighting) and Value (frequency x relevance x importance). The unrealized potential exists in tasks that are both frequent and important, not just in routine high-frequency work.

**7. The findings are highly stable: 8 of 10 top major categories appear in the top-10 gap ranking across all 4 config variants.**

The stable top-10 at the major level: Transportation, Office/Admin, Sales, Computer/Math, Management, Production, Food Prep, Architecture/Engineering. At the occupation level, 7 of 10 are stable: Cashiers, Sales Reps, General Managers, Stockers, Laborers/Freight, Bookkeeping, Waiters.

*Config: MCP v4 vs AEI Cumul. v4 | Time | Auto-aug ON | National | All tasks. Full data and sensitivity analysis in [questions/ai_transformative_potential/](../questions/ai_transformative_potential/README.md).*

---

## Job Elimination Risk

**Question:** Which occupations are most at risk of being lost to AI — where most of the job's task value is already being done by AI?

**Method:** Use AEI Cumul. v4 + Microsoft (actual AI usage data from Claude conversations and Copilot usage), averaged, with auto-aug ON and Value weighting (importance-weighted). Tier occupations by % tasks affected: High Risk (>=60%), Moderate Risk (40-60%), Restructuring (20-40%), Low Exposure (<20%). Compare against MCP v4 (capability-only) to identify emerging risks.

### Key findings

**1. Nine occupations have usage-confirmed evidence that 60%+ of their task value is AI-exposed.**

| Occupation | % Tasks | Employment |
|-----------|---------|------------|
| Poets, Lyricists and Creative Writers | 70.0% | 45K |
| Business Intelligence Analysts | 68.9% | 122K |
| Search Marketing Strategists | 66.0% | 431K |
| Market Research Analysts and Marketing Specialists | 63.1% | 431K |
| Patient Representatives | 62.6% | 117K |
| Data Warehousing Specialists | 62.5% | 32K |
| Financial Quantitative Analysts | 61.3% | 93K |
| Instructional Coordinators | 61.2% | 211K |
| Bioinformatics Technicians | 60.0% | 5K |

The largest by employment are Market Research Analysts and Search Marketing Strategists (both ~431K workers). These are information-processing occupations where AI's core strengths (data analysis, content generation, pattern recognition) directly overlap with the most valuable parts of the job.

**2. 7 of 9 high-risk occupations are stable across both Value and Time methods.**

Only Instructional Coordinators and Financial Quantitative Analysts drop below 60% when switching from Value to Time weighting. The other 7 remain high-risk regardless of how you weight task importance, meaning this isn't an artifact of the weighting methodology.

**3. 146 occupations representing 35.9M workers are in the moderate risk tier (40-60%).**

These are more likely to be restructured than eliminated — significant AI task overlap, but enough of the job remains human-dependent. This tier includes some of the largest occupations in the economy: Customer Service Reps (2.7M), General Office Clerks (2.5M), Secretaries (1.7M), Bookkeeping Clerks (1.5M).

**4. The gap between usage-confirmed and capability risk is dramatic: 9 vs 59 high-risk occupations.**

MCP v4 (what AI CAN do) puts 59 occupations above 60%. The 54 that are high-risk in capability but not yet in usage represent "emerging risk" — jobs where the technology exists to automate most of the work, but adoption hasn't caught up. The largest emerging-risk occupations:

| Occupation | MCP % | Usage % | Gap | Employment |
|-----------|-------|---------|-----|------------|
| Cashiers | 63.8% | 36.6% | 27.3pp | 3.1M |
| Customer Service Reps | 65.7% | 54.6% | 11.1pp | 2.7M |
| Office Clerks, General | 72.5% | 53.4% | 19.1pp | 2.5M |
| Secretaries/Admin Assistants | 78.3% | 50.5% | 27.9pp | 1.7M |
| Bookkeeping/Auditing Clerks | 67.9% | 43.4% | 24.4pp | 1.5M |

**5. Computer/Math, Business/Financial, and Arts/Entertainment have the highest concentration of at-risk occupations.**

These major categories have the largest shares of occupations in the moderate and high-risk tiers. Farming, Construction, and Building Maintenance are almost entirely in the low-exposure tier.

**6. Important framing: High task exposure does not equal job loss.**

It means the occupation's task bundle heavily overlaps with demonstrated AI capability and usage. Whether this leads to job elimination, restructuring, fewer new hires, or productivity gains depends on deployment economics, regulation, and organizational inertia — none of which this data measures. The data identifies WHERE the pressure exists, not what happens next.

*Config: AEI Cumul. v4 + Microsoft | Average | Value | Auto-aug ON | National | Occupation level. Sensitivity checks: Time method, MCP v4 capability comparison. Full data in [questions/job_elimination_risk/](../questions/job_elimination_risk/README.md).*

---

## Notes

All results generated by the same compute pipeline as the [AEA Dashboard](../ARCHITECTURE.md). Default config: AEI Cumul. v4, MCP v4, Microsoft; Average; freq; auto-aug on; national. Full methodology in the research paper.
