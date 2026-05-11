# Part 2 — Characterization: Where AI Exposure Falls

Six chart groups characterizing the structural distribution of AI exposure.
The Part 2 narrative moves from major-cat lens → forward trajectory → job
zone → work activities → SKA, with a physical / non-physical structural
overlay running through every chart.

## Figures

| Figure | What It Shows |
|--------|--------------|
| `major_categories.png` | All 22 majors as a 5-panel trio: Variant A (naive non-phys task share, no AI signal) · Variant B (% tasks exposed restricted to non-physical work) · All Confirmed % · Workers · Wages. n_occs-by-phys-bucket annotation in the subtitle replaces the dropped box plot. |
| `major_categories_trend.png` | Three panels (% tasks / workers / wages). Per-panel top-10 movers ranked by absolute observed change first → final snapshot. Solid bar = current value, faint hatched extension = 2-year linear OLS projection. |
| `job_zone_violin.png` | Violins of % tasks exposed per O*NET job zone (1–5) on the left, plus a thin stacked bar on the right showing the % of each zone's occupations that are Physical / Mixed / Non-Physical. |
| `job_zone_violin_nonphys.png` | Same chart as above but restricted to occupations with `pct_physical < 33%`. Tests whether the zone signal holds once the phys/non-phys structure is stripped. |
| `gwa_exposure.png` | Five-panel quintet matching the major trio: Variant A · Variant B · All Confirmed % · Workers · Wages. All ~41 GWAs shown, shared y-axis ordered by All Confirmed pct descending. |
| `ska_skills.png` | AI Top-10 average per Skill element, normalized to % of workforce maximum. Bar color: three-tier physical-mix coloring based on the mean `pct_physical` of occupations using the element at imp ≥ 3. |
| `ska_knowledge_abilities.png` | Knowledge (10 subcategories / 33 elements) + Abilities (15 subcategories / 52 elements), each subcategory bar colored by its mean element-level phys-mix tier. |

## Variants A and B

Two structural lenses run through the major-cat and GWA charts:

- **Variant A — Naive Physical Pct.** Per (occupation or GWA): `Σ freq_mean[non-physical tasks] / Σ freq_mean[all tasks] × 100`. No AI data touches this. It's the prediction you'd make if you knew nothing about AI except "non-physical tasks are AI-touchable, physical ones aren't."
- **Variant B — Within Non-Phys Real Pct.** Dashboard pipeline run with `physical_mode="exclude"`. Both numerator and denominator restricted to non-physical tasks. Auto-aug ON, freq weighting.

The gap between Variant A and the All Confirmed reading is the within-non-phys discriminatory signal in the AI data.

## SKA phys-mix coloring

Per element, mean of `pct_physical` across all occupations using the element at `importance ≥ 3` (unweighted; no employment weighting). Mapped to three tiers using the same `<33% / 33-67% / >67%` cuts as the major chart:

- **Non-physical (slate blue)** — element predominantly used by cognitive occupations
- **Mixed (sage green)** — element used by a mix of occupational physical profiles
- **Physical (gold)** — element predominantly used by physically-heavy occupations

Subcategory bars (Knowledge + Abilities chart) inherit a single tier color from the mean of their elements' phys scores.

## Major-cat trend projection

`major_categories_trend.png` fits a linear OLS through `ANALYSIS_CONFIG_SERIES["all_confirmed"]` (Mar 2025 → Feb 2026, 4 snapshots) per major × metric, then extrapolates 2 years past the final snapshot. Each panel's top 10 is ranked by absolute observed change from first to final snapshot. Linear extrapolation is the simplest defensible "if recent rate continued" frame at this horizon; longer horizons would need richer growth models.

## Config

All Confirmed (`final_all_confirmed_usage_2026-02-12`) | National | Freq (time-weighted) | Auto-aug ON

Variant B uses the same pipeline with `physical_mode="exclude"`.

## Run

```bash
venv/Scripts/python -m analysis.paper.results.part_2.run
```

## Tests

```bash
venv/Scripts/python -m pytest analysis/paper/results/part_2/test_part_2.py -v
```
