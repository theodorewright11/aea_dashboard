/**
 * JS color constants matching the CSS custom properties in globals.css.
 *
 * These exist because chart libraries like Plotly operate on raw data props
 * (e.g. `marker.color`) and cannot resolve CSS custom properties at runtime.
 *
 * When changing group colors:
 *   1. Update --group-a / --group-b in globals.css
 *   2. Update GROUP_A_COLOR / GROUP_B_COLOR below to match
 *
 * In Phase 2 (Recharts migration), these constants can be removed since
 * Recharts renders into the DOM where CSS variables resolve naturally.
 */
export const GROUP_A_COLOR = "#3a5f83";
export const GROUP_B_COLOR = "#4a7c6f";
