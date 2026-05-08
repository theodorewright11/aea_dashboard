# Economic Footprint: Job Structure

AI exposure increases with job preparation level up through Zone 4, then plateaus or slightly dips for Zone 5. The most highly-credentialed jobs (Zone 4 — bachelor's plus significant work experience) carry the highest average task exposure, which cuts against the simple story that AI replaces low-skill work. The ECO 2025 DWS outlook data (a non-linear 0-5 scale combining projected openings, growth, and wages) shows that higher-rated occupations — those with strong outlook and high wages — actually carry the highest AI exposure, inverting the precarity narrative.

---

## Job Zones and Exposure

O*NET's job zone classification runs from Zone 1 (little or no preparation) to Zone 5 (extensive preparation, typically a professional or doctoral degree). The question is whether AI exposure increases, decreases, or is uncorrelated with preparation level.

The answer from the data: exposure generally rises with zone, peaking at Zone 4. Average pct_tasks_affected by zone:

- **Zone 1** (little prep): ~26.9%
- **Zone 2** (some prep, typically high school): ~35.5%
- **Zone 3** (medium prep, some post-secondary): ~37.6%
- **Zone 4** (considerable prep, bachelor's + experience): ~50.9%
- **Zone 5** (extensive prep, advanced degree): ~49.3%

The Zone 4 peak is striking. These are managers, accountants, engineers, analysts, healthcare practitioners — jobs that require real education and experience. The fact that they carry the highest average exposure is not a claim that AI will replace them wholesale. It is a claim that a larger share of what they do on a given day is AI-capable than for someone in Zone 1.

Zone 5 actually shows slightly lower average exposure than Zone 4. These are researchers, physicians, attorneys, professors — jobs where a significant fraction of work involves judgment, originality, and domain expertise that AI hasn't fully cracked. The tasks in Zone 5 roles that AI *can* do are a smaller share of the total workload.

![AI Exposure Distribution by Job Zone](figures/zone_exposure_violin.png)

---

## The Worker Counts

The distribution of workers across tiers tells the fuller story. Looking at Zone 4:

- 12.4 million workers in the **High** exposure tier (>= 60% tasks affected)
- 10.6 million in **Moderate** (40-59%)
- 12.2 million in **Restructuring** (20-39%)
- Only 0.9 million in **Low** (<20%)

Almost all Zone 4 workers — about 35 million total — are in the moderate-to-high exposure range. That's the professional workforce of the United States: lawyers, managers, accountants, engineers, healthcare practitioners. The low-exposure pocket (0.9M) is tiny compared to the high-exposure mass (12.4M).

Zone 2 shows a very different distribution. 18.8 million Zone 2 workers are in the Low exposure tier — these are the physically-grounded service and trade jobs where AI capability drops off. But Zone 2 also has 10.4 million in High exposure. Those are likely the administrative, sales, and data-entry roles within Zone 2 — jobs that require some training but are heavily task-automated.

Zone 5 has 2.4 million in High exposure and 6.6 million in Moderate — significant numbers, but a larger fraction in the Restructuring tier (1.5M) and Low tier (0.4M) than Zone 4. Consistent with the pattern that Zone 5 work is more defended against full task penetration.

![Workers by Job Zone and Exposure Tier](figures/zone_tier_heatmap.png)

---

## Job Outlook and Exposure

The ECO 2025 DWS outlook rating is a non-linear 0-5 scale. It is **not** an ordered severity scale — different ratings represent different tradeoffs between labor market outlook and wages. The rating is based on Utah projected openings (90%), growth rate (10%), and median wages:

| Rating | Meaning |
|--------|---------|
| **5** | Strongest outlook + high wages |
| **4** | Good outlook + relatively high wages |
| **3** | Moderate-to-strong outlook + low-to-moderate wages |
| **2** | High wages + limited outlook |
| **1** | Low wages + strong outlook |
| **0** | Limited outlook + low wages |

Ratings 1 and 2 in particular are not ordered — they represent opposite tradeoffs (1 = strong demand but low pay; 2 = high pay but limited openings). This matters for interpretation: a jump from 1 to 2 is not an improvement, it's a completely different labor market profile.

Average AI task exposure by rating:

- **Rating 0** (limited outlook + low wages): ~31.9% — 307K workers
- **Rating 1** (low wages + strong outlook): ~29.8% — 2.7M workers
- **Rating 2** (high wages + limited outlook): ~33.9% — 62.8M workers
- **Rating 3** (moderate outlook + low-mod wages): ~39.2% — 28.9M workers
- **Rating 4** (good outlook + high wages): ~47.1% — 26.5M workers
- **Rating 5** (strongest outlook + high wages): ~47.8% — 32.0M workers

The pattern is the opposite of what a simple automation-replaces-bad-jobs story would predict. The highest-rated occupations — those with the strongest labor market outlook *and* the highest wages — carry the highest AI exposure. Rating 4 and 5 occupations average 47-48% tasks affected, nearly double the exposure of Rating 0-1 occupations. These are the professional, technical, and managerial roles where AI capability has penetrated deeply into information-processing tasks, but the jobs themselves remain in high demand precisely because the remaining tasks (judgment, leadership, client relationships) are durable.

Ratings 0 and 1 cluster at the low end of both exposure and employment. These are small-population occupations with either weak markets or low compensation — and low AI exposure suggests they're in sectors where AI capability hasn't arrived or the tasks are physically grounded.

Rating 2 is the largest bucket (62.8M workers) with moderate exposure (33.9%). These are high-wage roles with limited projected openings — potentially the most vulnerable segment, as AI exposure could further constrain already-limited growth.

![AI Exposure Distribution by Job Outlook Rating](figures/outlook_exposure_violin.png)

![Workers by Outlook Rating and Exposure Tier](figures/outlook_tier_heatmap.png)

---

## Sector × Zone Interactions

Looking at average pct_tasks_affected broken out by major sector and job zone gives a more granular picture. A few patterns stand out:

The Computer and Mathematical sector is high-exposure across all zones, but particularly in Zone 3-4 where most of those jobs sit. Sales is similarly high across zones. Education shows interesting variation — Zone 3 and 4 educational roles (community college instructors, high school teachers) have moderate exposure, but Zone 5 (university professors, researchers) show more mixed results.

Healthcare shows the largest within-sector zone variation: healthcare support roles (Zone 2-3) have substantially lower exposure than healthcare practitioners (Zone 4), which is partly counterintuitive — the higher-paid clinical roles are more task-penetrated by AI than the support roles, because the AI capability assessment captures the information-processing components of clinical work (documentation, diagnostics, knowledge retrieval) better than the physical patient care components.

![Average % Tasks Affected by Sector and Job Zone](figures/major_zone_heatmap.png)

---

## MCP-Only Zone Analysis

The primary config (All Confirmed) combines AEI conversational data, AEI API data, and Microsoft data. One concern is user self-selection bias: the occupations showing high exposure in Zone 4 might simply be the ones whose workers are more likely to use AI tools like Copilot or Claude, causing them to appear in the AEI usage data. To test this, we can look at MCP-only data — capability assessments derived from tool server specifications rather than user interaction logs.

MCP-only average pct_tasks_affected by zone:

- **Zone 1**: ~14.0%
- **Zone 2**: ~31.7%
- **Zone 3**: ~26.3%
- **Zone 4**: ~38.0%
- **Zone 5**: ~22.7%

The Zone 4 peak persists in MCP data, though at lower absolute levels (38% vs 51% in All Confirmed). The Zone 4 concentration is not purely an artifact of user selection bias — MCP servers are tool specifications, not user interaction logs. However, MCP carries its own bias: the tools built as MCP servers are likely built for the workflows of higher-zone professionals (code, analysis, document management), so the Zone 4 signal may be partly a reflection of which tools have been built, not which jobs are inherently most exposed.

The drop from Zone 4 to Zone 5 is sharper in MCP (38% → 23%) than in All Confirmed (51% → 49%), suggesting that Zone 5 work benefits more from conversational AI than from agentic tooling.

Zone 1 occupations show 14% exposure under MCP — lower than any other zone. This could mean Zone 1 tasks are genuinely less AI-capable, or it could mean the MCP tool ecosystem simply hasn't targeted those workflows. The fact that Zone 1 exposure is also low in All Confirmed (27%) — where user-driven data should pick up ChatGPT-style usage if it were happening — suggests the signal is real rather than a gap in tool coverage.

![AI Exposure by Job Zone — MCP Only](figures/zone_exposure_violin_mcp.png)

![Workers by Job Zone and Exposure Tier — MCP Only](figures/zone_tier_heatmap_mcp.png)

---

## Task Frequency and Normalized Penetration by Zone

To understand *why* certain zones show higher exposure, we can look at the underlying task-level data in the All Confirmed dataset.

**Task frequency (freq_mean)** measures how frequently each task appears in the AI capability data. Higher freq_mean means the task has been assessed as AI-capable more consistently across sources.

**Pct normalized (pct_normalized)** measures the normalized penetration level of each task — how deeply the AI capability claim penetrates that task.

![Average Task Frequency by Job Zone](figures/zone_freq_bar.png)

![Task Frequency Distribution by Job Zone](figures/zone_freq_violin.png)

![Average pct_normalized by Job Zone](figures/zone_pct_norm_bar.png)

![pct_normalized Distribution by Job Zone](figures/zone_pct_norm_violin.png)

---

## What This Means for Policy

The standard policy frame on automation is to focus on low-skill workers — the ones most at risk from routine displacement. This data complicates that. The highest absolute exposure is concentrated in Zone 4 — the credentialed, educated professional workforce. These workers have more resources to adapt, but they also represent a much larger share of aggregate wages. A 10% productivity shock to Zone 4 workers across all sectors has enormous wage implications.

Zone 1 and 2 workers carry lower average exposure but are far less buffered. Their jobs are exposed primarily through specific high-penetration pockets within otherwise lower-exposure sectors — the administrative layer embedded in physically-grounded work. When that layer gets automated, those workers have fewer alternatives.

The outlook data shows that the highest-rated jobs (Rating 4-5, strong outlook + high wages) carry the highest AI exposure. This inverts the simple automation-replaces-vulnerable-jobs narrative: the jobs the market values most are also the ones most penetrated by AI capability claims. Whether this means those jobs will be augmented (higher productivity, higher wages) or disrupted (fewer needed) is the open question.
