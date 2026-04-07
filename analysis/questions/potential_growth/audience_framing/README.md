# Audience Framing

**Question:** How do the potential growth findings land for different audiences — policy, workforce practitioners, researchers, and laypeople?

---

## What This Does

Pulls key results from `adoption_gap/`, `wage_potential/`, and `automation_opportunity/` and reframes them for four distinct audiences. Each audience cares about different dimensions of the same underlying finding.

**Policy:** Where should investment go? What's the GDP-scale opportunity? Which sectors are priority targets for AI adoption programs?

**Workforce / educators:** Which occupations are prime targets for AI tool-literacy training right now? Where does training today close a gap that already exists? (Caveat: we can point at Q3 and Q1 occupations as likely candidates, but what AI means for specific jobs is genuinely uncertain — commentary here is directional, not prescriptive.)

**Researchers:** How stable are these findings across configs? What are the methodological caveats? Where is the signal vs. noise?

**Laypeople:** Plain-language framing with concrete examples. The goal is to explain what the gap means for someone in a specific kind of work — not to make predictions, but to give honest context.

---

## Outputs

| File | Contents |
|------|----------|
| `results/policy_priorities.csv` | Sectors ranked by combined wage gap + workers gap |
| `results/workforce_targets.csv` | Q1 + Q3 occupations sorted by emp × median wage |
| `results/researcher_sensitivity.csv` | Gap magnitude across all 5 configs at major level |

Key figures (committed):
- `policy_investment_priorities.png` — sectors by wage gap + workers gap
- `workforce_training_targets.png` — Q1/Q3 occupations by employment × wage
- `researcher_config_sensitivity.png` — gap across configs
- `layperson_opportunity.png` — plain-language sector overview

---

## Note on Workforce / Layperson Framing

The workforce and layperson sections are intentionally loose. We know where the gap is. We don't fully know what it means for workers in specific jobs — that depends on organizational decisions, specific tool adoption, and factors this dataset can't capture. The framing here gives context and directional guidance, not prescriptions.

---

## Run

Requires the other three sub-questions to have been run first (loads their CSVs).

```bash
venv/Scripts/python -m analysis.questions.potential_growth.audience_framing.run
```
