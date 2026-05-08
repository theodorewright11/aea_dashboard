"""
run.py — Generate outputs for this question.

Usage from project root:
    venv/Scripts/python -m analysis.questions.<folder_name>.run
"""
from __future__ import annotations

from pathlib import Path

from analysis.config import (
    DEFAULT_OCC_CONFIG,
    make_config,
    run_occ_query,
    ensure_results_dir,
)
from analysis.utils import (
    style_figure,
    save_figure,
    save_csv,
    describe_config,
    generate_pdf,
)

# Directory for this question
HERE = Path(__file__).resolve().parent
# Name of the markdown report file (should match the question title)
REPORT_NAME = "question_title.md"


def main() -> None:
    results = ensure_results_dir(HERE)

    # -- Example: run a computation -----------------------------------------
    #
    # config = make_config(DEFAULT_OCC_CONFIG, geo="nat", agg_level="major")
    # result = run_occ_query(config)
    #
    # if result is None:
    #     print("  No data returned")
    #     return
    #
    # df, group_col = result
    # # df has columns: category, pct_tasks_affected, workers_affected,
    # #                 wages_affected, rank_workers, rank_wages, rank_pct
    #
    # # Save CSV
    # save_csv(df, results / "top_major_categories.csv")
    #
    # # Create and save figure (uses dashboard-matching styling from utils)
    # from analysis.utils import make_horizontal_bar
    # fig = make_horizontal_bar(
    #     df, "category", "workers_affected",
    #     title="Most AI-Exposed Major Occupation Categories",
    #     subtitle=describe_config(config),
    #     x_title="Workers Affected",
    # )
    # save_figure(fig, results / "figures" / "workers_by_major.png")
    #

    # -- Copy key figures to committed figures/ dir -------------------------
    # Figures in results/ are gitignored. Copy the ones referenced in the
    # report markdown to a committed figures/ directory so they render in git.
    #
    # import shutil
    # committed_figs = HERE / "figures"
    # committed_figs.mkdir(exist_ok=True)
    # for fname in ["workers_by_major.png"]:
    #     src = results / "figures" / fname
    #     if src.exists():
    #         shutil.copy2(src, committed_figs / fname)
    #

    # -- Generate PDF -------------------------------------------------------
    # md_path = HERE / REPORT_NAME
    # pdf_path = results / REPORT_NAME.replace(".md", ".pdf")
    # if md_path.exists():
    #     generate_pdf(md_path, pdf_path)
    #     print(f"  Saved {pdf_path.name}")

    print("  Template question — replace this with your analysis code.")


if __name__ == "__main__":
    main()
