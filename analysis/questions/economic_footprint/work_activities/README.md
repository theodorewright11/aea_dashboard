# Work Activities

**Question:** What does the GWA/IWA/DWA-level footprint look like through the economic footprint lens — which work activity types lead, and how do modes and trends compare?

## Scope note

This sub-question covers the **economic footprint angles** for work activities:
- Which GWAs/IWAs lead on workers/wages/pct
- Agentic vs conversational split at GWA level
- GWA-level trends over time (all_confirmed series)
- Cross-config heatmap at GWA level

For deeper WA exposure analysis (full tier distributions, WA SKA, education framing), see `analysis/questions/work_activity_exposure/`.

## Key outputs

| File | Description |
|------|-------------|
| `results/gwa_all_configs.csv` | GWA × 5 configs: workers, wages, pct |
| `results/iwa_primary.csv` | IWA breakdown, primary config |
| `results/gwa_mode_comparison.csv` | GWA × mode (conv vs agentic) |
| `results/gwa_trend.csv` | GWA trends over all_confirmed series |

## Key figures (committed)

| Figure | Description |
|--------|-------------|
| `figures/gwa_workers.png` | Top GWAs by workers affected |
| `figures/gwa_pct.png` | Top GWAs by % tasks affected |
| `figures/gwa_config_heatmap.png` | Heatmap: GWA × config |
| `figures/gwa_mode_butterfly.png` | Butterfly: agentic vs conv by GWA |
| `figures/gwa_trend.png` | Top 5 GWAs by pct growth (all_confirmed) |

## Run

```bash
venv/Scripts/python -m analysis.questions.economic_footprint.work_activities.run
```
