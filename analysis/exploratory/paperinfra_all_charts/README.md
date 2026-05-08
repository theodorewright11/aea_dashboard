# paperinfra_all_charts

Mirrors every committed figure from `analysis/paper/results/part_{1,2,3}/figures/` into one place, with `all_paper_charts.md` listing each one (no prose). Folder is carved out of the global `exploratory/` gitignore (see `.gitignore` exception) so it surfaces on GitHub.

## Run

```
venv/Scripts/python -m analysis.exploratory.paperinfra_all_charts.run
```

The script copies the current state of all three paper-part `figures/` dirs into `figures/part_{1,2,3}/`. Re-run after any paper figure update to keep this mirror in sync.

## Files

- `all_paper_charts.md` — chart-only listing
- `figures/part_1/`, `figures/part_2/`, `figures/part_3/` — copied PNGs
- `run.py` — sync script
