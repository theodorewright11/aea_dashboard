# Workforce Meeting v2

**Purpose:** V2 of the workforce meeting presentation charts. Charts only — no narrative text. 11 slides optimised for a non-technical audience (business and education leaders).

**Changes from v1:**
- Charts only (no narrative text in report)
- Dropped: headline stacked bar (01), auto-aug by sector (09), reskilling cost (10)
- Larger fonts throughout (titles 26px, axis 15px, inside bar annotations 20px)
- Primary values as large white text inside each bar
- No config subheadings on any chart
- X-axis scale visible on all charts
- "%" instead of "pp" for percentage deltas
- Chart 07: overlaid bars showing conversational vs. agentic AI reach side-by-side
- SKA reference line explicitly labelled "100% = avg job need in this skill"

**Config:** All Confirmed (AEI Both + Micro 2026-02-12) | Freq | Auto-aug ON | Utah  
**Trend window:** First → last date of all_confirmed series  
**Adoption gap:** all_confirmed vs all_ceiling (both Utah)  
**Agentic:** human_conversation vs agentic_confirmed (both Utah)  
**SKA:** national scope (geo-invariant)

**Charts:**

| File | What it shows |
|------|--------------|
| `01_sector_scope` | Top 7 Utah sectors by workers with AI-exposed tasks |
| `02_gwa_scope` | Top 7 work activity types by % tasks affected |
| `03_sector_trend` | Fastest-growing Utah sectors (Δ workers) |
| `04_gwa_trend` | Fastest-growing work types (Δ % tasks) |
| `05_sector_adoption_gap` | Where AI could still expand: sector worker gap |
| `06_gwa_adoption_gap` | Where AI could still expand: work activity gap |
| `07_human_vs_agentic` | Conversational vs. agentic AI reach by sector |
| `08_ska_human_skills` | Skills where humans still outperform AI |
| `09_ska_human_knowledge` | Knowledge domains where humans still outperform AI |
| `10_ska_ai_skills` | Skills where AI has surpassed average job requirements |
| `11_ska_ai_knowledge` | Knowledge domains where AI has surpassed average job requirements |

**Run:**
```
venv/Scripts/python -m analysis.questions.workforce_meeting_v2.run
```
