# Question: Where are the jobs and sectors with the greatest potential for AI to be transformative?

We compare a **capability ceiling** (AEI Cumul. Both v4 + MCP Cumul. v4 + Microsoft, combined with Max) against **current AI usage** (AEI Cumul. Both v4 alone) to find occupations and sectors where the gap between potential and current adoption is largest.

The ceiling represents the maximum AI capability observed across all our data sources for each task. AEI captures real conversational usage, MCP captures tool/API capability, and Microsoft captures Copilot usage patterns. Taking the Max across all three gives us the best available estimate of what AI *can* do today.

The gap = Ceiling score minus Current Usage score. A large positive gap means AI is capable of affecting that work (as demonstrated by at least one source), but real-world conversational adoption hasn't caught up yet. That's unrealized transformative potential.

---

## 1. Where Is the AI Capability Ceiling? (All Sources, Max)

**Primary config: Time, Auto-aug ON, National**

### Major Categories (by workers affected)

| Rank | Major Category | % Tasks | Workers Affected |
|------|---------------|---------|-----------------|
| 1 | Office and Administrative Support | 54.4% | 10.8M |
| 2 | Sales and Related | 54.2% | 7.1M |
| 3 | Business and Financial Operations | 40.8% | 4.5M |
| 4 | Food Preparation and Serving Related | 29.3% | 4.1M |
| 5 | Management | 31.8% | 4.1M |
| 6 | Educational Instruction and Library | 45.2% | 3.5M |
| 7 | Transportation and Material Moving | 18.0% | 3.4M |
| 8 | Computer and Mathematical | 65.3% | 3.3M |

Computer and Mathematical has the highest % tasks affected (65.3%) but ranks 8th in workers because the sector is smaller. The top 3 by worker impact are large, broad categories — office work, sales, and business/financial ops.

Because we take the Max across all sources, the ceiling reflects the highest capability observed *anywhere*. For most categories, MCP provides the ceiling. But for Education (45.2%), the ceiling comes from AEI conversational data — AI is already being used in education at rates that exceed tool-based capability measures.

![Capability Ceiling — Workers Affected by Major Category](figures/ceiling_workers_affected_major.png)

### Top Occupations (by workers affected)

| Rank | Occupation | % Tasks | Workers |
|------|-----------|---------|---------|
| 1 | Cashiers | 60.6% | 1.9M |
| 2 | Retail Salespersons | 47.7% | 1.8M |
| 3 | Customer Service Representatives | 64.0% | 1.7M |
| 4 | Office Clerks, General | 69.4% | 1.7M |
| 5 | Secretaries and Admin Assistants | 77.0% | 1.3M |
| 6 | General and Operations Managers | 37.1% | 1.3M |

---

## 2. Where Is AI Already Being Used Most? (AEI Cumul. Both v4)

### Major Categories (by workers affected)

| Rank | Major Category | % Tasks | Workers Affected |
|------|---------------|---------|-----------------|
| 1 | Office and Administrative Support | 32.8% | 8.4M |
| 2 | Sales and Related | 43.2% | 5.0M |
| 3 | Business and Financial Operations | 37.5% | 4.5M |
| 4 | Educational Instruction and Library | 45.2% | 3.5M |
| 5 | Management | 24.2% | 3.2M |
| 6 | Computer and Mathematical | 48.0% | 2.4M |

Notable: **Education ranks #4 in current usage** (3.5M workers, 45.2% of tasks). In fact, Education's current usage equals the capability ceiling — conversational AI adoption in education has already saturated the measured potential. This is unique among major categories.

**Business and Financial Operations** (37.5%) also matches or nearly matches its ceiling (40.8%), leaving minimal room for growth in that sector.

![Current Usage — Workers Affected by Major Category](figures/current_workers_affected_major.png)

### Top Occupations (by workers affected)

| Rank | Occupation | % Tasks | Workers |
|------|-----------|---------|---------|
| 1 | Customer Service Representatives | 59.4% | 1.6M |
| 2 | Retail Salespersons | 39.2% | 1.5M |
| 3 | Office Clerks, General | 56.6% | 1.4M |
| 4 | Secretaries and Admin Assistants | 53.3% | 926K |
| 5 | Cashiers | 22.6% | 711K |
| 6 | Bookkeeping, Accounting, Auditing | 45.0% | 655K |

---

## 3. Does Adding Microsoft Change Current Usage Numbers?

To test whether Microsoft's data materially changes the "current usage" picture, we ran AEI Cumul. Both v4 + Microsoft under both Average and Max combine methods.

**Short answer: yes, significantly.** Adding Microsoft changes current usage numbers substantially, especially for sectors where Microsoft data covers work that AEI conversations don't.

### Average combine (AEI + Microsoft)

| Major Category | AEI Only | + Microsoft (Avg) | Change |
|---------------|----------|-------------------|--------|
| Production | 323K | 845K | +161% |
| Building/Grounds Cleaning | 99K | 250K | +153% |
| Installation/Maintenance/Repair | 591K | 958K | +62% |
| Transportation/Material Moving | 878K | 1.4M | +57% |
| Food Preparation/Serving | 2.1M | 3.1M | +47% |
| Personal Care/Service | 461K | 664K | +44% |

Some categories decrease when averaged (Microsoft rates them lower than AEI):

| Major Category | AEI Only | + Microsoft (Avg) | Change |
|---------------|----------|-------------------|--------|
| Education | 3.5M | 2.9M | -18% |
| Legal | 439K | 375K | -15% |
| Business/Financial | 4.5M | 3.9M | -13% |
| Office/Admin Support | 8.4M | 7.5M | -11% |

### Max combine (AEI + Microsoft)

Using Max amplifies the effect — Production jumps +322%, Building/Grounds +305%, Installation/Maintenance +124%.

With Max, no category decreases (the Max of AEI and Microsoft is always >= AEI alone). Categories where Microsoft adds no additional coverage beyond AEI (like Arts/Media, Business/Financial, Computer/Math) show 0% change.

**Implication for this analysis:** We chose to keep current usage as AEI-only because AEI specifically captures conversational AI adoption patterns. Microsoft's Copilot data represents a different type of usage (integrated workplace tools), which is conceptually closer to "capability" than "conversational adoption." Including it in the ceiling (via Max) but not in the current-usage baseline gives us the cleanest separation between "what AI can do" and "how people are using conversational AI today."

---

## 4. Where Is the Unrealized Potential Largest? (Gap = Ceiling minus Current)

This is the core finding. A large positive gap means AI is capable of this work but real-world conversational adoption hasn't caught up yet.

Because the ceiling takes the Max across all sources (including AEI itself), the gap is always >= 0. There are no negative gaps — the ceiling is by definition at least as high as current usage.

### Major Categories (by workers gap)

| Rank | Major Category | Ceiling % | Current % | Gap (pp) | Workers Gap |
|------|---------------|-----------|-----------|----------|-------------|
| 1 | **Transportation and Material Moving** | 18.0% | 5.5% | +12.5 | +2.5M |
| 2 | **Office and Administrative Support** | 54.4% | 32.8% | +21.6 | +2.4M |
| 3 | **Sales and Related** | 54.2% | 43.2% | +11.0 | +2.1M |
| 4 | **Food Preparation and Serving** | 29.3% | 15.2% | +14.1 | +2.0M |
| 5 | **Production** | 15.8% | 4.2% | +11.6 | +1.0M |
| 6 | **Computer and Mathematical** | 65.3% | 48.0% | +17.3 | +947K |
| 7 | **Management** | 31.8% | 24.2% | +7.6 | +886K |
| 8 | **Installation, Maintenance, Repair** | 20.5% | 7.4% | +13.1 | +734K |

**Transportation is #1 by workers gap** despite a modest overall AI exposure rate (18% ceiling). The huge workforce (18.8M) means even a small percentage gap translates into 2.5M workers worth of untapped potential. This sector has the most room for AI adoption to grow.

**Food Preparation is #4** — a new entrant in the top rankings compared to the old MCP-only framing. With a 14.1 percentage-point gap and 2.0M workers, there's significant untapped potential in food service roles (scheduling, inventory, ordering workflows).

**Categories with zero or near-zero gap**: Education (0.0 pp), Healthcare Practitioners (0.0 pp), Business/Financial (3.3 pp). Education and Healthcare hit zero because their current AEI usage already equals the ceiling — conversational AI adoption has saturated measured capability in these sectors.

![Gap by Workers Affected — Major Category](figures/gap_workers_affected_major.png)

### Minor Categories (Top 10 by workers gap)

| Rank | Minor Category | Ceiling % | Current % | Gap (pp) | Workers Gap |
|------|---------------|-----------|-----------|----------|-------------|
| 1 | Material Moving Workers | 19.4% | 2.5% | +16.9 | +1.9M |
| 2 | Retail Sales Workers | 54.1% | 27.0% | +27.2 | +1.7M |
| 3 | Food and Beverage Serving Workers | 30.9% | 14.4% | +16.5 | +1.2M |
| 4 | Computer Occupations | 66.5% | 46.2% | +20.3 | +951K |
| 5 | Sales Representatives, Services | 58.4% | 48.2% | +10.3 | +830K |
| 6 | Top Executives | 26.2% | 21.8% | +4.4 | +785K |
| 7 | Secretaries and Admin Assistants | 71.6% | 47.5% | +24.2 | +718K |
| 8 | Financial Clerks | 55.0% | 31.0% | +24.0 | +593K |
| 9 | Cooks and Food Preparation Workers | 32.6% | 19.3% | +13.4 | +494K |
| 10 | Other Installation/Maintenance/Repair | 21.6% | 4.6% | +17.0 | +490K |

**Material Moving Workers** at #1 is striking — nearly 1.9M workers worth of gap. These are warehouse, shipping, and logistics roles where AI tools (scheduling, routing, inventory management) have clear capability but real-world conversational adoption is minimal (only 2.5% of tasks covered by AEI).

**Food and Beverage Serving Workers** enters the minor-level top 10 at #3 with 1.2M workers gap.

### Top Occupations (by workers gap)

| Rank | Occupation | Ceiling % | Current % | Gap (pp) | Workers Gap |
|------|-----------|-----------|-----------|----------|-------------|
| 1 | **Cashiers** | 60.6% | 22.6% | +38.0 | +1.20M |
| 2 | **Sales Reps of Services** | 70.8% | 0.0% | +70.8 | +842K |
| 3 | **General and Operations Managers** | 37.1% | 14.6% | +22.5 | +805K |
| 4 | **Stockers and Order Fillers** | 37.8% | 11.0% | +26.8 | +745K |
| 5 | **Waiters and Waitresses** | 37.9% | 6.2% | +31.8 | +731K |
| 6 | **Secretaries and Admin Assistants** | 77.0% | 53.3% | +23.7 | +412K |
| 7 | **Laborers and Freight Movers** | 16.6% | 3.0% | +13.6 | +406K |
| 8 | **Recycling and Reclamation Workers** | 13.6% | 0.0% | +13.6 | +404K |
| 9 | **Software QA Testers** | 72.4% | 21.2% | +51.2 | +371K |
| 10 | **Bookkeeping/Accounting Clerks** | 68.5% | 45.0% | +23.5 | +342K |

Several occupations have **0% current conversational usage** but significant capability: Sales Reps of Services (70.8% ceiling), Recycling Workers, Project Management Specialists (49.3%), Entertainment/Recreation Managers (44.6%), Substitute Teachers (38.1%), Industrial Truck Operators (29.3%). These represent totally untapped AI potential.

**Waiters and Waitresses** now shows a larger gap (+31.8 pp, +731K workers) than under the old MCP-only ceiling (which was 27.9%). The higher ceiling comes from Microsoft's Copilot data rating food service tasks higher than MCP alone.

**Software QA Testers** stand out in tech: the ceiling reaches 72.4% of their tasks, but only 21.2% shows up in real conversations. That's a 51 percentage-point gap. This is an area where AI tool capability is far ahead of conversational adoption.

![Gap by Workers Affected — Occupation Level](figures/gap_workers_affected_occupation.png)

---

## 5. Does the Method Toggle Matter? (Time vs Value)

**Short answer: not much.** The rankings are very stable between Time and Value methods.

At the major level, the gap rankings by workers are nearly identical. The biggest shift in wages gap is Sales (going from Time to Value) — meaning Sales tasks with the biggest AI gap tend to be frequent but lower-importance. Computer and Math goes slightly up under Value, confirming that its gap is in the core, important tasks.

At the occupation level, the top-10 by workers gap is largely the same. Value weights slightly favor occupations with important/relevant tasks (managers, knowledge workers) over high-frequency but routine ones (cashiers, stockers).

**What this means:** The unrealized potential story is robust regardless of whether you weight tasks by frequency alone or by their economic importance. The same sectors and occupations show up.

---

## 6. Does the Auto-Aug Toggle Matter? (ON vs OFF)

**Yes, dramatically. This is a key finding.**

When auto-aug is OFF, every AI-flagged task counts equally (as if all had maximum automation scores). When ON, tasks are scaled by their actual automation score (0-5).

### What changes:

**The gaps get massively larger with auto-aug OFF.** At the major level:

| Major Category | Gap (Workers, ON) | Gap (Workers, OFF) | Increase |
|---------------|-------------------|-------------------|----------|
| Office and Admin | +2.4M | +6.7M | +4.3M |
| Sales | +2.1M | +5.7M | +3.6M |
| Management | +886K | +5.3M | +4.4M |
| Transportation | +2.5M | +5.3M | +2.8M |
| Food Prep/Serving | +2.0M | +4.9M | +2.9M |
| Computer and Math | +947K | +2.2M | +1.2M |

**Management** has the most dramatic shift: from +886K workers gap (auto-aug ON) to +5.3M (OFF). This means most Management tasks flagged by AI sources have relatively low automation scores currently. If those scores increase over time — as AI tools get better — Management could see the largest increase in realized AI impact.

**Food Prep and Production** also show massive increases with auto-aug OFF, indicating their AI-flagged tasks currently have moderate automation scores with significant room to grow.

![Gap with Auto-aug OFF — Major Category](figures/gap_workers_major_time_autoaug_off.png)

### What this means:

The auto-aug OFF results represent the **theoretical maximum** if every AI-flagged task were fully automatable. The difference between ON and OFF shows **how much additional potential exists** if automation quality improves. The fact that Management, Food Prep, and Office Admin see the biggest increases means their tasks are flagged as AI-capable but with currently moderate automation scores — there's a second layer of unrealized potential beyond just adoption.

---

## 7. Stability Across All 4 Configs

| Level | Stable in Top-10 (all 4 configs) | Stable Categories |
|-------|----------------------------------|-------------------|
| Major | 8 of 10 | Computer/Math, Food Prep, Installation/Maintenance, Management, Office/Admin, Production, Sales, Transportation |
| Minor | 7 of 10 | Computer Occs, Food/Beverage Serving, Material Moving, Retail Sales, Sales Reps Services, Secretaries/Admin, Top Executives |
| Occupation | 6 of 10 | Cashiers, General/Ops Managers, Laborers/Freight, Sales Reps of Services, Stockers/Order Fillers, Waiters/Waitresses |

The story is highly robust. 6-8 of the top 10 appear regardless of method or auto-aug setting.

![Summary — % Tasks Gap by Major Category](figures/summary_gap_major.png)

---

## Config

- **Ceiling**: AEI Cumul. (Both) v4 + MCP Cumul. v4 + Microsoft | Max | Time | Auto-aug ON | National | All tasks
- **Current**: AEI Cumul. (Both) v4 | Time | Auto-aug ON | National | All tasks
- **Sensitivity**: 4 variants (Time/Value x Auto-aug ON/OFF), plus Microsoft sensitivity test on current usage
- **Aggregation**: Major, Minor, Occupation

## Files

### Core Results (Primary config: Time, Auto-aug ON)
| File | Description |
|------|-------------|
| `results/gap_major_time_autoaug_on.csv` | Gap rankings at major category level |
| `results/gap_minor_time_autoaug_on.csv` | Gap rankings at minor category level |
| `results/gap_occupation_time_autoaug_on.csv` | Gap rankings at occupation level |
| `results/ceiling_major_time_autoaug_on.csv` | Ceiling rankings (all sources, Max) |
| `results/current_major_time_autoaug_on.csv` | Current usage rankings (AEI only) |

### Sensitivity Variants
| File | Description |
|------|-------------|
| `results/gap_*_time_autoaug_off.csv` | Auto-aug OFF variant |
| `results/gap_*_value_autoaug_on.csv` | Value method variant |
| `results/gap_*_value_autoaug_off.csv` | Value + auto-aug OFF variant |

### Microsoft Sensitivity Test
| File | Description |
|------|-------------|
| `results/ms_sensitivity_full.csv` | Full comparison: AEI-only vs AEI+Microsoft (Average and Max) |
| `results/ms_sensitivity_average_*.csv` | Per-level detail, Average combine |
| `results/ms_sensitivity_max_*.csv` | Per-level detail, Max combine |

### Toggle Analysis
| File | Description |
|------|-------------|
| `results/stability_summary.csv` | How many top-10 entries are stable across all 4 configs |
| `results/toggle_comparison.csv` | Full gap values under ON vs OFF for each toggle |
| `results/toggle_movers_autoaug_*.csv` | Biggest movers when auto-aug toggles, per level |
| `results/toggle_movers_method_*.csv` | Biggest movers when method toggles, per level |

### Figures (Primary config)
| File | Description |
|------|-------------|
| `results/figures/gap_workers_affected_major.png` | Ceiling vs Current grouped bars, major, workers |
| `results/figures/gap_pct_tasks_affected_major.png` | Ceiling vs Current grouped bars, major, % tasks |
| `results/figures/gap_wages_affected_major.png` | Ceiling vs Current grouped bars, major, wages |
| `results/figures/ceiling_workers_affected_major.png` | Ceiling ranking, major |
| `results/figures/current_workers_affected_major.png` | Current usage ranking, major |
| `results/figures/summary_gap_major.png` | % Tasks gap overview by major category |
| (same pattern for minor and occupation levels) | |
