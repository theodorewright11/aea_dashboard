# Work Activity Comparison

**Question:** Which GWA-level work activities does AI touch most, and does this align with external platform data?

Compares our GWA-level exposure rankings (from the backend compute pipeline) to what
ChatGPT, Copilot, and AEI studies report about what types of work AI is actually doing.

The convergence is striking: Getting Information, Documenting/Recording, and Processing
Information appear as dominant work activity categories across every platform — despite
very different methodologies.

## Key external findings

| Source | Top GWA-aligned finding |
|--------|------------------------|
| ChatGPT (2025) | Writing (→ Documenting) = 40% of work sessions |
| Copilot (2025) | Getting Information = ~35% of enterprise sessions |
| AEI (2024) | Technical problem-solving (~37% of task-attempts) + 57% augmentative |

## Outputs

| File | Description |
|------|-------------|
| `figures/our_gwa_rankings.png` | Our top 15 GWAs by workers_affected |
| `figures/augment_vs_automate.png` | AEI's 57%/43% split |
| `figures/platform_gwa_alignment.png` | ChatGPT vs Copilot GWA distributions |
| `results/our_gwa_confirmed.csv` | Our GWA data (all_confirmed) |
| `results/chatgpt_gwa_distribution.csv` | ChatGPT GWA-mapped session data |
| `results/copilot_gwa_distribution.csv` | Copilot user goal GWA data |
| `results/aei_augment_automate.csv` | AEI augment/automate split |

## Run

```bash
venv/Scripts/python -m analysis.questions.field_benchmarks.work_activity_comparison.run
```
