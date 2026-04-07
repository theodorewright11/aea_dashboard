# Job Risk Scoring: Which Jobs Are Most at Risk?

*Config: all_confirmed (primary) | all_ceiling (comparison) | Weighted scoring, max 11 | Exposure gate at 33%*

---

## TLDR

A seven-flag weighted scoring system separates 923 occupations into three risk tiers. 195 occupations employing 50.7 million workers land in the high tier (scores 8--11), where both direct AI exposure and structural vulnerability converge. The moderate tier is the largest at 504 occupations and 82.5 million workers -- and the most internally diverse, ranging from structurally vulnerable jobs with almost no AI exposure to highly exposed jobs protected by education requirements or strong demand. The most useful finding: what drives a score of 4 is completely different from what drives a score of 7, and that distinction matters more than the tier label.

---

## How the Scoring Works

Seven binary flags, split into two categories. Flags 1--4 measure direct exposure signal: is AI already handling this job's tasks, does AI capability exceed the job's skill requirements, and are both of those trends accelerating? Flags 5--7 measure structural vulnerability: low preparation barrier (job zone 1--3), below-average labor market outlook, and commoditized software tooling.

| Flag | What it measures | Weight |
|------|------------------|--------|
| 1. pct_tasks_affected > median | Breadth of AI task coverage | 2x |
| 2. SKA gap > median | AI capability exceeds job's skill needs | 2x |
| 3. pct trend positive + above-median growth | Task exposure is accelerating | 2x |
| 4. SKA gap trend positive + above-median growth | Skill coverage is accelerating | 2x |
| 5. job_zone in {1, 2, 3} | Low-to-moderate preparation barrier | 1x |
| 6. outlook in {2, 3} | Below-average labor market outlook | 1x |
| 7. n_software > median | Commoditized tooling | 1x |

The exposure flags carry double weight because they measure what AI is actually doing to the job right now, while structural flags measure how defensible the job is against disruption. Maximum possible score: 11 (four exposure flags at 2x = 8, plus three structural flags at 1x = 3).

One guard rail: the **exposure gate**. Any occupation scoring 8+ but with less than 33% of tasks affected gets downgraded from high to moderate. The logic is simple -- if AI isn't touching a third of your tasks, calling you "high risk" based on structural factors alone would be misleading. 13 occupations triggered this gate.

**Tiers:** 8--11 = High Risk, 4--7 = Moderate, 0--3 = Low.

---

## The Distribution

| Tier | Occupations | Total Employment | Avg % Tasks Affected | Avg Risk Score | Workers Affected | Wages Affected |
|------|-------------|------------------|----------------------|----------------|------------------|----------------|
| **High (8--11)** | 195 | 50.7M | 56.4% | 9.08 | 28.9M | $1.39T |
| **Moderate (4--7)** | 504 | 82.5M | 35.9% | 5.62 | 28.1M | $2.28T |
| **Low (0--3)** | 224 | 20.1M | 19.0% | 2.10 | 4.3M | $321B |

The high-risk tier contains just 21% of scored occupations but accounts for 33% of total employment -- 50.7 million workers in jobs where multiple replacement signals line up. Average task exposure in this tier is 56.4%, roughly triple the low tier's 19.0%.

But the moderate tier is where the action is, at least in terms of economic scale. It covers 504 occupations, 82.5 million workers, and $2.28 trillion in affected wages -- more than the high tier on every dimension except average exposure intensity. The moderate tier's workers-affected count (28.1M) nearly matches the high tier's (28.9M). That's because the moderate tier is enormous and heterogeneous: it contains both the "exposed but protected" occupations (high task coverage, high job zone, good outlook) and the "structurally vulnerable but not yet exposed" occupations (low task coverage, low job zone, poor outlook). These are fundamentally different situations wearing the same label.

The low tier is small -- 224 occupations, 20.1 million workers. These jobs either have minimal AI task overlap, sit behind substantial preparation barriers, or both.

![Risk Tier Distribution](../questions/job_exposure/job_risk_scoring/figures/risk_tier_distribution.png)

---

## What Drives Each Score Level

This is the section that reveals what the composite score actually means at each level. The flag breakdown chart shows, for each score from 0 to 11, what percentage of occupations at that score have each flag active. The patterns are striking.

![Flag Breakdown by Score](../questions/job_exposure/job_risk_scoring/figures/flag_breakdown_by_score.png)

**Score 0 (9 occupations, avg pct 13.2%):** No flags triggered. These are occupations like Anesthesiologists, Emergency Medicine Physicians, and Pediatric Surgeons -- high job zone, strong outlook, minimal AI task overlap, skill requirements AI doesn't meet. The absence of every signal is itself a signal: these jobs sit outside AI's current reach on every measured dimension.

**Scores 1--3 (Low tier):** Flags appear sparsely and without clustering. A score of 1 might mean just a single structural flag (e.g., low job zone) or one exposure flag at 2x. A score of 3 could be one exposure flag plus one structural, or three structural flags. There's no dominant pattern here -- low-risk occupations are low-risk for varied reasons.

**Score 4 (141 occupations, avg pct 17.2%):** This is where it gets interesting. Score 4 sits at the bottom of the moderate tier, and its flag profile is almost entirely structural. 89% of score-4 occupations trigger the job zone flag. 87% trigger the outlook flag. But only 6% trigger the pct_tasks_affected flag, and trend flags are similarly rare. These are jobs that look vulnerable on paper -- low preparation barrier, weak labor market position, commoditized tools -- but where AI isn't yet doing much of the actual work. Think of it as latent risk: the structural conditions for displacement exist, but the technology hasn't arrived in these tasks yet.

**Score 5 (101 occupations, avg pct 29.8%):** The transition zone. Exposure flags start appearing alongside structural ones, but coverage is uneven. You see occupations where one exposure signal is strong (maybe high task percentage at 2x, pushing the score to 5 with one structural flag) mixed with occupations where moderate exposure meets moderate structural vulnerability.

**Score 6 (102 occupations, avg pct 33.3%):** Exposure flags become more common. Roughly half the occupations at this level trigger the pct flag, and trend flags start appearing with regularity. The balance between exposure-driven and structure-driven starts shifting toward exposure.

**Score 7 (160 occupations, avg pct 55.0%):** The crossover point. Score 7 is dominated by exposure signal: 91% trigger the pct flag, 88--89% trigger both trend flags. Structural flags are still present but they're no longer doing the heavy lifting. Market Research Analysts sit here -- 89.5% task exposure, but zone 4 and a favorable outlook (rating 4) keep them from triggering structural flags. Software Developers land at score 5 with 45.2% task exposure -- moderate AI overlap, but job zone 4 and strong outlook (rating 5) push their structural flags to zero.

**Score 8 (139 occupations, avg pct 52.4%):** The low end of the high tier. These occupations clear the exposure gate (pct >= 33%) and have all or nearly all exposure flags active, plus enough structural flags to cross the threshold. Waiters and Waitresses (39.4% pct, 2.3M workers) sit right at score 8, barely above the exposure gate. Economists score 8 too, at 82.5% task exposure -- they hit all four exposure flags at 2x = 8, but their high job zone means none of the structural flags trigger.

**Score 9--10:** Nearly all flags active, with one or two missing. The occupations that score 10 but not 11 typically miss one structural flag -- either they have adequate outlook, or their software count falls below the median.

**Score 11 (28 occupations, avg pct 64.7%):** Every flag active. The "perfect storm" occupations. Customer Service Representatives (84.1% pct, 2.7M workers, $113B in affected wages). Secretaries and Administrative Assistants (75.1% pct, 1.7M workers). Bookkeeping Clerks (69.6% pct, 1.5M workers). Data Entry Keyers (65.9%). These occupations combine broad AI task coverage, a skill profile AI already exceeds, accelerating trends on both dimensions, low preparation barriers, poor labor market outlook, and heavy commoditized tooling. Every measurable signal points the same direction.

**The key pattern across all of this:** the moderate tier contains two fundamentally different populations. Score 4 is structural vulnerability without exposure -- latent risk. Score 7 is exposure-driven risk that structural factors partially mitigate. Lumping these together under "moderate" obscures the distinction. The score-4 occupation might never face displacement if AI doesn't penetrate its task domain. The score-7 occupation is already exposed and is only held back by education requirements or demand conditions that could shift.

![Risk Score vs Task Exposure](../questions/job_exposure/job_risk_scoring/figures/risk_vs_pct_scatter.png)

---

## Cross-Config Robustness

The scoring framework runs identically across all five analysis configurations -- from All Confirmed (our primary, using only confirmed AI capabilities) to All Sources Ceiling (including theoretical maximum capabilities). The question: how stable are the tier assignments?

272 occupations change tier in at least one config. Most of these shifts are single-tier moves (moderate to high or low to moderate) driven by exposure flags flipping near the thresholds. Structural flags (job zone, outlook, software count) don't change between configs because they're properties of the occupation, not of the AI measurement source. So cross-config volatility is concentrated entirely in flags 1--4.

Four occupations make big jumps -- low to high or vice versa:

- **Geothermal Technicians:** Low risk under All Ceiling, high risk under Human Conversation and All Confirmed. The ceiling model doesn't think AI has penetrated their tasks much (they still land at 33.4% pct under all_confirmed, barely clearing the gate). But human conversational AI data tells a different story. Same job, dramatically different risk assessment depending on which AI capability source you trust.

- **First-Line Supervisors of Security Workers:** High risk under All Ceiling and Agentic Confirmed, low risk under Human Conversation. The pattern is reversed. Agentic AI sources see significant task overlap; conversational sources don't.

- **Insurance Appraisers, Auto Damage:** Low in Agentic Confirmed and Agentic Ceiling, high in Human Conversation and All Confirmed. Another case where the AI modality matters.

- **Non-Destructive Testing Specialists:** Low in All Ceiling, high in Human Conversation. Moderate everywhere else.

These examples are useful because they show where the analysis is genuinely uncertain. An occupation that stays in the same tier across all five configs is a robust finding. An occupation that swings from low to high depending on the capability source is telling you something about the limits of the measurement, not just about the job.

![Cross-Config Volatility](../questions/job_exposure/job_risk_scoring/figures/cross_config_volatility.png)

---

## What "High Risk" Actually Means

The label "high risk" invites a specific interpretation: these jobs are going away. But that's not quite what the scoring captures.

What score 8--11 actually says is: AI can already do a substantial share of this job's tasks, AI's capabilities meet or exceed the skill requirements, both of those trends are accelerating, and the job has few structural defenses -- low preparation barrier, weak demand, commoditized tools. All of that can be true and the job can still persist for years, because task exposure doesn't automatically translate to job elimination. Firms have to decide to automate. Workers have to not find adjacent tasks to absorb. Regulatory and institutional friction has to be low enough.

That said, the convergence of all seven signals in the score-11 occupations is hard to dismiss. Customer Service Representatives at 84.1% task exposure with every structural vulnerability flag active -- that's not "might be affected someday." That's a job where the technology exists, the economics favor substitution, and the trend line is accelerating. The question is timing, not direction.

The more interesting interpretive challenge is the moderate tier. A score-4 occupation and a score-7 occupation have the same tier label but face completely different situations. Policy responses should differ too: score-4 occupations need monitoring, while score-7 occupations need active workforce transition planning. The three-layer framing (exposure signal vs. structural vulnerability vs. composite) matters more than the tier label itself.

And the exposure gate does real work here. Without it, 13 more occupations would be labeled high risk despite having less than a third of their tasks exposed to AI. The gate ensures that "high risk" retains a minimum level of face validity -- you can't be high risk if AI isn't actually doing much of your work, no matter how structurally vulnerable you look.

---

## Config

**Primary:** All Confirmed (all_confirmed). This uses only confirmed AI capabilities across all source types -- the most conservative measure of what AI can demonstrably do today.

**Comparison:** All Sources Ceiling (all_ceiling) is shown as the upper bound throughout, representing what AI could theoretically handle given maximum capability assumptions.

**Three-layer framing:** The analysis separates exposure signal (flags 1--4, weighted 2x) from structural vulnerability (flags 5--7, weighted 1x) and composite score, allowing each dimension to be examined independently.

**Scoring:** Flags 1--4 weighted 2x each (max 8), flags 5--7 weighted 1x each (max 3), total max 11. Exposure gate at 33% pct_tasks_affected prevents structural-only high-risk assignments. Tiers: 8--11 High, 4--7 Moderate, 0--3 Low.

**Trend:** Computed as last minus first date across the full time series for each config. Cross-config comparison uses all five configs.

**Method:** freq, auto-aug ON, national scope.

## Files

| File | Description |
|------|-------------|
| `results/risk_scores_primary.csv` | All 923 occs: 7 flags, risk_score, risk_tier (all_confirmed) |
| `results/risk_scores_all_configs.csv` | Risk scores for all five configs |
| `results/risk_tier_summary.csv` | Tier counts, employment, wages |
| `results/flags_breakdown.csv` | How often each flag is triggered |
| `results/cross_config_tier_shifts.csv` | Occupations that change tier across configs |
| `results/pivot_distance_inputs.csv` | Top/bottom 10 occs per zone (input for pivot_distance) |
