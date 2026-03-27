# Cross-Source Robustness: Do AEI, MCP, and Microsoft Agree on AI Exposure?

Three independent AI scoring sources feed the AEA Dashboard. Each captures a different slice of AI capability: **AEI** (Anthropic Economic Index) measures what Claude is actually used for in real conversations and API calls, **MCP** (Model Context Protocol) captures what AI can do when given tool access and external resources, and **Microsoft** measures Copilot usage patterns across work tasks. If a finding holds across all three, we can trust it. If only one source drives it, we should flag that and ask why.

This analysis runs each source solo through the dashboard's compute pipeline at four aggregation levels (major category, minor category, broad occupation, and individual occupation), then compares their rankings, scores, and tier assignments to determine which findings are robust and which are source-dependent.

**Primary config:** Time method, Auto-aug ON, National, All tasks.

---

## 1. Economic Footprint: Similar Totals, Different Distributions

At the aggregate level, AEI and Microsoft produce nearly identical total workforce exposure --- 25.5% and 25.7% of US workers, respectively. MCP stands apart at **30.4%** (46.5M workers), roughly 5 percentage points higher.

| Source | Workers Affected | % of Workforce | Wages Affected | % of Wages |
|--------|----------------:|---------------:|---------------:|-----------:|
| AEI | 39.1M | 25.5% | $2,676B | 28.4% |
| MCP | 46.5M | 30.4% | $2,969B | 31.5% |
| Microsoft | 39.5M | 25.7% | $2,464B | 26.1% |

![Footprint Comparison](figures/footprint_comparison.png)

The similar AEI/Microsoft totals are deceptive --- as we'll see, the two sources arrive at ~25% through very different paths. MCP's higher footprint reflects its measurement of what AI systems *can* do with tools, rather than what users *are* doing in conversations.

---

## 2. The Central Finding: Agreement Degrades with Granularity

The most important finding of this entire analysis: **source agreement is strong at the major category level but weakens systematically as you zoom in.** This has direct implications for which findings should be treated as robust.

| Level | N Categories | Spearman rho range | High-confidence findings | % High |
|-------|:-----------:|:------------------:|:------------------------:|:------:|
| Major (22 groups) | 22 | 0.81 -- 0.85 | 6 of 13 in any top-10 | 46% |
| Minor (95 groups) | 95 | 0.73 -- 0.78 | 11 of 31 in any top-20 | 35% |
| Broad (439 groups) | 439 | 0.64 -- 0.71 | 1 of 52 in any top-20 | 2% |
| Occupation (923) | 923 | 0.56 -- 0.65 | 1 of 78 in any top-30 | 1% |

"High confidence" means all three sources place the category in their respective top-N. "Moderate" means two of three agree. "Low" means only one source drives the finding.

![Confidence distribution across levels](figures/confidence_summary.png)

This pattern is consistent across all three source pairs, and the decline is smooth --- not a cliff between two specific levels. MCP and Microsoft correlate most strongly (highest rho at every level), which makes sense because both measure AI *doing work* (tools and copilot) rather than *conversing about work* (AEI).

**The policy implication:** major-category findings can be cited with confidence. Minor-category findings need a source-agreement caveat. Broad and occupation-level findings should always note which source drives them.

---

## 3. Major Category Level: The Robust Core

At the highest aggregation level, the three sources show strong agreement. Spearman rank correlations range from 0.81 to 0.85 -- high by social science standards, and 8/10 of each source's top-10 categories overlap with each other pair.

Six categories are **high-confidence findings** -- all three sources place them in their top 10 for % Tasks Affected:

| Category | AEI | MCP | MS | Confidence |
|----------|:---:|:---:|:--:|:----------:|
| Computer and Mathematical | 48.0% (#1) | 65.3% (#1) | 43.4% (#1) | **High** |
| Sales and Related | 43.2% (#3) | 54.2% (#3) | 36.8% (#2) | **High** |
| Office and Administrative Support | 32.8% (#6) | 54.4% (#2) | 34.5% (#3) | **High** |
| Business and Financial Operations | 37.5% (#4) | 40.8% (#4) | 31.4% (#6) | **High** |
| Arts, Design, Entertainment, Sports, Media | 35.3% (#5) | 36.9% (#5) | 32.5% (#5) | **High** |
| Life, Physical, and Social Science | 25.6% (#9) | 27.3% (#8) | 27.7% (#10) | **High** |

These are the bedrock findings: **regardless of which AI system you look at, these occupational groups have the most AI task overlap.** Computer/Math is unanimous #1, with all sources scoring it above 43%.

![Major category comparison](figures/major_pct_tasks_affected.png)

![Source scores side by side](figures/score_dots_major.png)

### 3.1 Moderate-Confidence Findings (2 of 3 sources agree)

Five categories reach moderate confidence at the major level:

- **Educational Instruction and Library**: AEI ranks it #2 (45.2%), but MCP ranks it #11 (22.9%). AEI captures conversational AI usage -- teaching, tutoring, curriculum work -- which education workers use heavily. MCP's tool-based scoring doesn't see this because educational tasks don't typically involve the kind of tool access MCP measures.
- **Architecture and Engineering**: MCP ranks it #6 (33.6%), but AEI ranks it #11 (20.7%). The reverse -- engineering work involves tool-heavy AI usage (code execution, CAD, simulation) that MCP captures but conversational usage misses.
- **Community and Social Service**: AEI and Microsoft agree (both top-10), MCP does not. Social service work involves text-heavy, conversational tasks.
- **Legal Occupations**: AEI and MCP agree, Microsoft does not. Both Claude and tool-access AI see legal research and drafting; Copilot usage in legal is apparently lower.
- **Management**: AEI and MCP agree, Microsoft does not. Management involves diverse task types that both conversations and tools touch.

### 3.2 Low-Confidence Findings (single-source)

- **Personal Care and Service**: Only MCP sees it in the top 10, driven by tool-based scoring.
- **Food Preparation and Serving**: Only Microsoft sees it in the top 10 (29.3% vs MCP 16.6%, AEI 15.2%). Microsoft's Copilot data captures more food service task interaction than either Claude or MCP tools.

![Rank agreement at major level](figures/rank_heatmap_major.png)

---

## 4. Minor Category Level: Still Useful, but Caveats Needed

At 95 minor categories, Spearman correlations drop to 0.73--0.78. Eleven of the 31 categories appearing in any source's top 20 are high confidence:

| Category | AEI | MCP | MS | Confidence |
|----------|:---:|:---:|:--:|:----------:|
| Sales Reps, Wholesale/Manufacturing | 65.8% (#2) | 56.1% (#7) | 40.8% (#5) | **High** |
| Mathematical Science | 56.3% (#3) | 60.1% (#4) | 42.8% (#4) | **High** |
| Secretaries and Admin Assistants | 47.5% (#9) | 71.6% (#1) | 37.1% (#10) | **High** |
| Computer Occupations | 46.2% (#10) | 66.5% (#2) | 43.5% (#2) | **High** |
| Media and Communication Workers | 49.5% (#7) | 49.9% (#12) | 43.7% (#1) | **High** |
| Other Sales and Related | 51.7% (#6) | 54.7% (#10) | 36.6% (#14) | **High** |
| Sales Reps, Services | 48.2% (#8) | 58.4% (#5) | 34.4% (#17) | **High** |
| Other Office and Admin Support | 38.0% (#13) | 57.2% (#6) | 37.0% (#11) | **High** |
| Information and Record Clerks | 37.5% (#16) | 55.4% (#8) | 36.9% (#12) | **High** |
| Financial Specialists | 37.0% (#17) | 42.3% (#15) | 34.3% (#18) | **High** |
| Librarians, Curators, and Archivists | 33.6% (#20) | 40.3% (#18) | 39.6% (#7) | **High** |

Notice that even among high-confidence categories, the score spreads are large --- Secretaries shows a 34.5pp gap between MCP (71.6%) and Microsoft (37.1%). The sources agree it's a top category but disagree on *how much* exposure it has.

**Notable single-source outlier:** Postsecondary Teachers is AEI's #1 minor category (66.9%) but MCP's #33 (28.5%) and Microsoft's #27 (31.9%). This is a classic AEI signature -- teaching generates enormous conversational AI usage that neither tool-based nor copilot measurement captures.

![Minor category comparison](figures/minor_pct_tasks_affected.png)

![Rank heatmap at minor level](figures/rank_heatmap_minor.png)

![Score dots at minor level](figures/score_dots_minor.png)

---

## 5. Broad and Occupation Level: Source-Dependent Territory

At the broad occupation level (439 categories), only **1 category** (Computer Support Specialists) achieves high confidence across all three sources. At the individual occupation level (923), also just 1. The vast majority of findings at these levels are driven by a single source.

The broad-level results illustrate the pattern clearly:

- **MCP-dominant top occupations**: Telemarketers (90.1% MCP vs 61.2% AEI, 35.4% MS), Office Clerks, Receptionists, Desktop Publishers -- tool-assisted data entry and lookup.
- **AEI-dominant**: Market Research Analysts (78.8% AEI vs 58.5% MCP, 49.9% MS) -- heavy conversational research usage.
- **Microsoft-dominant**: Customer Service Representatives, Computer and Information Analysts -- Copilot integration patterns.

Score spreads at this level routinely exceed 25--50 percentage points between highest and lowest source. This isn't noise -- it reflects genuine differences in what each AI system does.

![Rank heatmap at broad level](figures/rank_heatmap_broad.png)

### 5.1 Pairwise Correlation at Each Level

The full correlation matrix shows the degradation pattern:

| Level | AEI vs MCP | AEI vs MS | MCP vs MS |
|-------|:----------:|:---------:|:---------:|
| Major | 0.85 | 0.81 | 0.85 |
| Minor | 0.77 | 0.73 | 0.78 |
| Broad | 0.67 | 0.64 | 0.71 |
| Occupation | 0.58 | 0.56 | 0.65 |

MCP vs Microsoft is the strongest pair at every level. Both measure AI *doing work*; AEI measures AI *being consulted*.

![AEI vs MCP scatter (occupation level)](figures/scatter_aei_vs_mcp_occupation.png)

![MCP vs Microsoft scatter (occupation level)](figures/scatter_mcp_vs_microsoft_occupation.png)

---

## 6. Pairwise Divergence: What Each Source Uniquely Captures

### 6.1 AEI vs MCP (Conversation vs Tools)

The largest systematic disagreement. AEI sees more exposure in education, social services, and legal (conversation-heavy). MCP sees more in office/admin, sales, and technical support (tool-heavy).

Biggest major-level gaps:
- **Education**: AEI 45.2% vs MCP 22.9% (+22.3pp) -- conversational tutoring and curriculum work
- **Office/Admin**: AEI 32.8% vs MCP 54.4% (-21.6pp) -- tool-based data entry, filing, scheduling

![AEI vs MCP divergence](figures/divergence_aei_vs_mcp_major.png)

### 6.2 MCP vs Microsoft (Capability vs Usage)

These two agree most, but MCP systematically rates Computer/Math, Office/Admin, and Sales higher. MCP captures the full tool-access frontier; Microsoft captures a narrower productivity-assistant pattern.

Biggest gap: Computer/Math at 65.3% MCP vs 43.4% Microsoft (+21.9pp).

![MCP vs Microsoft divergence](figures/divergence_mcp_vs_microsoft_major.png)

### 6.3 Why the Sources Diverge

The three sources measure genuinely different aspects of AI capability:

| Source | What it measures | Overweights | Underweights |
|--------|-----------------|-------------|--------------|
| **AEI** | What people ask Claude | Education, legal, psychology, social science | Tool-use occupations, physical work |
| **MCP** | What AI can do with tools | Office/admin, sales, technical support, data work | Teaching, social services |
| **Microsoft** | How Copilot is used | Moderate/uniform exposure everywhere | No extreme scores, misses high-risk |

![AEI vs MCP scatter at major level](figures/scatter_aei_vs_mcp_major.png)

![MCP vs Microsoft scatter at major level](figures/scatter_mcp_vs_microsoft_major.png)

---

## 7. Risk Tier Distribution: Microsoft Never Reaches "High Risk"

Using the job elimination risk tiers (High >= 60%, Moderate 40--60%, Restructuring 20--40%, Low < 20%):

| Tier | AEI | MCP | Microsoft |
|------|----:|----:|----------:|
| High Risk (>=60%) | 76 | 54 | **0** |
| Moderate (40--60%) | 113 | 120 | 121 |
| Restructuring (20--40%) | 198 | 304 | 433 |
| Low Exposure (<20%) | 536 | 445 | 369 |

![Tier distribution](figures/tier_comparison.png)

**Microsoft produces zero high-risk occupations.** Its maximum % tasks affected caps below 60%. AEI is the most concentrated (76 high-risk but also 536 low-exposure). MCP falls between, with fewer high-risk but also fewer low-exposure (broad moderate exposure).

For policy: using Microsoft alone would never flag any occupation as high-risk. The three-source average produces a more balanced picture.

![Tier shift: AEI to MCP](figures/tier_shift_aei_vs_mcp.png)

---

## 8. Sensitivity Analysis

### 8.1 Auto-Aug Toggle: The Biggest Lever

| Config | AEI | MCP | Microsoft |
|--------|----:|----:|----------:|
| Time + Aug ON (primary) | 25.5% | 30.4% | 25.7% |
| Time + Aug OFF | 30.7% | **56.5%** | **49.4%** |

Turning off auto-aug nearly doubles MCP and Microsoft's footprint but barely changes AEI. This means MCP and Microsoft flag many tasks as AI-relevant but rate them with low automatability scores. AEI's tasks tend to have higher auto-aug scores because its data captures tasks where AI is *actually being used effectively*.

![Sensitivity toggles](figures/sensitivity_toggles.png)

### 8.2 Physical Task Filter

AEI's physical-task exposure (15.1%) is notably lower than MCP (22.1%) and Microsoft (21.7%). People don't have conversations about physical tasks, but AI tools can still assist with informational components of physical jobs.

![Physical split](figures/physical_split.png)

### 8.3 Method Toggle

Top-10 major categories are perfectly stable across Time/Value methods for all three sources (10/10 overlap). The method toggle changes magnitudes, not rankings.

---

## 9. Key Takeaways

1. **Major-category findings are robust.** The top 6 most AI-exposed major categories are high-confidence findings supported by all three sources. Policy recommendations at this level are on solid ground.

2. **Agreement degrades with granularity.** Spearman rho drops from 0.81--0.85 at major to 0.56--0.65 at occupation. High-confidence findings drop from 46% to 1%. This is the most important structural finding.

3. **Minor-category findings are mostly usable** (35% high confidence, good correlations), but always note the source context. Broad and occupation-level findings require explicit source attribution.

4. **The three sources measure genuinely different things:** AEI = conversational usage (overweights education, legal), MCP = tool-augmented capability (overweights admin, sales, tech), Microsoft = copilot patterns (most conservative, no extreme scores).

5. **MCP sees the most total exposure** (30.4%) because tool access extends AI's reach beyond conversation. Microsoft produces the flattest, most conservative distribution.

6. **Microsoft never rates any occupation above 60%.** AEI finds 76 high-risk occupations, MCP finds 54, Microsoft finds zero.

7. **The dashboard's three-source average is the right default.** It triangulates across measurement approaches, dampens source-specific biases, and produces defensible numbers. The consensus effect is a feature.

8. **When citing specific occupations, always note the source.** "Telemarketers are 90% AI-exposed" is an MCP finding. "Postsecondary Teachers are 67% AI-exposed" is an AEI finding. Neither holds across all three sources.

---

## Config

- **Primary:** Time method | Auto-aug ON | National | All tasks
- **Sources (solo):** AEI Cumul. (Both) v4, MCP Cumul. v4, Microsoft
- **Aggregation levels:** Major, Minor, Broad, Occupation
- **Sensitivity:** Time vs Value, Auto-aug ON vs OFF, Physical toggle

## Files

**CSVs:**
- `economy_totals.csv` -- Total workers/wages/pct by source
- `confidence_major.csv`, `confidence_minor.csv`, `confidence_broad.csv`, `confidence_occupation.csv` -- Side-by-side scores, ranks, and confidence flags at each level
- `rank_correlations.csv` -- Spearman rho for all 12 level x pair combinations
- `divergence_*_vs_*_*.csv` -- Top-20 biggest disagreements per pair per level
- `{level}_{source}.csv` -- Full results per source per level
- `tier_counts.csv`, `tier_shift_*.csv` -- Risk tier distributions and shift matrices
- `occupations_tiered_*.csv` -- Full occupation lists with tiers per source
- `sensitivity_toggles.csv`, `physical_comparison.csv` -- Sensitivity analyses

**Key Figures:**
- `footprint_comparison.png` -- Economy-wide exposure by source
- `major/minor/broad_pct_tasks_affected.png` -- Grouped bars at each level
- `scatter_*_vs_*_*.png` -- Pairwise scatter plots (all levels)
- `divergence_*_vs_*_major.png` -- Biggest disagreement bars
- `confidence_summary.png` -- Confidence flag distribution across levels
- `rank_heatmap_major/minor/broad.png` -- Rank agreement heatmaps
- `score_dots_major/minor.png` -- Side-by-side score dot plots
- `tier_comparison.png`, `tier_shift_*.png` -- Risk tier charts
- `sensitivity_toggles.png`, `physical_split.png` -- Sensitivity charts
