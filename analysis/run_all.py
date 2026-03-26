"""
run_all.py — Regenerate all analysis question outputs.

Usage from project root:
    venv/Scripts/python -m analysis.run_all
"""
from __future__ import annotations

import importlib
import sys
import time
from pathlib import Path

from analysis.config import QUESTIONS_DIR


def discover_questions() -> list[str]:
    """Find all question folders that have a run.py module."""
    questions = []
    for d in sorted(QUESTIONS_DIR.iterdir()):
        if d.is_dir() and not d.name.startswith("_") and (d / "run.py").exists():
            questions.append(d.name)
    return questions


def run_question(name: str) -> bool:
    """Run a single question's run.py and return True if successful."""
    module_name = f"analysis.questions.{name}.run"
    print(f"\n{'='*60}")
    print(f"  Running: {name}")
    print(f"{'='*60}")
    try:
        mod = importlib.import_module(module_name)
        if hasattr(mod, "main"):
            mod.main()
        else:
            print(f"  WARNING: {module_name} has no main() function, skipping")
            return False
        return True
    except Exception as e:
        print(f"  ERROR in {name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main() -> None:
    questions = discover_questions()
    if not questions:
        print("No question folders found with run.py modules.")
        print(f"  Looked in: {QUESTIONS_DIR}")
        print("  Copy _template/ to a new folder and add a run.py with a main() function.")
        return

    print(f"Found {len(questions)} question(s): {', '.join(questions)}")

    results: dict[str, bool] = {}
    t0 = time.time()

    for name in questions:
        t1 = time.time()
        results[name] = run_question(name)
        elapsed = time.time() - t1
        status = "OK" if results[name] else "FAILED"
        print(f"  [{status}] {name} ({elapsed:.1f}s)")

    total = time.time() - t0
    passed = sum(1 for v in results.values() if v)
    failed = len(results) - passed

    print(f"\n{'='*60}")
    print(f"  Done: {passed} passed, {failed} failed, {total:.1f}s total")
    print(f"{'='*60}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
