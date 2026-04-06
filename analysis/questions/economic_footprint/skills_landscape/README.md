# Skills Landscape

**Question:** What do SKA gaps and technology category profiles look like across the economy? Where does AI lead over human skill, and where do humans still have the advantage?

## Two parts

1. **SKA element gaps** — Run the SKA pipeline for all 5 configs. At the economy level, identify which specific skill/ability/knowledge elements show the biggest AI advantage (gap > 0) vs human advantage (gap < 0). Aggregate gaps by major sector.

2. **Technology category exposure** — Load O*NET technology skills (v30.1, ~127 distinct commodity categories). Weight each category by `pct_tasks_affected × employment` summed across all occupations using it. Shows which technology domains sit in the highest-exposure parts of the economy.

## Key outputs

| File | Description |
|------|-------------|
| `results/ska_economy_elements.csv` | Per-element: ai_capability, eco_baseline, gap, domain |
| `results/ska_top_ai_leads.csv` | Top 30 elements where AI leads |
| `results/ska_top_human_leads.csv` | Top 30 elements where humans lead |
| `results/ska_major_gaps.csv` | Avg overall_gap per major × config |
| `results/tech_categories_economy.csv` | All ~127 tech categories with exposure weight |
| `results/tech_categories_major.csv` | Tech penetration by major sector |

## Key figures (committed)

| Figure | Description |
|--------|-------------|
| `figures/ska_leads_ai.png` | Top 20 elements where AI leads |
| `figures/ska_leads_human.png` | Top 20 elements where humans lead |
| `figures/ska_major_heatmap.png` | Heatmap: sector × config, avg SKA gap |
| `figures/tech_top_economy.png` | Top 25 tech categories by exposure weight |
| `figures/tech_major_heatmap.png` | Tech penetration heatmap by sector |

## Run

```bash
venv/Scripts/python -m analysis.questions.economic_footprint.skills_landscape.run
```
