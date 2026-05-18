[Paper Section Build Priority](https://www.notion.so/Paper-Section-Build-Priority-328e2b121d9e80398cf1de52b0c48629?pvs=21)

[Working Paper Notes](https://www.notion.so/Working-Paper-Notes-32ee2b121d9e80bf805bdc32212a4ea9?pvs=21)

# Automation Exposure Analysis: Measuring AI's Impact on the U.S. and Utah Workforce

## Working Paper — Draft Structure

---

## Abstract

[To be written last. 200-300 words summarizing: the problem, what we built, key findings across datasets, Utah-specific implications, and methodological contributions.]

---

## 1. Introduction & Framing

### 1.1 The Problem Space

- AI is reshaping labor markets, but measurement of this impact is in early stages and fraught with methodological limitations.
- Existing analyses tend to rely on single data sources, single methodologies, and produce single-number estimates that obscure uncertainty.
- Policy decisions (workforce development funding, educational curriculum changes, regulatory frameworks) are being made on incomplete evidence.
- "Analytical non-routine tasks are at risk to be impacted by AI" (Ozgul et al., 2024) — but which ones, how much, and with what confidence?

### 1.2 Why This Work Exists

- Originated through Utah's Office of AI Policy (OAIP) under the Department of Commerce.
- Utah is positioned as a case study: tech-forward state, unique demographic/economic profile, active policy interest in AI workforce impacts.
- The Anthropic Economic Index (AEI) provided a novel data source (real Claude conversation data mapped to O*NET tasks), but its analysis was limited to national-level, single-method findings.
- We extend this by: adding multiple data sources (MCP server classification, Microsoft analysis), building a multi-method interactive dashboard, producing Utah-specific estimates, and critically examining the limitations of all approaches.

### 1.3 What We Contribute

- A multi-source, multi-method measurement framework for AI automation exposure that makes uncertainty visible rather than hiding it.
- An interactive dashboard allowing policymakers and researchers to explore results under different assumptions (frequency vs. importance weighting, auto-augmentation adjustments, physical task filtering, geographic scope).
- A novel MCP server classification pipeline that independently measures AI tool capability exposure across occupational tasks.
- Utah-specific workforce exposure estimates with comparison to national patterns.
- A transparent accounting of data limitations, biases, and methodological choices — treating these as findings rather than footnotes.

### 1.4 Framing: The Cartoon Strip

[A simplified visual walkthrough of the core logic: Task exists → AI can do some of it → What does that mean for workers/wages/the economy? This section should make the core concept accessible to a non-technical reader in ~1 page. Think of it as "the version you'd explain at a dinner party."]

### 1.5 Roadmap

- Brief outline of paper structure for the reader.

---

## 2. Background & Related Work

### 2.1 The AI-Labor Literature Landscape

- Overview of existing approaches to measuring AI's impact on work: task-based frameworks (Autor, Acemoglu), exposure indices (Felten et al., Eloundou et al./GPT-4 paper), occupation-level assessments.
- The shift from "will AI replace jobs" to "which tasks within jobs are affected and how."
- The automation vs. augmentation distinction and why it matters for policy.

### 2.2 The Anthropic Economic Index

- What AEI measures: percent of Claude conversations used for specific occupational tasks.
- How they collected the data: 500K-1M conversations classified against O*NET task statements.
- Their key findings and the limitations they acknowledged.
- What they didn't do that we extend: multi-source comparison, geographic specificity, interactive exploration, methodological sensitivity analysis.

### 2.3 O*NET as the Task Taxonomy Backbone

- Role of O*NET in labor economics research.
- The hierarchical structure: tasks → DWA → IWA → GWA, and occupations → broad → minor → major.
- How O*NET data is collected (incumbent surveys, occupational experts, analyst review) — summarize Appendix B findings.
- Known limitations of O*NET: respondent representativeness unknown, cognitive burden on respondents leading to heuristic answering, the OE vs. incumbent skew toward higher job zones for OEs.
    - OE representation data: 66 analyst, 213 OE, 663 incumbent sources. 21% from OEs. Average job zone for OE = 4.0 vs incumbent = 2.9. Regression coefficient of 0.881 for job zone predicting OE source.
    - Years of experience: OE average 13-15 years across all zones, incumbent average 6-9 years.

### 2.4 BLS OEWS Data

- What it provides: employment counts and wage estimates by occupation, nationally and by state.
- Collection methodology and known limitations.
- Why we use 2024 data as the primary employment/wage reference.

### 2.5 The MCP Ecosystem as a Measurement Instrument

- What Model Context Protocol servers are and why they represent a different signal than conversation data.
- MCP servers represent tool capabilities AI can access, vs. AEI which represents tasks humans actually use AI for.
- This distinction matters: AEI measures revealed demand, MCP measures potential supply of AI capability.

### 2.6 The Microsoft Copilot Analysis

- What Microsoft's data contributes: a third independent signal of AI task relevance.
- Methodological differences from AEI and MCP.
- The auto_aug_mean metric and what it captures.

---

## 3. Data Sources & Construction

### 3.1 Data Source Overview

- Summary table of all data sources, their dates, what they measure, and their row/column structure.
- Timeline visualization: Microsoft (Sep 2024) → AEI v1 (Dec 2024) → AEI v2 (Mar 2025) → MCP v1 (Apr 2025) → MCP v2 (May 2025) → MCP v3 (Jul 2025) → AEI v3 (Aug 2025) → AEI v4 (Nov 2025) → MCP v4 (Feb 2026).

### 3.2 AEI Data Construction Pipeline

- Step 1: Map Anthropic task percentages to O*NET v20.1 (Oct 2015) task statements.
    - Why 2015 tasks: ensures full coverage of Anthropic's pct values; newer versions have increasing missing pct values. Unclear why Anthropic used 2015 version.
    - Normalization of duplicate tasks (4 duplicate pairs differing only in punctuation) — sum pcts.
    - Handling of tasks appearing in multiple occupations: n_occurrences column, pct divided by occurrence count for pct_normalized, original kept as pct_weighted.
- Step 2: Add SOC major occupational categories and broad counts from SOC Structure 2019.
- Step 3: Add 2024 wage and employment data.
    - 3.1: Crosswalk from 2010 to 2019 SOC codes for wage/employment merging.
    - 3.2: National wage data from OEWS May 2025. Fallback chain: detailed SOC → broad SOC → O*NET scraped wages (Jan 2020) with 1.24x inflation factor → hourly↔annual conversion.
    - 3.3: State (Utah) wage data. Fallback: hourly↔annual conversion → national wages.
    - 3.4: National employment. Fallback to broad category divided by broad_counts. Division by duplicate 2019 SOC count to avoid double-counting. Sum per occupation for finals.
    - 3.5: State (Utah) employment. Fallback: national employment × (Utah total emp / national total emp) proportion.
    - 3.6: Merge all wage/employment into task data.
- Step 4: Add 2015 wage and employment data (similar pipeline, no crosswalk needed since data is already on 2010 SOC).
- Step 5: Adjust employment columns for O*NET decimal SOC codes (e.g., 11-1011.00 vs 11-1011.03) using pct_normalized proportions to allocate employment.
- Step 6: Add task rating data.
    - 6.1: O*NET Task Ratings v29.3 (May 2025) and v20.1 (Oct 2015). Frequency conversion weights: 1=1/260, 2=3/260, 3=48/260, 4=130/260, 5=1, 6=3, 7=12.
    - 6.2: Merge ratings into task data on task + title match.
    - 6.3: Fill missing ratings — occupation average if ≥3 values exist, else major occupation category average. 2025: 647/4251 imputed (345 occupation-level, 302 major-level). 2015: 129/4251 imputed.
    - 6.4: Merge 2015 and 2025 ratings into single frame.
- Step 7: Final cleanup. Drop "None" task row, recalculate weighted pct, fill missing task_type (Core if relevance≥67 and importance≥3, else Supplemental), fill missing n_responding with occupation median.

### 3.3 Economy Baseline (ECO) Data Construction

- Step 8: Create economy-wide task frequency data.
    - 8.1/8.2: National ratings + employment for 2025 and 2015 using OEWS + O*NET ratings.
    - 8.3/8.4: State ratings + employment.
    - 8.5: Add major occupational categories.
    - These become the denominators (eco_2025.csv, eco_2015.csv) for all exposure calculations.
    - ECO 2015 used as baseline for AEI (2010 SOC). ECO 2025 used as baseline for MCP/Microsoft (2019 SOC).

### 3.4 MCP Server Classification Pipeline

- How MCP servers were collected and classified against O*NET tasks.
    - Date-based versioning: v1 (≤Apr 2025, ~2,978 MCPs), v2 (≤May 2025, ~6,361), v3 (≤Jul 2025, ~8,883), v4 (≤Feb 2026, ~10,058).
    - MCP v4 is cumulative (includes all prior data plus new). AEI versions are independent snapshots.
- The LLM classification pipeline: DWA selection, task rating (1-5 scale).
- Human validation results: 26 MCPs validated.
    - DWA recovery: 36.9% (LLM-chosen) / 29.9% (task rating input).
    - Task context coverage: 63.4% of human-identified tasks found in pipeline.
    - Rating agreement: pipeline mean 3.36 vs human implicit 5 (MAE 1.64). 13.3% rated 5, 40% rated 4, 20% rated 3.
    - GWA alignment: 50.1% recall, 0.140 Jaccard. IWA: 32.5% recall, 0.077 Jaccard.
- Physical task bias in MCP data: MCPs that rated physical tasks 3-5 had higher average mean ratings overall (2.18 vs 1.66). Not explained by language or description length — something about these MCPs' capabilities makes them seem more broadly applicable.
- MCP conditional distributions for auto/aug imputing (the scope bin table).
    - Global distribution: 40.5% rating 1, 31.6% rating 2, 20.6% rating 3, 6.8% rating 4, 0.5% rating 5. Global mean: 1.952.

### 3.5 Microsoft Data Integration

- Source and structure of Microsoft's automation/augmentation data.
- Mapping from Microsoft's task version (v29.0) to current version — ~50 tasks imputed using DWA majority rule.
- The auto_aug_mean and auto_aug_mean_adj columns.
- Physical task flagging from Microsoft's data.

### 3.6 Automation/Augmentation Score Construction

- Step 9 from pipeline: merging auto/aug data into task-level final data.
- Imputation of missing method distributions across three confidence tiers:
    - Low-confidence (filtered < 0.5): normalize existing method weights.
    - Mid-confidence (0.5–0.99): distribute filtered value proportionally using low-confidence task mix from same occupation/major category.
    - High-confidence (≥0.99): directly assign normalized occupation/category-level proportions.
- Robustness check: multiplying each column by pct_normalized yields sums within 1% of Anthropic's published values.

### 3.7 SOC Crosswalk: 2010 to 2019

- Why this is needed: AEI uses 2010 SOC codes, MCP/Microsoft use 2019.
- The crosswalk pipeline in compute.py: split_count normalization (dividing task_comp by number of 2019 titles per 2010 title), task_prop deflation (accounting for different task set sizes between 2010 and 2015 task lists vs 2025).
    - task_prop statistics: mean 1.035, median 1.0, max 3.3. About 75 titles >1.25, 147 >1.0, 269 >1.01 (out of 923).

### 3.8 Data Limitations & Known Issues

- AEI: 2015 task statements may not capture newer occupational tasks. ~4% of AEI data's DWA/IWA/GWA taxonomy doesn't merge.
- MCP: Classification pipeline has moderate agreement with human validation. Physical task bias exists. Cumulative versioning means trends show growth, not independent snapshots.
- Microsoft: Single time point only. Different task version requiring imputation.
- O*NET ratings: Imputation rates (4-15% depending on year), OE/incumbent bias, heuristic survey responses.
- Employment data: Broad category division assumes equal distribution. Utah imputation assumes proportional workforce composition.
- General: All three AI data sources measure different things (revealed demand vs. tool capability vs. expert assessment), making direct comparison informative but not apples-to-apples.

---

## 4. Methodology

### 4.1 Task Completion Computation

- Two methods, both producing a per-task weight:
    - Frequency method: task_comp = freq_mean (how often the task is performed daily).
    - Importance-weighted method: task_comp = relevance × 2^importance (exponentially weights important tasks).
- Rationale for both: frequency captures volume of work, importance captures value of work. Different policy questions favor different methods.
- Auto-augmentation multiplier (optional): task_comp × (auto_aug_mean / 5). Scales task completion by the degree to which AI can automate/augment the task. When applied, this shifts from "what tasks exist" to "what tasks are AI-exposed."
    - For MCP: auto_aug_mean_adj preferred (excludes flagged ratings).
    - Scale discussion: the 0-5 auto_aug divided by 5 produces a 0-1 multiplier. Since both numerator and denominator in the final ratio use the same task_comp formula, absolute scale differences between freq and importance methods cancel out in the percentage metric.

### 4.2 Occupation-Level Exposure Metrics

- Three output metrics, all derived from the task_comp ratio:
    - pct_tasks_affected = Σ(AI task_comp for matched tasks) / Σ(ECO task_comp for all tasks) × 100. This is a ratio-of-totals, never an average of percentages. Capped at 100%.
    - workers_affected = pct_tasks_affected / 100 × occupation employment.
    - wages_affected = pct_tasks_affected / 100 × occupation employment × median annual wage.
- Aggregation: occupation-level pct is computed per occupation, then workers/wages are summed up the hierarchy. For group-level pct (major/minor/broad), task_comp sums are reaggregated at the group level (not averaged from occupation pcts).

### 4.3 AEI Crosswalk Pipeline

- Detailed walkthrough of how AEI data (2010 SOC) gets mapped to 2019 SOC for comparison with ECO 2025 baseline:
    1. Dedup AEI on (title, task_normalized).
    2. Join crosswalk → O*NET-SOC 2019 Title.
    3. Divide task_comp and emp by split_count (number of 2019 titles per 2010 title).
    4. Group by (2019_title, task_normalized): sum task_comp, sum emp.
    5. Deflate task_comp by task_prop from eco_2025 (ratio of new task set size to old).

### 4.4 Multi-Dataset Combination

- When multiple datasets are selected, results are combined per-category by either averaging or taking the max of each metric across datasets.
- Outer join ensures categories present in any dataset appear in the combined result.
- Semantic interpretation: Average = "consensus estimate across sources." Max = "upper bound / most exposed according to any source."

### 4.5 Work Activity Analysis

- Same task_comp framework but aggregated to DWA/IWA/GWA levels instead of occupation hierarchy.
- Worker allocation: emp_per_task = occupation employment / number of unique tasks in that occupation. Each task's worker contribution = (AI_tc / ECO_tc) × emp_per_task.
- A task mapping to multiple DWAs contributes its full allocation to each DWA independently (they represent different facets of the same work, not competing allocations).
- AEI datasets use ECO 2015 baseline (2010 SOC). MCP/Microsoft use ECO 2025 baseline (2019 SOC). These groups cannot be mixed in a single computation.

### 4.6 Time Trend Analysis

- For dataset series with multiple versions (AEI v1-v4, MCP v1-v4), compute exposure metrics at each time point using the same methodology.
- Three combination modes at each time point: average across overlapping datasets, max, or individual (each dataset as separate line).
- Note on interpretation: AEI trends represent genuine temporal change (independent snapshots of Claude usage). MCP trends represent cumulative capability growth (each version includes all prior MCPs plus new ones).

### 4.7 Physical Task Handling

- Physical task flag sourced from Microsoft's analysis, mapped to O*NET tasks.
    - ~50 tasks imputed via DWA majority rule where Microsoft version didn't map directly.
- Three modes: include all tasks, exclude physical tasks, physical tasks only.
- Physical task composition: AEI data ~13.9% physical true, ~74.5% false, ~11.6% missing. MCP data: 31.3% true, 68.7% false (nearly complete coverage).
- Rationale: physical tasks are unlikely to be automatable by current AI, so excluding them may provide a more accurate picture of cognitive/digital work exposure.

### 4.8 Geographic Adjustment

- National estimates use OEWS national employment and wage data directly.
- Utah estimates use OEWS state data where available, with fallback to national proportional scaling.
    - Utah proportion = Utah total employment / national total employment.
    - Note from AEI paper: Utah may over-complete AI tasks relative to national average (population-proportional basis). This is not yet incorporated into our estimates but is discussed in limitations.

### 4.9 Configuration Sensitivity

- The dashboard exposes multiple methodological toggles. Each represents a legitimate analytical choice:
    - Freq vs. importance weighting → volume vs. value of affected work.
    - Auto-aug on vs. off → "tasks that exist in AI conversations" vs. "tasks weighted by AI capability."
    - Physical include vs. exclude → total workforce vs. cognitive/digital workforce.
    - Average vs. max combination → consensus vs. upper-bound exposure.
    - National vs. Utah → different employment/wage compositions.
- Sensitivity analysis: for each toggle, how much do the top-ranked categories change? Categories that are robust across all configurations are the strongest findings. Categories that shift dramatically are methodologically dependent — interesting but require caveats.

---

## 5. Results

### Part 1 — This is real (credibility)

### Part 2 — Here's what it is (characterization)

### Part 3 — Here's what to do about it (action)

---

## 6. Discussion & Implications

### 6.1 What This Tells Us About AI and Work

- The core finding pattern (to be refined once results are in): AI exposure is concentrated in [X] but present across virtually all occupation categories to some degree.
- The difference between "affected" and "replaced" — exposure metrics measure task overlap, not job elimination.
- The automation vs. augmentation framing: much of what we measure is augmentation (AI helping with tasks) rather than full automation.

### 6.2 Implications for Workforce Development

- "The future skills landscape demands a fundamental reorientation of educational priorities. Critical thinking, task delegation, and decision-making capabilities will become the core competencies of the AI-augmented workforce." (adapted from Luckin, 2024; Abulibdeh, 2025)
- Which sectors have high capability exposure but low adoption (MCP high, AEI low)? These represent potential productivity gains if adoption barriers are addressed.
- Which sectors are rapidly increasing in AI exposure over time? These need proactive workforce transition support.
- AI literacy as a universal need: "Early and frequent exposure to AI tools should become standard practice" — our data can inform where this is most urgent.

### 6.3 Implications for Policy

- How OAIP and similar bodies can use this dashboard for evidence-based policy.
- The value of the interactive, multi-method approach: policy decisions should not be based on a single number from a single source.
- Utah-specific policy recommendations (to be developed from Utah results).

### 6.4 Levels of Credibility

- Not all findings have equal evidentiary weight. Framework for interpreting results:
    - High credibility: findings consistent across all data sources, robust to config changes.
    - Medium credibility: findings consistent across most sources or most configs, with explainable variation.
    - Low credibility: findings dependent on a single source or highly sensitive to methodology choices.
- This framework should be applied to all specific claims made from the data.

### 6.5 What Extra Production Is Happening With AI

- Reframing exposure from "risk" to "productivity": if AI is doing X% of tasks in a sector, what does that mean for output?
- Sectors where AI adoption appears to be creating value vs. sectors where it's not yet visible.
- The relationship between adoption speed and sector characteristics.

---

## 7. Limitations

### 7.1 Data Source Limitations

- AEI: single LLM provider (Claude), voluntary user base (not representative of all workers), 2015 task taxonomy, conversation classification accuracy unknown.
- MCP: LLM-based classification with moderate validation agreement, physical task bias, cumulative versioning conflates temporal change with data growth.
- Microsoft: single time point, different task version, expert assessment rather than observed usage.
- O*NET: survey-based ratings with known respondent biases, imputation required for missing values.
- OEWS: broad category employment division assumes equal distribution, Utah imputation assumes proportional composition.

### 7.2 Methodological Limitations

- Task-based approach assumes tasks are independent units — in reality, tasks within a job are interdependent.
- Percentage-based exposure doesn't capture intensity — a task could be 80% automatable or 5% automatable and both count the same without auto-aug weighting.
- The crosswalk between 2010 and 2019 SOC introduces noise through split_count division and task_prop deflation.
- Averaging across data sources treats each source equally regardless of sample size or methodology quality.

### 7.3 Interpretive Limitations

- Exposure ≠ displacement. High task exposure may lead to job augmentation, not elimination.
- These metrics are backward-looking (based on current AI capabilities and current task definitions) — AI capabilities are changing rapidly.
- Wage impacts are estimated as proportional to task exposure, which oversimplifies the actual economic adjustment mechanisms.

---

## 8. Future Work

### 8.1 Actual Task Completion Counts

- Moving from percentages to absolute counts: multiply pct_normalized by total conversations, scale by Claude's market share, adjust for Utah's over-completion.
- Alternative: use task count data from AEI v3/v4 for exact counts.
- Skew adjustment: compare pct conversation proportions across Anthropic, Microsoft, ChatGPT weighted by market share to identify and correct for source-specific biases.

### 8.2 Enhanced MCP Analysis

- The MCP dataset could support its own standalone paper.
- Deeper analysis of what MCP capability profiles reveal about the AI tool ecosystem.
- Longitudinal tracking of MCP server growth and capability expansion.

### 8.3 Toward a Multi-Dimensional Framework for AI-Task Interaction

- The exposure metrics presented in this paper treat AI-task interaction as a single scalar value — a task either appears in AI conversations (AEI), has tool coverage (MCP), or receives an automatability rating (Microsoft). In reality, whether AI actually gets deployed for a given task is determined by the interaction of multiple independent dimensions.
- We are developing a three-layer classification framework:
    - **Task Profile**: structural characteristics of the task itself — how serializable is the context, how variable are inputs across instances, how verifiable is the output, how severe are errors, how much judgment is required, how relational or physical is the work.
    - **AI Capability Assessment**: what current AI systems can realistically do — assessed across task phases (context gathering, analysis/planning, execution, output formatting, self-verification), distinguishing theoretical capability from practical capability given real-world tooling.
    - **Deployment Feasibility**: the real-world friction that determines whether capability translates to adoption — task value density, implementation costs, verification overhead, error cost asymmetry, regulatory constraints, organizational readiness, trust/sentiment barriers.
- This framework addresses a critical gap: two tasks can receive identical single-number exposure scores while having fundamentally different deployment profiles. A high-exposure task with catastrophic error consequences and hard regulatory blocks (e.g., clinical diagnosis) has a very different trajectory than a high-exposure task with trivial error costs and zero regulatory friction (e.g., database searching). Current indices, including those presented in this paper, collapse this distinction.
- Illustrative example: the AEI data may show moderate conversation share for a medical assessment task, and MCP data may show emerging tool coverage. But the task profile (low context serialization, high error severity, high relational dependence) and deployment feasibility (hard regulatory blocks, high verification overhead, high trust friction) predict that real-world deployment will remain limited to augmentation rather than substitution — a prediction invisible to percentage-based metrics alone.
- The framework is designed for empirical validation against the multi-source dataset presented in this paper. Tasks classified along these dimensions should show predictable patterns in their AEI, MCP, and Microsoft exposure scores. Dimensions like context serialization and physical world dependence should predict exposure levels; dimensions like regulatory constraint and error cost asymmetry should predict the gap between capability (MCP scores) and revealed usage (AEI scores). This validation is the subject of forthcoming work.

### 8.4 Dashboard Enhancements

- Actual count integration when methodology is validated.
- Additional data source integration as new AI impact measurements become available.
- User-facing confidence intervals or uncertainty ranges on all metrics.

### 8.5 Broader Validation

- Cross-referencing with firm-level AI adoption surveys.
- Comparison with other AI exposure indices (Felten, Eloundou, etc.).
- Longitudinal validation: do high-exposure occupations actually experience observable labor market changes?

---

## References

[To be compiled. Key references to include:]

- Anthropic Economic Index paper
- Ozgul et al., 2024 (analytical non-routine tasks at risk)
- Luckin, 2024; Abulibdeh, 2025 (AI literacy and educational priorities)
- Felten et al. (AI occupational exposure)
- Eloundou et al. / OpenAI GPTs are GPTs paper
- Acemoglu & Restrepo (task-based framework)
- Autor (work of the future)
- O*NET methodology documentation
- BLS OEWS documentation
- arxiv.org/pdf/2510.23669

---

## Appendices

### Appendix A: Column Reference

[Appendix A: Column Reference](https://www.notion.so/Appendix-A-Column-Reference-327e2b121d9e8072b54cea9c1894e3cf?pvs=21)

### Appendix B: O*NET Data Collection Deep Dive

[The detailed O*NET methodology section from the write-up, including task creation process, surveying methodology, OE vs incumbent analysis, experience distribution tables, the full statistical breakdown.]

### Appendix C: Frequency Weight Assumptions

- 1 = 1/260 (once per year)
- 2 = 3/260 (more than once per year → ~3 times/year)
- 3 = 48/260 (more than once per month → ~4 times/month)
- 4 = 130/260 (more than once per week → ~2.5 times/week)
- 5 = 1 (daily)
- 6 = 3 (several times per day → ~3 times/day)
- 7 = 12 (hourly or more → ~1.5 times/hour, ~12 times/day)

### Appendix D: MCP Classification Pipeline Details

[Detailed methodology of how MCPs were scraped, classified, validated. The conditional distribution table. Physical task bias analysis. Human validation protocol and full results.]

### Appendix E: Imputation Summary Statistics

- AEI rating imputations: 2025 = 647/4251 (15.2%), 2015 = 129/4251 (3.0%).
- ECO rating imputations: 2025 = 4% DWA-based, 2015 = 13% DWA-based + <1% major.
- Employment imputations: national missing counts per merge step (see data merging write-up), Utah fallback rates.
- Wage imputation chain and fallback rates at each step.
- task_prop distribution: mean 1.035, std 0.274, 75 titles >1.25 out of 923.

### Appendix F: MCP Auto/Aug Rating Distributions

[The full scope bin table showing conditional distributions of ratings by pct_moderate_plus. 20 bins from 0-5% to 95-100% with N MCPs, N ratings, and full rating distribution for each.]

### Appendix G: Dashboard User Guide

The ranking in the trends — for value its on the max or average, for increase its on the start to finish differences

when hovering on Group A, show the delta as absolute difference and the percent as `(A - B) / B × 100` labeled as "vs Group B." When hovering on Group B, show `(B - A) / A × 100` labeled as "vs Group A." Each group always uses the other as the denominator. This way the percent always answers "how much more/less is this group compared to the other one." Positive means this group is higher, negative means lower.

### Appendix H: Configuration Sensitivity Full Results

[The complete sensitivity analysis output — all config variants across all dataset groups, with rank changes flagged.]