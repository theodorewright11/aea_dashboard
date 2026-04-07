*Config: All Confirmed (primary) | Method: Freq | Auto-aug ON | National | GWA level*

At the work-activity level, every platform data source tells the same story: what AI is actually doing at work is dominated by a small cluster of information-processing activities — getting information, documenting things, processing and analyzing data, and providing explanations or guidance. This is consistent enough across our confirmed usage data, ChatGPT session logs, and Copilot enterprise analysis that it shouldn't be treated as platform-specific behavior. It's a feature of where AI is genuinely useful, not an artifact of how any one source was built.

*Full detail: [work_activity_comparison_report.md](work_activity_comparison_report.md)*

## Our GWA Rankings

![Top 15 GWAs by workers affected (all_confirmed)](../questions/field_benchmarks/work_activity_comparison/figures/our_gwa_rankings.png)

Our top GWAs by workers affected are: Documenting/Recording Information (5.9M, 37.3% exposure), Getting Information (4.0M, 55.2%), Performing Administrative Activities (3.8M, 58.7%), and Making Decisions and Solving Problems (3.6M, 52.8%). The high exposure rates on Getting Information and Administrative Activities reflect where AI is most deeply embedded — these are activities where the work genuinely consists of information retrieval and processing, and AI has near-full task coverage.

Handling and Moving Objects appears high (4.7M workers) because it's a large-employment GWA category with moderate exposure from indirect AI involvement in logistics and warehouse coordination. It's the exception in this top-15 — everything else is information work.

## Augmentative vs. Automative

![AEI's 57% augmentative / 43% automative split](../questions/field_benchmarks/work_activity_comparison/figures/augment_vs_automate.png)

AEI (Humlum & Vestergaard, 2024) found that of confirmed AI task-attempts, 57% are augmentative — AI working alongside a human — versus 43% fully automative. This maps well to our framework's treatment of auto-augmentation: we flag tasks where AI extends human judgment separately from tasks where AI is performing end-to-end. The fact that augmentative use is the plurality mode, even in a dataset derived from Claude API logs (a higher-agency context than conversational use), suggests the "AI replaces humans" framing overstates what's actually happening in confirmed usage.

## Platform GWA Alignment

![ChatGPT vs Copilot GWA distributions](../questions/field_benchmarks/work_activity_comparison/figures/platform_gwa_alignment.png)

ChatGPT work sessions and Copilot enterprise sessions agree on the dominant GWA types. Getting Information leads Copilot (~35% of sessions) and is substantial in ChatGPT data as well. Writing/Documenting leads ChatGPT work sessions (40%) and is strong in Copilot. Processing Information (coding, technical work) is material in both. The divergence is mostly framing: Copilot surfaces enterprise workflow tasks (Getting Information dominates because Copilot is often queried mid-task for contextual lookups), while ChatGPT work use skews toward creative and compositional tasks (Writing at 40%).

What's notable about the Copilot analysis is the finding that ~40% of conversations show disjoint user goal IWAs versus AI action IWAs — the user thinks they're doing one thing, the AI does something related but categorically different. This suggests the task-alignment question (is AI covering the right tasks?) is more complex than headline coverage rates imply.

## Convergence with Our Data

Our top GWAs — Documenting, Getting Information, Administrative Activities — match the top GWA categories reported by ChatGPT and Copilot. This convergence across independent sources, different AI platforms, and different measurement approaches is one of the stronger validation signals in the field_benchmarks analysis. It means the high-exposure activities in our data aren't driven by dataset-specific quirks but by genuine patterns in how knowledge workers use AI tools.

## Key numbers

| Source | Top GWA / Activity Type | Value |
|--------|------------------------|-------|
| AEA (all_confirmed) | Documenting/Recording Information | 5.9M workers, 37.3% |
| AEA (all_confirmed) | Getting Information | 4.0M workers, 55.2% |
| ChatGPT work sessions | Writing (→ Documenting) | 40% of work sessions |
| Copilot enterprise | Getting Information | ~35% of sessions |
| AEI (2024) | Technical problem-solving (→ Computer/Math) | ~37% of task-attempts |
| AEI (2024) | Augmentative use | 57% of task-attempts |

## Config

| Setting | Value |
|---------|-------|
| Primary dataset | `AEI Both + Micro 2026-02-12` |
| Method | freq (time-weighted) |
| use_auto_aug | True |
| Geography | National |
| Activity level | GWA |

## Files

| File | Description |
|------|-------------|
| `figures/our_gwa_rankings.png` | Our top 15 GWAs |
| `figures/augment_vs_automate.png` | AEI augment/automate split |
| `figures/platform_gwa_alignment.png` | ChatGPT vs Copilot GWA distributions |
| `results/our_gwa_confirmed.csv` | Our GWA data |
| `results/chatgpt_gwa_distribution.csv` | ChatGPT GWA-mapped data |
| `results/copilot_gwa_distribution.csv` | Copilot user goal GWA data |
| `results/aei_augment_automate.csv` | AEI split |
