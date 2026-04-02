# Pivot Distance: Where Is It Cheap to Reskill, and Where Is It Expensive?

*Config: all_ceiling | Method: freq | Skills + Knowledge, importance >= 3 | Top 10 high/low risk per zone*

---

## 1. Framework

Workers in high-risk occupations are not trapped, but the cost of pivoting to a low-risk occupation depends heavily on how specialized the required knowledge is. We measure "pivot distance" as the total skill and knowledge gap a high-risk worker would need to close to reach the profile of a typical low-risk occupation in the same job zone.

For each job zone (1 through 5), we take the top 10 highest-risk and bottom 10 lowest-risk occupations by composite risk score, build their average Skills + Knowledge profiles (excluding Abilities, which are less trainable and therefore less useful for designing retraining programs), and compute per-element costs:

> `element_cost = max(0, low_risk_avg_score - high_risk_avg_score)`

Elements where the high-risk worker already meets or exceeds the low-risk need cost nothing. The total pivot cost is the sum of all positive element gaps. A higher total means the worker must acquire proficiency across more dimensions to complete the transition.

## 2. Pivot Cost by Job Zone

![Pivot Cost by Job Zone](figures/pivot_cost_by_zone.png)

The relationship between job zone and pivot cost is not linear. It peaks sharply at Zone 3, drops at Zone 5, and is cheapest at Zone 1:

| Zone | Description | Total Cost | Elements with Cost > 0 |
|------|-------------|-----------|----------------------|
| 1 | Little/no preparation | 133.8 | 20 |
| 2 | Some preparation | 178.7 | 18 |
| 3 | Medium preparation | 322.1 | 36 |
| 4 | Considerable preparation | 316.8 | 47 |
| 5 | Extensive preparation | 182.5 | 26 |

Zone 1 has the shortest pivot distance because the occupations at both ends of the risk spectrum require relatively shallow skill profiles. A barista or door-to-door salesperson does not need to acquire deep technical expertise to move into logging or farmwork -- the knowledge floor for both groups is low. Zone 2 follows a similar pattern, though the gap widens as destination occupations like carpenters and chemical plant operators begin requiring mechanical and operational knowledge that service-sector workers lack.

Zone 3 is the most expensive pivot in the entire labor market. Office and clerical workers -- billing clerks, bookkeepers, brokerage clerks -- face a 322.1-point total cost across 36 distinct elements to reach the profiles of bus mechanics, elevator installers, or dancers. This is not a narrow specialization gap; it is a broad-spectrum knowledge deficit spanning mechanical systems, building construction, physics, and hands-on troubleshooting. The sheer number of elements (36) means no single certification program covers the distance.

Zone 4 costs nearly as much (316.8) but distributes it across even more elements (47), reflecting the breadth of professional-level occupations. The gap between credit counselors and acute care nurses, or between compensation specialists and wind energy managers, spans clinical knowledge, engineering fundamentals, and domain-specific technical skills.

Zone 5 is surprisingly moderate at 182.5. At the highest education level, the knowledge foundations of high-risk academics (anthropology teachers, archivists, atmospheric sciences faculty) and low-risk clinicians (anesthesiologists, emergency physicians, oral surgeons) share enough common ground -- research methods, analytical reasoning, statistical literacy -- that the pivot cost is comparable to Zone 2 despite the far greater depth of both profiles.

## 3. Which Elements Drive the Cost

![Element Cost Heatmap](figures/element_cost_heatmap.png)

Summing each element's cost contribution across all five zones reveals a clear pattern: the most expensive gaps are almost entirely in specialized technical knowledge, not in transferable cognitive or interpersonal skills.

| Rank | Element | Total Cost (All Zones) |
|------|---------|----------------------|
| 1 | Building and Construction | 71.0 |
| 2 | Mechanical | 64.4 |
| 3 | Engineering and Technology | 52.6 |
| 4 | Quality Control Analysis | 51.6 |
| 5 | Psychology | 48.9 |
| 6 | Therapy and Counseling | 46.0 |
| 7 | Troubleshooting | 43.7 |
| 8 | Physics | 43.5 |
| 9 | Medicine and Dentistry | 40.7 |
| 10 | Operations Monitoring | 40.7 |

The top three cost drivers -- Building and Construction (71.0), Mechanical (64.4), and Engineering and Technology (52.6) -- together account for more pivot cost than the bottom five drivers combined. These are the knowledge domains that separate desk-based, information-processing work from hands-on, systems-oriented work. They are also the domains least likely to be picked up through general education or soft-skills training.

Quality Control Analysis (51.6) and Troubleshooting (43.7) represent applied diagnostic reasoning in physical systems -- skills that require not just classroom learning but supervised practice. Psychology (48.9) and Therapy and Counseling (46.0) appear because several low-risk Zone 4 and 5 occupations (special education teachers, nurses) demand behavioral and clinical knowledge that high-risk administrative and academic roles do not provide.

The policy implication is direct: retraining programs built around general workforce readiness -- communication, teamwork, digital literacy -- will not close these gaps. The binding constraint is technical certification and applied knowledge in mechanical, construction, and engineering domains.

## 4. Example Occupations

The pivots become concrete when we name the occupations that define each zone's high-risk and low-risk profiles:

| Zone | High-Risk (Top 3) | Low-Risk (Top 3) |
|------|-------------------|------------------|
| 1 | Amusement/Recreation Attendants, Baristas, Door-to-Door Sales Workers | Fallers, Farmworkers, Logging Equipment Operators |
| 2 | Bill Collectors, Customer Service Reps, Data Entry Keyers | Carpenters, Chemical Plant Operators, Mining Machine Operators |
| 3 | Billing Clerks, Bookkeeping/Accounting Clerks, Brokerage Clerks | Bus/Truck Mechanics, Dancers, Elevator Installers |
| 4 | Biological Technicians, Compensation Specialists, Credit Counselors | Special Ed Teachers, Wind Energy Managers, Acute Care Nurses |
| 5 | Anthropology Teachers, Archivists, Atmospheric Sciences Teachers | Anesthesiologists, Emergency Medicine Physicians, Oral Surgeons |

The Zone 1 pivot (service worker to outdoor/physical laborer) is intuitively plausible and programmatically cheap. The Zone 3 pivot (office clerk to skilled tradesperson) is the least intuitive and most expensive -- it asks a bookkeeper to become a diesel mechanic, which is a career change, not a career adjustment.

## 5. Key Takeaways

1. **Zone 3 is the crisis point.** At 322.1 total cost across 36 elements, mid-skill office and clerical workers face the most expensive reskilling path in the labor market. This is the population most likely to be stranded by automation without targeted intervention.

2. **Technical knowledge, not soft skills, is the bottleneck.** The top cost drivers -- Building and Construction (71.0), Mechanical (64.4), Engineering and Technology (52.6) -- are domains that require hands-on training, apprenticeships, and industry certification. Generic workforce development programs will not close these gaps.

3. **Zone 5 workers are more portable than expected.** Despite occupying the highest education tier, high-risk academics face a moderate 182.5-point pivot cost to reach clinical and technical professions, because advanced education provides a broad knowledge base that transfers across specializations.

4. **Retraining investment should be tiered by zone.** Zone 1 workers need short-duration orientation programs. Zone 2 workers need single-trade certification. Zone 3 workers need comprehensive multi-domain technical education -- and that is where public investment will have the highest marginal impact per displaced worker.

## Config

Primary: `All 2026-02-18`. Risk scores from `job_risk_scoring`. Skills + Knowledge only (importance >= 3). Top 10 occs per group per zone (min of 10 and available). Abilities excluded (less trainable).

## Files

| File | Description |
|------|-------------|
| `results/pivot_cost_by_zone.csv` | Per-zone: total cost, n occs, example high/low risk occs |
| `results/element_costs_by_zone.csv` | Per-element cost breakdown per zone |
| `results/high_risk_profiles.csv` | Avg skill+knowledge profile of high-risk occs per zone |
| `results/low_risk_profiles.csv` | Same for low-risk |
