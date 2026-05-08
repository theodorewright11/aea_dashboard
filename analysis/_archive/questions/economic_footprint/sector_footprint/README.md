# Sector Footprint

**Question:** Which sectors lead on workers affected, wages affected, and % tasks affected — and how wide is the uncertainty range from confirmed usage to the ceiling?

## Key outputs

| File | Description |
|------|-------------|
| `results/aggregate_totals.csv` | National aggregate: workers, wages, pct per config |
| `results/major_all_configs.csv` | Major category × 5 configs |
| `results/major_primary.csv` | Primary config major breakdown |
| `results/minor_primary.csv` | Minor category breakdown (primary config) |

## Key figures (committed)

| Figure | Description |
|--------|-------------|
| `figures/aggregate_totals.png` | Grouped bar: workers/pct across 5 configs |
| `figures/major_workers.png` | Top major categories by workers affected |
| `figures/major_wages.png` | Top major categories by wages affected |
| `figures/major_pct.png` | Top major categories by % tasks affected |
| `figures/floor_ceiling_range.png` | Dumbbell: confirmed vs ceiling per major |
| `figures/config_heatmap.png` | Heatmap: major × config |

## Run

```bash
venv/Scripts/python -m analysis.questions.economic_footprint.sector_footprint.run
```
