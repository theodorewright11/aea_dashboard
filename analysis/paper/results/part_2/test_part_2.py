"""Unit tests for the new Part 2 compute paths.

Covers the three pure-function helpers added during the Part 2 rebuild:
- compute_variant_a (naive non-physical task share, ratio of totals)
- compute_variant_a_gwa (same, scoped to GWA task pool)
- _linear_project (OLS slope + projection used by both Part 1 and 2)
- _phys_tier (boundary semantics for the SKA color buckets)
- _load_occ_phys_map (per-occupation pct_physical lookup)
- _coerce_phys_bool (matches backend.compute._phys_bool semantics)

These tests hit `data/final_eco_2025.csv` for the integration-style
assertions but pin to row counts / specific majors that are stable
across data refreshes.

Run from project root:
    venv/Scripts/python -m pytest analysis/paper/results/part_2/test_part_2.py -v
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from analysis.paper.results.part_2.run import (
    _coerce_phys_bool,
    _linear_project,
    _phys_tier,
    _load_occ_phys_map,
    compute_variant_a,
    compute_variant_a_gwa,
    PHYS_LOWER,
    PHYS_UPPER,
)


# ── _coerce_phys_bool ────────────────────────────────────────────────────

class TestCoercePhysBool:
    def test_true_values(self):
        assert _coerce_phys_bool(True) is True
        assert _coerce_phys_bool(1) is True
        assert _coerce_phys_bool("True") is True
        assert _coerce_phys_bool("true") is True
        assert _coerce_phys_bool("1") is True
        assert _coerce_phys_bool("yes") is True

    def test_false_values(self):
        assert _coerce_phys_bool(False) is False
        assert _coerce_phys_bool(0) is False
        assert _coerce_phys_bool("False") is False
        assert _coerce_phys_bool("0") is False
        assert _coerce_phys_bool("no") is False

    def test_nan_treated_as_false(self):
        assert _coerce_phys_bool(float("nan")) is False
        assert _coerce_phys_bool(None) is False


# ── _phys_tier ──────────────────────────────────────────────────────────

class TestPhysTier:
    def test_boundaries(self):
        # PHYS_LOWER / PHYS_UPPER bound the Mixed bucket inclusively at
        # the lower edge and exclusively at the upper edge.
        assert _phys_tier(0.0) == "Non-physical"
        assert _phys_tier(PHYS_LOWER - 0.01) == "Non-physical"
        assert _phys_tier(PHYS_LOWER) == "Mixed"
        assert _phys_tier(50.0) == "Mixed"
        assert _phys_tier(PHYS_UPPER) == "Mixed"
        assert _phys_tier(PHYS_UPPER + 0.01) == "Physical"
        assert _phys_tier(100.0) == "Physical"


# ── _linear_project ─────────────────────────────────────────────────────

class TestLinearProject:
    def test_perfect_line(self):
        # y = 10 + 0.1 t. Project 100 days past last → 10 + 0.1*(200) = 30
        dates = [pd.Timestamp("2025-01-01") + pd.Timedelta(days=i*10) for i in range(11)]
        yvals = [10.0 + 0.1 * (i * 10) for i in range(11)]
        slope_per_day, projected, r2 = _linear_project(dates, yvals, horizon_days=100)
        assert slope_per_day == pytest.approx(0.1, abs=1e-9)
        assert projected == pytest.approx(30.0, abs=1e-6)
        assert r2 == pytest.approx(1.0, abs=1e-9)

    def test_flat_line(self):
        dates = [pd.Timestamp("2025-01-01") + pd.Timedelta(days=i*30) for i in range(4)]
        yvals = [25.0, 25.0, 25.0, 25.0]
        slope_per_day, projected, r2 = _linear_project(dates, yvals, horizon_days=365)
        assert slope_per_day == pytest.approx(0.0, abs=1e-9)
        assert projected == pytest.approx(25.0, abs=1e-9)
        # ss_tot == 0 → degenerate R²; the helper returns 1.0 as a sentinel.
        assert r2 == pytest.approx(1.0, abs=1e-9)

    def test_single_point_returns_last_value(self):
        slope_per_day, projected, r2 = _linear_project(
            [pd.Timestamp("2025-01-01")], [42.0], horizon_days=730
        )
        assert slope_per_day == 0.0
        assert projected == 42.0
        assert r2 == 0.0


# ── compute_variant_a ───────────────────────────────────────────────────

class TestComputeVariantA:
    @pytest.fixture(scope="module")
    def variant_a_major(self):
        return compute_variant_a("major")

    def test_major_returns_all_22_majors(self, variant_a_major):
        # 22 SOC major categories ship with eco_2025
        assert len(variant_a_major) == 22

    def test_major_values_bounded_0_100(self, variant_a_major):
        assert variant_a_major["pct_tasks_affected"].min() >= 0.0
        assert variant_a_major["pct_tasks_affected"].max() <= 100.0

    def test_computer_math_is_high(self, variant_a_major):
        # Computer/Math is essentially all-cognitive → near-100 variant A
        cm = variant_a_major[
            variant_a_major["category"] == "Computer and Mathematical Occupations"
        ]
        assert not cm.empty
        assert float(cm["pct_tasks_affected"].iloc[0]) > 90.0

    def test_construction_is_low(self, variant_a_major):
        # Construction/Extraction is heavily physical → low variant A
        co = variant_a_major[
            variant_a_major["category"] == "Construction and Extraction Occupations"
        ]
        assert not co.empty
        assert float(co["pct_tasks_affected"].iloc[0]) < 30.0

    def test_columns(self, variant_a_major):
        assert set(variant_a_major.columns) == {"category", "pct_tasks_affected"}

    def test_occupation_level_count(self):
        df = compute_variant_a("occupation")
        # Eco_2025 has 923 occupations
        assert len(df) == 923


# ── compute_variant_a_gwa ───────────────────────────────────────────────

class TestComputeVariantAGwa:
    def test_returns_non_empty(self):
        df = compute_variant_a_gwa()
        assert len(df) > 0

    def test_values_bounded(self):
        df = compute_variant_a_gwa()
        assert df["pct_tasks_affected"].min() >= 0.0
        assert df["pct_tasks_affected"].max() <= 100.0


# ── _load_occ_phys_map ──────────────────────────────────────────────────

class TestLoadOccPhysMap:
    @pytest.fixture(scope="module")
    def phys_map(self):
        return _load_occ_phys_map()

    def test_has_all_occupations(self, phys_map):
        assert len(phys_map) == 923

    def test_values_bounded(self, phys_map):
        assert phys_map.min() >= 0.0
        assert phys_map.max() <= 100.0

    def test_cognitive_occ_is_low(self, phys_map):
        # Software Developers should have ~0% physical
        idx_match = phys_map.index.str.contains("Software Developer", case=False, na=False)
        candidates = phys_map[idx_match]
        assert len(candidates) >= 1
        assert candidates.iloc[0] < 20.0

    def test_physical_occ_is_high(self, phys_map):
        # Carpenters / construction labourers should be heavily physical
        idx_match = phys_map.index.str.contains("Carpenters", case=False, na=False)
        candidates = phys_map[idx_match]
        assert len(candidates) >= 1
        assert candidates.iloc[0] > 50.0
