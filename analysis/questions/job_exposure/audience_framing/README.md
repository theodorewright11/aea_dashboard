# Audience Framing

**Question:** How do the job exposure findings frame for different audiences?

Two targeted sub-analyses designed to produce policy-ready and researcher-ready framing:

1. **Hidden at-risk jobs** — Which occupations share a skill profile with high-exposure jobs but currently have low exposure themselves? These are the next wave of disruption.

2. **Skill domain concentration** — Which skill and knowledge domains are most dominant in high-exposure, low-outlook occupations? These are the areas where workforce development investment is most urgent.

Uses Skills + Knowledge (importance ≥ 3). Abilities excluded.

## Sub-analyses

### 1. Shared Skill Profiles
- Define high-exposure: pct_tasks_affected > median (all_ceiling config)
- Build average skill+knowledge profile of all high-exposure occupations
- For every occupation: compute cosine similarity to the high-exposure profile
- Flag low-exposure occupations with high similarity = "hidden at-risk"

### 2. Dominant Domains in High-Exposure / Low-Outlook
- High-exposure: pct > median
- Low-outlook: DWS star rating ∈ {2, 3} (not 1 which is good outcome / low wage)
- For qualifying occupations: aggregate skill+knowledge by avg (importance × level)
- Rank elements by dominance

## Key outputs

| File | Description |
|------|-------------|
| `results/hidden_at_risk_occs.csv` | Low-exposure occs ranked by skill similarity to high-exposure profile |
| `results/skill_profile_similarity.csv` | All occs: exposure level, similarity score |
| `results/dominant_elements_high_exp_low_outlook.csv` | Top elements in high-exposure / low-outlook jobs |
| `figures/hidden_at_risk_scatter.png` | Scatter: exposure vs skill-profile similarity |
| `figures/dominant_elements_bar.png` | Top 20 dominant skill+knowledge elements |

## Run

```bash
venv/Scripts/python -m analysis.questions.job_exposure.audience_framing.run
```
