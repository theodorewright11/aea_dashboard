# Automation Opportunity

**Question:** Where does AI capability already exceed human occupational need (positive SKA gap) AND the adoption gap is large — signaling where automation could happen right now?

---

## What This Measures

Two dimensions combined:

1. **SKA gap** (`overall_gap` from `compute_ska`) — positive = AI capability exceeds what the occupation needs; negative = human skills still lead.
2. **Adoption gap** — `pct_tasks_affected(ceiling) − pct_tasks_affected(confirmed)`.

**Quadrant framing:**

| | Large adoption gap | Small adoption gap |
|---|---|---|
| **AI leads (SKA gap > 0)** | Q1: Automation opportunity | Q2: Already adopted |
| **Humans lead (SKA gap < 0)** | Q3: Tool gap (training leverage) | Q4: Low priority |

Q1 is the primary target: AI can already do the work (SKA) and it's not being done yet (gap). When Q1 occupations also carry a **high risk tier** from job_risk_scoring, that's a signal for job transformation, not just upside opportunity.

---

## Outputs

| File | Contents |
|------|----------|
| `results/opportunity_scores.csv` | Per-occupation: SKA gap, adoption gap, quadrant, risk tier |
| `results/q1_occupations.csv` | Quadrant 1 occupations ranked by opportunity magnitude |
| `results/q1_transformation_signal.csv` | Q1 ∩ high-risk tier (transformation signal) |
| `results/sector_opportunity.csv` | Major-category average SKA gap × adoption gap |
| `results/quadrant_summary.csv` | Counts and employment by quadrant and major category |

Key figures (committed):
- `opportunity_scatter.png` — 2D scatter: SKA gap × adoption gap, colored by risk tier
- `opportunity_quadrant_summary.png` — quadrant distribution by major category
- `q1_top_occupations.png` — top Q1 occupations by workers × gap
- `transformation_signal.png` — Q1 + high risk occupations
- `sector_opportunity.png` — sector-level opportunity landscape

---

## Run

```bash
venv/Scripts/python -m analysis.questions.potential_growth.automation_opportunity.run
```
