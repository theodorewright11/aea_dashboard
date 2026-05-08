# AI Modes

**Question:** What's the automation/augmentation makeup of the footprint — agentic vs conversational, and how automatable are American workers' tasks?

## Three lenses

1. **Agentic vs conversational split** by major sector — using `human_conversation` vs `agentic_confirmed` configs
2. **Auto-aug score distribution** — employment-weighted histogram of the average auto-aug score across all occupations
3. **Mode scatter** — which sectors agentic leads vs conversational leads

## Key outputs

| File | Description |
|------|-------------|
| `results/mode_comparison_major.csv` | Major × mode: workers, wages, pct |
| `results/mode_totals.csv` | Aggregate totals per mode |
| `results/autoaug_by_major.csv` | Employment-weighted avg auto-aug score per major |
| `results/autoaug_by_config.csv` | Economy-wide auto-aug stats |

## Key figures (committed)

| Figure | Description |
|--------|-------------|
| `figures/agentic_vs_conversational.png` | Butterfly: agentic vs conversational by sector |
| `figures/autoaug_distribution.png` | Employment-weighted auto-aug score histogram |
| `figures/autoaug_by_major.png` | Avg auto-aug score per sector |
| `figures/mode_workers_scatter.png` | Scatter: agentic vs conv workers per sector |

## Run

```bash
venv/Scripts/python -m analysis.questions.economic_footprint.ai_modes.run
```
