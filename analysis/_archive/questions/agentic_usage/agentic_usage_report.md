*Primary config: AEI API 2026-02-12 (Agentic Confirmed) | MCP Cumul. v4 (MCP Only) | MCP + API 2026-02-18 (Agentic Ceiling) | AEI Both + Micro 2026-02-12 (Conv. Baseline) | Method: freq | Auto-aug ON | National*

The agentic AI exposure story has a floor, a ceiling, a shape, and a trajectory. The floor is 31.1M workers — occupations where confirmed agentic tool-use has been documented. The ceiling is 60.4M — where current AI tools are capable of affecting the work. The shape is concentrated in white-collar, information-processing, and coordination-heavy sectors. The trajectory is rapid growth through mid-2025, followed by deceleration as measurement frameworks approach saturation. Taken together, the five sub-analyses here paint a picture of AI that is already material, structurally uneven, and approaching a measurement ceiling that doesn't reflect a capability ceiling.

## 1. Exposure State
*Full detail: [exposure_state_report.md](exposure_state/exposure_state_report.md)*

At the February 2026 snapshot, the four exposure scenarios are:

| Scenario | Workers | % Employment | Wages |
|---|---|---|---|
| Agentic Confirmed (AEI API) | 31.1M | 20.3% | $2,161.9B |
| MCP Only | 46.5M | 30.4% | $2,968.8B |
| Agentic Ceiling (MCP+API) | 60.4M | 39.4% | $3,971.9B |
| Conv. Baseline | 61.3M | 40.0% | $3,993.2B |

The 30M workers in High-tier (>=60% task exposure) occupations under the ceiling are the priority planning cohort. At the confirmed level, only 36 occupations reach the High tier; under the ceiling, 156 do. The gap — 120 occupations, roughly 26M workers — is where deployment is plausible but not yet documented.

![Exposure State Comparison](exposure_state/figures/exposure_state_comparison.png)

## 2. Sector Footprint
*Full detail: [sector_footprint_report.md](sector_footprint/sector_footprint_report.md)*

The sector footprint is concentrated. Five major categories account for the bulk of agentic exposure by worker count:
- Office and Administrative Support: 12.9M workers, 62.1%
- Sales and Related Occupations: 9.2M workers, 68.5%
- Business and Financial Operations: 5.6M workers, 52.6%
- Management Occupations: 5.5M workers, 41.7%
- Computer and Mathematical: 3.8M workers, 75.0%

The agentic delta analysis (ceiling minus conv. baseline) reveals which sectors specifically benefit from agentic AI's tool-calling capabilities: Office/Admin (+11.0pp), Computer/Math (+9.3pp), Sales (+8.9pp). The negative deltas — Food Prep (-14.7pp), Community/Social Services (-11.9pp), Education (-11.7pp) — represent sectors where conversational AI already covers the relevant tasks and agentic capabilities don't add much.

![Sector Delta: Agentic vs. Conv.](sector_footprint/figures/agentic_vs_conv_delta.png)

![Sector Heatmap](sector_footprint/figures/sector_heatmap.png)

## 3. Work Activities
*Full detail: [work_activities_report.md](work_activities/work_activities_report.md)*

The top IWAs under the agentic ceiling are scheduling, database design, legal research, and system security — all near 90-95% task exposure. These are tasks where AI agents with tool access can handle the entire workflow. The IWA delta analysis shows something more revealing: the biggest gains when moving from Conv. Baseline to Agentic Ceiling are operational tasks — "Record information about environmental conditions" (+57.8pp), "Maintain operational records" (+51.1pp), "Prepare schedules for services or facilities" (+50.7pp). Agentic AI's marginal contribution over conversational AI is in automating the operational backbone of organizations.

The eco_2015 AEI API data shows a different picture: writing, legal research, and market analysis dominate — reflecting where text-heavy agentic AI was first deployed commercially.

![Top IWAs — Agentic Ceiling](work_activities/figures/top_iwas_agentic_ceiling.png)

![IWA Delta: Agentic vs. Conv. Baseline](work_activities/figures/iwa_delta_agentic_vs_conv.png)

## 4. MCP Profile
*Full detail: [mcp_profile_report.md](mcp_profile/mcp_profile_report.md)*

MCP's signature occupations — Telemarketers (90%), Online Merchants (87%), Web Developers (85%) — are roles with high digital system interaction. Where MCP leads AEI API most: Data Scientists (+72pp), Sales service reps (+71pp), Penetration Testers (+61pp). Where AEI API leads MCP: Patient Representatives (-53pp), Actors (-48pp), Industrial-Organizational Psychologists (-44pp).

The pattern is clean: MCP measures AI-system interaction capability; AEI API measures AI-human workflow deployment. They are complementary, not overlapping. The MCP-specific IWAs — scheduling, database design, processing digital data — confirm the system-interaction thesis.

![MCP Top Occupations](mcp_profile/figures/mcp_top_occupations.png)

![MCP vs. AEI Delta by Sector](mcp_profile/figures/mcp_vs_aei_delta_major.png)

## 5. Trends
*Full detail: [trends_report.md](trends/trends_report.md)*

The agentic ceiling grew from 33.4M workers (April 2025) to 60.4M (February 2026) — 81% growth in under a year. Growth was front-loaded: the August 2025 update added 9.4M workers in a single step. The pace slowed substantially in late 2025 and early 2026, with the last two updates adding a combined 1.0M workers. MCP cumulative growth also plateaued after v3.

AEI API grew more steadily: 23.4M (Aug 2025) to 31.1M (Feb 2026), tracking real enterprise deployment rather than benchmark capability expansion.

The fastest-growing sectors over the full agentic ceiling series: Sales (+28.7pp), Education (+27.3pp), Legal (+24.6pp), Business/Financial (+23.7pp), Community/Social (+22.8pp).

![Agentic Ceiling Trend](trends/figures/agentic_ceiling_trend.png)

![AEI API and MCP Trends](trends/figures/aei_api_mcp_trend.png)

## Cross-Cutting Findings

1. **The confirmed-to-ceiling gap (31M to 60M) is where policy acts** — the floor is real, the ceiling is plausible, and the 29M workers in between are the key uncertainty. Workforce programs targeting only confirmed exposure will miss the near-term wave.

2. **Agentic AI's marginal contribution over conversational AI is operational** — scheduling, records management, data processing. Not the creative/analytical work that gets attention. This distinction matters for training program design.

3. **MCP and AEI API are measuring different dimensions of the same phenomenon** — system-interaction capability vs. human-workflow deployment. Neither is sufficient alone; combined, they bracket the full agentic AI footprint.

4. **The growth trajectory is asymptoting** — not because AI stopped advancing, but because the current measurement framework (eco_2025 task taxonomy matched to MCP benchmarks) is nearly saturated. The real frontier may already exceed what current metrics can capture.

5. **Wage concentration is disproportionate** — $4T in wages at the ceiling represents about a quarter of the U.S. wage bill. The occupations most affected (Office/Admin, Sales, Computer/Math) are not the lowest-wage workers; they are the mid-to-upper-middle of the wage distribution.

6. **Sector convergence masks occupation divergence** — all sources agree on which major sectors are exposed. But within those sectors, which specific occupations bear the brunt depends heavily on which data source and which AI capability dimension you emphasize.

## Key Takeaways

1. **20.3% of employment is confirmed-exposed today** — 31.1M workers in occupations with documented agentic AI usage. This is the operational number for immediate workforce planning.
2. **39.4% is the plausible near-term ceiling** — 60.4M workers where current AI tools can materially affect the work. This is the planning horizon for the next 3-5 years.
3. **Office/Admin and Sales together hold 22M agentic-ceiling workers** — more than any other sector pair. These are not edge cases; they are the bulk of the footprint.
4. **The agentic delta is a scheduling/records/data story** — the biggest IWA gains from agentic AI are operational, not analytical. This shifts the policy focus toward operational roles in organizations.
5. **The growth trajectory is plateauing in current measurement** — 60.4M may be near the ceiling of what eco_2025 + current benchmarks can capture. The real exposure number may be higher once measurement catches up.

## Sub-Report Index

| Sub-Analysis | Report | What It Answers |
|---|---|---|
| Exposure State | [exposure_state_report.md](exposure_state/exposure_state_report.md) | What is the current state of agentic AI exposure? |
| Sector Footprint | [sector_footprint_report.md](sector_footprint/sector_footprint_report.md) | Which sectors are most affected and where does agentic AI add most? |
| Work Activities | [work_activities_report.md](work_activities/work_activities_report.md) | What kinds of work are most affected at the IWA/GWA level? |
| MCP Profile | [mcp_profile_report.md](mcp_profile/mcp_profile_report.md) | What is MCP's unique signature vs. AEI API? |
| Trends | [trends_report.md](trends/trends_report.md) | How has agentic AI exposure grown over time? |

## Config Reference

| Config Key | Dataset | Role |
|---|---|---|
| agentic_confirmed | AEI API 2026-02-12 | Confirmed agentic tool-use floor |
| mcp_only | MCP Cumul. v4 | MCP benchmark capability |
| agentic_ceiling | MCP + API 2026-02-18 | Agentic capability ceiling |
| all_confirmed | AEI Both + Micro 2026-02-12 | Conversational AI deployment baseline |
