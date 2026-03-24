# CLAUDE.md — Agent Instructions

Rules and patterns for any Claude Code session working on this project.

---

## Before You Start

- Read `PRD.md` to understand what the product does and who it's for.
- Read `ARCHITECTURE.md` to understand how the system is built.
- If your task touches computation logic, read the relevant sections of ARCHITECTURE.md and PRD.md carefully before writing code.
- If your task adds or removes a user-facing feature, check PRD.md to understand how it fits.
- This rule if very important: if a delta prompt is ambiguous about where a feature should live (which component, which endpoint, etc.) or how it should interact with existing features, or what it is that it's wanting you to implement, ask before implementing. Do not guess on things.

---

## After Every Change

- If you changed anything with the implementation of the dashboard (such as computation logic, API contracts, module boundaries, data flow, or added/removed cached functions, etc.): update ARCHITECTURE.md.
- If you added, removed, or changed a user-facing feature, page, control, or metric: update PRD.md. Make sure to tell me (the prompter) what you changed in PRD.md. 
- If you added a new pitfall or gotcha discovered during implementation: add it to the Common Pitfalls section of ARCHITECTURE.md.
- Write or update tests for any code you changed. If no test file exists for the module, create one.

---

## Code Quality Rules

### TypeScript (Frontend)
- Use strict TypeScript types for all props, state, and function signatures. No `any` except where explicitly suppressed with a comment explaining why.
- Define interfaces for all component props.
- Use type guards rather than type assertions where possible.

### Python (Backend)
- Use type hints on all function signatures (parameters and return types).
- Write defensive asserts at the entry points of compute functions — validate that expected columns exist, DataFrames are not empty, and critical values are not NaN before proceeding.
- Use `Optional[T]` and handle None cases explicitly rather than letting NaN propagate silently.

### General
- Keep functions focused — if a function is doing multiple unrelated things, split it.
- When adding a new endpoint, add it to the API contracts section of ARCHITECTURE.md.
- When adding a new frontend component, document its props and responsibilities in ARCHITECTURE.md.
- Prefer small, targeted edits over full file rewrites. If you need to change one function, change that function — don't rewrite the file.



## Guardrails

These are some common ways this codebase breaks. Check these when your change touches the relevant area:

- Computation: pct_tasks_affected must be ratio-of-totals, never average-of-percentages. If you're unsure, read ARCHITECTURE.md section 4.
- AEI: never bypass the crosswalk pipeline. If you're touching AEI data flow, read the AEI crosswalk section in ARCHITECTURE.md.
- Explorer table metrics (auto_aug, pct_norm variants): computed from unique task_norms pooled across the group, never averaged from per-occupation values.
- Chart page metrics (workers_affected, wages_affected): computed per-occupation then summed to group level. pct_tasks_affected is ratio-of-totals at whatever level it's computed.
- New cached functions: cache key must include every parameter that changes the output.
- Tables: max ~100 rendered rows. Use rowLimit pattern.
- Text inputs in useMemo deps: must be debounced first.