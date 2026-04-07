# Work Activity Exposure: Audience Framing

**TLDR:** Four audiences need four different framings of the same underlying finding. 82% of workers are in activities with at least 33% AI exposure. The robust activities are physical; the fragile ones are informational and cognitive. AI's footprint is growing. But what that means for investment, training, career decisions, and policy differs substantially by who's reading it.

---

## For Policymakers

The investment question is: where does workforce development funding have the highest return given AI's trajectory?

The key number: **82% of workers affected are doing activities with ≥33% AI exposure.** That's 64.5M out of 78.6M workers in activities with meaningful AI overlap. The at-risk population is not a niche — it's most of the working population.

But "at risk" varies enormously by intensity. The 23.6M workers in fragile activities (≥66% exposure) are in jobs where more than two-thirds of the task value is AI-reachable. These are the immediate policy targets: customer service, legal research and documentation, marketing, software design, data analysis, and instructional design. The 40.8M in moderate activities (33–66%) are likely to see restructuring rather than elimination — the composition of their work changes, but the job doesn't disappear.

**Where should training dollars go?**

The activities that are durable across all five data sources — physical supervision, caregiving, inspection, compliance monitoring — are the target for training investments that will hold value. The large-workforce durable activities (1.15M workers in "direct organizational operations," 549K in "assist individuals with special needs") are where training programs can reach scale.

The ceiling data shows the next wave: "Scheduling Work and Activities" is 45% confirmed but 85% ceiling. "Documenting/Recording Information" is 37% confirmed but 67% ceiling. Operational and administrative work that looks moderately exposed now is tracking toward highly exposed. Funding programs built around administrative efficiency should be time-limited with clear transition pathways.

The most important policy signal: **the education system's core activities are growing fastest.** Evaluating student work, developing learning materials, assessing student capabilities — these grew 50–77 percentage points in 15 months. Policy intervention in how schools are adapting to AI shouldn't wait for educators to self-report.

![Where Workforce Investment Matters Most](../questions/work_activity_exposure/audience_framing/figures/policy_gwa_workers.png)

---

## For Workforce Development and Educators

The practical question is: which activity types should you build training programs around, and which should you be restructuring away from?

**The training sweet spot:** activities that are robustly AI-resistant AND have a large workforce — these are where investment will have staying power.

Top 10 by workers:

| IWA | Workers | Confirmed % |
|-----|---------|------------|
| Direct organizational operations | 1.15M | 20.7% |
| Assist individuals with special needs | 549K | 7.5% |
| Provide food or beverage services | 521K | 18.8% |
| Supervise personnel activities | 496K | 18.7% |
| Monitor health conditions | 303K | 19.1% |
| Inspect commercial/industrial systems | 244K | 11.0% |
| Monitor operations for compliance | 239K | 22.8% |
| Stock supplies or products | 221K | 12.7% |

These activities share two characteristics: they happen in physical environments, and they require situational judgment in real time. Train people toward these — or train the adjacent skills that make people effective in these activity clusters.

**What to stop building:** any training program centered on activities with confirmed exposure ≥66% and a strong trend line. Legal research (93%), marketing content (85%), data analysis (79%), customer inquiry response (75%), technical product explanation (82%) — programs focused on these specific activities are training people for work that's already heavily AI-reached. The question isn't whether to include AI tools in the curriculum; it's what human contribution these roles need after AI handles the baseline.

**The "prompting" question:** some programs are pivoting to teach AI prompting as a core skill. The data says prompting is inside the fragile zone — "Operating computer systems or computerized equipment" (77%), "Working with Computers" (69%). Prompting AI is itself an AI-reached skill. Teaching people to prompt is valuable today; calling it the durable skill set is not supported by this data.

What is supported: teaching the layer above prompting. Judgment about when the AI is wrong. Evaluation of AI-generated outputs. Physical and operational competencies that provide the judgment context AI assists with. These sit in the durable tier.

![Training Sweet Spot — Large Workforce, AI-Resistant](../questions/work_activity_exposure/audience_framing/figures/workforce_training_targets.png)

---

## For Researchers

The methodological framing: what does this data actually support, and where are the key uncertainties?

**What's novel:** mapping AI exposure at the IWA level (rather than occupation level) lets you see the within-occupation variation in AI impact. A registered nurse's task set spans activities from "monitor health conditions" (19% — robust) to "respond to customer inquiries" (75% — fragile). Occupation-level analysis averages over that variation and misses it. Activity-level analysis surfaces it.

**What the data supports:** activity-level ranking of AI exposure across five independent data sources. The config comparison at the GWA level shows where sources agree (legal/writing/analysis activities: tight clustering) and where they diverge (scheduling, documentation, coaching: wide spread).

The widest cross-config disagreements:

| GWA | Confirmed % | Ceiling % | Range |
|-----|------------|-----------|-------|
| Scheduling Work and Activities | 44.9% | 85.3% | 40.4pp |
| Coaching and Developing Others | 51.7% | 51.7% | 38.0pp |
| Documenting/Recording Information | 37.3% | 67.1% | 29.8pp |
| Training and Teaching Others | 52.4% | 53.3% | 32.5pp |

"Scheduling" has a 40pp range because agentic AI (MCP + API configs) is very good at structured scheduling tasks but conversational AI isn't being used for them much. The source of the disagreement is architecturally specific — it's about which AI interface is being used, not uncertainty about whether AI can handle the work.

"Coaching and Developing Others" shows high confirmed usage in conversational configs but almost zero in agentic configs. Coaching happens through conversation; there's no agentic deployment pathway for it. This is structurally different from the scheduling gap.

**What the data doesn't support:** causal claims about whether AI exposure leads to employment changes. This is usage correlation and capability assessment data, not labor market outcome data. The exposure is real; what happens to jobs as a result requires separate evidence.

**The AEI-only picture (eco_2015 baseline):** this analysis uses pre-combined datasets (is_aei=False) for consistency, which means all five configs use the eco_2025 O*NET baseline. Running the raw AEI datasets against the eco_2015 baseline would give a second perspective, but comparing those results directly with the main analysis requires care because the task inventories differ. For work activity research requiring the AEI-specific baselines, use the raw AEI series (`AEI Both`, `AEI Conv`) through the backend WA pipeline separately.

![Config Agreement at GWA Level](../questions/work_activity_exposure/audience_framing/figures/researcher_config_comparison.png)

---

## For Laypeople

The plain-language version of what this data says.

**Is AI a fad?**

No. 284 out of 332 work activity categories got more AI-exposed between September 2024 and February 2026. That's 86% of the activity spectrum moving in the same direction. 72 activity types went from essentially zero AI impact to meaningfully impacted in 15 months.

The activities that grew the most include evaluating student work (+77pp), assessing student capabilities (+54pp), and developing lesson plans (+50pp). If AI were a fad, these activities would not be showing up in the top growth categories.

**Will my kids need to be programmers?**

Probably not in the traditional sense. Software design is 74% AI-exposed — the programming tasks themselves are highly reachable by AI tools. But that doesn't mean technical literacy doesn't matter. The skill that matters more is judgment: knowing when the AI is wrong, evaluating AI-generated outputs, understanding what you're trying to accomplish well enough to direct the AI toward it.

The durable activities — the ones AI isn't replacing — are physical, supervisory, and caregiving. Direct care for people with special needs. Supervising work on physical sites. Inspecting equipment. Monitoring compliance in real environments. These require being somewhere, knowing a physical context, and making judgments in real time. That's what the data says is hard to replace.

**What fraction will be prompting or doing spreadsheets?**

AI-accessible activities (≥33% exposure) cover 82% of the workforce by exposure count. Prompting and spreadsheet work both sit inside this zone — "Working with Computers" is 69% exposed. Using AI tools is a skill; it's just not a skill that's likely to be scarce for long. What will be scarce is the judgment and physical capability that AI assists rather than replaces.

**So what should I tell my kid to study?**

The data points toward: physical competency, caregiving and supervision, real-world operational skills, and the analytical layer *above* AI-generated output — not the layer AI handles directly. The interpersonal domain (47% avg exposure) is partially AI-adjacent and partially not; the non-AI portion of it involves real human relationships and situational judgment that doesn't reduce to text generation.

There's also a reasonable argument for studying the things that are most exposed — not to replace AI, but to direct it effectively. Someone who deeply understands legal research, marketing strategy, or data analysis will use AI tools more effectively than someone who doesn't. The exposed activities aren't worthless; they're restructuring.

![AI Exposure Over Time — Is It Growing?](../questions/work_activity_exposure/audience_framing/figures/layperson_ai_trend.png)

---

## Config

- **Primary**: AEI Both + Micro 2026-02-12 | freq | auto-aug on | national
- **Ceiling**: All 2026-02-18 | freq | auto-aug on | national
- **Trend**: AEI Both + Micro series (2024-09-30 → 2026-02-12)

## Files

| File | Description |
|------|-------------|
| `results/policy_key_stats.csv` | High-level policy statistics |
| `results/workforce_training_sweet_spot.csv` | Robust IWAs with large workforce |
| `results/researcher_config_spread.csv` | GWA config spread and CV |
| `results/layperson_gwa_summary.csv` | GWA summary for lay audience |
