# Zone Pivot Anatomy: Why Zone 3 Peaks

*Config: all_confirmed — AEI Both + Micro 2026-02-12 | Skills + Knowledge, importance ≥ 3 | Pivot groups: same top-10 high/low risk per zone as pivot_distance/*

---

Zone 3's 359-unit pivot cost isn't just the highest — it's structurally different from what's happening in zones 4 and 5. The short answer is that zone 3's high-risk workers (clerks, tutors, bookkeepers) are being asked to pivot into skilled trades (nuclear operators, solar installers, geothermal managers), and those two populations have almost nothing in common. Zones 4 and 5 are pivoting professional to professional — writers to teachers, academics to clinicians — and the profiles share enough ground that the distance is smaller. But the more important finding for retraining targeting is this: job zone is not the right filter. Zone 4 has more high-risk occupations than zone 3, zone 5 has almost none, and the zone-level cost figures are an artifact of which sectors ended up on each side of the risk line within each zone.

---

## How many at-risk occupations are in each zone?

![Occupation Counts by Zone and Risk Tier](results/figures/occ_counts_by_zone_tier.png)

The top-line finding here overrides the intuition the zone-3-crisis framing creates. Zone 4 has the most high-risk occupations in the entire system — 45, more than zone 3 (35) or zone 2 (32). Zone 5 has almost none: 2 high-risk occupations out of 154. If you're trying to target retraining investment, "focus on zone 3" is only right if you're targeting the hardest reskilling cases. If you're targeting the largest at-risk population, zone 4 is actually where the action is.

Zone 2 is underappreciated in this framing too. It has 32 high-risk occupations and 124 mod-high — a massive risk pool in a zone that has relatively cheap pivots (181 units). That combination (large at-risk group, low cost to help them) is arguably the best-value retraining target in the system.

Zone 1 effectively has zero high-risk presence (1 occupation). Zone 5's 2 high-risk occupations are almost certainly statistical edge cases — the exposure gate and SKA flag combination rarely triggers for doctoral-level work.

---

## What's driving the exposure difference within each zone?

![Mean % Tasks Affected by Zone and Risk Tier](results/figures/zone_exposure_profiles.png)

Exposure scales sharply with job zone in the high tier. Zone 3 high-risk occupations average 63% tasks affected; zone 4 averages 69%; zone 5 averages 78% (on just 2 occupations). So the exposure isn't flat — higher zones do have more AI task penetration in their at-risk occupations.

The more important pattern is the mod-high tier. Zone 4 mod-high occupations average 53% tasks affected, and zone 5 mod-high averages 70%. That's higher than zone 3's mod-high (31%). This means a lot of zone 4–5 occupations that would score high on raw exposure are being held at mod-high by the other risk flags — they don't hit the full weighted score threshold. These are occupations that are heavily AI-exposed but don't show the supporting structural signals (outlook, trend growth, software, auto-aug). That's actually a real segment: occupations where AI is already doing a lot but the formal risk tier undersells it.

---

## Why does zone 3 have higher pivot cost than zones 4 and 5?

![SKA Profile Structure: Shared Mass vs. Pivot Cost vs. Drop Cost](results/figures/ska_mass_and_overlap.png)

The stacked bars show three components in absolute imp×level units:
- **Blue (shared)**: what the high-risk worker already has that matches the low-risk destination
- **Orange (must acquire)**: the actual pivot cost — new SKA mass the worker needs to build
- **Gray (drop)**: what the high-risk worker has that the low-risk destination doesn't need (surplus that doesn't help)

Two things stand out immediately. First, zone 3 has the largest orange bar — 347 units to acquire, compared to 231 for zone 4. Second, zone 3 has an almost nonexistent gray bar (66 units), meaning the high-risk workers barely have any surplus over the destination. They're not over-qualified and misaligned — they're under-equipped and starting from a shallower profile.

The numbers make the asymmetry concrete:
| Zone | High-risk SKA mass | Low-risk SKA mass | Shared | Overlap % |
|------|-------------------|-------------------|--------|-----------|
| 1 | 307 | 200 | 142 | 70.8% |
| 2 | 400 | 354 | 180 | 51.0% |
| 3 | 475 | 755 | 409 | 54.1% |
| 4 | 609 | 711 | 480 | 67.5% |
| 5 | 608 | 689 | 447 | 65.0% |

Zone 3's low-risk occupations have a 755-unit SKA mass — 280 units more than the high-risk side. That's the destination zone 3 workers are being asked to reach. By contrast, zone 4's gap is 102 units and zone 5's is 80 units. The destination profiles in zones 4 and 5 are large, but the starting points are also large and they overlap more (67–65% vs. 54%).

The reason the gap is so severe in zone 3 is structural, not mathematical. Skilled trades and nuclear/energy operations (the zone 3 low-risk jobs) require deep technical and applied science knowledge — physics, mechanical systems, building/construction, operations monitoring. Office and administrative workers (the zone 3 high-risk jobs) don't develop any of that. It's not that the reskilling cost is high because the math happens to work out that way — it's that these two labor market segments have almost nothing in common, and they both live in zone 3.

Zones 4 and 5 are different. High-risk zone 4 workers (writers, translators, statistical assistants) and low-risk zone 4 workers (special education teachers, biofuels production managers, brownfield specialists) both operate in knowledge-intensive professional environments. The shared intellectual infrastructure — research frameworks, analytical methods, professional judgment — makes the transition more about redirecting skills than building new foundations.

---

## Which sectors are the at-risk occupations in each zone?

![Sector Composition of High-Risk Occupations by Zone](results/figures/sector_composition_high_risk.png)

The sector chart is where the "is job zone the right filter?" question gets answered directly.

Zone 3 high-risk occupations are almost entirely Office and Administrative Support. The risk picture in zone 3 isn't spread across industries — it's concentrated in one labor market segment that also happens to be the largest occupational group in the economy. Any retraining program targeting zone 3 is effectively targeting clerical and administrative workers.

Zone 4 is more distributed. Business/Finance, Management, Legal, Education, and Healthcare all contribute meaningfully to zone 4's high-risk pool. This is actually harder to program for — there's no single sector to target — but it also means the risk is spread across labor market segments with higher wages and more organizational capacity to absorb retraining costs.

Zone 2 shows a similar concentration pattern to zone 3 but at a lower zone — predominantly Sales and Office/Admin, with some Healthcare support occupations.

Zone 5's two high-risk occupations are too small a sample to draw conclusions from.

---

## Zone 3 vs. Zone 4: who's at risk and where?

![Zone 3 vs Zone 4 Occupations: Exposure × Risk Score by Sector](results/figures/zone34_scatter.png)

The scatter puts individual occupations on the board. A few things are immediately visible.

Zone 3 is dense in the upper-right quadrant — many Office/Admin occupations with high exposure (>60%) and high risk scores (7–10). The high-risk zone 3 occupations are a large, coherent block: they're not scattered across sectors and exposure levels, they're concentrated in one region of the chart. This is what makes zone 3 an obvious targeting zone: the at-risk workers are numerous, similar to each other, and clustered in one sector.

Zone 4 is more dispersed. High-risk zone 4 occupations (scores 8–10) come from multiple sectors and span a wider exposure range. There are fewer occupations in the extreme high-risk corner, but more scattered across the 50–80% exposure band. The "at risk but not maximally so" zone 4 population — the mod-high cluster — is large and heterogeneous.

The 33% exposure gate (gray dotted line) shows that almost all zone 4 occupations are above it — zone 4 exposure is generally high across the board, meaning the risk tier distinctions in zone 4 are being driven by the supporting flags (trend, SKA, software, auto-aug) rather than raw exposure. That's different from zone 3, where there are more occupations below the exposure gate.

---

## The targeting question

Job zone is a useful *cost* signal for retraining, not a *scale* signal. Here's how to read it for a "where to invest" frame:

**Zone 2** is the highest-value retraining opportunity: large at-risk population (32 high, 124 mod-high), relatively low pivot cost (181 units), and pivots that are heavily AI-assisted (98.6%). The workers are predominantly in Sales and Office/Admin — accessible labor market segments. The gap elements are mechanical and construction knowledge, which requires hands-on training but not years of professional school.

**Zone 3** is the hard case. Large at-risk population (35 high, 104 mod-high), highest pivot cost (359 units), and the required reskilling is fundamentally a sector change — from clerical/knowledge work to skilled trades. Programs that work here need to be trades-oriented, apprenticeship-heavy, and willing to run for 12–24 months. Short-cycle digital literacy programs will not close a physics-and-mechanical knowledge gap.

**Zone 4** has the most individual high-risk occupations (45) but lower pivot costs (231 units) and higher overlap (67.5%). These workers are professional-level and pivoting to other professional-level jobs. The reskilling is more about domain transfer than building from scratch. Higher organizational capacity (employers, professional associations) to absorb training costs. Probably the best candidate for employer-led upskilling programs rather than public workforce programs.

**Zone 5** is not a retraining target. Two high-risk occupations, both extreme edge cases. The Mod-High population in zone 5 is real (55 occupations, 70% average exposure) but is being held back by risk factors other than exposure — that population is worth watching but doesn't look like a near-term displacement cohort.

The paper's "where to invest" signal is probably zone 2 (high value, accessible) and zone 3 (large and hard, needs specialized programs), with zone 4 as a secondary target for employer-led professional development. Zone is not the only dimension — zone × sector is the right cell. Zone 3 × Office/Admin is the single biggest retraining target in the system. Zone 4 × Business/Finance and Zone 2 × Sales are close behind.

---

## Config and files

| Setting | Value |
|---------|-------|
| Primary config | all_confirmed — AEI Both + Micro 2026-02-12 |
| SKA | compute_ska(), importance ≥ 3, skills + knowledge |
| Pivot groups | Same top-10 high/low risk per zone as pivot_distance/ |
| Risk scores | job_risk_scoring/results/risk_scores_primary.csv |

| File | What it contains |
|------|-----------------|
| `results/figures/occ_counts_by_zone_tier.png` | Stacked bar: n_occs by zone × tier |
| `results/figures/zone_exposure_profiles.png` | Grouped bar: mean pct_tasks_affected by zone × tier |
| `results/figures/ska_mass_and_overlap.png` | Stacked bar: shared / pivot / drop components per zone |
| `results/figures/sector_composition_high_risk.png` | Sector breakdown of high-risk occs per zone |
| `results/figures/zone34_scatter.png` | Scatter of zone 3 and zone 4 occs by exposure × risk score |
| `results/zone_overlap_stats.csv` | Zone-level overlap stats (shared mass, pivot cost, drop cost, overlap %) |
| `results/occ_counts_by_zone_tier.csv` | Raw occupation counts by zone × tier |
| `results/zone_exposure_by_tier.csv` | Mean/median pct_tasks_affected by zone × tier |
