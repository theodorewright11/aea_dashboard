# Work Activity Robustness

**TLDR:** 164 of 332 IWAs are robust (confirmed exposure < 33%) across all five configs. Only 4 are fragile (≥66%) in all five configs — activities where every data source agrees AI is deeply embedded. The "next wave" is 42 IWAs currently below 33% confirmed but where the ceiling already puts them at or above 33%. At the GWA level, only the physically-intensive categories are robust; everything involving information, coordination, or communication is moderate to fragile.

---

## Tier Distribution

| Tier | Threshold | IWAs | Description |
|------|-----------|------|-------------|
| Fragile | ≥ 66% | 52 | Majority of work is AI-exposed |
| Moderate | 33–66% | 116 | Significant AI overlap; expect restructuring |
| Robust | < 33% | 164 | Consistently below the exposure threshold |

164 robust IWAs is about half the universe. But the worker distribution is very different from the activity count: more workers are in moderate and fragile activities than robust ones (see education_lens for the workforce breakdown). Robust activities tend to be physical, operational, and caregiving work — sectors with many jobs but different economic profiles.

---

## The 4 Stably-Fragile Activities

Four IWAs are classified as fragile in every one of the five configs — including the agentic configs where scores are generally lower. These are the activities where confirmed usage, ceiling capability, conversational AI, and agentic AI all agree:

| IWA | Confirmed % |
|-----|------------|
| Research laws, precedents, or other legal data | 92.5% |
| Edit written materials or documents | 77.9% |
| Explain technical details of products or services | 81.9% |
| Analyze market or industry conditions | 76.5% |

Four activities, not ten. The more demanding criterion here is that all five configs include the agentic_confirmed config (AEI API only), which typically shows lower percentages than combined usage configs. For an activity to be fragile in all five configs, it needs to be deeply AI-reached even in tool-use and API patterns, not just conversational AI. Legal research, technical explanation, market analysis, and document editing clear that bar. Other activities that look fragile in three or four configs still show moderate agentic exposure.

Many more activities are fragile in 3–4 configs (the cross-config stability chart shows where configs agree vs. disagree). The four stably fragile are the most robust signal.

---

## The 122 Stably-Robust Activities

122 IWAs are classified as robust (< 33%) in all five configs. They're not at zero exposure — the average in this group is around 12% — but they're consistently below the meaningful-change threshold across every data source.

What characterizes this group? Look at the upper end of the robust tier (activities approaching 33% but staying below):

- Maintain operational records (21%)
- Direct organizational operations (21%)
- Provide food or beverage services (19%)
- Monitor health conditions of humans or animals (19%)
- Supervise personnel activities (19%)
- Monitor safety or security of work areas (13%)

The common thread: activities that require physical presence, real-time environmental awareness, or involve direct care and oversight of people and physical systems. These aren't "unimportant" activities — they're things that happen in a specific place at a specific time with a specific person.

At the bottom of even the robust tier — activities barely touched by any AI source — are truly physical operations: removing workpieces from production equipment (1.7%), operating vehicles (1.4%), cleaning tools and equipment (3.4%).

---

## The Next Wave: 42 IWAs

42 IWAs are currently below 33% confirmed but already have ceiling exposure at or above 33%. These are the activities where AI capability exists to materially affect the work, but that capability isn't yet reflected in usage patterns.

The top 10 by confirmed-to-ceiling gap:

| IWA | Confirmed % | Ceiling % | Gap |
|-----|------------|-----------|-----|
| Record information about environmental conditions | 14.4% | 72.3% | +57.8pp |
| Maintain operational records | 21.2% | 73.0% | +51.7pp |
| Prepare schedules for services or facilities | 31.2% | 82.1% | +50.9pp |
| Assign work to others | 27.8% | 75.3% | +47.5pp |
| Maintain sales or financial records | 28.1% | 75.2% | +47.1pp |
| Test sites or materials for environmental hazards | 0.1% | 46.2% | +46.1pp |
| Remove workpieces from production equipment | 1.7% | 47.1% | +45.4pp |
| Record images with photographic/audiovisual equipment | 21.1% | 64.3% | +43.2pp |
| Schedule operational activities | 26.1% | 66.9% | +40.9pp |
| Analyze environmental or geospatial data | 16.6% | 56.6% | +40.0pp |

The biggest gaps are in record-keeping, scheduling, and assignment work. These aren't creative or analytical activities — they're operational. The reason the ceiling is so much higher than confirmed is that agentic AI (MCP + API) is very good at structured data entry, scheduling, and record management, even though conversational AI usage doesn't show up strongly in these categories. The ceiling is being driven by the agentic configs.

This is actually an important observation about what "confirmed usage" captures vs. what it misses. Conversational AI (Claude, Copilot) shows up in analytical and communication work. Agentic AI shows up in operational and systems work. Activities where the two patterns diverge strongly are where the deployment gap is largest.

![Next Wave — Confirmed-to-Ceiling Gaps](figures/next_wave_gaps.png)

---

## GWA Robustness

At the GWA level, 5 categories are robust, 27 are moderate, and 4 are fragile.

**Robust GWAs (< 33%):**
- Operating Vehicles, Mechanized Devices, or Equipment (1.4%)
- Performing General Physical Activities (12.2%)
- Controlling Machines and Processes (12.7%)
- Repairing and Maintaining Mechanical Equipment (13.5%)
- Handling and Moving Objects (18.1%)

Every robust GWA is a physical-operations category. There is no interpersonal GWA, no cognitive GWA, no communication GWA in the robust tier. The AI-resistant slice of the GWA hierarchy is a clean physical boundary.

**Fragile GWAs (≥ 66%):**
- Working with Computers (69.3%)
- Communicating with People Outside the Organization (69.6%)
- Interpreting the Meaning of Information for Others (70.0%)
- Updating and Using Relevant Knowledge (72.0%)

Four fragile GWAs, and they're all about information and communication. "Communicating with people outside the organization" and "interpreting information for others" are the core activities of professional service work — consulting, customer service, knowledge transfer. That these are fragile categories tells you something about where AI's capabilities have concentrated.

![GWA Robustness Overview](figures/gwa_robustness.png)

---

## Cross-Config Stability

The dot chart below shows IWAs where configs disagree — filtered to activities with more than 3pp spread across the five configs (roughly two-thirds of all IWAs pass this). Each dot is one config's pct_tasks_affected value; the horizontal spread shows how much uncertainty exists for that activity.

The chart legend shows which color corresponds to which config. Activities at the top (high confirmed pct, tight grouping) are where configs agree on high exposure. Activities in the middle with wide spread are where the answer depends heavily on which AI measurement lens you use — often because conversational and agentic AI have different signatures in those activities.

The activities with the widest spread are where the training and workforce implications are most uncertain:

- **"Scheduling Work and Activities"**: confirmed 45%, ceiling 85%. Agentic AI can automate scheduling; conversational AI usage doesn't show it yet. The mode of AI deployment determines the exposure level.
- **"Coaching and Developing Others"**: conversational configs show ~52%; agentic configs show ~10%. Coaching happens through conversation, not through automated pipelines.
- **"Documenting/Recording Information"**: confirmed 37%, ceiling 67%. The gap is agentic deployment of documentation systems.

These aren't errors in the data — they're architecturally specific signals about which AI deployment model reaches each activity type.

![Cross-Config Stability — Where Configs Disagree](figures/cross_config_stability.png)

---

## Config

- **Primary**: AEI Both + Micro 2026-02-12 | freq | auto-aug on | national
- **Ceiling**: All 2026-02-18 | freq | auto-aug on | national
- **Stability check**: All five configs run independently, tier assignments compared

## Files

| File | Description |
|------|-------------|
| `results/iwa_robustness.csv` | All IWAs: confirmed pct, tier, ceiling pct, gap |
| `results/iwa_tier_stability.csv` | Number of configs where each IWA is robust |
| `results/gwa_robustness.csv` | GWA-level tier assignments |
| `results/next_wave_iwas.csv` | 42 IWAs currently robust but ceiling ≥ 33% |
