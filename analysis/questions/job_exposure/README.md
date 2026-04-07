# Job Exposure

**Overarching question:** Where is work being transformed by AI, who is most at risk of displacement rather than just augmentation, and what can workers and policymakers do about it?

---

## Sub-questions

| Folder | Question | Key output |
|--------|----------|-----------|
| `exposure_state/` | What is the current state of AI task exposure? | Tier distribution across 923 occs, five configs, time trends |
| `job_risk_scoring/` | Which jobs are most at risk of replacement (not just change)? | 7-factor composite risk scores, high/moderate/low tiers |
| `worker_resilience/` | What can individual workers do to stay relevant? | Per-occ SKA gap — where human advantage is largest vs. where AI leads |
| `pivot_distance/` | How costly is it to reskill from a high-risk to a low-risk job? | Average pivot cost by job zone, with example occupations |
| `audience_framing/` | How do findings translate for different audiences? | Shared skill profiles (hidden at-risk jobs), dominant domains in high-risk/low-outlook jobs |
| `occs_of_interest/` | How do all the above findings land for specific named occupations? | Focused outputs for 29 occupations across three groups |

---

## Five Dataset Configs

All sub-questions run against five canonical configs (defined in `analysis/config.py`):

| Key | Dataset | Story |
|-----|---------|-------|
| `all_ceiling` | `All 2026-02-18` | Upper bound — what AI can reach |
| `human_conversation` | `AEI Conv + Micro 2026-02-12` | Where conversational AI is being used today |
| `agentic_confirmed` | `AEI API 2026-02-12` | Where agentic tool-use is confirmed (AEI API only) |
| `all_confirmed` | `AEI Both + Micro 2026-02-12` | All confirmed usage (no MCP ceiling) |
| `agentic_ceiling` | `MCP + API 2026-02-18` | Agentic deployment potential |

The gap between `human_conversation` and `all_ceiling` shows deployment opportunity. The agentic configs show how much architectural investment (vs. browser usage) AI adoption requires.

---

## How to Run

Each sub-question is independent. From project root:

```bash
venv/Scripts/python -m analysis.questions.job_exposure.exposure_state.run
venv/Scripts/python -m analysis.questions.job_exposure.job_risk_scoring.run
venv/Scripts/python -m analysis.questions.job_exposure.worker_resilience.run
venv/Scripts/python -m analysis.questions.job_exposure.pivot_distance.run
venv/Scripts/python -m analysis.questions.job_exposure.audience_framing.run
venv/Scripts/python -m analysis.questions.job_exposure.occs_of_interest.run
```

`job_risk_scoring` must be run before `worker_resilience`, `pivot_distance`, `audience_framing`, and `occs_of_interest` (they load its risk scores).

---

## Notes

- `run.py` (in this folder root) is the old flat version — **reference only**, broken due to dataset renames.
- Trend analysis for each sub-question uses `ANALYSIS_CONFIG_SERIES` to rank by growth rate in addition to static value.
- SKA computation is real-time — see `analysis/data/compute_ska.py` for the formula.
