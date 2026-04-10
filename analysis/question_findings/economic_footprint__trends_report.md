# Economic Footprint: Time Trends

The All Confirmed worker count grew from 46.6M to 61.3M between March 2025 and February 2026 — a 31% increase in 11 months — with most of the growth coming from a sustained expansion of confirmed AI capability claims rather than changes in the labor market. At the sector level, Sales, Computer and Mathematical, and Legal occupations have seen the largest absolute gains in task exposure since March 2025. The ceiling estimates have grown in parallel, meaning the confirmed/ceiling gap hasn't meaningfully narrowed — new capabilities keep expanding both bounds simultaneously.

---

## How the Aggregate Has Moved

The All Confirmed series shows sustained growth over the full dataset window. The pattern across configurations:

- The ceiling configuration (All Sources) started at 46.6M workers in March 2025 and reached 77.1M by February 2026. That's a 65% increase in 11 months.
- Human Conversation (confirmed) started at 46.6M and reached 54.1M — a 16% increase over the same period.
- Agentic Confirmed (AEI API only) began tracking from August 2025 at 23.4M workers and reached 31.1M by February 2026 — a 33% increase over six months.

The ceiling and confirmed trajectories have moved together rather than converging. A narrowing ceiling/confirmed gap would suggest AI capability claims are becoming more reliable as evidence accumulates. The fact that both are expanding means the frontier is still advancing faster than the validation process can consolidate it. New capabilities keep getting proposed before old proposals fully harden into confirmed status.

The worker count growth is almost entirely driven by new capability claims being added — the labor market itself isn't changing quickly. What's changing is the assessed reach of AI into existing occupational tasks. The same jobs are there; AI keeps finding new footholds in them.

![% of Employment Reached Over Time — All Configs](../questions/economic_footprint/trends/figures/aggregate_trend_pct.png)

Note: the workers-affected trend and this chart are proportional by construction — pct of employment = workers affected / total employment, a fixed scalar. The workers chart is redundant and has been removed. The pct framing is more interpretable.

---

## Sector-Level Growth

The major category trends over the full All Confirmed series reveal which sectors have seen the fastest growth in AI task exposure. Ranked by absolute percentage-point gain from first to last available date:

1. **Sales and Related**: +18.6 pp (41.0% → 59.5%)
2. **Computer and Mathematical**: +16.0 pp (49.8% → 65.7%)
3. **Legal Occupations**: +14.0 pp (34.3% → 48.3%)
4. **Business and Financial Operations**: +12.0 pp (38.7% → 50.7%)
5. **Office and Administrative Support**: +11.7 pp (39.4% → 51.1%)
6. **Educational Instruction and Library**: +11.6 pp (42.0% → 53.6%)
7. **Community and Social Service**: +9.9 pp (37.3% → 47.3%)
8. **Life, Physical, and Social Science**: +9.8 pp (32.0% → 41.8%)

Sales jumping from 41.0% to 59.5% is the largest absolute gain in this window — a sector that was already substantial is now close to 60% task exposure. Computer and Mathematical at 49.8% in March 2025 already reflected broad early AI adoption; the additional 16pp gain to 65.7% reflects continued expansion into a sector that was leading from the start.

Legal grew from 34.3% to 48.3%. Much of Legal's growth had already occurred before March 2025 (Legal was among the fastest-growing sectors in the pre-window period), so the 14pp gain here is the continuation of a trend that began earlier rather than a new inflection.

At the bottom of the growth table: Farming/Forestry (+0.4 pp), Production (+1.5 pp), Transportation (+2.0 pp). Physical, equipment-dependent work where the task frontier hasn't moved much.

![Major Sector Exposure Growth (All Confirmed)](../questions/economic_footprint/trends/figures/major_growth_bar.png)

![Sector-Level Trends Over Time](../questions/economic_footprint/trends/figures/major_trends_confirmed.png)

---

## The Rate of Change Question

Looking at the pace across the series, growth hasn't been uniform. There are step-function jumps rather than smooth curves, corresponding to specific model releases or capability demonstrations that got confirmed across enough tasks to move the aggregate.

The implication: the trend line isn't a reliable basis for mechanical extrapolation. Future growth in assessed exposure will depend on which capabilities next-generation models demonstrate and how quickly those demonstrations propagate into confirmed task assessments. A model that cracks multimodal reasoning or real-world action-taking at scale would produce a jump much larger than anything in the current series.

But the baseline trajectory — a 65% ceiling increase in 11 months — is the kind of growth rate that typically means a technology is past the early-adopter stage and into broad diffusion. The question now is whether the economic impact grows proportionally, or whether deployment friction, organizational inertia, and regulatory constraint slow the realized impact well below the measured capability frontier.

---

## What's Not in the Trends

The trends here are all capability-side — how much of existing work AI can do. What's missing from this picture:

**Actual deployment.** The trend data says AI can do these tasks. It doesn't say firms are actually using AI for them at scale. Capability and deployment are on very different timelines in enterprise settings.

**Wage and employment effects.** Even if AI exposure has doubled, wages in Legal or Education haven't halved. Either firms are using AI to expand output rather than cut headcount, or the deployment curve is lagging the capability curve significantly, or the productivity gains are being captured elsewhere. Probably some of all three.

**Displacement vs. augmentation.** A rising exposure share could mean more workers are being displaced by AI, or it could mean more workers are being augmented by AI tools in their existing roles. The trend data alone can't distinguish these.

The trends analysis sets up the right questions for deeper investigation. The direction is clear: assessed AI capability in the labor market has grown substantially and shows no sign of plateauing. Whether that translates into proportional economic disruption depends on factors that aren't captured in task-level capability data.
