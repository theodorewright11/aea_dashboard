# Work Activity Exposure

**Overarching question:** Which types of work are most affected by AI, and what does that mean for where education and workforce development should focus?

Unlike the job exposure analysis, this question is organized around what people *do* rather than what job they *hold*. The IWA (Intermediate Work Activity) level is the primary lens — specific enough to be actionable, broad enough to interpret across sectors.

---

## Sub-questions

| Folder | Question | Key output |
|--------|----------|-----------|
| `exposure_state/` | What is the current state of AI task exposure across work activities? | Ranked IWA/GWA/DWA tables, five configs, confirmed vs ceiling, trends |
| `activity_robustness/` | Which activities are AI-resistant, and which are in the next wave? | Robustness tiers, stable-robust IWAs, confirmed-to-ceiling gaps |
| `education_lens/` | What does this mean for what we teach and train? | Durable training targets, workforce-by-tier, domain exposure, growth trends |
| `audience_framing/` | How do findings translate for each audience? | Policy, workforce, researcher, and layperson framings with dedicated figures |

---

## Five Dataset Configs

All sub-questions use the same five canonical configs from `analysis/config.py`. All five are pre-combined datasets (is_aei=False) so they use the eco_2025 O*NET baseline — consistent across comparisons.

| Key | Dataset | Story |
|-----|---------|-------|
| `all_confirmed` | AEI Both + Micro 2026-02-12 | **PRIMARY** — All confirmed usage |
| `all_ceiling` | All 2026-02-18 | Upper bound — what AI can reach |
| `human_conversation` | AEI Conv + Micro 2026-02-12 | Conversational AI only |
| `agentic_confirmed` | AEI API 2026-02-12 | Confirmed agentic tool-use (AEI API only) |
| `agentic_ceiling` | MCP + API 2026-02-18 | Agentic deployment potential |

---

## How to Run

```bash
venv/Scripts/python -m analysis.questions.work_activity_exposure.exposure_state.run
venv/Scripts/python -m analysis.questions.work_activity_exposure.activity_robustness.run
venv/Scripts/python -m analysis.questions.work_activity_exposure.education_lens.run
venv/Scripts/python -m analysis.questions.work_activity_exposure.audience_framing.run
```

Sub-questions are independent and can be run in any order.
