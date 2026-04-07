# Potential Growth

**Overarching question:** Where is current AI usage far below demonstrated capability, and what is the economic value of closing that gap?

This is the "opportunity" counterpart to the exposure and risk analyses. Rather than asking who is most exposed or at risk, it asks: where does unrealized potential live, and who benefits if it gets captured?

---

## Sub-Questions

| Sub-folder | Question |
|------------|----------|
| `adoption_gap/` | Where is confirmed usage furthest below the capability ceiling, across occupations and work activities? |
| `wage_potential/` | Which occupations and sectors have the highest economic value locked in their adoption gap? |
| `automation_opportunity/` | Where does AI capability exceed human need (SKA) AND the adoption gap is large — signaling maximum automation opportunity, with job transformation as an embedded signal? |
| `audience_framing/` | How do the potential growth findings translate for policy, workforce, researchers, and laypeople? |

---

## Primary Config

All sub-questions use `all_confirmed` as the baseline (what AI is actually doing) and `all_ceiling` as the ceiling (what AI could demonstrably do). The gap between them is the core analytic object.

See `ANALYSIS_PRD.md` for the full five-config reference.

---

## Key Outputs

- `adoption_gap_report.md` — standouts at every aggregation level (major/minor/broad/occ and GWA/IWA/DWA)
- `wage_potential_report.md` — wage dollars locked in the gap; hotspot occupations
- `automation_opportunity_report.md` — SKA × adoption gap quadrant analysis with risk tier overlay
- `audience_framing_report.md` — four audience lenses on the same findings
- `potential_growth_report.md` — aggregate synthesis across all four sub-questions

---

## Running

Run each sub-question from the project root:

```bash
venv/Scripts/python -m analysis.questions.potential_growth.adoption_gap.run
venv/Scripts/python -m analysis.questions.potential_growth.wage_potential.run
venv/Scripts/python -m analysis.questions.potential_growth.automation_opportunity.run
venv/Scripts/python -m analysis.questions.potential_growth.audience_framing.run
```

Note: `audience_framing` loads CSVs from the other three sub-questions; run it last.
