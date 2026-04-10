# Trajectory Shapes: How Occupations Grew

*Config: all_confirmed series (AEI Both + Micro, 4 dates Mar 2025 – Feb 2026) | Method: freq | Auto-aug ON | National*

---

More than half of all occupations — 468 of 923 — went basically nowhere over the 11-month window: their confirmed AI exposure moved less than 5 percentage points. The action was concentrated in a 209-occupation "plateaued" group that grew strongly in the first part of the window and then stalled, and a 63-occupation "steady grower" group that grew consistently across the full period. The occupations already at high exposure in March 2025 — Computer and Mathematical, Architecture and Engineering — form the "early mover" group (110 occupations) that started high and added little. The large laggard count reflects that the window now starts after the big pre-2025 growth wave had already happened for many occupations.

---

## The Six Trajectory Types

Each occupation was classified based on how its confirmed exposure changed across 4 dataset snapshots (Mar 2025 to Feb 2026), not just the first-to-last delta. The full classification logic distinguishes starting level, total gain, early-period gain vs. late-period gain, and growth monotonicity.

| Type | Count | Avg Start | Avg End | Avg Gain |
|------|-------|-----------|---------|----------|
| **Laggard** | 468 | 19.5% | 20.4% | +0.8pp |
| **Plateaued** | 209 | 38.1% | 57.4% | +19.3pp |
| **Early Mover** | 110 | 46.8% | 52.3% | +5.5pp |
| **Mixed** | 72 | 22.5% | 29.4% | +6.9pp |
| **Steady** | 63 | 38.5% | 61.8% | +23.3pp |
| **Late Mover** | 1 | 27.1% | 38.1% | +11.0pp |

![Trajectory Type Mix by Sector](../questions/time_trends/trajectory_shapes/figures/trajectory_type_by_sector.png)

The laggard category is the most important for understanding what didn't happen. 468 occupations — 51% of the total — are not occupations where AI made meaningful additional inroads during the measurement window. They're almost entirely in physical, operational, or equipment-dependent work: Transportation and Material Moving, Construction, Production, Installation and Repair. These sectors don't appear because AI systems couldn't score their tasks; they appear because confirmed capability didn't grow there. The large laggard count also reflects a changed window: many occupations that were growing in 2024 had already reached their new plateau by March 2025.

---

## The Plateaued Group

The 209 plateaued occupations are the core of what happened during this window. Starting around 38% confirmed exposure, they grew strongly — mostly in the August 2025 dataset update — and then slowed materially by the end of the window, averaging 57.4% at February 2026.

Why does this group dominate where "steady growers" did before? Because the window now starts in March 2025, after the large pre-window growth wave. Many occupations that showed steady linear growth in the broader pre-window period now look like plateaued growers in this window — their growth was mostly front-loaded into the August 2025 update, and the back half of the window saw much smaller gains.

## The Steady Growers

The 63 steady-grower occupations showed consistent upward movement across both halves of the window (March to August 2025, and August 2025 to February 2026), averaging from 38.5% to 61.8%. These are the occupations where confirmed AI capability was still being incrementally validated across the full window rather than in one concentrated update.

---

## Early Movers: Already There

The 110 early movers — starting at 47% and ending at 52%, a gain of only 5.5pp — were already at high exposure by March 2025 and didn't add much during the window. Computer and Mathematical and Architecture and Engineering occupations dominate this group.

This reflects a shift from the earlier analysis window: more occupations qualify as "early movers" now because the window starts later, after much of the initial growth wave. These are occupations where confirmed AI capability had effectively stabilized before March 2025.

![Trajectory Shape: Starting Level vs Total Growth](../questions/time_trends/trajectory_shapes/figures/trajectory_scatter.png)

---

## Late Movers: The Exception

Only 1 occupation fits the late-mover profile in this window: starting below 28% at the midpoint (Aug 2025) and then gaining 10+ percentage points in the second half. The near-zero count suggests that truly new AI footholds — rather than continued growth in already-exposed work — were essentially absent in this period. This is consistent with the pattern from the other analyses: AI expansion during this window was primarily deepening coverage of already-exposed domains, not opening new ones.

---

## What Trajectory Tells You

The sector-by-sector trajectory mix reveals where the AI transition is in different parts of the economy.

Sectors with mostly laggards (Transportation, Construction, Production, Installation/Repair) are in a genuine pause. Confirmed AI capability hasn't been expanding there.

Sectors dominated by plateaued occupations saw strong growth concentrated in the August 2025 update and then slowed. These sectors had the most active expansion in this window but are showing early signs of slowing.

Sectors with early movers (Computer/Math, Architecture/Engineering) reflect occupations where confirmed AI capability had already stabilized before the window started — they're at a new high-exposure equilibrium.

The key difference from the earlier analysis window: the March 2025 start captures a fundamentally different moment. Many occupations that looked like "steady growers" in the Sep 2024–Feb 2026 window now look like early movers or plateaued occupations here — their growth was front-loaded before the window opens.

![Example Occupation Trajectories](../questions/time_trends/trajectory_shapes/figures/trajectory_example_lines.png)

---

## Config

Dataset: `AEI Both + Micro` series (4 dates: 2025-03-06, 2025-08-11, 2025-11-13, 2026-02-12) | Method: freq | Auto-aug ON | National | Occupation level

## Files

| File | Description |
|------|-------------|
| `results/trajectory_classifications.csv` | All 923 occupations with trajectory type, start/end/gain values, major sector |
| `results/trajectory_summary.csv` | Count, avg start, avg end, avg gain per trajectory type |
| `results/sector_trajectory_matrix.csv` | Count of each trajectory type per major sector |
| `figures/trajectory_type_by_sector.png` | Stacked bar: trajectory mix per sector (committed) |
| `figures/trajectory_scatter.png` | Scatter: total gain vs starting level, colored by type (committed) |
| `figures/trajectory_example_lines.png` | Line chart: example occupations per trajectory type (committed) |
