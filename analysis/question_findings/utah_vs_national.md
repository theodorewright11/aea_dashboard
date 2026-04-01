# Question: Do Utah's AI Exposure Results Meaningfully Differ From National?

We re-ran the three existing analyses — Economic Footprint, AI Transformative Potential, and Job Exposure — with Utah geography and compared against the national results. This report covers only the notable divergences.

The key structural fact: **% tasks affected is geography-independent.** It's computed from O*NET task scores and AI auto-aug scores, which don't vary by state. Only workers affected and wages affected change, because they depend on BLS employment counts and wage levels. So divergences show up as ranking shifts and different sector shares — driven entirely by Utah's occupational mix being different from the national average.

Utah is 1.5% of the national workforce (2.3M vs 153.2M workers).

---

## 1. Economic Footprint: Same Headline, Different Composition

At the aggregate level, Utah matches the national picture almost exactly:

| Geography | % of Workforce AI-Exposed | Workers Affected |
|-----------|--------------------------|-----------------|
| National | 27.2% | 41.7M |
| Utah | 27.4% | 620K |

The 0.2pp difference is negligible. But the sector-level composition tells a different story.

### Where Utah's mix diverges

Four major categories show share differences of 2+ percentage points:

| Major Category | National Share | Utah Share | Difference |
|---------------|---------------|------------|-----------|
| Computer and Mathematical | 6.4% | 10.4% | **+4.1pp** |
| Sales and Related | 13.7% | 9.8% | **-3.9pp** |
| Office and Administrative Support | 20.6% | 17.6% | **-3.0pp** |
| Business and Financial Operations | 9.6% | 12.4% | **+2.8pp** |

Utah's AI exposure is more concentrated in tech and business/financial occupations and less in traditional office and retail work. This reflects Silicon Slopes — Utah's outsized tech sector means a larger share of its AI-exposed workforce is in high-skill, high-wage roles.

![Economic Footprint Share Divergence](figures/footprint_share_divergence_workers.png)

### Minor category detail

The minor-level data sharpens this picture:

| Minor Category | Share Diff (pp) |
|---------------|----------------|
| Computer Occupations | +3.1 |
| Business Operations Specialists | +3.0 |
| Retail Sales Workers | -2.6 |
| Healthcare Diagnosing/Treating | +2.3 |
| Engineers | +1.8 |
| Secretaries and Admin Assistants | -1.7 |

Utah has proportionally more of its AI-exposed workforce in computer occupations, business operations, healthcare practitioners, and engineering — and less in retail, administrative, and teaching roles.

### Agentic vs Conversational: No meaningful difference

| | National | Utah |
|---|---------|------|
| Agentic (% of workforce) | 24.7% | 25.0% |
| Conversational (% of workforce) | 22.6% | 22.7% |

The agentic-vs-conversational split is essentially identical. Utah's tech concentration doesn't shift the balance between AI modes in any notable way.

---

## 2. AI Transformative Potential: Minor ranking shifts at the major level

The gap analysis (MCP v4 capability minus AEI Cumul. Both v4 usage) produces similar rankings nationally and in Utah. At the major category level, only 3 of 22 categories shift by 3+ rank positions.

The share of the unrealized-potential gap is more revealing:

| Category | National Share of Gap | Utah Share of Gap | Diff (pp) |
|----------|---------------------|-------------------|-----------|
| Healthcare Practitioners | -7.1% | -23.0% | -15.9 |
| Computer and Mathematical | 12.8% | 26.1% | +13.3 |
| Transportation | 33.8% | 39.1% | +5.3 |
| Management | 12.0% | 16.8% | +4.9 |

Utah's unrealized AI potential is much more concentrated in Computer/Math and Management occupations. The Healthcare Practitioners negative gap (where usage exceeds capability) is proportionally larger in Utah, likely reflecting Utah's healthcare industry concentration and relatively strong AI adoption in clinical settings.

![Transformative Potential Gap Share Divergence](figures/transformative_gap_share_major.png)

At the occupation level, rank shifts are widespread (807 of 923 shift by 3+ positions) — but this is expected at high granularity where small employment differences in Utah create large rank changes. No individual occupation shift tells a story that the major-level data doesn't already capture.

---

## 3. Job Exposure: Utah has a slightly different tier profile

Since % tasks affected is geography-independent, the same occupations are in the same exposure tiers. But the share of Utah's workforce in each tier differs:

| Tier | National | Utah | Difference |
|------|----------|------|-----------|
| High Exposure (>=60%) | 1.0% | 2.0% | **+1.0pp** |
| Moderate Exposure (40-60%) | 23.4% | 21.7% | -1.7pp |
| Restructuring (20-40%) | 34.7% | 36.6% | +1.9pp |
| Low Exposure (<20%) | 40.9% | 39.7% | -1.3pp |

**Utah has double the share of workers in high-exposure occupations** (2.0% vs 1.0%). This is driven by tech occupations like Search Marketing Strategists and Market Research Analysts being overrepresented in Utah's workforce — these are among the 9 high-exposure occupations nationally, and Utah has proportionally more of them.

![Exposure Tier Comparison](figures/risk_tier_comparison.png)

### Utah's largest most-exposed occupations

The top 20 moderate-and-high-exposure occupations by Utah employment:

| Rank | Occupation | Utah Emp | % Tasks | Tier |
|------|-----------|----------|---------|------|
| 1 | Customer Service Representatives | 48,770 | 54.6% | Moderate |
| 2 | Retail Salespersons | 39,580 | 47.1% | Moderate |
| 3 | Office Clerks, General | 36,950 | 53.4% | Moderate |
| 4 | First-Line Supervisors of Office/Admin | 18,770 | 41.0% | Moderate |
| 5 | Investment Fund Managers | 16,306 | 45.1% | Moderate |
| 6 | **Search Marketing Strategists** | 15,075 | **66.0%** | **High** |
| 7 | Secretaries and Admin Assistants | 14,910 | 50.5% | Moderate |
| 8 | Bookkeeping/Auditing Clerks | 13,980 | 43.4% | Moderate |
| 9 | Sales Reps, Wholesale/Mfg | 13,930 | 59.2% | Moderate |
| 10 | Computer Systems Engineers/Architects | 13,276 | 43.8% | Moderate |

![Utah's Largest Most-Exposed Occupations](figures/utah_largest_at_risk.png)

### What's different about Utah's top 20 vs national

Six occupations appear in Utah's top 20 most-exposed but not the national top 20:

- **Search Marketing Strategists** (15K workers, 66% — high exposure)
- **Computer Systems Engineers/Architects** (13K, 44%)
- **Web Administrators** (13K, 51%)
- **Market Research Analysts** (12K, 63% — high exposure)
- **Online Merchants** (10K, 57%)
- **Document Management Specialists** (8K, 46%)

These are all tech and digital marketing roles — occupations that are proportionally larger in Utah than nationally. Conversely, Utah's top 20 misses several large national occupations like Management Analysts (894K nationally), Medical Secretaries (831K), and Middle School Teachers (620K) that simply have smaller Utah footprints.

### Sector-level exposure concentration

The share of each major category's workforce in moderate-or-high-exposure tiers also diverges:

| Major Category | National | Utah | Diff |
|---------------|----------|------|------|
| Protective Service | 16.6% | 29.2% | **+12.6pp** |
| Arts/Design/Entertainment | 43.3% | 34.2% | **-9.1pp** |
| Business and Financial | 49.3% | 42.3% | **-7.0pp** |
| Legal | 1.1% | 5.4% | +4.3pp |
| Architecture and Engineering | 11.4% | 15.6% | +4.2pp |
| Computer and Mathematical | 65.9% | 69.6% | +3.7pp |

The Protective Service divergence (+12.6pp) is the largest and may be driven by Utah's specific mix of protective service occupations — if Utah has proportionally more of the AI-exposed roles within that category (like Customs/Border Protection officers, which appear in Utah's top-20 list).

### Capability ceiling

Under the capability ceiling (all sources, Max), the tier distribution is much more similar between Utah and national — no tier differs by more than 1pp. The Utah-specific divergences are largely a feature of the usage-confirmed data, not the ceiling.

---

## 4. Key Takeaways

1. **The headline is the same.** Utah's overall AI exposure (27.4%) matches the national average (27.2%). National findings can be applied to Utah with high confidence at the aggregate level.

2. **The composition is different.** Utah's AI-exposed workforce is more concentrated in tech (+4.1pp in Computer/Math) and business/financial (+2.8pp) and less in retail (-3.9pp) and office/admin (-3.0pp). This reflects Silicon Slopes.

3. **Utah has double the high-exposure workforce share** (2.0% vs 1.0%), driven by outsized employment in tech and marketing occupations that happen to be in the high-exposure tier. This is the most policy-relevant divergence.

4. **Utah's top most-exposed occupations include more tech roles** — Search Marketing Strategists, Computer Systems Engineers, Web Administrators, Online Merchants — that don't appear in the national top 20 because they're proportionally smaller nationally.

5. **Sector-level exposure concentration differs** in Protective Service (+12.6pp more exposed in Utah), Arts/Entertainment (-9.1pp less), and Business/Financial (-7.0pp less). These are driven by Utah's specific occupational composition within each sector.

6. **The agentic-vs-conversational split and methodology sensitivity are unchanged.** These findings are robust to geography.

**For Utah OAIP:** The national findings are broadly applicable, but Utah's tech concentration means the state may feel the impact of AI on knowledge-worker occupations more acutely than the national average suggests. The 6 tech/digital occupations that are uniquely prominent in Utah's most-exposed list are worth monitoring specifically.

---

## Config

All analyses use the same configs as the original questions, with `geo="ut"` substituted:
- **Economic Footprint**: Combined (all sources, Average) | Time | Auto-aug ON
- **Transformative Potential**: MCP v4 vs AEI Cumul. Both v4 | Time | Auto-aug ON
- **Job Exposure**: AEI Cumul. (Both) v4 + Microsoft | Average | Value | Auto-aug ON | Occupation level

## Files

| File | Description |
|------|-------------|
| `results/footprint_share_workers_major.csv` | Major category share comparison (workers) |
| `results/footprint_share_wages_major.csv` | Major category share comparison (wages) |
| `results/footprint_share_workers_minor.csv` | Minor category share comparison |
| `results/footprint_ai_mode_comparison.csv` | Agentic vs Conversational, both geos |
| `results/transformative_gap_rank_major.csv` | Gap ranking shifts at major level |
| `results/transformative_gap_share_major.csv` | Gap share divergence at major level |
| `results/risk_tier_comparison.csv` | Usage-confirmed exposure tier distribution, both geos |
| `results/risk_tier_comparison_ceiling.csv` | Ceiling exposure tier distribution, both geos |
| `results/utah_largest_at_risk.csv` | Utah's top 20 moderate+high exposure occupations |
| `results/risk_major_moderate_high_comparison.csv` | Moderate+high exposure share by major, both geos |
| `results/summary.csv` | One-line comparison per key metric |
