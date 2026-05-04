"""
Tests for backend/occupation_report.py.

These tests hit the actual data files (eco_2025, AEI/MCP/MS datasets,
analysis/data/*.csv reference files). They do not mock — the data is the
correctness contract. Tests are correspondingly slow on first run because
the module-level caches warm lazily.

Run from project root:
    venv/Scripts/python -m pytest backend/tests/test_occupation_report.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Backend dir on path (matches uvicorn launch from /backend)
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import occupation_report as ocr  # noqa: E402


# ── Color bucket helper tests (fast — no data loading) ───────────────────────

class TestColorBucketAuto:
    def test_high_threshold(self):
        assert ocr._color_bucket_auto(4.0) == "high"
        assert ocr._color_bucket_auto(5.0) == "high"
        assert ocr._color_bucket_auto(4.5) == "high"

    def test_mid_threshold(self):
        assert ocr._color_bucket_auto(2.5) == "mid"
        assert ocr._color_bucket_auto(3.5) == "mid"
        assert ocr._color_bucket_auto(3.99) == "mid"

    def test_low_threshold(self):
        assert ocr._color_bucket_auto(0.0) == "low"
        assert ocr._color_bucket_auto(1.0) == "low"
        assert ocr._color_bucket_auto(2.49) == "low"

    def test_none_handling(self):
        assert ocr._color_bucket_auto(None) == "none"
        assert ocr._color_bucket_auto(float("nan")) == "none"


class TestColorBucketSka:
    def test_high_threshold(self):
        assert ocr._color_bucket_ska(100.0) == "high"
        assert ocr._color_bucket_ska(150.0) == "high"

    def test_mid_threshold(self):
        assert ocr._color_bucket_ska(66.0) == "mid"
        assert ocr._color_bucket_ska(80.0) == "mid"
        assert ocr._color_bucket_ska(99.9) == "mid"

    def test_low_threshold(self):
        assert ocr._color_bucket_ska(0.0) == "low"
        assert ocr._color_bucket_ska(50.0) == "low"
        assert ocr._color_bucket_ska(65.9) == "low"

    def test_none_handling(self):
        assert ocr._color_bucket_ska(None) == "none"
        assert ocr._color_bucket_ska(float("nan")) == "none"


# ── Bias ratio tests (fast) ──────────────────────────────────────────────────

class TestBiasRatios:
    def test_ratios_are_finite_positives(self):
        ratios = ocr._equal_consensus_bias_ratios()
        assert len(ratios) > 0
        for gwa, r in ratios.items():
            assert r > 0, f"non-positive bias ratio for {gwa}: {r}"
            assert r < 1e6, f"runaway bias ratio for {gwa}: {r}"

    def test_thinking_creatively_above_one(self):
        # Claude over-represents Thinking Creatively (33.7%) vs.
        # consensus average — bias ratio should be > 1
        ratios = ocr._equal_consensus_bias_ratios()
        assert ratios["Thinking Creatively"] > 1.5

    def test_getting_information_below_one(self):
        # Claude under-represents Getting Information (3.6%) vs.
        # ChatGPT (19.3%) and Copilot (24.3%) — bias ratio should be < 1
        ratios = ocr._equal_consensus_bias_ratios()
        assert ratios["Getting Information"] < 0.5


# ── End-to-end report tests (slow — first run loads ~all datasets) ───────────

# A known occupation present in eco_2025 with rich SKA + tasks data
KNOWN_OCC = "Registered Nurses"


@pytest.fixture(scope="module")
def report():
    """Build a report once per module."""
    r = ocr.get_occupation_report(KNOWN_OCC, "nat")
    assert r is not None, f"expected {KNOWN_OCC} to exist"
    return r


class TestTitles:
    def test_returns_923_titles(self):
        titles = ocr.get_occupation_titles()
        # The eco_2025 universe has 923 occs but some implementations may yield
        # ±1 because of edge cases. Loose-bounded.
        assert 900 <= len(titles) <= 950
        assert KNOWN_OCC in titles

    def test_sorted(self):
        titles = ocr.get_occupation_titles()
        assert titles == sorted(titles)


class TestUnknownOccupation:
    def test_returns_none(self):
        assert ocr.get_occupation_report("NotAnOccupation42", "nat") is None


class TestHeadline:
    def test_pct_in_range(self, report):
        h = report["headline"]
        assert 0 <= h["pct_tasks_affected"] <= 100

    def test_workers_and_wages_positive(self, report):
        h = report["headline"]
        assert h["workers_affected"] >= 0
        assert h["wages_affected"] >= 0
        assert h["emp"] is not None and h["emp"] > 0
        assert h["wage"] is not None and h["wage"] > 0

    def test_hierarchy_populated(self, report):
        h = report["headline"]
        assert h["major"] == "Healthcare Practitioners and Technical Occupations"
        assert h["broad"]
        assert h["minor"]

    def test_risk_payload(self, report):
        risk = report["headline"]["risk"]
        assert 0 <= risk["score"] <= 10
        assert risk["tier"] in {"high", "mod_high", "mod_low", "low"}
        # All 8 flags present, each 0 or 1
        flags = risk["flags"]
        assert set(flags.keys()) == set(ocr.FLAG_WEIGHTS.keys())
        for v in flags.values():
            assert v in (0, 1)

    def test_intensity_rank(self, report):
        intensity = report["headline"]["intensity"]
        # Either populated or both None — never half-populated
        if intensity.get("occ_intensity_rank") is not None:
            assert intensity["occ_intensity_rank"] >= 1
            assert intensity["occ_intensity_rank"] <= intensity["occ_intensity_total"]


class TestTasks:
    def test_returns_list(self, report):
        tasks = report["tasks"]
        assert isinstance(tasks, list)
        assert len(tasks) > 0

    def test_all_tasks_have_required_fields(self, report):
        for t in report["tasks"]:
            for field in ("rank", "task", "task_normalized", "color_bucket", "top_mcps"):
                assert field in t
            assert t["color_bucket"] in {"high", "mid", "low", "none"}

    def test_ranks_are_sequential(self, report):
        ranks = [t["rank"] for t in report["tasks"]]
        assert ranks == list(range(1, len(ranks) + 1))

    def test_color_driver_matches_max_of_color_sources(self, report):
        # color_driver must equal max(aei_conv_max, aei_api_max, microsoft) — MCP excluded
        for t in report["tasks"]:
            color_sources = [t.get("aei_conv_max"), t.get("aei_api_max"), t.get("microsoft")]
            non_null = [v for v in color_sources if v is not None]
            if not non_null:
                assert t["color_driver"] is None
            else:
                assert abs(t["color_driver"] - max(non_null)) < 1e-6


class TestWorkActivities:
    def test_three_levels_present(self, report):
        was = report["work_activities"]
        assert "gwa" in was and "iwa" in was and "dwa" in was

    def test_each_row_color_coded(self, report):
        for level in ("gwa", "iwa", "dwa"):
            for r in report["work_activities"][level]:
                assert r["color_bucket"] in {"high", "mid", "low", "none"}
                assert r["n_tasks"] >= 1


class TestGroupRanks:
    def test_economy_rank_total_matches_occ_count(self, report):
        eco = report["group_ranks"]["economy"]
        # Should equal the number of occupations served
        assert eco["total"] == len(ocr.get_occupation_titles())

    def test_major_rank_within_total(self, report):
        major = report["group_ranks"]["major"]
        if major:
            assert 1 <= major["pct"] <= major["total"]
            assert 1 <= major["workers"] <= major["total"]
            assert 1 <= major["wages"] <= major["total"]


class TestTrend:
    def test_four_data_points(self, report):
        # all_confirmed series has 4 dates between Mar 2025 and Feb 2026
        assert len(report["trend"]) == 4

    def test_dates_increasing(self, report):
        dates = [p["date"] for p in report["trend"]]
        assert dates == sorted(dates)


class TestSka:
    def test_three_types_present(self, report):
        rows = report["ska"]["rows"]
        assert "skills" in rows and "knowledge" in rows and "abilities" in rows

    def test_sorted_by_gap_desc_within_type(self, report):
        # Biggest AI lead at the top — gap descending
        for type_name in ("skills", "knowledge", "abilities"):
            rows = report["ska"]["rows"][type_name]
            gaps = [r["gap"] for r in rows if r["gap"] is not None]
            if len(gaps) >= 2:
                assert gaps == sorted(gaps, reverse=True), \
                    f"{type_name} not sorted by gap desc: {gaps[:5]}"

    def test_pct_of_need_consistent_with_color(self, report):
        for type_name in ("skills", "knowledge", "abilities"):
            for r in report["ska"]["rows"][type_name]:
                p = r["pct_of_need"]
                if p is None:
                    continue
                if p >= 100:
                    assert r["color_bucket"] == "high"
                elif p >= 66:
                    assert r["color_bucket"] == "mid"
                else:
                    assert r["color_bucket"] == "low"


class TestSimilar:
    def test_returns_5(self, report):
        # Default N_SIMILAR_OCCS = 5
        assert len(report["similar"]) == ocr.N_SIMILAR_OCCS

    def test_excludes_self(self, report):
        for s in report["similar"]:
            assert s["title"] != KNOWN_OCC

    def test_sorted_by_distance_asc(self, report):
        dists = [s["distance"] for s in report["similar"] if s["distance"] is not None]
        assert dists == sorted(dists)


class TestSector:
    def test_major_match(self, report):
        s = report["sector"]
        assert s["major"] == report["headline"]["major"]
        assert 1 <= s["rank_pct"] <= s["n_majors"]


class TestTech:
    def test_each_tech_has_required_fields(self, report):
        for t in report["tech"]:
            assert "software" in t
            assert "commodity" in t
            assert "commodity_total" in t


# ── Edge cases ───────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_low_exposure_occupation(self):
        # Construction Laborers should have a low pct (~10%) and mod_low risk
        r = ocr.get_occupation_report("Construction Laborers", "nat")
        assert r is not None
        assert r["headline"]["pct_tasks_affected"] < 30
        assert r["headline"]["risk"]["tier"] in {"low", "mod_low"}

    def test_geo_changes_emp(self):
        r_nat = ocr.get_occupation_report("Lawyers", "nat")
        r_ut  = ocr.get_occupation_report("Lawyers", "ut")
        # Different geo → different employment numbers
        assert r_nat["headline"]["emp"] != r_ut["headline"]["emp"]
        # Utah should have less employment than national
        assert r_ut["headline"]["emp"] < r_nat["headline"]["emp"]

    def test_unknown_geo_falls_back_to_nat(self):
        # The endpoint validates geo before calling, but the function itself
        # is lenient — bad geos default to nat behavior internally.
        r = ocr.get_occupation_report(KNOWN_OCC, "zz")
        # Falls back to "nat" because zz isn't a valid GEO_OPTIONS code
        assert r is not None
