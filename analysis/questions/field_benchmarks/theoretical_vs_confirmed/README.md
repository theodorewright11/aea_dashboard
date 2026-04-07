# Theoretical vs. Confirmed

**Question:** Where does confirmed usage sit relative to deployment readiness and technical capability?

Positions the AEA Dashboard's confirmed-usage numbers within the full methodological
spectrum: confirmed real-world usage → deployment-constrained readiness → technical
capability ceiling.

Key insight: our confirmed usage (~40%) already exceeds Iceberg's technical capability
estimate (11.7%) because they measure different things. This sub-analysis makes that
explicit with a unified view.

## Measurement layers

| Layer | What it captures |
|-------|-----------------|
| Confirmed usage (Layer 1) | What AI is actually doing right now in practice |
| Deployment-constrained (Layer 2) | What orgs could deploy today with current governance/oversight |
| Technical capability (Layer 3) | What AI tools are technically capable of performing |

## Outputs

| File | Description |
|------|-------------|
| `figures/measurement_spectrum.png` | All sources on one horizontal dot plot |
| `figures/layer_breakdown.png` | Grouped bar by measurement layer |
| `results/measurement_spectrum.csv` | All sources with layer classification and metric basis |

## Run

```bash
venv/Scripts/python -m analysis.questions.field_benchmarks.theoretical_vs_confirmed.run
```
