"""
compute.py — Core compute engine, adapted from dashboard/live_compute.py.
All @st.cache_data decorators replaced with a simple in-process dict cache.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional

from config import ECO_BASELINE_FILE, CROSSWALK_PATHS, AGG_LEVEL_COL, DATASETS, SORT_COL_MAP

# ── Simple in-process cache (module-level dicts) ──────────────────────────────
_crosswalk_cache: Optional[pd.DataFrame] = None
_eco_raw_cache:   Optional[pd.DataFrame] = None
_eco_baseline_cache: dict = {}
_dataset_cache:      dict = {}


def _find_crosswalk() -> Optional[Path]:
    for p in CROSSWALK_PATHS:
        if Path(p).exists():
            return Path(p)
    return None


def crosswalk_available() -> bool:
    return _find_crosswalk() is not None


def load_crosswalk() -> Optional[pd.DataFrame]:
    global _crosswalk_cache
    if _crosswalk_cache is None:
        path = _find_crosswalk()
        if path is None:
            return None
        _crosswalk_cache = pd.read_csv(path)
    return _crosswalk_cache


def load_eco_raw() -> Optional[pd.DataFrame]:
    global _eco_raw_cache
    if _eco_raw_cache is None:
        if not Path(ECO_BASELINE_FILE).exists():
            return None
        _eco_raw_cache = pd.read_csv(ECO_BASELINE_FILE)
    return _eco_raw_cache


def dataset_exists(name: str) -> bool:
    meta = DATASETS.get(name)
    if meta is None:
        return False
    return Path(meta["file"]).exists()


# ── Task-level transformations ─────────────────────────────────────────────────

def apply_physical_filter(df: pd.DataFrame, physical_mode: str) -> pd.DataFrame:
    if "physical" not in df.columns or physical_mode == "all":
        return df
    if physical_mode == "exclude":
        return df[df["physical"] != True].copy()
    if physical_mode == "only":
        return df[df["physical"] == True].copy()
    return df


def compute_task_comp(
    df: pd.DataFrame,
    method: str,
    use_auto_aug: bool,
    use_adj_mean: bool,
) -> pd.Series:
    if method == "freq":
        tc = df["freq_mean"].copy().fillna(0.0)
    else:
        tc = df["relevance"].fillna(0.0) * (2.0 ** df["importance"].fillna(0.0))

    if use_auto_aug:
        if use_adj_mean and "auto_aug_mean_adj" in df.columns:
            aug = df["auto_aug_mean_adj"].fillna(0.0)
        elif "auto_aug_mean" in df.columns:
            aug = df["auto_aug_mean"].fillna(0.0)
        else:
            aug = pd.Series(1.0, index=df.index)
        tc = tc * (aug / 5.0)

    return tc


def dedup_and_compute(
    df: pd.DataFrame,
    title_col: str,
    emp_col: str,
    wage_col: str,
    method: str,
    use_auto_aug: bool,
    use_adj_mean: bool,
) -> pd.DataFrame:
    keep = [
        emp_col, wage_col,
        "broad_occ", "minor_occ_category", "major_occ_category",
        "freq_mean", "importance", "relevance", "auto_aug_mean",
    ]
    if "auto_aug_mean_adj" in df.columns:
        keep.append("auto_aug_mean_adj")

    agg_dict = {c: "first" for c in keep if c in df.columns}
    deduped = (
        df.groupby([title_col, "task_normalized"], sort=False)
        .agg(agg_dict)
        .reset_index()
    )
    deduped["task_comp"] = compute_task_comp(deduped, method, use_auto_aug, use_adj_mean)
    return deduped


# ── ECO Baseline ───────────────────────────────────────────────────────────────

def load_eco_baseline(method: str, physical_mode: str, geo: str) -> Optional[pd.DataFrame]:
    key = (method, physical_mode, geo)
    if key in _eco_baseline_cache:
        return _eco_baseline_cache[key]

    eco = load_eco_raw()
    if eco is None:
        return None
    eco = apply_physical_filter(eco, physical_mode)
    if eco.empty:
        return None

    emp_col  = f"emp_tot_{geo}_2024"
    wage_col = f"a_med_{geo}_2024"
    result = dedup_and_compute(eco, "title_current", emp_col, wage_col, method, False, False)
    _eco_baseline_cache[key] = result
    return result


# ── Aggregation ────────────────────────────────────────────────────────────────

def aggregate_results(
    ai_df:     pd.DataFrame,
    eco_df:    pd.DataFrame,
    title_col: str,
    agg_level: str,
    emp_col:   str,
    wage_col:  str,
) -> pd.DataFrame:
    group_col = AGG_LEVEL_COL[agg_level]

    ai_by_occ = (
        ai_df.groupby(title_col)["task_comp"]
        .sum()
        .reset_index()
        .rename(columns={"task_comp": "ai_task_comp"})
    )

    eco_agg: dict = {"eco_task_comp": ("task_comp", "sum")}
    for c in [emp_col, wage_col, "broad_occ", "minor_occ_category", "major_occ_category"]:
        if c in eco_df.columns:
            eco_agg[c] = (c, "first")

    eco_by_occ = eco_df.groupby("title_current").agg(**eco_agg).reset_index()

    occ = eco_by_occ.merge(
        ai_by_occ, left_on="title_current", right_on=title_col, how="left"
    )
    if title_col != "title_current" and title_col in occ.columns:
        occ.drop(columns=[title_col], inplace=True)

    occ["ai_task_comp"] = occ["ai_task_comp"].fillna(0.0)
    occ["pct_tasks_affected"] = (
        (occ["ai_task_comp"] / occ["eco_task_comp"].replace(0, np.nan)) * 100
    ).fillna(0.0).clip(upper=100.0)

    if emp_col in occ.columns:
        occ["workers_affected"] = occ["pct_tasks_affected"] / 100.0 * occ[emp_col]
        if wage_col in occ.columns:
            occ["wages_affected"] = (
                occ["pct_tasks_affected"] / 100.0 * occ[emp_col] * occ[wage_col]
            )
        else:
            occ["wages_affected"] = np.nan
    else:
        occ["workers_affected"] = np.nan
        occ["wages_affected"]   = np.nan

    if agg_level == "occupation":
        return occ[["title_current", "pct_tasks_affected",
                    "workers_affected", "wages_affected"]].copy()

    ai_by_group = (
        ai_df.groupby(group_col)["task_comp"]
        .sum().reset_index()
        .rename(columns={"task_comp": "ai_task_comp_group"})
    )
    eco_by_group = (
        eco_df.groupby(group_col)["task_comp"]
        .sum().reset_index()
        .rename(columns={"task_comp": "eco_task_comp_group"})
    )

    grp = eco_by_group.merge(ai_by_group, on=group_col, how="left")
    grp["ai_task_comp_group"] = grp["ai_task_comp_group"].fillna(0.0)
    grp["pct_tasks_affected"] = (
        (grp["ai_task_comp_group"] / grp["eco_task_comp_group"].replace(0, np.nan)) * 100
    ).fillna(0.0).clip(upper=100.0)

    if group_col in occ.columns:
        occ_by_group = (
            occ.groupby(group_col)
            .agg(workers_affected=("workers_affected", "sum"),
                 wages_affected=("wages_affected", "sum"))
            .reset_index()
        )
        grp = grp.merge(occ_by_group, on=group_col, how="left")
    else:
        grp["workers_affected"] = np.nan
        grp["wages_affected"]   = np.nan

    return grp[[group_col, "pct_tasks_affected", "workers_affected", "wages_affected"]].copy()


# ── Single-dataset compute ─────────────────────────────────────────────────────

def compute_single_dataset(
    file_path:     str,
    is_aei:        bool,
    method:        str,
    use_auto_aug:  bool,
    use_adj_mean:  bool,
    physical_mode: str,
    geo:           str,
    agg_level:     str,
) -> Optional[pd.DataFrame]:
    key = (file_path, is_aei, method, use_auto_aug, use_adj_mean, physical_mode, geo, agg_level)
    if key in _dataset_cache:
        return _dataset_cache[key]

    if not Path(file_path).exists():
        return None

    eco_deduped = load_eco_baseline(method, physical_mode, geo)
    if eco_deduped is None or eco_deduped.empty:
        return None

    df = pd.read_csv(file_path)
    df = apply_physical_filter(df, physical_mode)
    if df.empty:
        return None

    emp_col  = f"emp_tot_{geo}_2024"
    wage_col = f"a_med_{geo}_2024"

    if is_aei:
        crosswalk = load_crosswalk()
        if crosswalk is None:
            return None

        ai_deduped = dedup_and_compute(
            df, "title", emp_col, wage_col, method, use_auto_aug, use_adj_mean
        )

        soc_lookup = df[["title", "soc_code_2010"]].drop_duplicates("title")
        ai_deduped = ai_deduped.merge(soc_lookup, on="title", how="left")

        ai_deduped = ai_deduped.merge(
            crosswalk[["O*NET-SOC 2010 Code", "O*NET-SOC 2019 Title"]],
            left_on="soc_code_2010", right_on="O*NET-SOC 2010 Code",
            how="left",
        )

        split_counts = (
            crosswalk.groupby("O*NET-SOC 2010 Code")["O*NET-SOC 2019 Title"]
            .nunique()
            .reset_index(name="split_count")
        )
        ai_deduped = ai_deduped.merge(
            split_counts,
            left_on="soc_code_2010", right_on="O*NET-SOC 2010 Code",
            how="left", suffixes=("", "_sc"),
        )
        ai_deduped.drop(
            columns=[c for c in ai_deduped.columns if c.endswith("_sc")],
            inplace=True,
        )
        ai_deduped["split_count"] = ai_deduped["split_count"].fillna(1.0)
        ai_deduped["task_comp"] /= ai_deduped["split_count"]
        if emp_col in ai_deduped.columns:
            ai_deduped[emp_col] /= ai_deduped["split_count"]

        agg_cols: dict = {"task_comp": "sum"}
        if emp_col in ai_deduped.columns:
            agg_cols[emp_col] = "sum"
        for c in ["broad_occ", "minor_occ_category", "major_occ_category", wage_col]:
            if c in ai_deduped.columns:
                agg_cols[c] = "first"

        ai_final = (
            ai_deduped
            .groupby(["O*NET-SOC 2019 Title", "task_normalized"], sort=False)
            .agg(agg_cols)
            .reset_index()
            .rename(columns={"O*NET-SOC 2019 Title": "title_current"})
        )

        eco_raw = load_eco_raw()
        if eco_raw is not None and "task_prop" in eco_raw.columns:
            tp = eco_raw[["title_current", "task_prop"]].drop_duplicates("title_current")
            ai_final = ai_final.merge(tp, on="title_current", how="left")
            ai_final["task_prop"] = ai_final["task_prop"].fillna(1.0).clip(lower=1.0)
            ai_final["task_comp"] /= ai_final["task_prop"]
            ai_final.drop(columns=["task_prop"], inplace=True)

        if eco_raw is not None:
            eco_groups = eco_raw[
                ["title_current", "broad_occ", "minor_occ_category", "major_occ_category"]
            ].drop_duplicates("title_current")
            for gc in ["broad_occ", "minor_occ_category", "major_occ_category"]:
                if gc in ai_final.columns:
                    mask = ai_final[gc].isna()
                    if mask.any():
                        fill = ai_final.loc[mask, ["title_current"]].merge(
                            eco_groups[["title_current", gc]],
                            on="title_current", how="left",
                        )
                        ai_final.loc[mask, gc] = fill[gc].values

        title_col_for_agg = "title_current"

    else:
        ai_final = dedup_and_compute(
            df, "title_current", emp_col, wage_col, method, use_auto_aug, use_adj_mean
        )
        title_col_for_agg = "title_current"

    result = aggregate_results(
        ai_final, eco_deduped, title_col_for_agg, agg_level, emp_col, wage_col
    )
    _dataset_cache[key] = result
    return result


# ── Multi-dataset combination ──────────────────────────────────────────────────

def combine_results(
    results:        list[Optional[pd.DataFrame]],
    group_col:      str,
    combine_method: str,
) -> pd.DataFrame:
    valid = [r for r in results if r is not None and not r.empty]
    if not valid:
        return pd.DataFrame()
    if len(valid) == 1:
        return valid[0].copy()

    metric_cols = ["pct_tasks_affected", "workers_affected", "wages_affected"]

    renamed = []
    for i, r in enumerate(valid):
        sub = r[[group_col] + metric_cols].copy()
        sub = sub.rename(columns={mc: f"{mc}_{i}" for mc in metric_cols})
        renamed.append(sub)

    combined = renamed[0]
    for sub in renamed[1:]:
        combined = combined.merge(sub, on=group_col, how="outer")

    for mc in metric_cols:
        cols = [f"{mc}_{i}" for i in range(len(valid))]
        if combine_method == "Max":
            combined[mc] = combined[cols].max(axis=1)
        else:
            combined[mc] = combined[cols].mean(axis=1)

    return combined[[group_col] + metric_cols].copy()


# ── Group data (mirrors data_loader.get_group_data) ───────────────────────────

def get_group_data(settings: dict) -> Optional[pd.DataFrame]:
    selected = settings.get("selected_datasets", [])
    if not selected:
        return None

    method        = settings["method"]
    use_auto_aug  = settings["use_auto_aug"]
    use_adj_mean  = settings["use_adj_mean"]
    physical_mode = settings["physical_mode"]
    geo           = settings["geo"]
    agg_level     = settings["agg_level"]
    sort_by       = settings["sort_by"]
    top_n         = settings["top_n"]
    combine       = settings.get("combine_method", "Average")

    results = []
    for name in selected:
        meta = DATASETS.get(name)
        if meta is None:
            continue
        effective_adj_mean = use_adj_mean and meta["is_mcp"]
        r = compute_single_dataset(
            file_path     = meta["file"],
            is_aei        = meta["is_aei"],
            method        = method,
            use_auto_aug  = use_auto_aug,
            use_adj_mean  = effective_adj_mean,
            physical_mode = physical_mode,
            geo           = geo,
            agg_level     = agg_level,
        )
        results.append(r)

    group_col = AGG_LEVEL_COL[agg_level]
    df = combine_results(results, group_col, combine)
    if df is None or df.empty:
        return None

    sort_col = SORT_COL_MAP.get(sort_by, "workers_affected")
    if sort_col not in df.columns:
        for c in ["workers_affected", "wages_affected", "pct_tasks_affected"]:
            if c in df.columns:
                sort_col = c
                break
        else:
            return df

    df = (
        df
        .sort_values(sort_col, ascending=False, na_position="last")
        .head(top_n)
        .sort_values(sort_col, ascending=True, na_position="first")
        .reset_index(drop=True)
    )
    return df
